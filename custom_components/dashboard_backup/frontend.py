"""Frontend for Dashboard Backup."""
import os
import logging
from typing import List

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "dashboard_card.js"


async def async_setup_frontend(hass: HomeAssistant) -> bool:
    """Set up the Dashboard Backup frontend."""
    # Get the URL for the dashboard card
    root_path = f"/custom_components/{DOMAIN}/"
    card_url = f"{root_path}{CARD_FILENAME}"

    # Try to add the card to the frontend
    try:
        # Try to import the function
        from homeassistant.components.frontend import add_extra_js_url
        
        # Add the card to the frontend
        add_extra_js_url(hass, card_url)
        _LOGGER.info("Added dashboard card to frontend: %s", card_url)
    except ImportError:
        # Function doesn't exist in this version of HA
        try:
            # Try alternative method
            from homeassistant.components.frontend import async_register_built_in_panel
            
            await async_register_built_in_panel(
                hass,
                "custom",
                "dashboard_backup",
                "mdi:backup-restore",
                "Dashboard Backup",
                js_url=card_url,
            )
            _LOGGER.info("Registered dashboard card as built-in panel: %s", card_url)
        except ImportError:
            # Neither method is available
            _LOGGER.warning(
                "Could not register dashboard card with frontend. "
                "You may need to manually add it to your resources."
            )

    return True
