import sqlite3
import os
import sys

# Ensure search path is correct
sys.path.append(os.getcwd())

try:
    from inventory_app.utils import get_data_dir
    data_dir = get_data_dir()
    db_path = os.path.join(data_dir, 'inventory.db')
    
    print(f"Bypassing Startup Wizard. Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Ensure settings table exists
    cur.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    
    # Set default values to skip the wizard
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('company_type', 'general_retail')")
    cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('company_name', 'My Business')")
    
    conn.commit()
    conn.close()
    print("SUCCESS: Startup Wizard bypassed. You can now login.")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
