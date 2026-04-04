"""
Mintaka Sphere - Database Migration: Industry Type Support
===========================================================
Migration script to add industry_type configuration to the database.

This migration:
1. Adds 'industry_type' setting to the settings table
2. Adds 'enabled_verticals' setting for multi-vertical support
3. Creates 'vertical_configs' table for vertical-specific settings

Safe to run multiple times (idempotent).
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Import database connection utilities - FIXED FOR inventory_app folder
try:
    from database import DB_FILE, get_connection
    # Use a helper to get a safe connection for migration
    def get_migration_conn():
        import sqlite3
        return sqlite3.connect(DB_FILE)
except (ImportError, ModuleNotFoundError):
    # Fallback: direct connection
    import os
    import sqlite3
    DB_FILE = os.path.join(os.path.dirname(__file__), 'data', 'inventory.db')
    
    def get_migration_conn():
        return sqlite3.connect(DB_FILE)
    
    def get_connection():
        return sqlite3.connect(DB_FILE)


# ============================================
# UNIFIED INDUSTRY METADATA (Single Source of Truth)
# ============================================
INDUSTRIES = {
    'retail': {
        'name': 'General Retail',
        'icon': '🛒',
        'desc': 'Standard retail inventory and POS',
        'color': '#2563EB',  # Royal Blue
        'vertical': None
    },
    'pharma': {
        'name': 'Pharmacy',
        'icon': '💊',
        'desc': 'Medical supplies and batch tracking',
        'color': '#10B981',  # Emerald
        'vertical': 'pharma'
    },
    'electronics': {
        'name': 'Electronics',
        'icon': '📱',
        'desc': 'IMEI/Serial tracking and repairs',
        'color': '#8B5CF6',  # Violet
        'vertical': 'electronics'
    },
    'lease_rental': {
        'name': 'Lease & Rental',
        'icon': '📋',
        'desc': 'Equipment and property rental',
        'color': '#F59E0B',  # Amber
        'vertical': 'lease_rental'
    },
    'manufacturing': {
        'name': 'Manufacturing',
        'icon': '🏭',
        'desc': 'BOM and production tracking',
        'color': '#F59E0B',  # Amber
        'vertical': 'manufacturing'
    },
    'healthcare': {
        'name': 'Healthcare',
        'icon': '🏥',
        'desc': 'Patient billing and medical records',
        'color': '#EF4444',  # Red
        'vertical': 'healthcare'
    }
}

DEFAULT_INDUSTRY = 'retail'


def get_industry_metadata(industry_id: str = None) -> dict:
    """Get metadata for a specific industry or all industries."""
    if industry_id is None:
        return INDUSTRIES
    return INDUSTRIES.get(industry_id.lower(), INDUSTRIES[DEFAULT_INDUSTRY])


MIGRATION_VERSION = 4  # Incremented for standardized IDs
MIGRATION_NAME = "standardize_industry_ids"


def run_migration() -> bool:
    """
    Run the industry type migration
    
    Returns:
        True if migration succeeded, False otherwise
    """
    logger.info(f"Starting migration: {MIGRATION_NAME}")
    
    conn = None
    try:
        conn = get_migration_conn()
        cursor = conn.cursor()
        
        # Ensure schema_version table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if version exists
        cursor.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO schema_version (version) VALUES (0)")
            current_version = 0
        else:
            current_version = row[0]
            
        if current_version >= MIGRATION_VERSION:
            logger.info(f"Migration {MIGRATION_NAME} already applied (version {current_version})")
            return True
        
        # Step 1: Add industry_type to settings table (if not exists)
        logger.info("Adding industry_type setting...")
        _add_setting_if_not_exists(
            cursor,
            key='industry_type',
            value=DEFAULT_INDUSTRY,
            category='business',
            description='Primary business type/industry'
        )
        
        # Step 2: Standardize existing industry names
        cursor.execute("SELECT value FROM settings WHERE key = 'industry_type'")
        current_val_row = cursor.fetchone()
        if current_val_row:
            old_val = current_val_row[0]
            new_val = old_val.lower().replace(' ', '_').replace('&', '').replace('__', '_')
            # Fix specific mismatches
            if new_val == 'pharmacy': new_val = 'pharma'
            if new_val not in INDUSTRIES:
                new_val = DEFAULT_INDUSTRY
            
            if old_val != new_val:
                logger.info(f"Updating industry from '{old_val}' to '{new_val}'")
                cursor.execute("UPDATE settings SET value = ? WHERE key = 'industry_type'", (new_val,))
        
        # Step 3: Add enabled_verticals setting
        logger.info("Adding enabled_verticals setting...")
        _add_setting_if_not_exists(
            cursor,
            key='enabled_verticals',
            value='["retail"]',  # Default to retail only
            category='business',
            description='JSON array of enabled vertical module names'
        )
        
        # Step 4: Create vertical_configs table for vertical-specific settings
        logger.info("Creating vertical_configs table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vertical_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vertical_name TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                config_type TEXT DEFAULT 'string',
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vertical_name, config_key)
            )
        """)
        
        # Insert default vertical configurations
        default_vertical_configs = [
            ('pharma', 'enable_batch_tracking', '1', 'boolean', 'Enable batch number tracking'),
            ('pharma', 'enable_expiry_alerts', '1', 'boolean', 'Enable expiry date alerts'),
            ('pharma', 'expiry_alert_days', '30', 'integer', 'Days before expiry to alert'),
            ('lease_rental', 'enable_late_fees', '1', 'boolean', 'Enable automatic late fee calculation'),
            ('lease_rental', 'default_late_fee_percent', '5', 'float', 'Default late fee percentage'),
            ('retail', 'enable_loyalty_program', '1', 'boolean', 'Enable customer loyalty program'),
            ('retail', 'loyalty_points_per_dollar', '1', 'integer', 'Loyalty points earned per dollar'),
        ]
        
        for config in default_vertical_configs:
            cursor.execute("""
                INSERT OR IGNORE INTO vertical_configs 
                (vertical_name, config_key, config_value, config_type, description)
                VALUES (?, ?, ?, ?, ?)
            """, config)
        
        # Step 5: Update schema version
        cursor.execute("UPDATE schema_version SET version = ?", (MIGRATION_VERSION,))
        
        conn.commit()
        logger.info(f"Migration {MIGRATION_NAME} completed successfully")
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration {MIGRATION_NAME} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        if conn:
            conn.close()


