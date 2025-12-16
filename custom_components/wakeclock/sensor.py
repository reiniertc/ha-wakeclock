from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .state import WakeClockState


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    add_entities: AddEntitiesCallback,
) -> None:
    state: WakeClockState = hass.data[DOMAIN]["state"]
    ent = WakeClockNextAlarmSensor(state)
    hass.data[DOMAIN]["entity_sensor"] = ent
    add_entities([ent], update_before_add=True)


class WakeClockNextAlarmSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Next alarm"
    _attr_unique_id = "wakeclock_nextalarm"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:alarm"

    def __init__(self, state: WakeClockState) -> None:
        self._state = state

    @property
    def native_value(self) -> datetime | None:
        # Switch uit => sensor "leeg"
        if not self._state.enabled:
            return None

        dt = self._state.get_nextalarm_dt()
        if dt is None:
            return None

        # Home Assistant verwacht tz-aware datetime voor timestamp sensors
        return dt_util.as_utc(dt)
