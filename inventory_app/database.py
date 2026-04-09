"""
Enhanced SQLite Database Module
================================
Enterprise-grade database with encryption support, multi-location,
supplier management, and audit trails.

All features work OFFLINE. SQLite is built into Python.

ARCHITECTURE NOTE:
  This module is the SINGLE source of truth for all database access.
  UI files MUST NOT run SQL directly. Use InventoryDB methods or the
  service layer (services.py) for all data operations.
"""

import sqlite3
import os
import json
import logging
import threading
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Tuple

try:
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir

# Database file path
DB_FILE = os.path.join(get_data_dir(), "inventory.db")

# Thread-local storage for database connections
_local = threading.local()

# Schema version for migrations
SCHEMA_VERSION = 4

logger = logging.getLogger(__name__)


# ============================================================
# LOW-LEVEL CONNECTION HELPERS (kept for backward compatibility)
# ============================================================

def get_connection():
    """Get thread-local database connection with error recovery and performance optimizations."""
    if not hasattr(_local, 'connection') or _local.connection is None:
        try:
            _local.connection = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10.0)
            _local.connection.row_factory = sqlite3.Row

            # Performance and concurrency optimizations
            _local.connection.execute("PRAGMA journal_mode = WAL")  # Allows concurrent reads/writes
            _local.connection.execute("PRAGMA busy_timeout = 5000")  # Wait 5s for locks
            _local.connection.execute("PRAGMA synchronous = NORMAL")  # Faster writes, safe enough
            _local.connection.execute("PRAGMA cache_size = -64000")  # 64MB cache
            _local.connection.execute("PRAGMA foreign_keys = ON")
            _local.connection.execute("PRAGMA wal_autocheckpoint = 1000")  # Checkpoint every 1000 pages

            logger.debug("Database connection opened with WAL mode and optimizations")
        except Exception as e:
            logger.error(f"Failed to open database: {e}")
            raise
    return _local.connection


def close_connection():
    """Close thread-local database connection."""
    if hasattr(_local, 'connection') and _local.connection is not None:
        try:
            _local.connection.close()
            _local.connection = None
            logger.debug("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")


@contextmanager
def get_db_cursor(retries=3, retry_delay=0.1):
    """Context manager for database operations with error handling and retry logic.
    
    Args:
        retries: Number of retry attempts for locked database errors (default 3)
        retry_delay: Base delay between retries in seconds (default 0.1)
    """
    import time
    
    conn = get_connection()
    cursor = conn.cursor()
    
    last_error = None
    for attempt in range(retries + 1):
        try:
            yield cursor
            conn.commit()
            return  # Success, exit the context manager
        except sqlite3.OperationalError as e:
            last_error = e
            if "locked" in str(e).lower() and attempt < retries:
                logger.warning(f"Database locked, retry {attempt + 1}/{retries} after {retry_delay}s")
                conn.rollback()
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                cursor = conn.cursor()  # Get fresh cursor
            else:
                conn.rollback()
                logger.error(f"Database operation failed after {attempt + 1} attempts: {e}")
                raise e
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise e
    
    # Should not reach here, but just in case
    if last_error:
        raise last_error


# ============================================================
# InventoryDB — the single class for ALL database access
# ============================================================

