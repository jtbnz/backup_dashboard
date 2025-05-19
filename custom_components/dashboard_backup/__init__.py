"""The Dashboard Backup integration."""
from __future__ import annotations

import os
import logging
import voluptuous as vol
from datetime import datetime
import yaml
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv
from homeassistant.util import slugify
from homeassistant.exceptions import HomeAssistantError
# Try to import frontend functions, with fallbacks for different HA versions
try:
    from homeassistant.components.frontend import async_get_frontend_data
except ImportError:
    # Function doesn't exist in this version of HA
    async def async_get_frontend_data(hass):
        """Fallback implementation when async_get_frontend_data is not available."""
        return None
from homeassistant.components.lovelace import dashboard

from .const import (
    DOMAIN,
    CONF_BACKUP_PATH,
    DEFAULT_BACKUP_PATH,
    SERVICE_CREATE_BACKUP,
    SERVICE_RESTORE_BACKUP,
    ATTR_DASHBOARD_ID,
    ATTR_BACKUP_FILE,
    ATTR_TIMESTAMP,
    EVENT_BACKUP_CREATED,
    EVENT_BACKUP_RESTORED,
    EVENT_BACKUP_FAILED,
    EVENT_RESTORE_FAILED,
    ERROR_DASHBOARD_NOT_FOUND,
    ERROR_BACKUP_FAILED,
    ERROR_RESTORE_FAILED,
    ERROR_BACKUP_NOT_FOUND,
    ERROR_INVALID_YAML,
)
from .frontend import async_setup_frontend

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_BACKUP_PATH, default=DEFAULT_BACKUP_PATH): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

BACKUP_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DASHBOARD_ID): cv.string,
    }
)

