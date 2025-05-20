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
from .update_www import copy_card_files

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

    # Copy card files to www directory
    copy_card_files()
    
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
            # Determine the storage file path
            storage_file = get_storage_file_path(hass, dashboard_id)
            
            if not os.path.exists(storage_file):
                raise HomeAssistantError(f"Storage file not found: {storage_file}")
            
            # Create a timestamp for the backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Get the backup directory
            backup_path = hass.data[DOMAIN].get(CONF_BACKUP_PATH, DEFAULT_BACKUP_PATH)
            full_backup_path = os.path.join(hass.config.config_dir, backup_path)
            
            # Create the backup filename (JSON format)
            json_filename = f"dashboard_{dashboard_id}_{timestamp}.json"
            json_backup_file = os.path.join(full_backup_path, json_filename)
            
            # Copy the storage file directly
            with open(storage_file, "r") as src, open(json_backup_file, "w") as dst:
                dst.write(src.read())
            
            # Also create a YAML version for human readability
            yaml_filename = f"dashboard_{dashboard_id}_{timestamp}.yaml"
            yaml_backup_file = os.path.join(full_backup_path, yaml_filename)
            
            # Read the JSON file
            with open(storage_file, "r") as f:
                storage_data = json.load(f)
            
            # Extract the dashboard configuration
            dashboard_config = storage_data.get("data", {})
            
            # Save the dashboard configuration to the YAML file
            with open(yaml_backup_file, "w") as f:
                yaml.dump(dashboard_config, f, default_flow_style=False)
            
            _LOGGER.info("Created backup of dashboard %s: %s and %s", 
                        dashboard_id, json_backup_file, yaml_backup_file)
            
            # Fire an event to notify of successful backup
            hass.bus.async_fire(
                EVENT_BACKUP_CREATED,
                {
                    ATTR_DASHBOARD_ID: dashboard_id,
                    ATTR_BACKUP_FILE: json_filename,
                    ATTR_TIMESTAMP: timestamp,
                },
            )
            
            # Show a notification
            try:
                hass.components.persistent_notification.async_create(
                    f"Successfully created backup of dashboard '{dashboard_id}'.",
                    title="Dashboard Backup",
                )
            except AttributeError:
                # Fall back to using the service directly
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": f"Successfully created backup of dashboard '{dashboard_id}'.",
                        "title": "Dashboard Backup"
                    }
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
            try:
                hass.components.persistent_notification.async_create(
                    f"Failed to create backup of dashboard '{dashboard_id}': {str(ex)}",
                    title="Dashboard Backup Error",
                )
            except AttributeError:
                # Fall back to using the service directly
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": f"Failed to create backup of dashboard '{dashboard_id}': {str(ex)}",
                        "title": "Dashboard Backup Error"
                    }
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
                # Look for JSON backups first
                json_backup_files = [
                    f for f in os.listdir(full_backup_path)
                    if f.startswith(f"dashboard_{dashboard_id}_") and f.endswith(".json")
                ]
                
                if json_backup_files:
                    # Sort by timestamp (newest first)
                    json_backup_files.sort(reverse=True)
                    backup_file = json_backup_files[0]
                else:
                    # Fall back to YAML backups
                    yaml_backup_files = [
                        f for f in os.listdir(full_backup_path)
                        if f.startswith(f"dashboard_{dashboard_id}_") and f.endswith(".yaml")
                    ]
                    
                    if not yaml_backup_files:
                        raise HomeAssistantError(ERROR_BACKUP_NOT_FOUND)
                    
                    # Sort by timestamp (newest first)
                    yaml_backup_files.sort(reverse=True)
                    backup_file = yaml_backup_files[0]
            
            # Get the full path to the backup file
            backup_file_path = os.path.join(full_backup_path, backup_file)
            
            if not os.path.exists(backup_file_path):
                raise HomeAssistantError(ERROR_BACKUP_NOT_FOUND)
            
            # Determine the storage file path
            storage_file = get_storage_file_path(hass, dashboard_id)
            
            # If it's a JSON backup and ends with .json, directly copy it to the storage file
            if backup_file.endswith(".json"):
                _LOGGER.info("Restoring JSON backup directly to storage file")
                
                # Make a backup of the original file if it exists
                if os.path.exists(storage_file):
                    backup_storage = f"{storage_file}.bak"
                    with open(storage_file, "r") as src, open(backup_storage, "w") as dst:
                        dst.write(src.read())
                
                # Copy the backup file to the storage file
                with open(backup_file_path, "r") as src, open(storage_file, "w") as dst:
                    dst.write(src.read())
                
                # Try to reload the UI
                try:
                    _LOGGER.debug("Reloading UI")
                    await hass.services.async_call("lovelace", "reload")
                except Exception as ex:
                    _LOGGER.debug("Could not reload UI: %s", str(ex))
                
                _LOGGER.info("Restored dashboard %s from backup: %s", dashboard_id, backup_file)
            else:
                # For YAML backups, use the normal restore process
                _LOGGER.info("Restoring YAML backup through configuration API")
                
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
            try:
                hass.components.persistent_notification.async_create(
                    f"Successfully restored dashboard '{dashboard_id}' from backup.",
                    title="Dashboard Backup",
                )
            except AttributeError:
                # Fall back to using the service directly
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": f"Successfully restored dashboard '{dashboard_id}' from backup.",
                        "title": "Dashboard Backup"
                    }
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
            try:
                hass.components.persistent_notification.async_create(
                    f"Failed to restore dashboard '{dashboard_id}': {str(ex)}",
                    title="Dashboard Backup Error",
                )
            except AttributeError:
                # Fall back to using the service directly
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "message": f"Failed to restore dashboard '{dashboard_id}': {str(ex)}",
                        "title": "Dashboard Backup Error"
                    }
                )
            
            raise HomeAssistantError(f"{ERROR_RESTORE_FAILED}: {str(ex)}")

    # Register the services
    hass.services.async_register(
        DOMAIN, SERVICE_CREATE_BACKUP, create_backup, schema=BACKUP_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESTORE_BACKUP, restore_backup, schema=RESTORE_SCHEMA
    )