class InventoryDB:
    """
    Centralized database access for the inventory system.

    RULES:
      - All SQL lives inside this class.
      - Every method opens a cursor, does its work, and returns.
      - No UI code should ever call cursor().execute() directly.
      - After any write (insert/update/delete) the UI must call
        its own refresh_from_db() which re-reads through these methods.
    """

    # ── singleton per-thread ──────────────────────────────
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── helpers ────────────────────────────────────────────
    # Whitelist of allowed column names for each table (defense-in-depth)
    _VALID_COLUMNS = {
        "products": {
            # Basic fields (all industries)
            "id", "model", "category", "supplier", "purchase_price", "selling_price",
            "stock", "reorder_point", "notes", "status", "created_at", "updated_at",
            "category_id", "supplier_id", "barcode", "sku", "description", "location_id",
            # Electronics-specific fields
            "serial_number", "serial_no", "imei",
            "ram", "ram_gb", "storage", "storage_gb",
            "screen_type", "screen_size",
            "camera", "camera_mp",
            "battery", "battery_mah",
            "color", "warranty_months", "warranty_expiry", "warranty_expiry_date",
            "device_condition", "condition",
            # Pharmacy-specific fields
            "batch_no", "batch_number", "expiry_date", "manufacturer",
            "dosage_form", "strength",
            # Location/warehouse fields
            "default_location_id", "rack_location", "shelf_location",
            # Additional fields
            "brand", "qr_code", "cost_avg", "max_stock", "min_stock",
            "images", "specifications", "created_by"
        },
        "sales": {"id", "product_id", "quantity", "price", "total", "customer_name",
                  "sale_date", "notes", "created_at", "model", "month"},
        "categories": {"id", "name", "description", "is_active", "created_at"},
        "suppliers": {"id", "name", "contact", "address", "phone", "email", "is_active", "created_at"},
        "locations": {"id", "name", "code", "type", "address", "city", "country", "capacity", "is_active"},
        "customers": {"id", "name", "phone", "email", "address", "is_active", "created_at"},
    }

    @staticmethod
    def _sanitize_keys(keys, table: str = None):
        """Validate column names to prevent SQL injection.
        
        Args:
            keys: Column names to validate
            table: Optional table name for whitelist validation
        """
        for k in keys:
            if not str(k).isidentifier():
                raise ValueError(f"Invalid column name: {k}")
            # Extra defense-in-depth: check against whitelist if available
            if table and table in InventoryDB._VALID_COLUMNS:
                if k not in InventoryDB._VALID_COLUMNS[table]:
                    raise ValueError(f"Unknown column '{k}' for table '{table}'")

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert sqlite3.Row to dict."""
        if row is None:
            return {}
        return dict(row)

    @staticmethod
    def _rows_to_dicts(rows) -> List[dict]:
        """Convert list of sqlite3.Row to list of dicts."""
        return [dict(r) for r in rows]

    # ── PRODUCTS / INVENTORY ──────────────────────────────

    def fetch_products(self, active_only: bool = True) -> List[dict]:
        """Return all products as list of dicts."""
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE status = 'active'"
        with get_db_cursor() as cur:
            cur.execute(query)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_product_by_model(self, model: str) -> Optional[dict]:
        """Return a single product by model name."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM products WHERE model = ?", (model,))
            row = cur.fetchone()
            return self._row_to_dict(row) if row else None

    def fetch_product_by_id(self, product_id: int) -> Optional[dict]:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cur.fetchone()
            return self._row_to_dict(row) if row else None

    def insert_product(self, data: dict) -> int:
        """Insert a new product. Returns the new product id."""
        self._sanitize_keys(data.keys(), table="products")
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO products ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def update_product(self, model: str, data: dict) -> bool:
        """Update an existing product identified by model name."""
        if not data:
            return False
        self._sanitize_keys(data.keys(), table="products")
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [model]
        with get_db_cursor() as cur:
            cur.execute(
                f"UPDATE products SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                values,
            )
            return cur.rowcount > 0

    def upsert_product(self, data: dict) -> int:
        """Insert or update a product by model name. Returns product id."""
        model = data.get("model")
        if not model:
            raise ValueError("Product must have a 'model' field")
        existing = self.fetch_product_by_model(model)
        if existing:
            update_fields = {k: v for k, v in data.items() if k != "model"}
            if update_fields:
                self.update_product(model, update_fields)
            return existing["id"]
        else:
            return self.insert_product(data)

    def delete_product(self, model: str) -> bool:
        """Soft-delete a product (set status = 'deleted')."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE products SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (model,),
            )
            return cur.rowcount > 0

    def hard_delete_product(self, model: str) -> bool:
        """Permanently remove a product row."""
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM products WHERE model = ?", (model,))
            return cur.rowcount > 0

    def adjust_stock(self, model: str, delta: int) -> bool:
        """Add or subtract from stock. delta can be negative."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE products SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (delta, model),
            )
            return cur.rowcount > 0

    def set_stock(self, model: str, quantity: int) -> bool:
        """Set absolute stock quantity."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE products SET stock = ?, updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (quantity, model),
            )
            return cur.rowcount > 0

    # ── SALES ─────────────────────────────────────────────

    def fetch_sales_orders(self, status: Optional[str] = None) -> List[dict]:
        query = "SELECT * FROM sales_orders"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY order_date DESC"
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_sales_order_items(self, order_id: int) -> List[dict]:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM sales_order_items WHERE order_id = ?", (order_id,))
            return self._rows_to_dicts(cur.fetchall())

    def insert_sales_order(self, order_data: dict, items: List[dict]) -> int:
        """Insert a sales order and its items atomically. Returns order id."""
        self._sanitize_keys(order_data.keys())
        columns = ", ".join(order_data.keys())
        placeholders = ", ".join(["?"] * len(order_data))
        values = list(order_data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO sales_orders ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            order_id = cur.fetchone()[0]

            for item in items:
                item_vals = (order_id, item.get("product_id"), item.get("quantity", 0),
                             item.get("unit_price", 0), item.get("total_price", 0),
                             item.get("serial_number"))
                cur.execute(
                    "INSERT INTO sales_order_items (order_id, product_id, quantity, unit_price, total_price, serial_number) VALUES (?, ?, ?, ?, ?, ?)",
                    item_vals,
                )
        return order_id

    def delete_sales_order(self, order_id: int) -> bool:
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM sales_order_items WHERE order_id = ?", (order_id,))
            cur.execute("DELETE FROM sales_orders WHERE id = ?", (order_id,))
            return cur.rowcount > 0

    def update_sales_order(self, order_id: int, updates: dict) -> bool:
        """Update fields on a sales order. `updates` is a dict of column -> value."""
        if not updates:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [order_id]
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE sales_orders SET {set_clause} WHERE id = ?", values)
            return cur.rowcount > 0

    # ── LOCATIONS ─────────────────────────────────────────

    def fetch_locations(self, active_only: bool = True) -> List[dict]:
        query = "SELECT * FROM locations"
        if active_only:
            query += " WHERE is_active = 1"
        with get_db_cursor() as cur:
            cur.execute(query)
            return self._rows_to_dicts(cur.fetchall())

    def insert_location(self, data: dict) -> int:
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO locations ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def update_location(self, code: str, data: dict) -> bool:
        if not data:
            return False
        self._sanitize_keys(data.keys())
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [code]
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE locations SET {set_clause} WHERE code = ?", values)
            return cur.rowcount > 0

    def delete_location(self, code: str) -> bool:
        with get_db_cursor() as cur:
            cur.execute("UPDATE locations SET is_active = 0 WHERE code = ?", (code,))
            return cur.rowcount > 0

    # ── SUPPLIERS ─────────────────────────────────────────

    def fetch_suppliers(self, active_only: bool = True) -> List[dict]:
        query = "SELECT * FROM suppliers"
        if active_only:
            query += " WHERE is_active = 1"
        with get_db_cursor() as cur:
            cur.execute(query)
            return self._rows_to_dicts(cur.fetchall())

    def insert_supplier(self, data: dict) -> int:
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO suppliers ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def update_supplier(self, code: str, data: dict) -> bool:
        if not data:
            return False
        self._sanitize_keys(data.keys())
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [code]
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE suppliers SET {set_clause} WHERE code = ?", values)
            return cur.rowcount > 0

    # ── CUSTOMERS ─────────────────────────────────────────

    def fetch_customers(self, active_only: bool = True) -> List[dict]:
        query = "SELECT * FROM customers"
        if active_only:
            query += " WHERE is_active = 1"
        with get_db_cursor() as cur:
            cur.execute(query)
            return self._rows_to_dicts(cur.fetchall())

    def insert_customer(self, data: dict) -> int:
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO customers ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def update_customer(self, customer_id: int, data: dict) -> bool:
        if not data:
            return False
        self._sanitize_keys(data.keys())
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [customer_id]
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE customers SET {set_clause} WHERE id = ?", values)
            return cur.rowcount > 0

    # ── INVOICES ──────────────────────────────────────────

    def fetch_invoices(self, status: Optional[str] = None) -> List[dict]:
        query = "SELECT * FROM invoices"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY invoice_date DESC"
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_invoice_items(self, invoice_id: int) -> List[dict]:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            return self._rows_to_dicts(cur.fetchall())

    def insert_invoice(self, invoice_data: dict, items: List[dict]) -> int:
        self._sanitize_keys(invoice_data.keys())
        columns = ", ".join(invoice_data.keys())
        placeholders = ", ".join(["?"] * len(invoice_data))
        values = list(invoice_data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO invoices ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            invoice_id = cur.fetchone()[0]

            for item in items:
                item_vals = (invoice_id, item.get("product_id"), item.get("product_name", ""),
                             item.get("quantity", 0), item.get("unit_price", 0),
                             item.get("discount_percent", 0), item.get("discount_amount", 0),
                             item.get("line_total", 0))
                cur.execute(
                    "INSERT INTO invoice_items (invoice_id, product_id, product_name, quantity, unit_price, discount_percent, discount_amount, line_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    item_vals,
                )
        return invoice_id

    # ── LEASES ────────────────────────────────────────────

    def fetch_leases(self, status: Optional[str] = None) -> List[dict]:
        query = "SELECT * FROM leases"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def insert_lease(self, data: dict) -> str:
        """Insert a lease. Returns lease_id."""
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO leases ({columns}) VALUES ({placeholders})",
                values,
            )
        return data.get("lease_id", "")

    def update_lease(self, lease_id: str, data: dict) -> bool:
        if not data:
            return False
        self._sanitize_keys(data.keys())
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [lease_id]
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE leases SET {set_clause} WHERE lease_id = ?", values)
            return cur.rowcount > 0

    # ── RETURNS / RMA ─────────────────────────────────────

    def fetch_returns(self, status: Optional[str] = None) -> List[dict]:
        query = "SELECT * FROM returns"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    # ── USERS ─────────────────────────────────────────────

    def fetch_user(self, username: str) -> Optional[dict]:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
            row = cur.fetchone()
            return self._row_to_dict(row) if row else None

    def insert_user(self, data: dict) -> int:
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO users ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def update_user(self, user_id: int, data: dict) -> bool:
        if not data:
            return False
        self._sanitize_keys(data.keys())
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [user_id]
        with get_db_cursor() as cur:
            cur.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            return cur.rowcount > 0

    # ── SETTINGS / CONFIG ─────────────────────────────────

    def get_setting(self, key: str) -> Optional[str]:
        with get_db_cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str, category: str = "general", description: str = "") -> bool:
        with get_db_cursor() as cur:
            cur.execute(
                "INSERT INTO settings (key, value, category, description, updated_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP",
                (key, value, category, description),
            )
            return True

    def get_industry_type(self) -> str:
        """Return the current industry type (e.g. 'electronics', 'retail', 'pharma')."""
        val = self.get_setting("industry_type")
        return val if val else "electronics"  # Default to electronics

    def set_industry_type(self, industry: str) -> bool:
        return self.set_setting("industry_type", industry, "general", "Current industry type")

    # ── AUDIT LOG ─────────────────────────────────────────

    def audit_event(self, username: str, action: str, table_name: str = "",
                    record_id: int = None, details: str = "") -> None:
        with get_db_cursor() as cur:
            cur.execute(
                "INSERT INTO audit_log (username, action, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)",
                (username, action, table_name, record_id, details),
            )
        # Notify UI of real-time database changes
        try:
            from app_core import app_state
            app_state.notify_ui_updates("db_changed", {"table": table_name, "action": action})
        except ImportError:
            pass

    # ── STATISTICS ────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return dashboard statistics."""
        stats = {}
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM products WHERE status = 'active'")
            stats['total_products'] = cur.fetchone()['count']

            try:
                cur.execute("SELECT COUNT(*) as count FROM v_low_stock WHERE stock_status IN ('critical', 'warning')")
                stats['low_stock_count'] = cur.fetchone()['count']
            except Exception:
                stats['low_stock_count'] = 0

            cur.execute("SELECT COUNT(*) as count FROM suppliers WHERE is_active = 1")
            stats['total_suppliers'] = cur.fetchone()['count']

            try:
                cur.execute("SELECT COUNT(*) as count FROM locations WHERE is_active = 1")
                stats['total_locations'] = cur.fetchone()['count']
            except Exception:
                stats['total_locations'] = 0

            try:
                cur.execute("SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'")
                stats['pending_sync'] = cur.fetchone()['count']
            except Exception:
                stats['pending_sync'] = 0

            try:
                cur.execute("SELECT COUNT(*) as count FROM alerts WHERE is_read = 0")
                stats['unread_alerts'] = cur.fetchone()['count']
            except Exception:
                stats['unread_alerts'] = 0

        return stats

    # ── SERIAL NUMBERS ────────────────────────────────────

    def fetch_serial_numbers(self, product_id: Optional[int] = None) -> List[dict]:
        """Fetch serial numbers, optionally filtered by product_id."""
        query = "SELECT * FROM serial_numbers"
        params: tuple = ()
        if product_id:
            query += " WHERE product_id = ?"
            params = (product_id,)
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def insert_serial_number(self, data: dict) -> int:
        """Insert a serial number. Returns serial number id."""
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO serial_numbers ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def update_serial_status(self, serial_number: str, status: str) -> bool:
        """Update the status of a serial number."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE serial_numbers SET status = ? WHERE serial_number = ?",
                (status, serial_number),
            )
            return cur.rowcount > 0

    # ── PURCHASE ORDERS ───────────────────────────────────

    def fetch_purchase_orders(self, status: Optional[str] = None) -> List[dict]:
        """Fetch purchase orders, optionally filtered by status."""
        query = "SELECT * FROM purchase_orders"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY order_date DESC"
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_po_items(self, po_id: int) -> List[dict]:
        """Fetch items for a purchase order."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM po_items WHERE po_id = ?", (po_id,))
            return self._rows_to_dicts(cur.fetchall())

    def insert_purchase_order(self, order_data: dict, items: List[dict]) -> int:
        """Insert a purchase order and its items. Returns PO id."""
        self._sanitize_keys(order_data.keys())
        columns = ", ".join(order_data.keys())
        placeholders = ", ".join(["?"] * len(order_data))
        values = list(order_data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO purchase_orders ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            po_id = cur.fetchone()[0]

            for item in items:
                item_vals = (po_id, item.get("product_id"), item.get("sku"),
                             item.get("quantity_ordered", 0), item.get("quantity_received", 0),
                             item.get("unit_price", 0), item.get("total_price", 0),
                             item.get("notes"))
                cur.execute(
                    "INSERT INTO po_items (po_id, product_id, sku, quantity_ordered, quantity_received, unit_price, total_price, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    item_vals,
                )
        return po_id

    def update_purchase_order_status(self, po_id: int, status: str, received_date: Optional[str] = None) -> bool:
        """Update purchase order status."""
        with get_db_cursor() as cur:
            if received_date:
                cur.execute(
                    "UPDATE purchase_orders SET status = ?, received_date = ? WHERE id = ?",
                    (status, received_date, po_id),
                )
            else:
                cur.execute(
                    "UPDATE purchase_orders SET status = ? WHERE id = ?",
                    (status, po_id),
                )
            return cur.rowcount > 0

    # ── RETURNS / RMA (additional methods) ────────────────

    def fetch_returns(self, status: Optional[str] = None) -> List[dict]:
        """Fetch returns, optionally filtered by status."""
        query = "SELECT * FROM returns"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY return_date DESC"
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def insert_return(self, return_data: dict, items: List[dict]) -> int:
        """Insert a return and its items. Returns return id."""
        self._sanitize_keys(return_data.keys())
        columns = ", ".join(return_data.keys())
        placeholders = ", ".join(["?"] * len(return_data))
        values = list(return_data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO returns ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return_id = cur.fetchone()[0]

            for item in items:
                item_vals = (return_id, item.get("product_id"), item.get("product_name", ""),
                             item.get("quantity", 0), item.get("unit_price", 0),
                             item.get("line_total", 0), item.get("condition", "good"),
                             item.get("restock", 1))
                cur.execute(
                    "INSERT INTO return_items (return_id, product_id, product_name, quantity, unit_price, line_total, condition, restock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    item_vals,
                )
        return return_id

    def fetch_return_items(self, return_id: int) -> List[dict]:
        """Fetch items for a return."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM return_items WHERE return_id = ?", (return_id,))
            return self._rows_to_dicts(cur.fetchall())

    def update_return_status(self, return_id: int, status: str) -> bool:
        """Update return status."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE returns SET status = ? WHERE return_id = ?",
                (status, return_id),
            )
            return cur.rowcount > 0

    # ── TRADE-INS ─────────────────────────────────────────

    def fetch_trade_ins(self, status: Optional[str] = None) -> List[dict]:
        """Fetch trade-ins, optionally filtered by status."""
        query = "SELECT * FROM trade_ins"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def insert_trade_in(self, data: dict) -> int:
        """Insert a trade-in. Returns trade-in id."""
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO trade_ins ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    # ── SERVICE TICKETS ───────────────────────────────────

    def fetch_service_tickets(self, status: Optional[str] = None) -> List[dict]:
        """Fetch service tickets, optionally filtered by status."""
        query = "SELECT * FROM service_tickets"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def insert_service_ticket(self, data: dict) -> int:
        """Insert a service ticket. Returns ticket id."""
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO service_tickets ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    # ── STOCK TRANSFERS ───────────────────────────────────

    def fetch_stock_transfers(self, status: Optional[str] = None) -> List[dict]:
        """Fetch stock transfers, optionally filtered by status."""
        query = """
            SELECT st.id, st.transfer_number, st.from_location_id, st.to_location_id,
                   st.transfer_date, st.status, st.notes, st.created_by,
                   fl.name as from_location_name, tl.name as to_location_name,
                   u.username as created_by_name,
                   (SELECT COUNT(*) FROM stock_transfer_items WHERE transfer_id = st.id) as item_count
            FROM stock_transfers st
            LEFT JOIN locations fl ON st.from_location_id = fl.id
            LEFT JOIN locations tl ON st.to_location_id = tl.id
            LEFT JOIN users u ON st.created_by = u.id
        """
        params: tuple = ()
        if status:
            query += " WHERE st.status = ?"
            params = (status,)
        query += " ORDER BY st.transfer_date DESC"
        with get_db_cursor() as cur:
            cur.execute(query, params)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_stock_transfer_items(self, transfer_id: int) -> List[dict]:
        """Fetch items for a stock transfer."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT sti.id, sti.product_id, sti.quantity, sti.received_quantity, sti.notes,
                       p.model as product_name, p.stock as current_stock
                FROM stock_transfer_items sti
                JOIN products p ON sti.product_id = p.id
                WHERE sti.transfer_id = ?
            """, (transfer_id,))
            return self._rows_to_dicts(cur.fetchall())

    def insert_stock_transfer(self, transfer_data: dict, items: List[dict]) -> int:
        """Insert a stock transfer and its items. Returns transfer id."""
        self._sanitize_keys(transfer_data.keys())
        columns = ", ".join(transfer_data.keys())
        placeholders = ", ".join(["?"] * len(transfer_data))
        values = list(transfer_data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO stock_transfers ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            transfer_id = cur.fetchone()[0]

            for item in items:
                cur.execute(
                    "INSERT INTO stock_transfer_items (transfer_id, product_id, quantity, received_quantity, notes) VALUES (?, ?, ?, 0, ?)",
                    (transfer_id, item.get("product_id"), item.get("quantity", 0), item.get("notes", "")),
                )
        return transfer_id

    def complete_stock_transfer(self, transfer_id: int) -> bool:
        """Complete a stock transfer: update status to 'completed'."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE stock_transfers SET status = 'completed' WHERE id = ?",
                (transfer_id,),
            )
            return cur.rowcount > 0

    def get_transfer_locations(self, transfer_id: int) -> Optional[tuple]:
        """Get from_location_id and to_location_id for a transfer."""
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT from_location_id, to_location_id FROM stock_transfers WHERE id = ?",
                (transfer_id,),
            )
            row = cur.fetchone()
            return (row["from_location_id"], row["to_location_id"]) if row else None

    def update_product_stock_location(self, product_id: int, location_id: int, delta: int) -> None:
        """Update product stock at a location (can be negative for deduction)."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE product_stock SET quantity = quantity + ? WHERE product_id = ? AND location_id = ?",
                (delta, product_id, location_id),
            )

    def upsert_product_stock_location(self, product_id: int, location_id: int, quantity: int) -> None:
        """Insert or update product stock at a location."""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO product_stock (product_id, location_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(product_id, location_id) DO UPDATE SET quantity = quantity + excluded.quantity
            """, (product_id, location_id, quantity))

    def update_transfer_item_received_quantity(self, transfer_id: int, product_id: int, quantity: int) -> None:
        """Update received quantity for a transfer item."""
        with get_db_cursor() as cur:
            cur.execute(
                "UPDATE stock_transfer_items SET received_quantity = ? WHERE transfer_id = ? AND product_id = ?",
                (quantity, transfer_id, product_id),
            )

    def fetch_products_with_stock(self) -> List[dict]:
        """Fetch active products that have stock > 0."""
        with get_db_cursor() as cur:
            cur.execute(
                "SELECT id, model, category_id, stock, selling_price FROM products WHERE status = 'active' AND stock > 0 ORDER BY model",
            )
            return self._rows_to_dicts(cur.fetchall())

    # ── PHARMACY ──────────────────────────────────────────

    def fetch_pharmacy_inventory(self) -> List[dict]:
        """Fetch products with pharma-specific fields (expiry, batch, prescription)."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.id, p.model, p.category_id, c.name as category_name,
                       p.stock, p.purchase_price, p.selling_price,
                       p.expiry_date, p.batch_number, p.manufacturer,
                       p.status, p.condition,
                       CASE WHEN p.expiry_date IS NOT NULL AND p.expiry_date < date('now') THEN 'expired'
                            WHEN p.expiry_date IS NOT NULL AND p.expiry_date < date('now', '+30 days') THEN 'expiring_soon'
                            ELSE 'ok' END as expiry_status
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.status = 'active'
                ORDER BY p.model
            """)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_pharmacy_stats(self) -> dict:
        """Fetch pharmacy dashboard stats."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN expiry_date < date('now') THEN 1 ELSE 0 END) as expired,
                    SUM(CASE WHEN expiry_date < date('now', '+30 days') AND expiry_date >= date('now') THEN 1 ELSE 0 END) as expiring_soon,
                    SUM(CASE WHEN stock <= 5 THEN 1 ELSE 0 END) as low_stock,
                    SUM(stock) as total_units
                FROM products
                WHERE status = 'active' AND expiry_date IS NOT NULL
            """)
            row = cur.fetchone()
            return self._row_to_dict(row) if row else {"total": 0, "expired": 0, "expiring_soon": 0, "low_stock": 0, "total_units": 0}

    def fetch_batches(self) -> List[dict]:
        """Fetch all active batches with product and supplier info."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT p.model, p.batch_number, p.stock, p.expiry_date,
                       p.manufacturer, s.name as supplier_name
                FROM products p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.batch_number IS NOT NULL AND p.status = 'active'
                ORDER BY p.expiry_date ASC
            """)
            return self._rows_to_dicts(cur.fetchall())

    def fetch_expiring_products(self, days: int = 30) -> List[dict]:
        """Fetch products expiring within N days."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, model, category_id, stock, expiry_date, batch_number, manufacturer,
                       julianday(expiry_date) - julianday('now') as days_until_expiry
                FROM products
                WHERE status = 'active' AND expiry_date IS NOT NULL
                  AND expiry_date < date('now', '+' || ? || ' days')
                ORDER BY expiry_date ASC
            """, (days,))
            return self._rows_to_dicts(cur.fetchall())

    # ── LEASE PAYMENTS ────────────────────────────────────

    def fetch_lease_payments(self, lease_id: Optional[str] = None) -> List[dict]:
        """Fetch lease payments, optionally filtered by lease_id."""
        if lease_id:
            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT payment_date, amount_paid, payment_method, notes FROM lease_payments WHERE lease_id = ? ORDER BY payment_date DESC",
                    (lease_id,),
                )
                return self._rows_to_dicts(cur.fetchall())
        with get_db_cursor() as cur:
            cur.execute("SELECT lease_id, amount_paid, payment_date FROM lease_payments")
            return self._rows_to_dicts(cur.fetchall())

    def insert_lease_payment(self, data: dict) -> int:
        """Insert a lease payment. Returns payment id."""
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO lease_payments ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    # ── CATEGORIES ────────────────────────────────────────

    def fetch_categories(self, active_only: bool = True) -> List[dict]:
        """Fetch categories."""
        query = "SELECT * FROM categories"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        with get_db_cursor() as cur:
            cur.execute(query)
            return self._rows_to_dicts(cur.fetchall())

    def insert_category(self, data: dict) -> int:
        """Insert a category. Returns category id."""
        self._sanitize_keys(data.keys())
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        with get_db_cursor() as cur:
            cur.execute(
                f"INSERT INTO categories ({columns}) VALUES ({placeholders})",
                values,
            )
            cur.execute("SELECT last_insert_rowid()")
            return cur.fetchone()[0]

    def fetch_category_by_id(self, category_id: int) -> Optional[dict]:
        """Fetch a category by ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None

    def fetch_supplier_by_id(self, supplier_id: int) -> Optional[dict]:
        """Fetch a supplier by ID."""
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None

    def fetch_id_by_name(self, table: str, name: str) -> Optional[int]:
        """Fetch an ID by name from a specified table (case-insensitive).
        
        Only allows specific tables for security (prevents SQL injection).
        """
        # Whitelist of allowed tables
        if table not in ('categories', 'suppliers', 'customers', 'products'):
            raise ValueError(f"Table '{table}' not allowed for name lookup")
        
        with get_db_cursor() as cur:
            cur.execute(f"SELECT id FROM {table} WHERE lower(name) = lower(?) LIMIT 1", (name,))
            row = cur.fetchone()
            if row:
                return row[0]
            return None

    # ── EXPORT / IMPORT ───────────────────────────────────

    def export_to_json(self) -> str:
        """Export key tables to JSON for backup."""
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

    def import_from_json(self, json_data: str) -> bool:
        """Import data from JSON backup.
        
        Security: Only known tables are allowed to prevent SQL injection.
        """
        # Whitelist of tables that can be imported into
        ALLOWED_TABLES = {
            "products", "sales", "categories", "suppliers", "customers",
            "locations", "invoices", "leases", "returns", "trade_ins",
            "service_tickets", "serial_numbers", "stock_transfers",
            "pharmacy_batches", "pharmacy_prescriptions", "settings",
            "users", "audit_log", "alerts", "purchase_orders",
            "sales_orders", "vertical_configs"
        }
        
        data = json.loads(json_data)
        with get_db_cursor() as cur:
            for table, rows in data.items():
                # Security check: only allow known tables
                if table not in ALLOWED_TABLES:
                    logger.warning(f"Import skipped unknown table: {table}")
                    continue
                    
                if not rows:
                    continue
                    
                # Validate column names
                columns = list(rows[0].keys())
                for col in columns:
                    if not col.isidentifier():
                        raise ValueError(f"Invalid column name in import: {col}")
                        
                placeholders = ','.join(['?' for _ in columns])
                col_names = ','.join(columns)
                for row in rows:
                    values = [row[col] for col in columns]
                    try:
                        cur.execute(
                            f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
                            values,
                        )
                    except Exception as e:
                        logger.error(f"Failed to import row into {table}: {e}")
        return True


# ============================================================
# Module-level singleton for convenience
# ============================================================
db = InventoryDB()


# ============================================================
# BACKWARD-COMPATIBILITY WRAPPERS
# These let existing imports keep working while we migrate.
# ============================================================

def get_inventory_unified():
    """Backward-compatible wrapper. Returns products as list of dicts."""
    try:
        products = db.fetch_products(active_only=True)
        # Map to the same dict shape the old function returned
        return [{
            "id": p.get('id'),
            "model": p.get('model'),
            "category": p.get('category_id'),
            "supplier": p.get('supplier_id'),
            "purchase_price": p.get('purchase_price'),
            "selling_price": p.get('selling_price'),
            "stock": p.get('stock'),
            "notes": p.get('notes'),
            "ram": p.get('ram'),
            "storage": p.get('storage'),
            "expiry_date": p.get('expiry_date'),
            "batch_number": p.get('batch_number'),
            "brand": p.get('brand'),
            "status": p.get('status'),
            "condition": p.get('condition'),
            "warranty_months": p.get('warranty_months'),
            "manufacturer": p.get('manufacturer'),
        } for p in products]
    except Exception as e:
        logging.debug(f"DB fetch failed, returning empty list: {e}")
        return []


def save_inventory_unified(data: List[dict]):
    """Backward-compatible wrapper. Upserts each product."""
    for item in data:
        try:
            db.upsert_product(item)
        except Exception as e:
            logging.error(f"Failed to save product {item.get('model')}: {e}")


# ============================================================
# DATABASE-BACKED AUTHENTICATION
# ============================================================

def create_user_db(username, password, role="staff", created_by=None, email=None, full_name=None):
    """
    Create a new user in the database with secure password hashing.
    
    Args:
        username: Unique username
        password: Plain text password (will be hashed)
        role: User role (admin, staff, etc.)
        created_by: ID of user who created this account
        email: User's email address
        full_name: User's full name
    
    Returns:
        int: The new user's ID
    
    Raises:
        ValueError: If user already exists
    """
    import hashlib
    import secrets
    
    # Hash the password
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100_000)
    password_hash_hex = password_hash.hex()
    
    with get_db_cursor() as cur:
        # Check if user exists
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            raise ValueError(f"User '{username}' already exists")
        
        # Insert new user
        cur.execute("""
            INSERT INTO users (username, password_hash, password_salt, password_algo, 
                             role, email, full_name, is_active, status, created_by)
            VALUES (?, ?, ?, 'pbkdf2', ?, ?, ?, 1, 'ACTIVE', ?)
        """, (username, password_hash_hex, salt, role, email, full_name, created_by))
        
        user_id = cur.lastrowid
        logging.info(f"User '{username}' created with ID {user_id}, role: {role}")
        return user_id


