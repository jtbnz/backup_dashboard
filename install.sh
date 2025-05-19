#!/bin/bash
# Installation script for Home Assistant Dashboard Backup

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Home Assistant Dashboard Backup Installer${NC}"
echo "This script will install the Dashboard Backup component to your Home Assistant installation."
echo ""

# Ask for Home Assistant config directory
read -p "Enter your Home Assistant config directory (e.g., /config or ~/.homeassistant): " HA_CONFIG_DIR

# Validate the directory
if [ ! -d "$HA_CONFIG_DIR" ]; then
    echo -e "${RED}Error: Directory $HA_CONFIG_DIR does not exist.${NC}"
    exit 1
fi

# Check if the directory is a Home Assistant config directory
if [ ! -f "$HA_CONFIG_DIR/configuration.yaml" ]; then
    echo -e "${YELLOW}Warning: configuration.yaml not found in $HA_CONFIG_DIR.${NC}"
    read -p "Are you sure this is your Home Assistant config directory? (y/n): " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo "Installation aborted."
        exit 1
    fi
fi

# Create custom_components directory if it doesn't exist
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
if [ ! -d "$CUSTOM_COMPONENTS_DIR" ]; then
    echo "Creating custom_components directory..."
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
fi

# Create dashboard_backup directory
COMPONENT_DIR="$CUSTOM_COMPONENTS_DIR/dashboard_backup"
if [ -d "$COMPONENT_DIR" ]; then
    echo -e "${YELLOW}Warning: dashboard_backup directory already exists.${NC}"
    read -p "Do you want to overwrite it? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Installation aborted."
        exit 1
    fi
    rm -rf "$COMPONENT_DIR"
fi

# Copy files
echo "Copying component files..."
mkdir -p "$COMPONENT_DIR"
cp -r custom_components/dashboard_backup/* "$COMPONENT_DIR/"

# Create backup directory
BACKUP_DIR="$HA_CONFIG_DIR/dashboard_backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating dashboard_backups directory..."
    mkdir -p "$BACKUP_DIR"
fi

# Set permissions
echo "Setting permissions..."
chmod -R 755 "$COMPONENT_DIR"

echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Configuration > Integrations"
echo "3. Add the Dashboard Backup integration"
echo "4. Add the Dashboard Backup card to your dashboard"
echo ""
echo "For more information, see the README.md file."
