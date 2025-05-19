"""Frontend for Dashboard Backup."""
import os
import logging
from typing import List

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "dashboard_card.js"


async def async_setup_frontend(hass: HomeAssistant) -> bool:
    """Set up the Dashboard Backup frontend."""
    # Get the URL for the dashboard card
    root_path = f"/custom_components/{DOMAIN}/"
    card_url = f"{root_path}{CARD_FILENAME}"

    # Add the card to the frontend
    add_extra_js_url(hass, card_url)
    _LOGGER.info("Added dashboard card to frontend: %s", card_url)

    return True
