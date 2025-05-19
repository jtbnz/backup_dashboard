"""Config flow for Dashboard Backup integration."""
from __future__ import annotations

import os
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    # Validate that the backup path is valid
    backup_path = data.get(CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH)
    
    # Return validated data
    return {CONF_BACKUP_PATH: backup_path}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dashboard Backup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title="Dashboard Backup", data=info)
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        # Provide default values
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_BACKUP_PATH, default=DEFAULT_BACKUP_PATH
                ): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            try:
                return self.async_create_entry(title="", data=user_input)
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"

        # Get current values from config entry
        backup_path = self.config_entry.options.get(
            CONF_BACKUP_PATH,
            self.config_entry.data.get(CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH),
        )

        # Provide default values
        data_schema = vol.Schema(
            {
                vol.Optional(CONF_BACKUP_PATH, default=backup_path): cv.string,
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=data_schema, errors=errors
        )
