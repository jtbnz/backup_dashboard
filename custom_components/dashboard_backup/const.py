"""Constants for the Dashboard Backup integration."""

DOMAIN = "dashboard_backup"
NAME = "Dashboard Backup"

# Service names
SERVICE_CREATE_BACKUP = "create_backup"
SERVICE_RESTORE_BACKUP = "restore_backup"

# Config
CONF_BACKUP_PATH = "backup_path"
DEFAULT_BACKUP_PATH = "dashboard_backups"

# Attributes
ATTR_DASHBOARD_ID = "dashboard_id"
ATTR_BACKUP_FILE = "backup_file"
ATTR_TIMESTAMP = "timestamp"

# Events
EVENT_BACKUP_CREATED = f"{DOMAIN}_backup_created"
EVENT_BACKUP_RESTORED = f"{DOMAIN}_backup_restored"
EVENT_BACKUP_FAILED = f"{DOMAIN}_backup_failed"
EVENT_RESTORE_FAILED = f"{DOMAIN}_restore_failed"

# Error messages
ERROR_DASHBOARD_NOT_FOUND = "Dashboard not found"
ERROR_BACKUP_FAILED = "Failed to create backup"
ERROR_RESTORE_FAILED = "Failed to restore backup"
ERROR_BACKUP_NOT_FOUND = "Backup file not found"
ERROR_INVALID_YAML = "Invalid YAML in backup file"
