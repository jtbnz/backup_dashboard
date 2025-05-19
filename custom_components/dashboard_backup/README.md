# Dashboard Backup for Home Assistant

A custom component for Home Assistant that allows you to back up and restore your dashboards with a simple button press.

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

1. Download the latest release
2. Extract the `dashboard_backup` folder from the archive
3. Copy the folder to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click the "+" button
3. Search for "Dashboard Backup"
4. Click on "Dashboard Backup"
5. Configure the backup path (optional)
6. Click "Submit"

## Usage

### Adding the Dashboard Card

1. Go to your dashboard
2. Click the "Edit Dashboard" button
3. Click the "+" button to add a new card
4. Scroll down to "Custom: Dashboard Backup Card"
5. Click on it to add it to your dashboard
6. Configure the card (optional)
7. Click "Save"

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

### Backup Failed

If a backup fails, check the Home Assistant logs for more information. Common causes include:

- Dashboard not found
- Permission issues with the backup directory
- Insufficient disk space

### Restore Failed

If a restore fails, check the Home Assistant logs for more information. Common causes include:

- Backup file not found
- Invalid YAML in the backup file
- Dashboard configuration has changed significantly since the backup was created

## License

This project is licensed under the MIT License - see the LICENSE file for details.
