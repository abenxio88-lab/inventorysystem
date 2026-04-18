"""
Inventory Database Module
==========================
Handles all product-related database operations.
"""

import logging
from typing import List, Optional

try:
    from .database import get_db_cursor, InventoryDB
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, InventoryDB

logger = logging.getLogger(__name__)


class InventoryDBMixin:
    """Mixin for inventory/product database operations."""

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

    def resolve_category_display(self, category_id) -> str:
        """Return human-friendly category text for tree/form."""
        if category_id is None:
            return ""
        try:
            cid_int = int(category_id)
            with get_db_cursor() as cur:
                cur.execute("SELECT name FROM categories WHERE id = ?", (cid_int,))
                row = cur.fetchone()
                if row and row.get("name"):
                    return f"{row['name']} (ID: {cid_int})"
        except Exception:
            pass
        return str(category_id)

    def resolve_supplier_display(self, supplier_id) -> str:
        """Return human-friendly supplier text for tree/form."""
        if supplier_id is None:
            return ""
        try:
            sid_int = int(supplier_id)
            with get_db_cursor() as cur:
                cur.execute("SELECT name FROM suppliers WHERE id = ?", (sid_int,))
                row = cur.fetchone()
                if row and row.get("name"):
                    return f"{row['name']} (ID: {sid_int})"
        except Exception:
            pass
        return str(supplier_id)

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
