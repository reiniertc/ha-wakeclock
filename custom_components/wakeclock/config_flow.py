"""Config flow for the WakeClock integration."""

from __future__ import annotations

import re
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, WEEKDAYS, CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES


_RE_HHMM = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _normalize_hhmm(value: str) -> str:
    """Return '' for empty/invalid, else normalized 'HH:MM'."""
    value = (value or "").strip()
    if not value:
        return ""
    return value if _RE_HHMM.match(value) else ""


def _weekday_labels() -> dict[str, str]:
    # Keep storage keys stable (mon..sun). Labels can be localized later via translations.
    return {
        "mon": "Maandag",
        "tue": "Dinsdag",
        "wed": "Woensdag",
        "thu": "Donderdag",
        "fri": "Vrijdag",
        "sat": "Zaterdag",
        "sun": "Zondag",
    }


def _build_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    labels = _weekday_labels()

    schema: dict = {
        vol.Optional(
            CONF_SNOOZE_MINUTES,
            default=int(defaults.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES)),
        ): vol.All(int, vol.Clamp(min=1, max=60)),
    }

    for wd in WEEKDAYS:
        schema[vol.Optional(wd, default=str(defaults.get(wd, "")))] = str

    return vol.Schema(schema)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WakeClock."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Create the WakeClock config entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned: dict[str, str | int] = {}

            # Snooze minutes
            try:
                snooze = int(user_input.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES))
                if snooze < 1 or snooze > 60:
                    raise ValueError
                cleaned[CONF_SNOOZE_MINUTES] = snooze
            except Exception:
                errors[CONF_SNOOZE_MINUTES] = "invalid_snooze"

            # Week schedule (mon..sun): accept HH:MM or empty
            for wd in WEEKDAYS:
                cleaned[wd] = _normalize_hhmm(user_input.get(wd, ""))

            if not errors:
                # Single-instance: prevent multiple entries
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                title = "WakeClock"
                return self.async_create_entry(title=title, data=cleaned)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
            description_placeholders=_weekday_labels(),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for WakeClock."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned: dict[str, str | int] = {}

            # Snooze minutes
            try:
                snooze = int(user_input.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES))
                if snooze < 1 or snooze > 60:
                    raise ValueError
                cleaned[CONF_SNOOZE_MINUTES] = snooze
            except Exception:
                errors[CONF_SNOOZE_MINUTES] = "invalid_snooze"

            # Week schedule
            for wd in WEEKDAYS:
                cleaned[wd] = _normalize_hhmm(user_input.get(wd, ""))

            if not errors:
                return self.async_create_entry(title="", data=cleaned)

        # Merge current config + current options as defaults
        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(defaults),
            errors=errors,
            description_placeholders=_weekday_labels(),
        )
