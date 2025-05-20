"""Frontend for Dashboard Backup."""
import os
import logging
from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.components.lovelace.resources import ResourceStorageCollection

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "dashboard_card.js"
CARD_DIRECT_FILENAME = "dashboard_card_direct.js"


async def async_setup_frontend(hass: HomeAssistant) -> bool:
    """Set up the Dashboard Backup frontend."""
    # Get the URL for the dashboard cards
    # Files in the www directory are accessible via /local/
    root_path = f"/local/dashboard_backup/"
    card_url = f"{root_path}{CARD_FILENAME}"
    card_direct_url = f"{root_path}{CARD_DIRECT_FILENAME}"

    # Try multiple methods to register the cards
    success = False
    
    # Method 1: Try to add the card to the frontend using add_extra_js_url
    try:
        from homeassistant.components.frontend import add_extra_js_url
        
        add_extra_js_url(hass, card_url)
        _LOGGER.info("Added dashboard card to frontend: %s", card_url)
        success = True
    except ImportError:
        _LOGGER.debug("Could not import add_extra_js_url")
    
    # Method 2: Try to register the card as a built-in panel
    if not success:
        try:
            from homeassistant.components.frontend import async_register_built_in_panel
            
            await async_register_built_in_panel(
                hass,
                "custom",
                "dashboard_backup",
                "mdi:backup-restore",  # Use Material Design Icon
                "Dashboard Backup",
                js_url=card_url,
            )
            _LOGGER.info("Registered dashboard card as built-in panel: %s", card_url)
            success = True
        except ImportError:
            _LOGGER.debug("Could not import async_register_built_in_panel")
    
    # Method 3: Try to add the card as a Lovelace resource
    if not success:
        try:
            # Try to add the standard card as a Lovelace resource
            resource_url = f"{root_path}{CARD_FILENAME}"
            direct_resource_url = f"{root_path}{CARD_DIRECT_FILENAME}"
            
            # Check if the resource already exists
            if hasattr(hass.data, "lovelace") and "resources" in hass.data["lovelace"]:
                resources = hass.data["lovelace"]["resources"]
                if isinstance(resources, ResourceStorageCollection):
                    # Check if the standard resource already exists
                    for resource in resources.async_items():
                        if resource["url"] == resource_url:
                            _LOGGER.info("Resource already exists: %s", resource_url)
                            success = True
                            break
                    
                    # Add the standard resource if it doesn't exist
                    if not success:
                        try:
                            await resources.async_create_item({
                                "url": resource_url,
                                "type": "module",
                                "res_type": "module",
                            })
                            _LOGGER.info("Added card as Lovelace resource: %s", resource_url)
                            success = True
                        except Exception as ex:
                            _LOGGER.debug("Could not add resource: %s", str(ex))
                    
                    # Also try to add the direct import version
                    direct_exists = False
                    for resource in resources.async_items():
                        if resource["url"] == direct_resource_url:
                            _LOGGER.info("Direct import resource already exists: %s", direct_resource_url)
                            direct_exists = True
                            break
                    
                    if not direct_exists:
                        try:
                            await resources.async_create_item({
                                "url": direct_resource_url,
                                "type": "module",
                                "res_type": "module",
                            })
                            _LOGGER.info("Added direct import card as Lovelace resource: %s", direct_resource_url)
                        except Exception as ex:
                            _LOGGER.debug("Could not add direct import resource: %s", str(ex))
        except Exception as ex:
            _LOGGER.debug("Could not add card as Lovelace resource: %s", str(ex))
    
    # Method 4: Always register a service to manually add the card as a resource
    async def add_card_resource(call):
        """Add the dashboard card as a Lovelace resource."""
        try:
            # Try to add the standard card first
            await hass.services.async_call(
                "lovelace", 
                "resources", 
                {
                    "url": card_url,
                    "type": "module",
                    "res_type": "module",
                }
            )
            _LOGGER.info("Added card as Lovelace resource via service call: %s", card_url)
            
            # Also try to add the direct import version
            try:
                await hass.services.async_call(
                    "lovelace", 
                    "resources", 
                    {
                        "url": card_direct_url,
                        "type": "module",
                        "res_type": "module",
                    }
                )
                _LOGGER.info("Added direct import card as Lovelace resource: %s", card_direct_url)
            except Exception as ex:
                _LOGGER.debug("Could not add direct import card as resource: %s", str(ex))
                
        except Exception as ex:
            _LOGGER.error("Could not add card as Lovelace resource: %s", str(ex))
            
            # If the standard card fails, try the direct import version
            try:
                await hass.services.async_call(
                    "lovelace", 
                    "resources", 
                    {
                        "url": card_direct_url,
                        "type": "module",
                        "res_type": "module",
                    }
                )
                _LOGGER.info("Added direct import card as Lovelace resource: %s", card_direct_url)
            except Exception as ex2:
                _LOGGER.error("Could not add direct import card as resource: %s", str(ex2))
    
    async_register_admin_service(
        hass,
        DOMAIN,
        "add_card_resource",
        add_card_resource,
    )
    _LOGGER.info(
        "Registered service dashboard_backup.add_card_resource to manually add the card as a resource"
    )
    
    # If all methods failed, log a warning
    if not success:
        _LOGGER.warning(
            "Could not register dashboard card with frontend. "
            "You may need to manually add it to your resources: %s or %s", 
            card_url, card_direct_url
        )
        # Add a persistent notification to inform the user
        hass.components.persistent_notification.async_create(
            f"The Dashboard Backup card could not be automatically registered. "
            f"Please add one of the following options manually as a Lovelace resource:\n\n"
            f"Option 1 (Standard):\n"
            f"URL: {card_url}\n"
            f"Resource type: JavaScript Module\n\n"
            f"Option 2 (Direct Import - try this if Option 1 doesn't work):\n"
            f"URL: {card_direct_url}\n"
            f"Resource type: JavaScript Module\n\n"
            f"You can do this in Configuration > Lovelace Dashboards > Resources.\n\n"
            f"Alternatively, use the service dashboard_backup.add_card_resource to add both resources automatically.",
            title="Dashboard Backup Card Not Registered",
            notification_id="dashboard_backup_card_not_registered",
        )

    return True