def get_storage_file_path(hass: HomeAssistant, dashboard_id: str) -> str:
    """Get the path to the storage file for a dashboard."""
    # Handle different dashboard ID formats
    if dashboard_id == "lovelace":
        # Main dashboard
        storage_file = ".storage/lovelace"
    elif dashboard_id.startswith("dashboard_"):
        # Dashboard with prefix already
        storage_file = f".storage/lovelace.{dashboard_id}"
    else:
        # Dashboard without prefix
        storage_file = f".storage/lovelace.dashboard_{dashboard_id}"
    
    # Get the full path
    storage_path = os.path.join(hass.config.config_dir, storage_file)
    
    # Check if the file exists
    if os.path.exists(storage_path):
        return storage_path
    
    # If not, try alternative formats
    alternatives = [
        f".storage/lovelace.{dashboard_id}",  # Without dashboard_ prefix
        f".storage/lovelace.dashboard_{dashboard_id}",  # With dashboard_ prefix
        f".storage/lovelace_{dashboard_id}",  # With underscore
        f".storage/lovelace-{dashboard_id}",  # With hyphen
    ]
    
    for alt in alternatives:
        alt_path = os.path.join(hass.config.config_dir, alt)
        if os.path.exists(alt_path):
            return alt_path
    
    # If no alternatives found, return the original path
    return storage_path


