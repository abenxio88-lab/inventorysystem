"""
PASSWORD RESET - Fix your password
"""
import json
import hashlib
import secrets

print("="*60)
print("  MINATAKA SPHERE - PASSWORD RESET")
print("="*60)
print()

# Load users
with open('data/users.json', 'r') as f:
    users = json.load(f)

print("📋 Existing users:")
for i, (email, data) in enumerate(users.items(), 1):
    print(f"  {i}. {email} ({data.get('role', 'unknown')})")

print()
print("🔑 Resetting password for FIRST user...")
print()

# Reset password for first user
first_email = list(users.keys())[0]
new_password = 'Amy2026Secure!'

# Create new hash
salt = secrets.token_hex(16)
hash_obj = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000)
password_hash = f'pbkdf2:sha256:100000${salt}${hash_obj.hex()}'

users[first_email] = {
    'role': 'admin',
    'algo': 'pbkdf2',
    'hash': password_hash
}

with open('data/users.json', 'w') as f:
    json.dump(users, f, indent=2)

print("="*60)
print("  ✅ PASSWORD RESET SUCCESSFUL!")
print("="*60)
print()
print(f"📧 Username: {first_email}")
print(f"🔑 Password: {new_password}")
print()
print("="*60)
print("  NOW RUN THE APP AND LOGIN WITH THESE!")
print("="*60)
print()
print("Next steps:")
print("1. Run: python just_login.py")
print("2. Login with the username and password above")
print("3. You're in!")
print()
