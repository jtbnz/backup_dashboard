#!/bin/bash
# Uninstallation script for Home Assistant Dashboard Backup

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Home Assistant Dashboard Backup Uninstaller${NC}"
echo "This script will remove the Dashboard Backup component from your Home Assistant installation."
echo ""

# Ask for Home Assistant config directory
read -p "Enter your Home Assistant config directory (e.g., /config or ~/.homeassistant): " HA_CONFIG_DIR

# Validate the directory
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${RED}Error: Directory $HA_CONFIG_DIR does not exist.${NC}"
    exit 1
fi

# Check if the component directory exists
COMPONENT_DIR="$HA_CONFIG_DIR/custom_components/dashboard_backup"
if [ ! -d "$COMPONENT_DIR" ]; then
    echo -e "${RED}Error: Dashboard Backup component not found in $HA_CONFIG_DIR/custom_components.${NC}"
    exit 1
fi

# Ask for confirmation
echo -e "${YELLOW}Warning: This will remove the Dashboard Backup component and all its files.${NC}"
read -p "Are you sure you want to continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Uninstallation aborted."
    exit 1
fi

# Remove the component directory
echo "Removing component files..."
rm -rf "$COMPONENT_DIR"

# Ask if the user wants to keep backup files
echo ""
read -p "Do you want to keep the dashboard backup files? (y/n): " KEEP_BACKUPS
if [ "$KEEP_BACKUPS" != "y" ] && [ "$KEEP_BACKUPS" != "Y" ]; then
    BACKUP_DIR="$HA_CONFIG_DIR/dashboard_backups"
    if [ -d "$BACKUP_DIR" ]; then
        echo "Removing backup files..."
        rm -rf "$BACKUP_DIR"
    fi
fi

echo -e "${GREEN}Uninstallation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Home Assistant"
echo "2. Remove any Dashboard Backup cards from your dashboards"
echo "3. Remove the Dashboard Backup integration from Configuration > Integrations"
echo ""
