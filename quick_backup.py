"""
Quick Backup Script
====================
Run this before making any changes to create a backup.
"""

import os
import sys
import shutil
from datetime import datetime

# Add inventory_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'inventory_app'))

try:
    from utils import get_data_dir, backup_data
    BACKUP_AVAILABLE = True
except Exception as e:
    print(f"Error importing backup functions: {e}")
    BACKUP_AVAILABLE = False


def create_backup():
    """Create a backup of all data."""
    if not BACKUP_AVAILABLE:
        print("❌ Backup functions not available")
        return False
    
    try:
        print("🔄 Creating backup...")
        backup_path = backup_data()
        print(f"✅ Backup created successfully!")
        print(f"📁 Location: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


def main():
    """Main backup function."""
    print("="*60)
    print("  MINATAKA SPHERE - QUICK BACKUP")
    print("="*60)
    print()
    
    # Create backup
    success = create_backup()
    
    print()
    print("="*60)
    if success:
        print("✅ BACKUP COMPLETE")
        print()
        print("Your data is safe! You can now proceed with updates.")
    else:
        print("❌ BACKUP FAILED")
        print()
        print("Please check the error message above and try again.")
        print("Do not proceed until backup is successful!")
    print("="*60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
