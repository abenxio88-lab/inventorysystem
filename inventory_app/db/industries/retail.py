"""
RETAIL Industry Database Module
================================
Handles RETAIL-specific database operations:
- Simple products (basic fields only)
- Standard sales/orders
- Basic customers/suppliers
- NO serial numbers, batches, or expiry dates

This module EXTENDS the base classes.
ZERO duplication - only RETAIL-specific logic here.
"""

import logging
from typing import List, Optional, Dict

from ..base import DatabaseConnection, BaseRepository

logger = logging.getLogger(__name__)


class RetailProductRepository(BaseRepository):
    """
    RETAIL product operations.
    Simple products with basic fields only.
    """
    
    # Whitelist of allowed columns for security
    _ALLOWED_COLUMNS = {
        "products": {
            "id", "model", "category", "brand", "supplier", 
            "purchase_price", "selling_price", "stock", 
            "reorder_point", "min_stock", "max_stock",
            "description", "notes", "status", "condition",
            "created_at", "updated_at"
        }
    }
    
    def fetch_products(self, active_only: bool = True) -> List[dict]:
        """Fetch all retail products."""
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE status = 'active'"
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_product_by_model(self, model: str) -> Optional[dict]:
        """Fetch a single product by model."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE model = ?", (model,))
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def fetch_product_by_id(self, product_id: int) -> Optional[dict]:
        """Fetch a single product by ID."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def insert_product(self, data: dict) -> int:
        """Insert a new retail product."""
        self.sanitize_keys(data.keys(), whitelist=self._ALLOWED_COLUMNS)
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = list(data.values())
        
        with self.conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO products ({columns}) VALUES ({placeholders})",
                values
            )
            cur.execute("SELECT last_insert_rowid()")
            product_id = cur.fetchone()[0]
            logger.info(f"Retail product created: {data.get('model')} (ID: {product_id})")
            return product_id
    
    def update_product(self, model: str, data: dict) -> bool:
        """Update an existing retail product."""
        if not data:
            return False
        
        self.sanitize_keys(data.keys(), whitelist=self._ALLOWED_COLUMNS)
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [model]
        
        with self.conn.cursor() as cur:
            cur.execute(
                f"UPDATE products SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                values
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Retail product updated: {model}")
            return success
    
    def delete_product(self, model: str) -> bool:
        """Soft-delete a retail product."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (model,)
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Retail product soft-deleted: {model}")
            return success
    
    def adjust_stock(self, model: str, delta: int) -> bool:
        """Adjust product stock (delta can be negative)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET stock = stock + ?, updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (delta, model)
            )
            return cur.rowcount > 0
    
    def set_stock(self, model: str, quantity: int) -> bool:
        """Set absolute stock quantity."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET stock = ?, updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (quantity, model)
            )
            return cur.rowcount > 0


class RetailSalesRepository(BaseRepository):
    """
    RETAIL sales operations.
    Simple sales without serial numbers or complex tracking.
    """
    
    def fetch_sales_orders(self, status: Optional[str] = None) -> List[dict]:
        """Fetch all sales orders."""
        query = "SELECT * FROM sales_orders"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY order_date DESC"
        
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_sales_order_items(self, order_id: int) -> List[dict]:
        """Fetch items for a sales order."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM sales_order_items WHERE order_id = ?", 
                (order_id,)
            )
            return self.rows_to_dicts(cur.fetchall())
    
    def insert_sales_order(self, order_data: dict, items: List[dict]) -> int:
        """Insert a sales order with items."""
        with self.conn.cursor() as cur:
            # Insert order
            columns = ", ".join(order_data.keys())
            placeholders = ", ".join(["?"] * len(order_data))
            values = list(order_data.values())
            
            cur.execute(
                f"INSERT INTO sales_orders ({columns}) VALUES ({placeholders})",
                values
            )
            cur.execute("SELECT last_insert_rowid()")
            order_id = cur.fetchone()[0]
            
            # Insert order items
            for item in items:
                cur.execute(
                    """INSERT INTO sales_order_items 
                       (order_id, product_id, quantity, unit_price, total_price) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        order_id, 
                        item.get("product_id"), 
                        item.get("quantity", 0),
                        item.get("unit_price", 0), 
                        item.get("total_price", 0)
                    )
                )
            
            logger.info(f"Retail sales order created: #{order_id}")
            return order_id
    
    def delete_sales_order(self, order_id: int) -> bool:
        """Delete a sales order and its items."""
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM sales_order_items WHERE order_id = ?", 
                (order_id,)
            )
            cur.execute(
                "DELETE FROM sales_orders WHERE id = ?", 
                (order_id,)
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Retail sales order deleted: #{order_id}")
            return success


class RetailStatsRepository(BaseRepository):
    """
    RETAIL statistics and reporting.
    """
    
    def get_stats(self) -> dict:
        """Get retail dashboard statistics."""
        stats = {}
        
        with self.conn.cursor() as cur:
            # Total products
            cur.execute(
                "SELECT COUNT(*) as count FROM products WHERE status = 'active'"
            )
            stats['total_products'] = cur.fetchone()['count']
            
            # Total stock
            cur.execute(
                "SELECT COALESCE(SUM(stock), 0) as total FROM products WHERE status = 'active'"
            )
            stats['total_stock'] = cur.fetchone()['total']
            
            # Low stock count
            cur.execute(
                """SELECT COUNT(*) as count FROM products 
                   WHERE status = 'active' AND stock <= reorder_point"""
            )
            stats['low_stock_count'] = cur.fetchone()['count']
            
            # Total sales
            cur.execute("SELECT COUNT(*) as count FROM sales_orders")
            stats['total_sales'] = cur.fetchone()['count']
        
        return stats
