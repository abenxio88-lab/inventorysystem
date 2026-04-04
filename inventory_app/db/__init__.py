"""
Database Package for Mintaka Sphere Inventory System
=====================================================
Modular database access layer.

This package re-exports from the main database module for forward compatibility.
Eventually, database.py will be refactored into this package.

USAGE:
    from db import db, InventoryDB, init_database
    
    # Access the singleton
    products = db.fetch_products()
"""

# Re-export from main database module for now
import sys
import os

# Add parent directory to path to import database module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database import InventoryDB, init_database, migrate_database, get_db_cursor, DB_FILE

# Module-level singleton for convenience
db = InventoryDB()

__all__ = [
    "db",
    "InventoryDB",
    "get_db_cursor",
    "init_database",
    "migrate_database",
    "DB_FILE",
]