def _add_setting_if_not_exists(
    cursor,
    key: str,
    value: str,
    category: str,
    description: str
) -> None:
    """Add a setting to the settings table if it doesn't exist"""
    try:
        # Check if settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # Check if setting exists
        cursor.execute("SELECT id FROM settings WHERE key = ?", (key,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO settings (key, value, category, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, category, description))
            logger.info(f"Added setting: {key}")
        else:
            logger.info(f"Setting already exists: {key}")
    except Exception as e:
        logger.warning(f"Could not add setting {key}: {e}")


def get_industry_type() -> str:
    """
    Get the current industry type id from database.
    Delegates to industry_service — single source of truth.
    """
    try:
        from industry_service import get_current_industry_id
        return get_current_industry_id()
    except Exception as e:
        logger.debug(f"Error getting industry_type via service: {e}")
        return DEFAULT_INDUSTRY


def set_industry_type(industry_id: str) -> bool:
    """
    Set the industry type in database.
    Delegates to industry_service — handles validation, persistence, tab reload, AppState sync.
    """
    try:
        from industry_service import change_industry
        return change_industry(industry_id)
    except Exception as e:
        logger.error(f"Error setting industry_type via service: {e}")
        return False


if __name__ == "__main__":
    # Run migration when executed directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        print(f"  Current Industry: {get_industry_type()}")
    else:
        print("❌ Migration failed!")

