"""
ELECTRONICS Industry Database Module
=====================================
Handles ELECTRONICS-specific database operations:
- Products with serial numbers, IMEI, warranty
- Device specifications (RAM, storage, screen, camera, battery)
- Warranty tracking and expiry
- Device condition tracking (new, refurbished, used)

This module EXTENDS the base classes.
ZERO duplication - only ELECTRONICS-specific logic here.
"""

import logging
from typing import List, Optional, Dict

from ..base import DatabaseConnection, BaseRepository

logger = logging.getLogger(__name__)


class ElectronicsProductRepository(BaseRepository):
    """
    ELECTRONICS product operations.
    Products with serial numbers, IMEI, warranty, specifications.
    """
    
    # Whitelist of allowed columns (electronics-specific)
    _ALLOWED_COLUMNS = {
        "products": {
            # Base fields (inherited)
            "id", "model", "category", "brand", "supplier", 
            "purchase_price", "selling_price", "stock", 
            "reorder_point", "description", "notes", 
            "status", "created_at", "updated_at",
            # Electronics-specific fields
            "serial_number", "imei", "ram", "storage",
            "screen_type", "screen_size", "camera", "battery",
            "color", "warranty_months", "warranty_expiry",
            "device_condition", "specifications"
        }
    }
    
    def fetch_products(self, active_only: bool = True) -> List[dict]:
        """Fetch all electronics products."""
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE status = 'active'"
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_product_by_serial(self, serial_number: str) -> Optional[dict]:
        """Fetch a product by serial number (electronics-specific)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM products WHERE serial_number = ?", 
                (serial_number,)
            )
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def fetch_product_by_imei(self, imei: str) -> Optional[dict]:
        """Fetch a product by IMEI (electronics-specific)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM products WHERE imei = ?", 
                (imei,)
            )
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def fetch_product_by_model(self, model: str) -> Optional[dict]:
        """Fetch a product by model."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE model = ?", (model,))
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def fetch_product_by_id(self, product_id: int) -> Optional[dict]:
        """Fetch a product by ID."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def insert_product(self, data: dict) -> int:
        """Insert a new electronics product."""
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
            logger.info(f"Electronics product created: {data.get('model')} (ID: {product_id})")
            return product_id
    
    def update_product(self, model: str, data: dict) -> bool:
        """Update an electronics product."""
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
                logger.info(f"Electronics product updated: {model}")
            return success
    
    def delete_product(self, model: str) -> bool:
        """Soft-delete an electronics product."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (model,)
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Electronics product soft-deleted: {model}")
            return success
    
    def adjust_stock(self, model: str, delta: int) -> bool:
        """Adjust product stock."""
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


class ElectronicsSerialRepository(BaseRepository):
    """
    ELECTRONICS serial number tracking.
    Tracks individual devices with warranty, IMEI, status.
    """
    
    def fetch_serial_numbers(self, product_id: Optional[int] = None) -> List[dict]:
        """Fetch serial numbers, optionally filtered by product."""
        query = "SELECT * FROM serial_numbers"
        params = []
        
        if product_id:
            query += " WHERE product_id = ?"
            params.append(product_id)
        
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_by_serial(self, serial_number: str) -> Optional[dict]:
        """Fetch a specific serial number record."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM serial_numbers WHERE serial_number = ?", 
                (serial_number,)
            )
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def insert_serial_number(self, data: dict) -> int:
        """Register a new serial number."""
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO serial_numbers 
                   (product_id, serial_number, status, warranty_start, warranty_end) 
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    data.get("product_id"),
                    data.get("serial_number"),
                    data.get("status", "in_stock"),
                    data.get("warranty_start"),
                    data.get("warranty_end")
                )
            )
            sn_id = cur.lastrowid
            logger.info(f"Serial number registered: {data.get('serial_number')}")
            return sn_id
    
    def update_serial_status(self, serial_number: str, status: str) -> bool:
        """Update serial number status (sold, in_stock, returned, etc.)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE serial_numbers SET status = ? WHERE serial_number = ?",
                (status, serial_number)
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Serial number status updated: {serial_number} -> {status}")
            return success


class ElectronicsWarrantyRepository(BaseRepository):
    """
    ELECTRONICS warranty tracking.
    Monitor warranty expiry dates.
    """
    
    def fetch_expiring_warranties(self, days: int = 30) -> List[dict]:
        """Fetch products with warranties expiring within N days."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, model, serial_number, warranty_expiry,
                       julianday(warranty_expiry) - julianday('now') as days_remaining
                FROM products
                WHERE status = 'active' 
                  AND warranty_expiry IS NOT NULL
                  AND warranty_expiry < date('now', '+' || ? || ' days')
                ORDER BY warranty_expiry ASC
            """, (days,))
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_expired_warranties(self) -> List[dict]:
        """Fetch products with expired warranties."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, model, serial_number, warranty_expiry,
                       julianday('now') - julianday(warranty_expiry) as days_expired
                FROM products
                WHERE status = 'active' 
                  AND warranty_expiry IS NOT NULL
                  AND warranty_expiry < date('now')
                ORDER BY warranty_expiry ASC
            """)
            return self.rows_to_dicts(cur.fetchall())


class ElectronicsStatsRepository(BaseRepository):
    """
    ELECTRONICS statistics and reporting.
    """
    
    def get_stats(self) -> dict:
        """Get electronics dashboard statistics."""
        stats = {}
        
        with self.conn.cursor() as cur:
            # Total products
            cur.execute(
                "SELECT COUNT(*) as count FROM products WHERE status = 'active'"
            )
            stats['total_products'] = cur.fetchone()['count']
            
            # Total serial numbers registered
            cur.execute("SELECT COUNT(*) as count FROM serial_numbers")
            stats['total_serial_numbers'] = cur.fetchone()['count']
            
            # Warranty expiring soon
            cur.execute("""
                SELECT COUNT(*) as count FROM products 
                WHERE status = 'active' 
                  AND warranty_expiry IS NOT NULL
                  AND warranty_expiry < date('now', '+30 days')
            """)
            stats['expiring_warranties'] = cur.fetchone()['count']
            
            # Products by condition
            cur.execute("""
                SELECT device_condition, COUNT(*) as count 
                FROM products 
                WHERE status = 'active'
                GROUP BY device_condition
            """)
            stats['by_condition'] = {
                row['device_condition']: row['count'] 
                for row in cur.fetchall()
            }
        
        return stats
