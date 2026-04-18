"""
Diagnostic script to check user table and test login
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import get_db_cursor, init_database

print("=" * 80)
print("USER DATABASE DIAGNOSTIC")
print("=" * 80)

# Initialize database
try:
    init_database()
    print("\n✅ Database initialized")
except Exception as e:
    print(f"\n❌ Database initialization failed: {e}")
    sys.exit(1)

# Check user table structure
try:
    with get_db_cursor() as cur:
        cur.execute("PRAGMA table_info(users)")
        columns = cur.fetchall()
        
        print("\n📋 USERS TABLE STRUCTURE:")
        print("-" * 80)
        for col in columns:
            print(f"  {col['name']:20} {col['type']:20} {'NOT NULL' if col['notnull'] else 'NULLABLE':10} {'PK' if col['pk'] else ''}")
        
        # Check if password columns exist
        required_cols = ['username', 'password_hash', 'password_salt', 'password_algo', 'role', 'is_active', 'status']
        existing_cols = [col['name'] for col in columns]
        
        missing_cols = [c for c in required_cols if c not in existing_cols]
        if missing_cols:
            print(f"\n❌ Missing columns: {missing_cols}")
        else:
            print("\n✅ All required password columns exist")
        
except Exception as e:
    print(f"\n❌ Failed to check table structure: {e}")
    sys.exit(1)

# List all users
try:
    with get_db_cursor() as cur:
        cur.execute("SELECT id, username, role, is_active, status, password_algo, SUBSTR(password_hash, 1, 20) as hash_preview FROM users")
        users = cur.fetchall()
        
        print(f"\n👥 EXISTING USERS ({len(users)} users):")
        print("-" * 80)
        if users:
            for user in users:
                status_icon = "✅" if user['is_active'] and user['status'] == 'ACTIVE' else "❌"
                print(f"  {status_icon} ID: {user['id']:3} | Username: {user['username']:15} | Role: {user['role']:10} | Algo: {user['password_algo'] or 'N/A':10} | Status: {user['status']}")
        else:
            print("  ⚠️  No users found in database!")
            
except Exception as e:
    print(f"\n❌ Failed to list users: {e}")

# Test password verification
try:
    from database import verify_user_db
    
    print(f"\n🔐 TESTING LOGIN:")
    print("-" * 80)
    
    # Try admin login
    test_username = "admin"
    test_password = "admin123"
    
    print(f"  Testing: username='{test_username}', password='{test_password}'")
    success, role, user_id = verify_user_db(test_username, test_password)
    
    if success:
        print(f"  ✅ Login successful! Role: {role}, User ID: {user_id}")
    else:
        print(f"  ❌ Login failed!")
        
        # Try to manually check what's happening
        with get_db_cursor() as cur:
            cur.execute("SELECT id, username, password_hash, password_salt, password_algo, role, is_active, status FROM users WHERE username = ?", (test_username,))
            user = cur.fetchone()
            if user:
                print(f"\n  User found in database:")
                print(f"    ID: {user['id']}")
                print(f"    Username: {user['username']}")
                print(f"    Password Algo: {user['password_algo']}")
                print(f"    Password Hash (first 40): {user['password_hash'][:40] if user['password_hash'] else 'None'}")
                print(f"    Password Salt: {user['password_salt'][:20] if user['password_salt'] else 'None'}...")
                print(f"    Role: {user['role']}")
                print(f"    Is Active: {user['is_active']}")
                print(f"    Status: {user['status']}")
                
                # Test password hash manually
                import hashlib
                if user['password_algo'] == 'pbkdf2' and user['password_salt']:
                    computed_hash = hashlib.pbkdf2_hmac(
                        'sha256',
                        test_password.encode('utf-8'),
                        user['password_salt'].encode('utf-8'),
                        100_000
                    ).hex()
                    
                    print(f"\n  Password hash test:")
                    print(f"    Computed hash (first 40): {computed_hash[:40]}...")
                    print(f"    Stored hash (first 40):   {user['password_hash'][:40]}...")
                    print(f"    Match: {computed_hash == user['password_hash']}")
            else:
                print(f"  ⚠️  User '{test_username}' not found in database")
        
except Exception as e:
    import traceback
    print(f"\n❌ Login test failed: {e}")
    print(traceback.format_exc())

print("\n" + "=" * 80)
