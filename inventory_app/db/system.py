"""
System Database Module
=======================
Handles locations, suppliers, customers, users, settings, leases,
serial numbers, trade-ins, service tickets, and system utilities.
"""

import json
import sqlite3
import logging
from typing import List, Optional

try:
    from .database import get_db_cursor, get_connection, InventoryDB
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection, InventoryDB

logger = logging.getLogger(__name__)


class SystemDBMixin:
    """Mixin for system-related database operations."""

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
        """Return the current industry type (e.g. 'retail', 'pharma')."""
        val = self.get_setting("industry_type")
        return val if val else "retail"

    def set_industry_type(self, industry: str) -> bool:
        return self.set_setting("industry_type", industry, "general", "Current industry type")

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