async def get_dashboard_config(hass: HomeAssistant, dashboard_id: str) -> dict:
    """Get the configuration for a dashboard."""
    try:
        # Method 1: Try to get the dashboard configuration directly from the lovelace API
        try:
            _LOGGER.debug("Trying to get config directly from lovelace API")
            # This is the most direct method to get the raw configuration
            from homeassistant.components.lovelace import dashboard
            
            # Get the dashboard instance
            if dashboard_id == "lovelace":
                # For the main dashboard
                dashboard_instance = await dashboard.get_default_config(hass)
            else:
                # For other dashboards
                dashboard_instance = await dashboard.get_dashboard_for_mode(hass, dashboard_id)
            
            if dashboard_instance and hasattr(dashboard_instance, "config"):
                config = dashboard_instance.config
                if config:
                    _LOGGER.info("Got dashboard config directly from lovelace API: %s", config)
                    return config
        except Exception as ex:
            _LOGGER.debug("Could not get config directly from lovelace API: %s", str(ex))
        
        # Method 2: Try to get the dashboard configuration directly from the states
        try:
            # This is another reliable method to get the current UI state
            state = hass.states.get(f"lovelace.{dashboard_id}")
            if state and state.attributes.get("config"):
                config = state.attributes.get("config")
                _LOGGER.info("Got dashboard config from state: %s", config)
                return config
        except Exception as ex:
            _LOGGER.debug("Could not get config from state: %s", str(ex))
        
        # Method 3: Try to get it from the lovelace component
        try:
            if "lovelace" in hass.data and dashboard_id in hass.data["lovelace"]:
                lovelace_config = hass.data["lovelace"][dashboard_id].config
                if lovelace_config:
                    _LOGGER.info("Got dashboard config from lovelace component: %s", lovelace_config)
                    return lovelace_config
        except Exception as ex:
            _LOGGER.debug("Could not get config from lovelace component: %s", str(ex))
        
        # Method 4: Try to get it directly from the lovelace service
        try:
            # Try to call the lovelace.get_config service
            from homeassistant.components.websocket_api import async_register_command
            
            # Create a temporary event to get the result
            event_name = f"dashboard_backup_get_config_{dashboard_id}"
            result = None
            
            # Define a callback to handle the result
            @callback
            def handle_result(event):
                nonlocal result
                result = event.data.get("config")
            
            # Register a temporary event listener
            remove_listener = hass.bus.async_listen(event_name, handle_result)
            
            # Call the service
            await hass.services.async_call(
                "lovelace",
                "get_config",
                {"dashboard_id": dashboard_id},
                blocking=True
            )
            
            # Remove the listener
            remove_listener()
            
            # Check if we got a result
            if result:
                _LOGGER.info("Got dashboard config from lovelace service: %s", result)
                return result
        except Exception as ex:
            _LOGGER.debug("Could not get config from lovelace service: %s", str(ex))
        
        # Method 5: Try to get it from the .storage directory
        try:
            storage_file = f".storage/lovelace.{dashboard_id}"
            if dashboard_id == "lovelace":
                storage_file = ".storage/lovelace"
            
            storage_path = os.path.join(hass.config.config_dir, storage_file)
            
            if os.path.exists(storage_path):
                with open(storage_path, "r") as f:
                    storage_data = json.load(f)
                    if "data" in storage_data:
                        _LOGGER.info("Got dashboard config from storage file: %s", storage_data.get("data"))
                        return storage_data.get("data", {})
        except Exception as ex:
            _LOGGER.debug("Could not get config from storage file: %s", str(ex))
        
        # Method 6: Try to get it from the frontend data
        try:
            frontend_data = await async_get_frontend_data(hass)
            if frontend_data and "dashboards" in frontend_data:
                for dash_id, dash_data in frontend_data["dashboards"].items():
                    if dash_id == dashboard_id:
                        _LOGGER.info("Got dashboard config from frontend data: %s", dash_data)
                        return dash_data
        except Exception as ex:
            _LOGGER.debug("Could not get frontend data: %s", str(ex))
            
        # Method 7: Try to get it from the configuration.yaml file
        try:
            config_file = os.path.join(hass.config.config_dir, "ui-lovelace.yaml")
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        _LOGGER.info("Got dashboard config from YAML file: %s", config_data)
                        return config_data
        except Exception as ex:
            _LOGGER.debug("Could not get configuration from YAML file: %s", str(ex))
        
        # Method 8: Try to get it from the browser storage
        try:
            # Try to get the current UI configuration from the browser storage
            browser_storage_file = os.path.join(hass.config.config_dir, ".storage", "browser_mod.browserEntities")
            if os.path.exists(browser_storage_file):
                with open(browser_storage_file, "r") as f:
                    browser_data = json.load(f)
                    if "data" in browser_data:
                        for entity_id, entity_data in browser_data["data"].items():
                            if "lovelace" in entity_data and dashboard_id in entity_data["lovelace"]:
                                _LOGGER.info("Got dashboard config from browser storage: %s", entity_data["lovelace"][dashboard_id])
                                return entity_data["lovelace"][dashboard_id]
        except Exception as ex:
            _LOGGER.debug("Could not get config from browser storage: %s", str(ex))
        
        # Method 9: Try to get it from the raw editor
        try:
            # Try to get the raw configuration from the editor
            raw_config_file = os.path.join(hass.config.config_dir, f"ui-lovelace.{dashboard_id}.yaml")
            if dashboard_id == "lovelace":
                raw_config_file = os.path.join(hass.config.config_dir, "ui-lovelace.yaml")
            
            if os.path.exists(raw_config_file):
                with open(raw_config_file, "r") as f:
                    raw_config = yaml.safe_load(f)
                    if raw_config:
                        _LOGGER.info("Got dashboard config from raw editor file: %s", raw_config)
                        return raw_config
        except Exception as ex:
            _LOGGER.debug("Could not get config from raw editor file: %s", str(ex))
        
        # Method 10: Create a dummy config if we can't find one
        try:
            # Create a dummy config if we can't find one
            _LOGGER.debug("Creating dummy dashboard config")
            return {
                "title": f"Dashboard {dashboard_id}",
                "views": [
                    {
                        "title": "Home",
                        "path": "home",
                        "cards": []
                    }
                ]
            }
        except Exception as ex:
            _LOGGER.debug("Could not create dummy config: %s", str(ex))
        
        # If all else fails, return None
        _LOGGER.warning("Could not find dashboard configuration for %s", dashboard_id)
        return None
    
    except Exception as ex:
        _LOGGER.error("Error getting dashboard configuration: %s", str(ex))
        return None


