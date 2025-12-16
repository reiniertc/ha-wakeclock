from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ATTR_SNOOZETIME, ATTR_NEXTALARM, DAYS
from .state import WakeClockState


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    add_entities: AddEntitiesCallback,
) -> None:
    state: WakeClockState = hass.data[DOMAIN]["state"]
    ent = WakeClockSwitch(hass, state)
    hass.data[DOMAIN]["entity_switch"] = ent
    add_entities([ent], update_before_add=True)


class WakeClockSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "WakeClock"
    _attr_icon = "mdi:alarm"
    _attr_unique_id = "wakeclock_switch"

    def __init__(self, hass: HomeAssistant, state: WakeClockState) -> None:
        self.hass = hass
        self._state = state

    @property
    def is_on(self) -> bool:
        return bool(self._state.enabled)

    @property
    def extra_state_attributes(self):
        attrs = {
            ATTR_SNOOZETIME: self._state.snoozetime,
            ATTR_NEXTALARM: self._state.nextalarm,
        }
        for d in DAYS:
            attrs[d] = getattr(self._state, d)
        return attrs

    async def async_turn_on(self, **kwargs) -> None:
        self._state.enabled = True
        self._state.recalc_next()
        await self.hass.data[DOMAIN]["save"]()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._state.enabled = False
        # nextalarm blijft staan; sensor blijft dus ook een timestamp tonen
        await self.hass.data[DOMAIN]["save"]()
        self.async_write_ha_state()