def verify_user_db(username, password):
    """
    Verify user credentials against the database.
    
    Args:
        username: Username to verify
        password: Plain text password to check
    
    Returns:
        tuple: (success: bool, role: str|None, user_id: int|None)
               Returns (True, role, user_id) on success, (False, None, None) on failure
    """
    import hashlib
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, username, password_hash, password_salt, password_algo, 
                   role, is_active, status
            FROM users 
            WHERE username = ?
        """, (username,))
        
        user = cur.fetchone()
        if not user:
            logging.warning(f"Login attempt for non-existent user: {username}")
            return False, None, None
        
        # Check if user is active
        if not user['is_active'] or user['status'] != 'ACTIVE':
            logging.warning(f"Login attempt for inactive user: {username}")
            return False, None, None
        
        # Verify password
        stored_hash = user['password_hash']
        salt = user['password_salt']
        algo = user['password_algo'] if user['password_algo'] else 'pbkdf2'
        
        try:
            if algo == 'pbkdf2':
                computed_hash = hashlib.pbkdf2_hmac(
                    'sha256', 
                    password.encode('utf-8'), 
                    salt.encode('utf-8'), 
                    100_000
                ).hex()
                
                if computed_hash != stored_hash:
                    logging.warning(f"Invalid password for user: {username}")
                    return False, None, None
            else:
                logging.error(f"Unsupported password algorithm: {algo}")
                return False, None, None
            
            # Update last login timestamp
            from datetime import datetime
            cur.execute("""
                UPDATE users 
                SET last_login = ? 
                WHERE id = ?
            """, (datetime.now().isoformat(), user['id']))
            
            logging.info(f"User '{username}' authenticated successfully, role: {user['role']}")
            return True, user['role'], user['id']
            
        except Exception as e:
            logging.error(f"Password verification failed for {username}: {e}")
            return False, None, None


def ensure_default_admin():
    """Create default admin user if it doesn't already exist."""
    with get_db_cursor() as cur:
        cur.execute("SELECT id FROM users WHERE username = 'admin'")
        if cur.fetchone():
            return  # Admin already exists

    try:
        user_id = create_user_db("admin", "admin123", role="admin", full_name="System Administrator")
        logging.info(f"Default admin user created with ID {user_id}")
    except ValueError:
        logging.info("Admin user already exists (possible race condition)")
    except Exception as e:
        logging.error(f"Failed to create default admin user: {e}")


