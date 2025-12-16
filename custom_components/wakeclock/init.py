from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .services import async_load_state, async_save_state, async_register_services

PLATFORMS = ["switch"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    state = await async_load_state(hass)
    hass.data[DOMAIN]["state"] = state

    async def _save():
        await async_save_state(hass, hass.data[DOMAIN]["state"])

    hass.data[DOMAIN]["save"] = _save

    def _notify_update():
        ent = hass.data[DOMAIN].get("entity")
        if ent is not None:
            ent.async_write_ha_state()

    async_register_services(
        hass,
        get_state=lambda: hass.data[DOMAIN]["state"],
        notify_update=_notify_update,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return ok