async def restore_dashboard_config(
    hass: HomeAssistant, dashboard_id: str, config: dict
) -> None:
    """Restore a dashboard configuration."""
    success = False
    
    try:
        # Method 1: Try to use the lovelace service to save the config
        try:
            _LOGGER.debug("Trying to save config using lovelace service")
            await hass.services.async_call(
                "lovelace",
                "save_config",
                {
                    "config": config,
                    "dashboard_id": dashboard_id
                }
            )
            _LOGGER.info("Saved config using lovelace service")
            success = True
        except Exception as ex:
            _LOGGER.debug("Could not save config using lovelace service: %s", str(ex))
        
        # Method 2: Try to update the dashboard configuration through the lovelace component
        if not success:
            try:
                _LOGGER.debug("Trying to save config through lovelace component")
                if "lovelace" in hass.data and dashboard_id in hass.data["lovelace"]:
                    await hass.data["lovelace"][dashboard_id].async_save_config(config)
                    _LOGGER.info("Saved config through lovelace component")
                    success = True
            except Exception as ex:
                _LOGGER.debug("Could not save config through lovelace component: %s", str(ex))
        
        # Method 3: Try to update it in the .storage directory
        if not success:
            try:
                _LOGGER.debug("Trying to save config to storage file")
                storage_file = f".storage/lovelace.{dashboard_id}"
                if dashboard_id == "lovelace":
                    storage_file = ".storage/lovelace"
                
                storage_path = os.path.join(hass.config.config_dir, storage_file)
                
                if os.path.exists(storage_path):
                    with open(storage_path, "r") as f:
                        storage_data = json.load(f)
                    
                    # Make a backup of the original file
                    backup_path = f"{storage_path}.bak"
                    with open(backup_path, "w") as f:
                        json.dump(storage_data, f)
                    
                    # Update the data
                    storage_data["data"] = config
                    
                    # Write the updated data
                    with open(storage_path, "w") as f:
                        json.dump(storage_data, f)
                    
                    _LOGGER.info("Saved config to storage file")
                    success = True
                    
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
            except Exception as ex:
                _LOGGER.debug("Could not update storage file: %s", str(ex))
        
        # Method 4: Try to write to the YAML configuration file
        if not success:
            try:
                _LOGGER.debug("Trying to save config to YAML file")
                config_file = os.path.join(hass.config.config_dir, "ui-lovelace.yaml")
                if dashboard_id == "lovelace":
                    # Make a backup of the original file if it exists
                    if os.path.exists(config_file):
                        backup_path = f"{config_file}.bak"
                        with open(config_file, "r") as src, open(backup_path, "w") as dst:
                            dst.write(src.read())
                    
                    # Write the updated config
                    with open(config_file, "w") as f:
                        yaml.dump(config, f, default_flow_style=False)
                    
                    _LOGGER.info("Saved config to YAML file")
                    success = True
            except Exception as ex:
                _LOGGER.debug("Could not write to YAML configuration file: %s", str(ex))
        
        # Method 5: Try to use the frontend API
        if not success:
            try:
                _LOGGER.debug("Trying to save config using frontend API")
                # This is a more direct approach that might work in some cases
                await hass.components.frontend.async_set_user_data(
                    "lovelace", 
                    {"config": config},
                    dashboard_id
                )
                _LOGGER.info("Saved config using frontend API")
                success = True
            except Exception as ex:
                _LOGGER.debug("Could not save config using frontend API: %s", str(ex))
        
        # If all methods failed, raise an error
        if not success:
            _LOGGER.error("All methods to restore dashboard %s failed", dashboard_id)
            raise HomeAssistantError(f"Could not restore dashboard {dashboard_id}")
        
        # Try to reload the UI
        try:
            _LOGGER.debug("Reloading UI")
            await hass.services.async_call("lovelace", "reload")
        except Exception as ex:
            _LOGGER.debug("Could not reload UI: %s", str(ex))
    
    except Exception as ex:
        _LOGGER.error("Error restoring dashboard configuration: %s", str(ex))
        raise
