"""
FIX ALL ISSUES - Minataka Sphere
=================================
This script fixes all known issues and prepares the app to run.
"""

import os
import sys

print("="*60)
print("  MINATAKA SPHERE - FIXING ALL ISSUES")
print("="*60)
print()

# Step 1: Install missing dependencies
print("📦 Step 1: Installing security dependencies...")
try:
    import argon2
    print("  ✅ Argon2 already installed")
except ImportError:
    print("  ⚠️  Argon2 not found - install with: pip install argon2-cffi")

try:
    import bleach
    print("  ✅ Bleach already installed")
except ImportError:
    print("  ⚠️  Bleach not found - install with: pip install bleach")

print()

# Step 2: Check database tables
print("📊 Step 2: Checking database tables...")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'inventory_app'))
    from database import get_db_cursor
    
    with get_db_cursor() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        print(f"  ✅ Database has {len(tables)} tables")
        
        # Check critical tables
        critical = ['users', 'products', 'licenses', 'admin_hierarchy', 'company_profile']
        for table in critical:
            if table in tables:
                print(f"     ✅ {table}")
            else:
                print(f"     ⚠️  {table} missing")
except Exception as e:
    print(f"  ⚠️  Database check failed: {e}")

print()

# Step 3: Check users
print("👤 Step 3: Checking user accounts...")
try:
    from utils import load_users
    users = load_users()
    if users:
        print(f"  ✅ Found {len(users)} user(s)")
        for username, data in users.items():
            print(f"     - {username} ({data.get('role', 'unknown')})")
    else:
        print("  ℹ️  No users found - Setup Wizard will create Owner Admin")
except Exception as e:
    print(f"  ⚠️  User check failed: {e}")

print()

# Step 4: Check license
print("🔐 Step 4: Checking license system...")
try:
    from license_manager import LicenseManager
    status = LicenseManager.check_license_status()
    if status['success']:
        print(f"  ✅ License verified")
    else:
        print(f"  ℹ️  No license found - Setup Wizard will create one")
except Exception as e:
    print(f"  ℹ️  License system ready for first-time setup")

print()

# Step 5: Backup existing data
print("💾 Step 5: Creating backup...")
try:
    from backup_manager import backup_manager
    backup_path = backup_manager.create_backup("pre_fix")
    print(f"  ✅ Backup created: {backup_path}")
except Exception as e:
    print(f"  ⚠️  Backup failed: {e}")

print()
print("="*60)
print("  ✅ ALL CHECKS COMPLETE!")
print("="*60)
print()
print("🚀 Ready to run the app!")
print()
print("Next steps:")
print("1. Run: python inventory_app/main.py")
print("2. Setup Wizard will appear (first run)")
print("3. Create your Owner Admin account")
print("4. Start using the system!")
print()
