"""Coordinator for WakeClock.

Responsibilities:
- Hold the configured weekly schedule (mon..sun -> "HH:MM" or "")
- Compute next alarm datetime (timezone-aware)
- Apply snooze increments (stackable) by adding snooze_minutes repeatedly
- Expose async methods used by services/entities
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, WEEKDAYS, CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES

_RE_HHMM = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _parse_hhmm(value: str) -> time | None:
    value = (value or "").strip()
    if not value or not _RE_HHMM.match(value):
        return None
    h = int(value[0:2])
    m = int(value[3:5])
    return time(hour=h, minute=m)


def _combine_local(d: datetime, t: time) -> datetime:
    """Combine date from d with time t as local, tz-aware datetime."""
    # dt_util.DEFAULT_TIME_ZONE is the HA configured tz.
    tz = dt_util.DEFAULT_TIME_ZONE
    combined = datetime(d.year, d.month, d.day, t.hour, t.minute, 0)
    return combined.replace(tzinfo=tz)


@dataclass
class WakeClockData:
    """Runtime data exposed by the coordinator."""
    schedule: dict[str, str]          # keys: mon..sun values: "HH:MM" or ""
    snooze_minutes: int
    next_alarm: datetime | None       # tz-aware
    override_active: bool             # true after snooze, until dismiss (or explicit clear)


class WakeClockCoordinator(DataUpdateCoordinator[WakeClockData]):
    """In-memory coordinator; no polling needed.

    It still subclasses DataUpdateCoordinator to give entities a standard way
    to subscribe to updates (async_set_updated_data).
    """

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass=hass,
            logger=None,  # optional; set in other modules if you want
            name=f"{DOMAIN}_coordinator",
            update_interval=None,  # push-based
        )

        schedule: dict[str, str] = {}
        for wd in WEEKDAYS:
            schedule[wd] = (config.get(wd, "") or "").strip()

        snooze = int(config.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES))

        self.data = WakeClockData(
            schedule=schedule,
            snooze_minutes=snooze,
            next_alarm=None,
            override_active=False,
        )

        # initial compute
        self.recalc_next(now=dt_util.now())

    # ---------- Public API (called by services / entity) ----------

    def recalc_next(self, now: datetime | None = None) -> datetime | None:
        """Compute next alarm from weekly schedule. Clears override flag."""
        now = now or dt_util.now()

        best: datetime | None = None
        for offset in range(0, 8):
            wd = WEEKDAYS[(now.weekday() + offset) % 7]  # Monday=0
            t = _parse_hhmm(self.data.schedule.get(wd, ""))
            if t is None:
                continue

            cand_day = now + timedelta(days=offset)
            cand = _combine_local(cand_day, t)

            # strictly in the future
            if cand <= now:
                continue

            if best is None or cand < best:
                best = cand

        self.data.next_alarm = best
        self.data.override_active = False
        self.async_set_updated_data(self.data)
        return best

    def snooze(self, now: datetime | None = None) -> datetime | None:
        """Add snooze_minutes to next alarm, stackable."""
        now = now or dt_util.now()

        if self.data.next_alarm is None or self.data.next_alarm <= now:
            base = now
        else:
            base = self.data.next_alarm

        self.data.next_alarm = base + timedelta(minutes=self.data.snooze_minutes)
        self.data.override_active = True
        self.async_set_updated_data(self.data)
        return self.data.next_alarm

    def dismiss(self, now: datetime | None = None) -> datetime | None:
        """Stop current alarm/override and return to schedule."""
        return self.recalc_next(now=now)

    def set_schedule(self, schedule_updates: dict[str, str], now: datetime | None = None) -> None:
        """Update one or more weekday times.

        schedule_updates keys: mon..sun, values: "HH:MM" or "" (disable that day).
        Invalid values are treated as "".
        """
        for wd, val in schedule_updates.items():
            if wd not in WEEKDAYS:
                continue
            v = (val or "").strip()
            self.data.schedule[wd] = v if _RE_HHMM.match(v) else ""

        # If not in override mode, immediately recalc. If in override, keep next_alarm as-is.
        if not self.data.override_active:
            self.recalc_next(now=now)
        else:
            self.async_set_updated_data(self.data)

    def set_snooze_minutes(self, minutes: int) -> None:
        minutes = int(minutes)
        if minutes < 1:
            minutes = 1
        if minutes > 60:
            minutes = 60
        self.data.snooze_minutes = minutes
        self.async_set_updated_data(self.data)

    # ---------- Optional: helper accessors ----------

    @property
    def next_alarm(self) -> datetime | None:
        return self.data.next_alarm

    @property
    def schedule(self) -> dict[str, str]:
        return dict(self.data.schedule)

    @property
    def snooze_minutes(self) -> int:
        return self.data.snooze_minutes

    @property
    def override_active(self) -> bool:
        return self.data.override_active
