from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for WakeClock (UI-install only, no options, no UI fields)."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the config entry immediately."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="WakeClock",
            data={}
        )