RESTORE_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DASHBOARD_ID): cv.string,
        vol.Optional(ATTR_BACKUP_FILE): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Dashboard Backup component."""
    if DOMAIN in config:
        hass.data[DOMAIN] = config[DOMAIN]
    else:
        hass.data[DOMAIN] = {CONF_BACKUP_PATH: DEFAULT_BACKUP_PATH}

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Dashboard Backup from a config entry."""
    # Store the config entry data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Create backup directory if it doesn't exist
    backup_path = entry.data.get(CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH)
    full_backup_path = os.path.join(hass.config.config_dir, backup_path)
    os.makedirs(full_backup_path, exist_ok=True)

    # Register services
    register_services(hass)

    # Set up frontend
    await async_setup_frontend(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove the config entry data
    hass.data[DOMAIN].pop(entry.entry_id)

    # If there are no more config entries, remove the component data
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True


def register_services(hass: HomeAssistant) -> None:
    """Register component services."""

    @callback
    async def create_backup(call: ServiceCall) -> None:
        """Create a backup of the specified dashboard."""
        dashboard_id = call.data.get(ATTR_DASHBOARD_ID, "lovelace")
        
        try:
            # Get the dashboard configuration
            dashboard_config = await get_dashboard_config(hass, dashboard_id)
            
            if not dashboard_config:
                raise HomeAssistantError(ERROR_DASHBOARD_NOT_FOUND)
            
            # Create a timestamp for the backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get the backup directory
            backup_path = hass.data[DOMAIN].get(CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH)
            full_backup_path = os.path.join(hass.config.config_dir, backup_path)
            
            # Create the backup filename
            filename = f"dashboard_{dashboard_id}_{timestamp}.yaml"
            backup_file = os.path.join(full_backup_path, filename)
            
            # Save the dashboard configuration to the backup file
            with open(backup_file, "w") as f:
                yaml.dump(dashboard_config, f, default_flow_style=False)
            
            _LOGGER.info("Created backup of dashboard %s: %s", dashboard_id, backup_file)
            
            # Fire an event to notify of successful backup
            hass.bus.async_fire(
                EVENT_BACKUP_CREATED,
                {
                    ATTR_DASHBOARD_ID: dashboard_id,
                    ATTR_BACKUP_FILE: filename,
                    ATTR_TIMESTAMP: timestamp,
                },
            )
            
            # Show a notification
            hass.components.persistent_notification.async_create(
                f"Successfully created backup of dashboard '{dashboard_id}'.",
                title="Dashboard Backup",
            )
            
        except Exception as ex:
            _LOGGER.error("Failed to create backup: %s", str(ex))
            
            # Fire an event to notify of failed backup
            hass.bus.async_fire(
                EVENT_BACKUP_FAILED,
                {
                    ATTR_DASHBOARD_ID: dashboard_id,
                    "error": str(ex),
                },
            )
            
            # Show a notification
            hass.components.persistent_notification.async_create(
                f"Failed to create backup of dashboard '{dashboard_id}': {str(ex)}",
                title="Dashboard Backup Error",
            )
            
            raise HomeAssistantError(f"{ERROR_BACKUP_FAILED}: {str(ex)}")

    @callback
    async def restore_backup(call: ServiceCall) -> None:
        """Restore a dashboard from a backup."""
        dashboard_id = call.data.get(ATTR_DASHBOARD_ID, "lovelace")
        backup_file = call.data.get(ATTR_BACKUP_FILE)
        
        try:
            # Get the backup directory
            backup_path = hass.data[DOMAIN].get(CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH)
            full_backup_path = os.path.join(hass.config.config_dir, backup_path)
            
            # If no backup file is specified, use the most recent one
            if not backup_file:
                backup_files = [
                    f for f in os.listdir(full_backup_path)
                    if f.startswith(f"dashboard_{dashboard_id}_") and f.endswith(".yaml")
                ]
                
                if not backup_files:
                    raise HomeAssistantError(ERROR_BACKUP_NOT_FOUND)
                
                # Sort by timestamp (newest first)
                backup_files.sort(reverse=True)
                backup_file = backup_files[0]
            
            # Get the full path to the backup file
            backup_file_path = os.path.join(full_backup_path, backup_file)
            
            if not os.path.exists(backup_file_path):
                raise HomeAssistantError(ERROR_BACKUP_NOT_FOUND)
            
            # Load the dashboard configuration from the backup file
            with open(backup_file_path, "r") as f:
                try:
                    dashboard_config = yaml.safe_load(f)
                except yaml.YAMLError:
                    raise HomeAssistantError(ERROR_INVALID_YAML)
            
            # Restore the dashboard configuration
            await restore_dashboard_config(hass, dashboard_id, dashboard_config)
            
            _LOGGER.info("Restored dashboard %s from backup: %s", dashboard_id, backup_file)
            
            # Fire an event to notify of successful restore
            hass.bus.async_fire(
                EVENT_BACKUP_RESTORED,
                {
                    ATTR_DASHBOARD_ID: dashboard_id,
                    ATTR_BACKUP_FILE: backup_file,
                },
            )
            
            # Show a notification
            hass.components.persistent_notification.async_create(
                f"Successfully restored dashboard '{dashboard_id}' from backup.",
                title="Dashboard Backup",
            )
            
        except Exception as ex:
            _LOGGER.error("Failed to restore backup: %s", str(ex))
            
            # Fire an event to notify of failed restore
            hass.bus.async_fire(
                EVENT_RESTORE_FAILED,
                {
                    ATTR_DASHBOARD_ID: dashboard_id,
                    "error": str(ex),
                },
            )
            
            # Show a notification
            hass.components.persistent_notification.async_create(
                f"Failed to restore dashboard '{dashboard_id}': {str(ex)}",
                title="Dashboard Backup Error",
            )
            
            raise HomeAssistantError(f"{ERROR_RESTORE_FAILED}: {str(ex)}")

    # Register the services
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_BACKUP, create_backup, schema=BACKUP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESTORE_BACKUP, restore_backup, schema=RESTORE_SCHEMA
    )


