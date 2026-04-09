"""
Database Package for Mintaka Sphere Inventory System
=====================================================
Modular, industry-isolated database access layer.

ARCHITECTURE:
- base.py: Base classes and utilities (NO industry logic)
- core.py: Shared functionality (users, auth, settings, audit)
- industries/: Industry-specific database operations
  - retail.py: RETAIL database (simple products)
  - electronics.py: ELECTRONICS database (serial numbers, warranty)
  - pharma.py: PHARMA database (batches, expiry)

USAGE:
    # Get connection
    from db import get_connection
    conn = get_connection()
    
    # Use industry-specific repository
    from db.industries.electronics import ElectronicsProductRepository
    repo = ElectronicsProductRepository(conn)
    products = repo.fetch_products()
    
    # Or use the factory (recommended)
    from industry_factory import create_industry
    industry = create_industry("electronics", conn)
    products = industry["service"].get_all_products()
"""

import os
import sys

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import base infrastructure
from .base import DatabaseConnection, BaseRepository
from .core import UserRepository, AuditRepository, SettingsRepository

# Import legacy compatibility (will be removed in future)
try:
    from database import (
        init_database,
        migrate_database,
        get_db_cursor,
        get_connection as get_legacy_connection,
        DB_FILE,
        InventoryDB,
    )
except ImportError:
    pass

# Module-level connection (singleton)
_db_connection = None


def get_connection(db_path: str = None) -> DatabaseConnection:
    """
    Get the global database connection.
    Creates one if it doesn't exist.
    
    Args:
        db_path: Path to database file (optional)
        
    Returns:
        DatabaseConnection: Thread-safe connection manager
    """
    global _db_connection
    
    if _db_connection is None:
        if db_path is None:
            from utils import get_data_dir
            db_path = os.path.join(get_data_dir(), "inventory.db")
        
        _db_connection = DatabaseConnection(db_path)
    
    return _db_connection


def reset_connection():
    """Reset the global connection (useful for testing)."""
    global _db_connection
    if _db_connection:
        _db_connection.close_connection()
        _db_connection = None


__all__ = [
    # New modular system
    "DatabaseConnection",
    "BaseRepository",
    "UserRepository",
    "AuditRepository",
    "SettingsRepository",
    "get_connection",
    "reset_connection",
    # Legacy compatibility
    "init_database",
    "migrate_database",
    "get_db_cursor",
    "DB_FILE",
    "InventoryDB",
]

