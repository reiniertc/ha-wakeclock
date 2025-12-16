from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .services import async_load_state, async_save_state, async_register_services

PLATFORMS: list[str] = ["switch"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the WakeClock integration (no YAML config; UI via config flow)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WakeClock from a config entry (created via the UI)."""
    hass.data.setdefault(DOMAIN, {})

    state = await async_load_state(hass)
    hass.data[DOMAIN]["state"] = state

    async def _save() -> None:
        await async_save_state(hass, hass.data[DOMAIN]["state"])

    hass.data[DOMAIN]["save"] = _save

    def _notify_update() -> None:
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
    """Unload WakeClock."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
