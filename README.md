# Home Assistant Dashboard Backup

A custom component for Home Assistant that allows you to back up and restore your dashboards with a simple button press.

## Overview

Home Assistant Dashboard Backup provides a simple way to save and restore your carefully crafted dashboard configurations. With just a button press, you can create a backup of your current dashboard, allowing you to experiment with changes knowing you can easily revert if needed.

![Dashboard Backup Card](https://via.placeholder.com/400x200?text=Dashboard+Backup+Card)

## Features

- Back up your dashboard configuration with a single button press
- Restore your dashboard from the most recent backup
- Automatic timestamping of backups
- Simple configuration through the Home Assistant UI
- Custom dashboard card for easy access to backup and restore functions

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Go to HACS > Integrations
3. Click the "+" button
4. Search for "Dashboard Backup"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/dashboard_backup` directory from this repository to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click the "+" button
3. Search for "Dashboard Backup"
4. Click on "Dashboard Backup"
5. Configure the backup path (optional)
6. Click "Submit"

## Usage

### Adding the Dashboard Card

#### Automatic Method
1. Go to your dashboard
2. Click the "Edit Dashboard" button
3. Click the "+" button to add a new card
4. Scroll down to "Custom: Dashboard Backup Card"
5. Click on it to add it to your dashboard
6. Configure the card (optional)
7. Click "Save"

#### Manual Method (if the card doesn't appear in the card list)
If the card doesn't appear in the list of available cards, you'll need to add it as a resource first:

1. Go to Configuration > Lovelace Dashboards > Resources
2. Click the "+" button to add a new resource
3. Enter the URL: `/custom_components/dashboard_backup/dashboard_card.js`
4. Select Resource type: "JavaScript Module"
5. Click "Create"
6. Refresh your browser

After adding the resource, follow the steps in the Automatic Method to add the card to your dashboard.

#### Using the Service
You can also add the card as a resource using the service:

1. Go to Developer Tools > Services
2. Select service: `dashboard_backup.add_card_resource`
3. Click "Call Service"
4. Refresh your browser

### Card Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `title` | The title of the card | "Dashboard Backup" |
| `description` | The description text | "Backup and restore your dashboard configuration." |
| `dashboard_id` | The ID of the dashboard to back up/restore | Current dashboard |

Example configuration:

```yaml
type: 'custom:dashboard-backup-card'
title: 'My Dashboard Backup'
description: 'Backup and restore this dashboard'
dashboard_id: 'lovelace'
```

### Using the Services

You can also call the services directly:

#### dashboard_backup.create_backup

Creates a backup of the specified dashboard.

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `dashboard_id` | The ID of the dashboard to back up | No | "lovelace" |

#### dashboard_backup.restore_backup

Restores a dashboard from a backup.

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `dashboard_id` | The ID of the dashboard to restore | No | "lovelace" |
| `backup_file` | The filename of the backup to restore | No | Most recent backup |

## Backup Storage

Backups are stored in the `dashboard_backups` directory within your Home Assistant configuration directory by default. You can change this location in the integration settings.

Backup files are named using the format `dashboard_[dashboard_id]_[timestamp].yaml`.

## Troubleshooting

See the [Troubleshooting Guide](custom_components/dashboard_backup/README.md#troubleshooting) for common issues and solutions.

# Note: If the card doesn't appear in the list of available cards when adding a card to your dashboard,
# you'll need to add it as a resource first:
#
# 1. Go to Settings >  Dashboards > three dots top right - Resources
# 2. Click the "+" button to add a new resource
# 3. Enter the URL: `/custom_components/dashboard_backup/dashboard_card.js`
# 4. Select Resource type: "JavaScript Module"
# 5. Click "Create"
# 6. Refresh your browser
#
# Alternatively, you can use the service `dashboard_backup.add_card_resource` to add the card as a resource.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](custom_components/dashboard_backup/LICENSE) file for details.