def list_users_db(active_only=True):
    """
    List all users from the database.
    
    Args:
        active_only: If True, only return active users
    
    Returns:
        list[dict]: List of user records
    """
    query = "SELECT id, username, role, email, full_name, is_active, status, last_login, created_at FROM users"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY username"
    
    with get_db_cursor() as cur:
        cur.execute(query)
        return [dict(row) for row in cur.fetchall()]


def update_user_db(user_id, **kwargs):
    """
    Update user fields in the database.
    
    Args:
        user_id: ID of user to update
        **kwargs: Fields to update (role, email, full_name, is_active, status, etc.)
    """
    allowed_fields = {'role', 'email', 'full_name', 'is_active', 'status', 'password_hash', 'password_salt'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        raise ValueError(f"No valid fields to update. Allowed: {allowed_fields}")
    
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [user_id]
    
    with get_db_cursor() as cur:
        cur.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        logging.info(f"User {user_id} updated: {list(updates.keys())}")


def delete_user_db(user_id):
    """
    Soft-delete a user (set is_active = 0).
    
    Args:
        user_id: ID of user to delete
    """
    with get_db_cursor() as cur:
        cur.execute("UPDATE users SET is_active = 0, status = 'INACTIVE' WHERE id = ?", (user_id,))
        logging.info(f"User {user_id} soft-deleted")


def migrate_json_users_to_db():
    """
    Migrate users from JSON file (utils.py) to the database.
    Only migrates users that don't already exist in the DB.
    
    Returns:
        int: Number of users migrated
    """
    try:
        from utils import load_users as load_json_users
        
        json_users = load_json_users()
        if not json_users:
            logging.info("No JSON users to migrate")
            return 0
        
        migrated = 0
        for username, user_data in json_users.items():
            try:
                role = user_data.get('role', 'staff')
                algo = user_data.get('algo', 'pbkdf2')
                
                # Check if user already exists in DB
                with get_db_cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
                    if cur.fetchone():
                        logging.debug(f"User '{username}' already exists in DB, skipping")
                        continue
                    
                    # For PBKDF2 users, migrate hash and salt directly
                    if algo == 'pbkdf2' and 'hash' in user_data and 'salt' in user_data:
                        cur.execute("""
                            INSERT INTO users (username, password_hash, password_salt, 
                                             password_algo, role, is_active, status)
                            VALUES (?, ?, ?, 'pbkdf2', ?, 1, 'ACTIVE')
                        """, (username, user_data['hash'], user_data['salt'], role))
                        migrated += 1
                        logging.info(f"Migrated user '{username}' from JSON to DB (pbkdf2)")
                    
                    # For argon2 users, we need to re-hash on next login
                    elif algo == 'argon2' and 'hash' in user_data:
                        # Store argon2 hash temporarily, will be re-hashed on next password change
                        cur.execute("""
                            INSERT INTO users (username, password_hash, password_algo, 
                                             role, is_active, status)
                            VALUES (?, ?, 'argon2', ?, 1, 'ACTIVE')
                        """, (username, user_data['hash'], role))
                        migrated += 1
                        logging.info(f"Migrated user '{username}' from JSON to DB (argon2)")
                    
                    else:
                        logging.warning(f"Skipping user '{username}' - unsupported algo or missing hash")
                        
            except Exception as e:
                logging.error(f"Failed to migrate user '{username}': {e}")
                continue
        
        if migrated > 0:
            logging.info(f"Migration complete: {migrated} users moved from JSON to DB")
        
        return migrated
        
    except Exception as e:
        logging.error(f"JSON user migration failed: {e}")
        return 0


def get_db_stats():
    """Backward-compatible wrapper."""
    return db.get_stats()


# ============================================================
# SCHEMA INITIALIZATION & MIGRATION
# ============================================================

def init_database():
    """Initialize the database with all required tables."""
    with get_db_cursor() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        exists = cur.fetchone()
        if exists:
            logging.info("Database already initialized, checking for migrations")
            migrate_database()
            return

        cur.execute("""CREATE TABLE schema_version (
            version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # Settings
        cur.execute("""CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL,
            value TEXT, category TEXT DEFAULT 'general', description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        cur.execute("SELECT id FROM settings WHERE key = 'industry_type'")
        if not cur.fetchone():
            cur.execute("INSERT INTO settings (key, value) VALUES ('industry_type', 'electronics')")

        # Users
        cur.execute("""CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE,
            username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            password_salt TEXT, password_algo TEXT DEFAULT 'pbkdf2',
            security_pin_hash TEXT, role TEXT DEFAULT 'staff', email TEXT,
            full_name TEXT, phone TEXT, department TEXT, is_active INTEGER DEFAULT 1,
            status TEXT DEFAULT 'ACTIVE', device_fingerprint TEXT, ip_address TEXT,
            authorized_by TEXT, authorized_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, last_login TEXT,
            created_by INTEGER, FOREIGN KEY (created_by) REFERENCES users(id))""")

        # Locations
        cur.execute("""CREATE TABLE locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, type TEXT DEFAULT 'warehouse', address TEXT,
            city TEXT, country TEXT, phone TEXT, email TEXT, manager_id INTEGER,
            capacity INTEGER, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users(id))""")

        # Categories
        cur.execute("""CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            parent_id INTEGER, description TEXT, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id))""")

        # Suppliers
        cur.execute("""CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, contact_person TEXT, email TEXT, phone TEXT,
            mobile TEXT, address TEXT, city TEXT, country TEXT, gst_number TEXT,
            tax_id TEXT, payment_terms TEXT, lead_time_days INTEGER DEFAULT 7,
            rating INTEGER DEFAULT 5, notes TEXT, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # Products
        cur.execute("""CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE, model TEXT NOT NULL,
            category_id INTEGER, supplier_id INTEGER, barcode TEXT, qr_code TEXT,
            purchase_price REAL DEFAULT 0, selling_price REAL DEFAULT 0, cost_avg REAL DEFAULT 0,
            stock INTEGER DEFAULT 0, min_stock INTEGER DEFAULT 5, reorder_point INTEGER DEFAULT 10,
            max_stock INTEGER, brand TEXT, serial_number TEXT, ram TEXT, storage TEXT,
            screen_type TEXT, screen_size TEXT, camera TEXT, battery TEXT, color TEXT,
            warranty_months INTEGER, warranty_expiry TEXT,
            expiry_date TEXT, batch_number TEXT, manufacturer TEXT,
            dosage_form TEXT, strength TEXT,
            status TEXT DEFAULT 'active', condition TEXT DEFAULT 'new',
            default_location_id INTEGER, rack_location TEXT, shelf_location TEXT,
            description TEXT, notes TEXT, images TEXT, specifications TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (default_location_id) REFERENCES locations(id),
            FOREIGN KEY (created_by) REFERENCES users(id))""")

        # Product stock by location
        cur.execute("""CREATE TABLE product_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL, quantity INTEGER DEFAULT 0,
            reserved INTEGER DEFAULT 0,
            last_counted TEXT, last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_id, location_id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (location_id) REFERENCES locations(id))""")

        # Serial numbers
        cur.execute("""CREATE TABLE serial_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
            serial_number TEXT NOT NULL, status TEXT DEFAULT 'in_stock',
            purchase_date TEXT, warranty_start TEXT, warranty_end TEXT,
            sold_date TEXT, sale_id INTEGER, notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_id, serial_number),
            FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Purchase Orders
        cur.execute("""CREATE TABLE purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL, order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            expected_date TEXT, received_date TEXT, status TEXT DEFAULT 'draft',
            total_amount REAL DEFAULT 0, notes TEXT, created_by INTEGER,
            approved_by INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id))""")

        cur.execute("""CREATE TABLE po_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, po_id INTEGER NOT NULL,
            product_id INTEGER, sku TEXT, quantity_ordered INTEGER DEFAULT 0,
            quantity_received INTEGER DEFAULT 0, unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0, notes TEXT,
            FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Sales Orders
        cur.execute("""CREATE TABLE sales_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER, customer_name TEXT, customer_phone TEXT,
            customer_email TEXT, order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            delivery_date TEXT, status TEXT DEFAULT 'confirmed',
            total_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'pending', notes TEXT, created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id))""")

        cur.execute("""CREATE TABLE sales_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL, quantity INTEGER DEFAULT 0,
            unit_price REAL DEFAULT 0, total_price REAL DEFAULT 0,
            serial_number TEXT,
            FOREIGN KEY (order_id) REFERENCES sales_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Customers
        cur.execute("""CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            phone TEXT, email TEXT, address TEXT, city TEXT, country TEXT,
            gst_number TEXT, credit_limit REAL DEFAULT 0, balance REAL DEFAULT 0,
            notes TEXT, is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # Stock transfers
        cur.execute("""CREATE TABLE stock_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, transfer_number TEXT UNIQUE NOT NULL,
            from_location_id INTEGER NOT NULL, to_location_id INTEGER NOT NULL,
            transfer_date TEXT DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'pending',
            notes TEXT, created_by INTEGER, approved_by INTEGER,
            FOREIGN KEY (from_location_id) REFERENCES locations(id),
            FOREIGN KEY (to_location_id) REFERENCES locations(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id))""")

        cur.execute("""CREATE TABLE stock_transfer_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, transfer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL, quantity INTEGER DEFAULT 0,
            received_quantity INTEGER DEFAULT 0, notes TEXT,
            FOREIGN KEY (transfer_id) REFERENCES stock_transfers(id),
            FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Audit log
        cur.execute("""CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER, username TEXT, action TEXT NOT NULL, table_name TEXT,
            record_id INTEGER, old_values TEXT, new_values TEXT, ip_address TEXT,
            session_id TEXT, details TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id))""")

        # Sync queue
        cur.execute("""CREATE TABLE sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT, operation TEXT NOT NULL,
            table_name TEXT NOT NULL, record_id INTEGER, data TEXT,
            status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            synced_at TEXT, error_message TEXT, retry_count INTEGER DEFAULT 0)""")

        # Sync history
        cur.execute("""CREATE TABLE sync_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, sync_type TEXT NOT NULL,
            status TEXT NOT NULL, records_synced INTEGER DEFAULT 0,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP, completed_at TEXT,
            error_message TEXT, details TEXT)""")

        # Google credentials
        cur.execute("""CREATE TABLE google_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE NOT NULL,
            encrypted_token TEXT, token_expiry TEXT, refresh_token TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id))""")

        # Alerts
        cur.execute("""CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT NOT NULL,
            severity TEXT DEFAULT 'medium', title TEXT NOT NULL, message TEXT NOT NULL,
            record_type TEXT, record_id INTEGER, is_read INTEGER DEFAULT 0,
            is_acknowledged INTEGER DEFAULT 0, acknowledged_by INTEGER,
            acknowledged_at TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (acknowledged_by) REFERENCES users(id))""")

        # Alert settings
        cur.execute("""CREATE TABLE alert_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, alert_type TEXT UNIQUE NOT NULL,
            enabled INTEGER DEFAULT 1, threshold_value INTEGER,
            email_enabled INTEGER DEFAULT 0, sms_enabled INTEGER DEFAULT 0,
            in_app_enabled INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # Leases
        cur.execute("""CREATE TABLE leases (
            lease_id TEXT PRIMARY KEY, customer_name TEXT NOT NULL,
            customer_phone TEXT, customer_email TEXT, customer_address TEXT,
            product_id INTEGER, product_name TEXT NOT NULL, start_date TEXT,
            end_date TEXT, return_date TEXT, monthly_amount REAL DEFAULT 0,
            duration_months INTEGER DEFAULT 12, security_deposit REAL DEFAULT 0,
            security_deduction REAL DEFAULT 0, total_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'active', return_condition TEXT, return_notes TEXT,
            last_payment_date TEXT, notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT, FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Lease payments
        cur.execute("""CREATE TABLE lease_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, lease_id TEXT NOT NULL,
            payment_date TEXT, amount_paid REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash', payment_reference TEXT, notes TEXT,
            recorded_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lease_id) REFERENCES leases(lease_id))""")

        # Invoices
        cur.execute("""CREATE TABLE invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL, customer_id INTEGER,
            customer_name TEXT NOT NULL, customer_email TEXT, customer_phone TEXT,
            customer_address TEXT, invoice_date TEXT, due_date TEXT,
            payment_terms TEXT, subtotal REAL DEFAULT 0, tax_rate REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0, discount_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0, amount_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'pending', notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by TEXT)""")

        # Invoice items
        cur.execute("""CREATE TABLE invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL,
            product_id INTEGER, product_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0, unit_price REAL DEFAULT 0,
            discount_percent REAL DEFAULT 0, discount_amount REAL DEFAULT 0,
            line_total REAL DEFAULT 0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
            FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Invoice payments
        cur.execute("""CREATE TABLE invoice_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER NOT NULL,
            payment_date TEXT, amount_paid REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'cash', payment_reference TEXT, notes TEXT,
            recorded_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id))""")

        # Returns
        cur.execute("""CREATE TABLE returns (
            return_id INTEGER PRIMARY KEY AUTOINCREMENT,
            return_number TEXT UNIQUE NOT NULL, invoice_id INTEGER,
            customer_name TEXT NOT NULL, customer_email TEXT, customer_phone TEXT,
            return_date TEXT, reason TEXT, status TEXT DEFAULT 'pending',
            total_refund REAL DEFAULT 0, refund_method TEXT, notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by TEXT,
            FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id))""")

        # Return items
        cur.execute("""CREATE TABLE return_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, return_id INTEGER NOT NULL,
            product_id INTEGER, product_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0, unit_price REAL DEFAULT 0,
            line_total REAL DEFAULT 0, condition TEXT DEFAULT 'good',
            restock INTEGER DEFAULT 1,
            FOREIGN KEY (return_id) REFERENCES returns(return_id),
            FOREIGN KEY (product_id) REFERENCES products(id))""")

        # Trade-ins
        cur.execute("""CREATE TABLE trade_ins (
            trade_in_id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_in_number TEXT UNIQUE NOT NULL, customer_name TEXT NOT NULL,
            customer_phone TEXT, product_name TEXT NOT NULL,
            product_condition TEXT, trade_in_value REAL DEFAULT 0,
            credit_amount REAL DEFAULT 0, status TEXT DEFAULT 'pending',
            notes TEXT, trade_in_date TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT)""")

        # Service tickets
        cur.execute("""CREATE TABLE service_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL, customer_name TEXT NOT NULL,
            customer_phone TEXT, customer_email TEXT, device_type TEXT,
            device_brand TEXT, device_model TEXT, serial_number TEXT,
            issue_description TEXT, status TEXT DEFAULT 'received',
            estimated_cost REAL DEFAULT 0, final_cost REAL DEFAULT 0,
            notes TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, created_by TEXT)""")

        # Prescriptions
        cur.execute("""CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, patient_name TEXT,
            doctor_name TEXT, items TEXT, status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # License
        cur.execute("""CREATE TABLE license (
            id INTEGER PRIMARY KEY AUTOINCREMENT, license_key TEXT UNIQUE,
            admin_email TEXT NOT NULL, device_fingerprint TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE', licensed_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # Admin hierarchy
        cur.execute("""CREATE TABLE admin_hierarchy (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            role_level INTEGER, can_authorize_admins INTEGER DEFAULT 0,
            can_authorize_staff INTEGER DEFAULT 0, can_deactivate_users INTEGER DEFAULT 0,
            created_at TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id), FOREIGN KEY (user_id) REFERENCES users(user_id))""")

        # Authorization log
        cur.execute("""CREATE TABLE authorization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, authorized_by TEXT,
            authorized_user TEXT, action TEXT, timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # User authorization requests
        cur.execute("""CREATE TABLE user_authorization_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE,
            username TEXT NOT NULL, email TEXT NOT NULL, department TEXT,
            reason TEXT, status TEXT DEFAULT 'PENDING', requested_date TEXT,
            approved_by TEXT, approved_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

        # User permissions
        cur.execute("""CREATE TABLE user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            permission_key TEXT NOT NULL, permission_value INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, permission_key),
            FOREIGN KEY (user_id) REFERENCES users(id))""")

        # Views
        cur.execute("""CREATE VIEW IF NOT EXISTS v_low_stock AS
            SELECT p.id, p.sku, p.model, p.stock, p.min_stock, p.reorder_point,
                p.supplier_id, s.name as supplier_name,
                CASE WHEN p.stock <= 0 THEN 'critical'
                     WHEN p.stock <= p.min_stock THEN 'critical'
                     WHEN p.stock <= p.reorder_point THEN 'warning'
                     ELSE 'ok' END as stock_status
            FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.stock <= p.reorder_point AND p.status = 'active'""")

        cur.execute("""CREATE VIEW IF NOT EXISTS v_stock_value AS
            SELECT p.id, p.sku, p.model, p.stock, p.purchase_price, p.selling_price,
                (p.stock * p.purchase_price) as cost_value,
                (p.stock * p.selling_price) as retail_value,
                (p.stock * (p.selling_price - p.purchase_price)) as potential_profit
            FROM products p WHERE p.status = 'active'""")

        cur.execute("""CREATE VIEW IF NOT EXISTS v_prescriptions_active AS
            SELECT * FROM prescriptions WHERE status = 'pending'""")

        # Indexes for performance optimization
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_model ON products(model)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_status ON products(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sales_order_items_order_id ON sales_order_items(order_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_po_items_po_id ON po_items(po_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_locations_active ON locations(is_active)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_returns_status ON returns(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read, created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(username, timestamp DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_product ON serial_numbers(product_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_product_stock_lookup ON product_stock(product_id, location_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)")

        # Default data
        cur.execute("INSERT OR IGNORE INTO locations (code, name, type, address, city, country) VALUES ('MAIN', 'Main Warehouse', 'warehouse', '', '', 'Pakistan')")

        default_settings = [
            ('company_name', 'Mintaka Sphere', 'general', 'Company name'),
            ('currency', 'PKR', 'general', 'Default currency'),
            ('tax_rate', '0', 'general', 'Default tax rate percentage'),
            ('low_stock_threshold', '10', 'alerts', 'Default low stock threshold'),
            ('backup_frequency', 'daily', 'backup', 'Backup frequency'),
            ('sync_frequency', '10', 'sync', 'Google Drive sync frequency in minutes'),
            ('auto_sync_enabled', '0', 'sync', 'Enable automatic sync'),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO settings (key, value, category, description) VALUES (?, ?, ?, ?)",
            default_settings,
        )

        alert_types = [
            ('low_stock', 10, 1, 0, 1), ('out_of_stock', 0, 1, 0, 1),
            ('overstock', 100, 0, 0, 1), ('expiry_warning', 30, 1, 0, 1),
            ('warranty_expiry', 30, 0, 0, 1),
        ]
        cur.executemany(
            "INSERT OR IGNORE INTO alert_settings (alert_type, threshold_value, enabled, email_enabled, in_app_enabled) VALUES (?, ?, ?, ?, ?)",
            alert_types,
        )

        cur.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
        logging.info(f"Database initialized with schema version {SCHEMA_VERSION}")


def migrate_database():
    """Run database migrations if needed."""
    with get_db_cursor() as cur:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
        if not cur.fetchone():
            logging.warning("schema_version table missing, cannot migrate")
            return

        cur.execute("SELECT version FROM schema_version")
        row = cur.fetchone()
        current_version = row['version'] if row else 0

        if current_version >= SCHEMA_VERSION:
            return

        logging.info(f"Migrating database from version {current_version} to {SCHEMA_VERSION}")

        if current_version < 2:
            try:
                cur.execute("PRAGMA table_info(users)")
                columns = [col[1] for col in cur.fetchall()]
                for col_name in ('security_pin_hash', 'authorized_date', 'authorized_by'):
                    if col_name not in columns:
                        cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} TEXT")
                        logging.info(f"Added {col_name} column to users table")
            except Exception as e:
                logging.warning(f"Migration column check failed: {e}")

        if current_version < 3:
            # Add performance indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_products_model ON products(model)",
                "CREATE INDEX IF NOT EXISTS idx_products_status ON products(status)",
                "CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id)",
                "CREATE INDEX IF NOT EXISTS idx_products_supplier_id ON products(supplier_id)",
                "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
                "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
                "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
                "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date DESC)",
                "CREATE INDEX IF NOT EXISTS idx_sales_order_items_order_id ON sales_order_items(order_id)",
                "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
                "CREATE INDEX IF NOT EXISTS idx_po_items_po_id ON po_items(po_id)",
                "CREATE INDEX IF NOT EXISTS idx_locations_active ON locations(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)",
                "CREATE INDEX IF NOT EXISTS idx_returns_status ON returns(status)",
                "CREATE INDEX IF NOT EXISTS idx_alerts_unread ON alerts(is_read, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status)",
                "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(username, timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_serial_numbers_product ON serial_numbers(product_id)",
                "CREATE INDEX IF NOT EXISTS idx_product_stock_lookup ON product_stock(product_id, location_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            ]
            for idx_sql in indexes:
                try:
                    cur.execute(idx_sql)
                except Exception as e:
                    logging.warning(f"Failed to create index: {e}")
            logging.info("Added performance indexes for version 3")

        if current_version < 4:
            try:
                cur.execute("PRAGMA table_info(products)")
                columns = [col[1] for col in cur.fetchall()]
                if 'screen_type' not in columns:
                    cur.execute("ALTER TABLE products ADD COLUMN screen_type TEXT")
                    logging.info("Added screen_type column to products table")
            except Exception as e:
                logging.warning(f"Migration screen_type check failed: {e}")

        cur.execute("UPDATE schema_version SET version = ?", (max(current_version, SCHEMA_VERSION),))
        logging.info(f"Database migrated to version {max(current_version, SCHEMA_VERSION)}")


# NOTE: Database initialization is now EXPLICIT, not automatic on import.
# Call init_database() and migrate_database() from main() only.
# This prevents side-effects during tests and helper script imports.
