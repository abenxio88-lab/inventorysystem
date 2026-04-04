"""
PASSWORD RESET - Interactive CLI Tool

Usage:
    python reset_password.py

This tool will prompt you for:
    1. The email/username of the user to reset
    2. The new password (with strength validation)
    3. Confirmation of the new password

WARNING: This tool modifies data/users.json. Use with caution.
         After running, the user can log in with the new password.
"""
import json
import hashlib
import secrets
import sys
import os

from security import validate_password_strength, hash_password

def main():
    print("=" * 60)
    print("  MINTAKA SPHERE - PASSWORD RESET TOOL")
    print("=" * 60)
    print()

    # Check if users file exists
    users_file = os.path.join(os.path.dirname(__file__), "data", "users.json")
    if not os.path.exists(users_file):
        print("❌ Error: users.json not found in data directory.")
        print(f"   Expected path: {users_file}")
        sys.exit(1)

    # Load users
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
    except json.JSONDecodeError:
        print("❌ Error: users.json is corrupted. Please fix manually.")
        sys.exit(1)

    if not users:
        print("❌ Error: No users found in users.json.")
        sys.exit(1)

    # Show existing users
    print("📋 Existing users:")
    for i, (email, data) in enumerate(users.items(), 1):
        role = data.get('role', 'unknown')
        print(f"  {i}. {email} ({role})")
    print()

    # Get user to reset
    target_email = input("Enter the email/username to reset (or press Ctrl+C to cancel): ").strip()
    if not target_email:
        print("❌ No user specified. Aborting.")
        sys.exit(1)

    if target_email not in users:
        print(f"❌ Error: User '{target_email}' not found.")
        print("   Please check the list above and try again.")
        sys.exit(1)

    # Get new password
    print()
    print("🔑 Enter new password (min 8 chars, uppercase, lowercase, number, special):")
    
    # Use getpass if available, otherwise fallback to input
    try:
        import getpass
        new_password = getpass.getpass("New password: ")
        confirm_password = getpass.getpass("Confirm password: ")
    except (ImportError, Exception):
        new_password = input("New password: ")
        confirm_password = input("Confirm password: ")

    # Validate
    if new_password != confirm_password:
        print("❌ Error: Passwords do not match.")
        sys.exit(1)

    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        print(f"❌ Weak password: {error_msg}")
        print("   Password must be at least 8 characters with uppercase, lowercase, number, and special char.")
        sys.exit(1)

    # Hash and save
    try:
        password_hash = hash_password(new_password)
        users[target_email]['hash'] = password_hash
        users[target_email]['algo'] = 'pbkdf2'

        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)

        print()
        print("=" * 60)
        print("  ✅ PASSWORD RESET SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"📧 User: {target_email}")
        print(f"🔒 Password has been securely hashed and saved.")
        print()
        print("You can now run the app and log in with the new password.")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error saving password: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
