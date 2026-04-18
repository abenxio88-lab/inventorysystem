"""
Orders Database Module
=======================
Handles sales orders, purchase orders, invoices, returns, and transfers.
"""

import logging
from typing import List, Optional
from datetime import datetime

try:
    from .database import get_db_cursor, InventoryDB
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, InventoryDB

logger = logging.getLogger(__name__)


class OrdersDBMixin:
    """Mixin for order-related database operations."""

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

    # ── RETURNS / RMA ─────────────────────────────────────

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
