"""
Enhanced SQLite Database Module
================================
Enterprise-grade database with encryption support, multi-location, 
supplier management, and audit trails.

All features work OFFLINE. SQLite is built into Python.
"""

import sqlite3
import os
import json
import logging
import threading
from datetime import datetime
from contextlib import contextmanager

try:
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir

# Database file path
DB_FILE = os.path.join(get_data_dir(), "inventory.db")

# Thread-local storage for database connections
_local = threading.local()

# Schema version for migrations
SCHEMA_VERSION = 2


def get_connection():
    """Get thread-local database connection."""
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
        # Enable foreign keys
        _local.connection.execute("PRAGMA foreign_keys = ON")
    return _local.connection


def close_connection():
    """Close thread-local database connection."""
    if hasattr(_local, 'connection') and _local.connection is not None:
        _local.connection.close()
        _local.connection = None


@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.exception("Database error")
        raise e


def init_database():
    """
    Initialize the database with all required tables.
    Creates tables if they don't exist.
    """
    with get_db_cursor() as cur:
        # Check if schema exists
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_version'
        """)
        exists = cur.fetchone()
        
        if exists:
            logging.info("Database already initialized, checking for migrations")
            # We still need to check for migrations even if initialized
            migrate_database()
            return
        
        # Create schema version table
        cur.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============================================
        # CORE TABLES
        # ============================================
        
        # Users table (enhanced)
        cur.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT,
                password_algo TEXT DEFAULT 'pbkdf2',
                security_pin_hash TEXT,
                role TEXT DEFAULT 'staff',
                email TEXT,
                full_name TEXT,
                phone TEXT,
                department TEXT,
                is_active INTEGER DEFAULT 1,
                status TEXT DEFAULT 'ACTIVE',
                device_fingerprint TEXT,
                ip_address TEXT,
                authorized_by TEXT,
                authorized_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Locations/Warehouses table
        cur.execute("""
            CREATE TABLE locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT DEFAULT 'warehouse',
                address TEXT,
                city TEXT,
                country TEXT,
                phone TEXT,
                email TEXT,
                manager_id INTEGER,
                capacity INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES users(id)
            )
        """)
        
        # Categories table
        cur.execute("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
        """)
        
        # Suppliers table
        cur.execute("""
            CREATE TABLE suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                mobile TEXT,
                address TEXT,
                city TEXT,
                country TEXT,
                gst_number TEXT,
                tax_id TEXT,
                payment_terms TEXT,
                lead_time_days INTEGER DEFAULT 7,
                rating INTEGER DEFAULT 5,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Products table (enhanced for electronics)
        cur.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE,
                model TEXT NOT NULL,
                category_id INTEGER,
                supplier_id INTEGER,
                barcode TEXT,
                qr_code TEXT,
                
                -- Pricing
                purchase_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                cost_avg REAL DEFAULT 0,
                
                -- Stock control
                stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 5,
                reorder_point INTEGER DEFAULT 10,
                max_stock INTEGER,
                
                -- Electronics specific
                brand TEXT,
                serial_number TEXT,
                ram TEXT,
                storage TEXT,
                screen_size TEXT,
                camera TEXT,
                battery TEXT,
                color TEXT,
                warranty_months INTEGER,
                warranty_expiry TEXT,
                
                -- Status
                status TEXT DEFAULT 'active',
                condition TEXT DEFAULT 'new',
                
                -- Location
                default_location_id INTEGER,
                rack_location TEXT,
                shelf_location TEXT,
                
                -- Metadata
                description TEXT,
                notes TEXT,
                images TEXT,
                specifications TEXT,
                
                -- Timestamps
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                
                FOREIGN KEY (category_id) REFERENCES categories(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (default_location_id) REFERENCES locations(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Product stock by location
        cur.execute("""
            CREATE TABLE product_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 0,
                reserved INTEGER DEFAULT 0,
                available INTEGER GENERATED ALWAYS AS (quantity - reserved) STORED,
                last_counted TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, location_id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (location_id) REFERENCES locations(id)
            )
        """)
        
        # Serial numbers tracking
        cur.execute("""
            CREATE TABLE serial_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                serial_number TEXT NOT NULL,
                status TEXT DEFAULT 'in_stock',
                purchase_date TEXT,
                warranty_start TEXT,
                warranty_end TEXT,
                sold_date TEXT,
                sale_id INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_id, serial_number),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # ============================================
        # TRANSACTION TABLES
        # ============================================
        
        # Purchase Orders
        cur.execute("""
            CREATE TABLE purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER NOT NULL,
                order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                expected_date TEXT,
                received_date TEXT,
                status TEXT DEFAULT 'draft',
                total_amount REAL DEFAULT 0,
                notes TEXT,
                created_by INTEGER,
                approved_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        
        # Purchase Order Items
        cur.execute("""
            CREATE TABLE po_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER NOT NULL,
                product_id INTEGER,
                sku TEXT,
                quantity_ordered INTEGER DEFAULT 0,
                quantity_received INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                total_price REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Sales Orders
        cur.execute("""
            CREATE TABLE sales_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT,
                customer_phone TEXT,
                customer_email TEXT,
                order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                delivery_date TEXT,
                status TEXT DEFAULT 'confirmed',
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                payment_status TEXT DEFAULT 'pending',
                notes TEXT,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # Sales Order Items
        cur.execute("""
            CREATE TABLE sales_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                total_price REAL DEFAULT 0,
                serial_number TEXT,
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Customers table
        cur.execute("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                country TEXT,
                gst_number TEXT,
                credit_limit REAL DEFAULT 0,
                balance REAL DEFAULT 0,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Stock transfers between locations
        cur.execute("""
            CREATE TABLE stock_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_number TEXT UNIQUE NOT NULL,
                from_location_id INTEGER NOT NULL,
                to_location_id INTEGER NOT NULL,
                transfer_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_by INTEGER,
                approved_by INTEGER,
                FOREIGN KEY (from_location_id) REFERENCES locations(id),
                FOREIGN KEY (to_location_id) REFERENCES locations(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        
        # Stock transfer items
        cur.execute("""
            CREATE TABLE stock_transfer_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 0,
                received_quantity INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # ============================================
        # AUDIT & LOGS
        # ============================================
        
        # Audit log (enhanced)
        cur.execute("""
            CREATE TABLE audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username TEXT,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                session_id TEXT,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Sync queue (for Google Drive sync)
        cur.execute("""
            CREATE TABLE sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id INTEGER,
                data TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                synced_at TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            )
        """)
        
        # Sync history
        cur.execute("""
            CREATE TABLE sync_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT NOT NULL,
                status TEXT NOT NULL,
                records_synced INTEGER DEFAULT 0,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                error_message TEXT,
                details TEXT
            )
        """)
        
        # Google credentials (encrypted)
        cur.execute("""
            CREATE TABLE google_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                encrypted_token TEXT,
                token_expiry TEXT,
                refresh_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ============================================
        # ALERTS & NOTIFICATIONS
        # ============================================
        
        # Alerts
        cur.execute("""
            CREATE TABLE alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                record_type TEXT,
                record_id INTEGER,
                is_read INTEGER DEFAULT 0,
                is_acknowledged INTEGER DEFAULT 0,
                acknowledged_by INTEGER,
                acknowledged_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (acknowledged_by) REFERENCES users(id)
            )
        """)
        
        # Alert settings
        cur.execute("""
            CREATE TABLE alert_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT UNIQUE NOT NULL,
                enabled INTEGER DEFAULT 1,
                threshold_value INTEGER,
                email_enabled INTEGER DEFAULT 0,
                sms_enabled INTEGER DEFAULT 0,
                in_app_enabled INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ============================================
        # LEASE & RENTAL TABLES (Phase 15)
        # ============================================
        
        # Leases table
        cur.execute("""
            CREATE TABLE leases (
                lease_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                customer_email TEXT,
                customer_address TEXT,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                start_date TEXT,
                end_date TEXT,
                return_date TEXT,
                monthly_amount REAL DEFAULT 0,
                duration_months INTEGER DEFAULT 12,
                security_deposit REAL DEFAULT 0,
                security_deduction REAL DEFAULT 0,
                total_paid REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                return_condition TEXT,
                return_notes TEXT,
                last_payment_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Lease payments table
        cur.execute("""
            CREATE TABLE lease_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lease_id TEXT NOT NULL,
                payment_date TEXT,
                amount_paid REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'cash',
                payment_reference TEXT,
                notes TEXT,
                recorded_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lease_id) REFERENCES leases(lease_id)
            )
        """)
        
        # ============================================
        # INVOICING TABLES (Phase 15)
        # ============================================
        
        # Invoices table
        cur.execute("""
            CREATE TABLE invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_email TEXT,
                customer_phone TEXT,
                customer_address TEXT,
                invoice_date TEXT,
                due_date TEXT,
                payment_terms TEXT,
                subtotal REAL DEFAULT 0,
                tax_rate REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                amount_paid REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        # Invoice items table
        cur.execute("""
            CREATE TABLE invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Invoice payments table
        cur.execute("""
            CREATE TABLE invoice_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                payment_date TEXT,
                amount_paid REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'cash',
                payment_reference TEXT,
                notes TEXT,
                recorded_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
            )
        """)
        
        # ============================================
        # RMA/RETURNS TABLES (Phase 5)
        # ============================================
        
        # Returns/RMA table
        cur.execute("""
            CREATE TABLE returns (
                return_id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE NOT NULL,
                invoice_id INTEGER,
                customer_name TEXT NOT NULL,
                customer_email TEXT,
                customer_phone TEXT,
                return_date TEXT,
                reason TEXT,
                status TEXT DEFAULT 'pending',
                total_refund REAL DEFAULT 0,
                refund_method TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
            )
        """)
        
        # Return items table
        cur.execute("""
            CREATE TABLE return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                condition TEXT DEFAULT 'good',
                restock INTEGER DEFAULT 1,
                FOREIGN KEY (return_id) REFERENCES returns(return_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # ============================================
        # TRADE-IN TABLES (Phase 5)
        # ============================================
        
        # Trade-ins table
        cur.execute("""
            CREATE TABLE trade_ins (
                trade_in_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_in_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                product_name TEXT NOT NULL,
                product_condition TEXT,
                trade_in_value REAL DEFAULT 0,
                credit_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                trade_in_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        # ============================================
        # SERVICE/REPAIR TABLES (Phase 5)
        # ============================================
        
        # Service tickets table
        cur.execute("""
            CREATE TABLE service_tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT,
                customer_email TEXT,
                device_type TEXT,
                device_brand TEXT,
                device_model TEXT,
                serial_number TEXT,
                issue_description TEXT,
                status TEXT DEFAULT 'received',
                estimated_cost REAL DEFAULT 0,
                final_cost REAL DEFAULT 0,
                received_date TEXT,
                completed_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        """)
        
        # Service parts used table
        cur.execute("""
            CREATE TABLE service_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                FOREIGN KEY (ticket_id) REFERENCES service_tickets(ticket_id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # ============================================
        # COMPANY PROFILE TABLE (Phase 13)
        # ============================================
        
        # Company profile table
        cur.execute("""
            CREATE TABLE company_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                company_address TEXT,
                company_phone TEXT,
                company_email TEXT,
                company_logo_path TEXT,
                tax_number TEXT,
                tax_rate REAL DEFAULT 0,
                currency TEXT DEFAULT 'PKR',
                business_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default company profile
        cur.execute("""
            INSERT INTO company_profile (company_name, currency, tax_rate)
            VALUES ('Minataka Sphere', 'PKR', 0)
        """)
        
        # ============================================
        # USER PERMISSIONS TABLE (Phase 10)
        # ============================================
        
        # User permissions table
        cur.execute("""
            CREATE TABLE user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_key TEXT NOT NULL,
                permission_value INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, permission_key),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ============================================
        # SETTINGS & CONFIG
        # ============================================
        
        # System settings
        cur.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                category TEXT,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        """)
        
        # ============================================
        # VIEWS (for common queries)
        # ============================================
        
        # Low stock view
        cur.execute("""
            CREATE VIEW v_low_stock AS
            SELECT 
                p.id,
                p.sku,
                p.model,
                p.stock,
                p.min_stock,
                p.reorder_point,
                p.supplier_id,
                s.name as supplier_name,
                CASE 
                    WHEN p.stock <= 0 THEN 'critical'
                    WHEN p.stock <= p.min_stock THEN 'critical'
                    WHEN p.stock <= p.reorder_point THEN 'warning'
                    ELSE 'ok'
                END as stock_status
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.stock <= p.reorder_point
            AND p.status = 'active'
        """)
        
        # Stock value view
        cur.execute("""
            CREATE VIEW v_stock_value AS
            SELECT 
                p.id,
                p.sku,
                p.model,
                p.stock,
                p.purchase_price,
                p.selling_price,
                (p.stock * p.purchase_price) as cost_value,
                (p.stock * p.selling_price) as retail_value,
                (p.stock * (p.selling_price - p.purchase_price)) as potential_profit
            FROM products p
            WHERE p.status = 'active'
        """)
        
        # Insert schema version
        cur.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        
        # Insert default settings
        default_settings = [
            ('company_name', 'Minataka Sphere', 'general', 'Company name'),
            ('currency', 'PKR', 'general', 'Default currency'),
            ('tax_rate', '0', 'general', 'Default tax rate percentage'),
            ('low_stock_threshold', '10', 'alerts', 'Default low stock threshold'),
            ('backup_frequency', 'daily', 'backup', 'Backup frequency'),
            ('sync_frequency', '10', 'sync', 'Google Drive sync frequency in minutes'),
            ('auto_sync_enabled', '0', 'sync', 'Enable automatic sync'),
        ]
        cur.executemany(
            "INSERT INTO settings (key, value, category, description) VALUES (?, ?, ?, ?)",
            default_settings
        )
        
        # Insert default alert settings
        alert_types = [
            ('low_stock', 10, 1, 0, 1),
            ('out_of_stock', 0, 1, 0, 1),
            ('overstock', 100, 0, 0, 1),
            ('expiry_warning', 30, 1, 0, 1),
            ('warranty_expiry', 30, 0, 0, 1),
        ]
        cur.executemany(
            "INSERT INTO alert_settings (alert_type, threshold_value, enabled, email_enabled, in_app_enabled) VALUES (?, ?, ?, ?, ?)",
            alert_types
        )
        
        # ============================================
        # LICENSING & ADMIN HIERARCHY TABLES (Phase 16)
        # ============================================
        
        # License table
        cur.execute("""
            CREATE TABLE license (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE,
                admin_email TEXT NOT NULL,
                device_fingerprint TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                licensed_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Admin hierarchy table
        cur.execute("""
            CREATE TABLE admin_hierarchy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role_level INTEGER,
                can_authorize_admins INTEGER DEFAULT 0,
                can_authorize_staff INTEGER DEFAULT 0,
                can_deactivate_users INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Authorization log table
        cur.execute("""
            CREATE TABLE authorization_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                authorized_by TEXT,
                authorized_user TEXT,
                action TEXT,
                timestamp TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User authorization requests table
        cur.execute("""
            CREATE TABLE user_authorization_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                department TEXT,
                reason TEXT,
                status TEXT DEFAULT 'PENDING',
                requested_date TEXT,
                approved_by TEXT,
                approved_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default location
        cur.execute("""
            INSERT INTO locations (code, name, type, address, city, country)
            VALUES ('MAIN', 'Main Warehouse', 'warehouse', '', '', 'Pakistan')
        """)
        
        logging.info(f"Database initialized with schema version {SCHEMA_VERSION}")
    
    return True


def migrate_database():
    """Run database migrations if needed."""
    with get_db_cursor() as cur:
        # Check if schema_version table exists first
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_version'
        """)
        if not cur.fetchone():
            logging.warning("schema_version table missing, cannot migrate")
            return

        cur.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        current_version = row['version'] if row else 0
        
        if current_version >= SCHEMA_VERSION:
            # Check for missing tables anyway as a safeguard (case for manual deletions or interrupted updates)
            _ensure_phase16_tables(cur)
            return
        
        logging.info(f"Migrating database from version {current_version} to {SCHEMA_VERSION}")
        
        # Migration from 1 to 2: Add security_pin_hash and Phase 16 tables
        if current_version < 2:
            # 1. Add security_pin_hash to users table if it doesn't exist
            try:
                cur.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cur.fetchall()]
                if 'security_pin_hash' not in columns:
                    cur.execute("ALTER TABLE users ADD COLUMN security_pin_hash TEXT")
                    logging.info("Added security_pin_hash column to users table")
            except Exception as e:
                logging.warning(f"Failed to add security_pin_hash: {e}")

            # 2. Add Phase 16 tables
            _ensure_phase16_tables(cur)
        
        cur.execute("UPDATE schema_version SET version = ?", (SCHEMA_VERSION,))
        logging.info(f"Database migrated to version {SCHEMA_VERSION}")


def _ensure_phase16_tables(cur):
    """Ensure Phase 16 tables exist (Licensing & Admin Hierarchy)."""
    # License table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS license (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE,
            admin_email TEXT NOT NULL,
            device_fingerprint TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            licensed_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Admin hierarchy table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_hierarchy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role_level INTEGER,
            can_authorize_admins INTEGER DEFAULT 0,
            can_authorize_staff INTEGER DEFAULT 0,
            can_deactivate_users INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Authorization log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authorization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            authorized_by TEXT,
            authorized_user TEXT,
            action TEXT,
            timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User authorization requests table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_authorization_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT,
            reason TEXT,
            status TEXT DEFAULT 'PENDING',
            requested_date TEXT,
            approved_by TEXT,
            approved_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logging.info("Verified Phase 16 tables structure")


def export_to_json():
    """Export entire database to JSON for backup."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    tables = [
        'products', 'categories', 'suppliers', 'locations',
        'customers', 'purchase_orders', 'po_items',
        'sales_orders', 'sales_order_items', 'stock_transfers',
        'stock_transfer_items', 'serial_numbers', 'product_stock'
    ]
    
    data = {}
    for table in tables:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {table}")
        rows = cur.fetchall()
        data[table] = [dict(row) for row in rows]
    
    return json.dumps(data, indent=2, default=str)


def import_from_json(json_data):
    """Import data from JSON backup."""
    data = json.loads(json_data)
    
    with get_db_cursor() as cur:
        for table, rows in data.items():
            if not rows:
                continue
            
            columns = list(rows[0].keys())
            placeholders = ','.join(['?' for _ in columns])
            col_names = ','.join(columns)
            
            for row in rows:
                values = [row[col] for col in columns]
                try:
                    cur.execute(
                        f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
                        values
                    )
                except Exception as e:
                    logging.error(f"Failed to import row into {table}: {e}")
    
    return True


def get_db_stats():
    """Get database statistics."""
    with get_db_cursor() as cur:
        stats = {}
        
        # Product count
        cur.execute("SELECT COUNT(*) as count FROM products WHERE status = 'active'")
        stats['total_products'] = cur.fetchone()['count']
        
        # Low stock count
        cur.execute("SELECT COUNT(*) as count FROM v_low_stock WHERE stock_status IN ('critical', 'warning')")
        stats['low_stock_count'] = cur.fetchone()['count']
        
        # Supplier count
        cur.execute("SELECT COUNT(*) as count FROM suppliers WHERE is_active = 1")
        stats['total_suppliers'] = cur.fetchone()['count']
        
        # Location count
        cur.execute("SELECT COUNT(*) as count FROM locations WHERE is_active = 1")
        stats['total_locations'] = cur.fetchone()['count']
        
        # Pending sync count
        cur.execute("SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'")
        stats['pending_sync'] = cur.fetchone()['count']
        
        # Unread alerts
        cur.execute("SELECT COUNT(*) as count FROM alerts WHERE is_read = 0")
        stats['unread_alerts'] = cur.fetchone()['count']
        
        return stats


# Initialize database on module import (for development)
# In production, call init_database() explicitly after login
try:
    if not os.path.exists(DB_FILE):
        init_database()
        logging.info("Database auto-initialized")
    else:
        # If database exists, still check for migrations
        migrate_database()
        logging.info("Database auto-migrated")
except Exception as e:
    logging.warning(f"Database auto-init/migration skipped: {e}")