async def get_dashboard_config(hass: HomeAssistant, dashboard_id: str) -> dict:
    """Get the configuration for a dashboard."""
    try:
        # Try to get the dashboard configuration from the lovelace component
        if hasattr(hass.data, "lovelace") and dashboard_id in hass.data["lovelace"]:
            lovelace_config = hass.data["lovelace"][dashboard_id].config
            if lovelace_config:
                return lovelace_config
        
        # If that fails, try to get it from the .storage directory
        storage_file = f".storage/lovelace.{dashboard_id}"
        if dashboard_id == "lovelace":
            storage_file = ".storage/lovelace"
        
        storage_path = os.path.join(hass.config.config_dir, storage_file)
        
        if os.path.exists(storage_path):
            with open(storage_path, "r") as f:
                storage_data = json.load(f)
                return storage_data.get("data", {})
        
        # If that fails, try to get it from the frontend data
        try:
            frontend_data = await async_get_frontend_data(hass)
            if frontend_data and "dashboards" in frontend_data:
                for dash_id, dash_data in frontend_data["dashboards"].items():
                    if dash_id == dashboard_id:
                        return dash_data
        except Exception as ex:
            _LOGGER.debug("Could not get frontend data: %s", str(ex))
            
        # Try to get it from the configuration.yaml file
        try:
            config_file = os.path.join(hass.config.config_dir, "ui-lovelace.yaml")
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    return config_data
        except Exception as ex:
            _LOGGER.debug("Could not get configuration from YAML file: %s", str(ex))
        
        # If all else fails, return None
        return None
    
    except Exception as ex:
        _LOGGER.error("Error getting dashboard configuration: %s", str(ex))
        return None


async def restore_dashboard_config(
    hass: HomeAssistant, dashboard_id: str, config: dict
) -> None:
    """Restore a dashboard configuration."""
    try:
        # Try to update the dashboard configuration through the lovelace component
        try:
            if hasattr(hass.data, "lovelace") and dashboard_id in hass.data["lovelace"]:
                await hass.data["lovelace"][dashboard_id].async_save_config(config)
                return
        except Exception as ex:
            _LOGGER.debug("Could not save config through lovelace component: %s", str(ex))
        
        # If that fails, try to update it in the .storage directory
        storage_file = f".storage/lovelace.{dashboard_id}"
        if dashboard_id == "lovelace":
            storage_file = ".storage/lovelace"
        
        storage_path = os.path.join(hass.config.config_dir, storage_file)
        
        if os.path.exists(storage_path):
            try:
                with open(storage_path, "r") as f:
                    storage_data = json.load(f)
                
                storage_data["data"] = config
                
                with open(storage_path, "w") as f:
                    json.dump(storage_data, f)
                
                # Try to reload the lovelace configuration
                try:
                    await hass.services.async_call("lovelace", "reload_resources")
                except Exception as ex:
                    _LOGGER.debug("Could not reload lovelace resources: %s", str(ex))
                    # Try alternative reload method
                    try:
                        await hass.services.async_call("frontend", "reload_themes")
                    except Exception:
                        pass
                return
            except Exception as ex:
                _LOGGER.debug("Could not update storage file: %s", str(ex))
        
        # If that fails, try to write to the YAML configuration file
        try:
            config_file = os.path.join(hass.config.config_dir, "ui-lovelace.yaml")
            if dashboard_id == "lovelace" and os.path.exists(config_file):
                with open(config_file, "w") as f:
                    yaml.dump(config, f, default_flow_style=False)
                return
        except Exception as ex:
            _LOGGER.debug("Could not write to YAML configuration file: %s", str(ex))
        
        # If all else fails, raise an error
        raise HomeAssistantError(f"Could not restore dashboard {dashboard_id}")
    
    except Exception as ex:
        _LOGGER.error("Error restoring dashboard configuration: %s", str(ex))
        raise
