from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time
import re

from homeassistant.util import dt as dt_util

from .const import DAYS

_RE_HHMM = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

ALARM_DISABLED = "disabled"
ALARM_ENABLED = "enabled"
ALARM_RINGING = "ringing"
ALARM_SNOOZED = "snoozed"

ALARM_STATES = {ALARM_DISABLED, ALARM_ENABLED, ALARM_RINGING, ALARM_SNOOZED}


def _parse_hhmm(s: str) -> time | None:
    s = (s or "").strip()
    if not s or not _RE_HHMM.match(s):
        return None
    return time(hour=int(s[:2]), minute=int(s[3:5]))


def _weekday_index_to_day(i: int) -> str:
    # datetime.weekday(): mon=0..sun=6  -> DAYS: ma..zo
    return DAYS[i]


def _combine_local(d: datetime, t: time) -> datetime:
    tz = dt_util.DEFAULT_TIME_ZONE
    return datetime(d.year, d.month, d.day, t.hour, t.minute, 0, tzinfo=tz)


@dataclass
class WakeClockState:
    enabled: bool = True
    snoozetime: int = 9  # minutes
    nextalarm: str = ""  # ISO string (local tz, stored as isoformat)

    # weekschema (HH:MM of leeg)
    ma: str = ""
    di: str = ""
    wo: str = ""
    do: str = ""
    vr: str = ""
    za: str = ""
    zo: str = ""

    # functionele status (als attribuut op de switch)
    alarm_state: str = ALARM_DISABLED

    @staticmethod
    def from_dict(data: dict) -> "WakeClockState":
        s = WakeClockState()
        for k, v in (data or {}).items():
            if hasattr(s, k):
                setattr(s, k, v)

        # sanitize snoozetime
        try:
            s.snoozetime = int(s.snoozetime)
        except Exception:
            s.snoozetime = 9
        s.snoozetime = max(1, min(60, s.snoozetime))

        # sanitize schedule times
        for d in DAYS:
            val = (getattr(s, d) or "").strip()
            setattr(s, d, val if _RE_HHMM.match(val) else "")

        # sanitize nextalarm
        s.nextalarm = (s.nextalarm or "").strip()

        # sanitize alarm_state
        s.alarm_state = str(getattr(s, "alarm_state", ALARM_DISABLED) or ALARM_DISABLED)
        if s.alarm_state not in ALARM_STATES:
            s.alarm_state = ALARM_DISABLED

        # normalize alarm_state relative to enabled if needed
        if not bool(s.enabled):
            s.alarm_state = ALARM_DISABLED
        elif s.alarm_state == ALARM_DISABLED:
            s.alarm_state = ALARM_ENABLED

        return s

    def to_dict(self) -> dict:
        return asdict(self)

    def schedule_dict(self) -> dict[str, str]:
        return {d: getattr(self, d) for d in DAYS}

    def get_nextalarm_dt(self) -> datetime | None:
        if not self.nextalarm:
            return None
        try:
            dt = dt_util.parse_datetime(self.nextalarm)
            if dt is None:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
            return dt
        except Exception:
            return None

    def set_nextalarm_dt(self, dt: datetime | None) -> None:
        if dt is None:
            self.nextalarm = ""
        else:
            self.nextalarm = dt_util.as_local(dt).isoformat()

    def recalc_next(self, now: datetime | None = None) -> datetime | None:
        now = now or dt_util.now()
        best: datetime | None = None
        sched = self.schedule_dict()

        for offset in range(0, 8):
            cand_day = now + timedelta(days=offset)
            day_key = _weekday_index_to_day(cand_day.weekday())
            t = _parse_hhmm(sched.get(day_key, ""))
            if not t:
                continue

            cand = _combine_local(cand_day, t)
            if cand <= now:
                continue

            if best is None or cand < best:
                best = cand

        self.set_nextalarm_dt(best)

        # alarm_state: alleen “enabled/disabled” hier; ringing/snoozed komt via services/automations
        if not self.enabled:
            self.alarm_state = ALARM_DISABLED
        elif self.alarm_state == ALARM_DISABLED:
            self.alarm_state = ALARM_ENABLED

        return best

    def snooze(self, now: datetime | None = None) -> datetime | None:
        now = now or dt_util.now()
        cur = self.get_nextalarm_dt()
        base = cur if (cur is not None and cur > now) else now

        # rond af op minuut voor nette timestamps
        base = base.replace(second=0, microsecond=0)

        nxt = base + timedelta(minutes=self.snoozetime)
        self.set_nextalarm_dt(nxt)

        if self.enabled:
            self.alarm_state = ALARM_SNOOZED
        else:
            self.alarm_state = ALARM_DISABLED

        return nxt
