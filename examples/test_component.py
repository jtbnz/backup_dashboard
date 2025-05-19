#!/usr/bin/env python3
"""
Test script for the Dashboard Backup component.
This script helps verify that the component is working correctly.
"""
import os
import sys
import argparse
import requests
import json
import yaml
from datetime import datetime

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test the Dashboard Backup component")
    parser.add_argument("--url", default="http://localhost:8123", help="Home Assistant URL")
    parser.add_argument("--token", required=True, help="Long-lived access token")
    parser.add_argument("--dashboard", default="lovelace", help="Dashboard ID to backup/restore")
    parser.add_argument("--action", choices=["backup", "restore", "list"], default="backup", 
                        help="Action to perform (backup, restore, or list backups)")
    parser.add_argument("--backup-file", help="Specific backup file to restore (for restore action)")
    return parser.parse_args()

def get_headers(token):
    """Get the headers for API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

def create_backup(args):
    """Create a backup of the specified dashboard."""
    url = f"{args.url}/api/services/dashboard_backup/create_backup"
    data = {"dashboard_id": args.dashboard}
    
    print(f"Creating backup of dashboard '{args.dashboard}'...")
    response = requests.post(url, headers=get_headers(args.token), json=data)
    
    if response.status_code == 200:
        print("Backup created successfully!")
        return True
    else:
        print(f"Error creating backup: {response.status_code} - {response.text}")
        return False

def restore_backup(args):
    """Restore a backup of the specified dashboard."""
    url = f"{args.url}/api/services/dashboard_backup/restore_backup"
    data = {"dashboard_id": args.dashboard}
    
    if args.backup_file:
        data["backup_file"] = args.backup_file
    
    print(f"Restoring dashboard '{args.dashboard}' from backup...")
    if args.backup_file:
        print(f"Using backup file: {args.backup_file}")
    else:
        print("Using most recent backup")
    
    response = requests.post(url, headers=get_headers(args.token), json=data)
    
    if response.status_code == 200:
        print("Backup restored successfully!")
        return True
    else:
        print(f"Error restoring backup: {response.status_code} - {response.text}")
        return False

def list_backups(args):
    """List available backups for the specified dashboard."""
    url = f"{args.url}/api/config"
    
    print(f"Fetching Home Assistant configuration...")
    response = requests.get(url, headers=get_headers(args.token))
    
    if response.status_code != 200:
        print(f"Error fetching configuration: {response.status_code} - {response.text}")
        return False
    
    config = response.json()
    config_dir = config.get("config_dir", "")
    
    # Try to find the backup directory
    backup_dirs = [
        os.path.join(config_dir, "dashboard_backups"),
        os.path.join(config_dir, "backup", "dashboard_backups"),
        os.path.join(config_dir, "backups", "dashboard_backups"),
    ]
    
    backup_files = []
    for backup_dir in backup_dirs:
        try:
            # Use the API to list files in the directory
            files_url = f"{args.url}/api/template"
            template = (
                "{{ states.sensor.date.last_updated }}"
                "{% set files = states('sensor.date') %}"
                f"{{% for file in states.sensor.date.attributes.files %}}"
                f"{{% if file.startswith('dashboard_{args.dashboard}_') and file.endswith('.yaml') %}}"
                "{{ file }},"
                f"{{% endif %}}"
                f"{{% endfor %}}"
            )
            template_data = {"template": template}
            
            files_response = requests.post(files_url, headers=get_headers(args.token), json=template_data)
            if files_response.status_code == 200:
                file_list = files_response.text.strip().split(",")
                if file_list and file_list[0]:
                    backup_files = file_list
                    break
        except Exception as e:
            print(f"Error listing files in {backup_dir}: {str(e)}")
    
    if not backup_files:
        print(f"No backups found for dashboard '{args.dashboard}'")
        return False
    
    print(f"\nAvailable backups for dashboard '{args.dashboard}':")
    for i, file in enumerate(sorted(backup_files, reverse=True)):
        if file:  # Skip empty entries
            # Try to parse the timestamp from the filename
            try:
                timestamp_str = file.split("_", 2)[2].split(".")[0]
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{i+1}. {file} (Created: {formatted_time})")
            except:
                print(f"{i+1}. {file}")
    
    return True

def main():
    """Main function."""
    args = parse_args()
    
    if args.action == "backup":
        create_backup(args)
    elif args.action == "restore":
        restore_backup(args)
    elif args.action == "list":
        list_backups(args)

if __name__ == "__main__":
    main()
