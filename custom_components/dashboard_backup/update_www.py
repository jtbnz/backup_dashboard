"""Script to copy dashboard card files to www directory."""
import os
import shutil
import logging

_LOGGER = logging.getLogger(__name__)

def copy_card_files():
    """Copy dashboard card files to www directory."""
    try:
        # Get the current directory (should be custom_components/dashboard_backup)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the Home Assistant config directory (parent of custom_components)
        config_dir = os.path.dirname(os.path.dirname(current_dir))
        
        # Create the www/dashboard_backup directory if it doesn't exist
        www_dir = os.path.join(config_dir, "www", "dashboard_backup")
        os.makedirs(www_dir, exist_ok=True)
        
        # Copy the card files
        card_files = ["dashboard_card.js", "dashboard_card_direct.js"]
        for file in card_files:
            src = os.path.join(current_dir, file)
            dst = os.path.join(www_dir, file)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                _LOGGER.info("Copied %s to %s", src, dst)
            else:
                _LOGGER.warning("Source file %s does not exist", src)
        
        return True
    except Exception as ex:
        _LOGGER.error("Error copying card files: %s", str(ex))
        return False

if __name__ == "__main__":
    # This allows the script to be run directly for testing
    copy_card_files()
