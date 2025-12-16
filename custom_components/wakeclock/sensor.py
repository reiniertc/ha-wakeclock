from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .state import WakeClockState

_DOW_ABBR = ["ma", "di", "wo", "do", "vr", "za", "zo"]


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
    def suggested_object_id(self) -> str:
        return "wakeclock_nextalarm"

    @property
    def native_value(self) -> datetime | None:
        dt = self._state.get_nextalarm_dt()
        if dt is None:
            return None
        return dt_util.as_utc(dt)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        dt = self._state.get_nextalarm_dt()
        if dt is None:
            return {"nextalarm_label": ""}

        local = dt_util.as_local(dt)
        return {"nextalarm_label": f"{_DOW_ABBR[local.weekday()]} {local.strftime('%H:%M')}"}
