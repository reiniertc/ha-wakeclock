from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORE_KEY, STORE_VERSION, DAYS
from .state import WakeClockState, _RE_HHMM

def _day_schema():
    return vol.In(DAYS)

def _time_schema():
    # allow "" to clear, or HH:MM
    def _v(v):
        v = (v or "").strip()
        if v == "":
            return ""
        if not _RE_HHMM.match(v):
            raise vol.Invalid("time must be HH:MM or empty")
        return v
    return _v

async def async_load_state(hass: HomeAssistant) -> WakeClockState:
    store = Store(hass, STORE_VERSION, STORE_KEY)
    data = await store.async_load() or {}
    return WakeClockState.from_dict(data)

async def async_save_state(hass: HomeAssistant, state: WakeClockState) -> None:
    store = Store(hass, STORE_VERSION, STORE_KEY)
    await store.async_save(state.to_dict())

def async_register_services(hass: HomeAssistant, get_state, notify_update):
    # get_state(): WakeClockState
    # notify_update(): schedule entity state write + persist

    async def _persist_and_update(state: WakeClockState):
        await async_save_state(hass, state)
        notify_update()

    async def set_day_time(call: ServiceCall):
        state = get_state()
        day = call.data["day"]
        t = call.data.get("time", "")
        setattr(state, day, t)
        if state.enabled:
            state.recalc_next()
        await _persist_and_update(state)

    async def set_schedule(call: ServiceCall):
        state = get_state()
        sched = call.data.get("schedule", {})
        for day, t in sched.items():
            if day in DAYS:
                setattr(state, day, (t or "").strip() if _RE_HHMM.match((t or "").strip()) else "")
        if state.enabled:
            state.recalc_next()
        await _persist_and_update(state)

    async def set_snooze(call: ServiceCall):
        state = get_state()
        minutes = int(call.data["minutes"])
        state.snoozetime = max(1, min(60, minutes))
        await _persist_and_update(state)

    async def recalc_next(call: ServiceCall):
        state = get_state()
        if state.enabled:
            state.recalc_next()
        await _persist_and_update(state)

    async def snooze(call: ServiceCall):
        state = get_state()
        if state.enabled:
            state.snooze()
        await _persist_and_update(state)

    async def dismiss(call: ServiceCall):
        state = get_state()
        if state.enabled:
            state.recalc_next()
        await _persist_and_update(state)

    hass.services.async_register(
        DOMAIN,
        "set_day_time",
        set_day_time,
        schema=vol.Schema({
            vol.Required("day"): _day_schema(),
            vol.Required("time", default=""): _time_schema(),
        }),
    )

    hass.services.async_register(
        DOMAIN,
        "set_schedule",
        set_schedule,
        schema=vol.Schema({
            vol.Required("schedule"): dict,  # validated lightly inside
        }),
    )

    hass.services.async_register(
        DOMAIN,
        "set_snooze",
        set_snooze,
        schema=vol.Schema({
            vol.Required("minutes"): vol.All(cv.positive_int, vol.Clamp(min=1, max=60)),
        }),
    )

    hass.services.async_register(DOMAIN, "recalc_next", recalc_next)
    hass.services.async_register(DOMAIN, "snooze", snooze)
    hass.services.async_register(DOMAIN, "dismiss", dismiss)
