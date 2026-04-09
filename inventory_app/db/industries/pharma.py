"""
PHARMA Industry Database Module
=================================
Handles PHARMACY-specific database operations:
- Products with batch numbers, expiry dates
- Manufacturer tracking
- Dosage forms and strength
- Prescription tracking
- Expiry monitoring and alerts

This module EXTENDS the base classes.
ZERO duplication - only PHARMA-specific logic here.
"""

import logging
from typing import List, Optional, Dict

from ..base import DatabaseConnection, BaseRepository

logger = logging.getLogger(__name__)


class PharmaProductRepository(BaseRepository):
    """
    PHARMA product operations.
    Products with batch tracking, expiry, dosage information.
    """
    
    # Whitelist of allowed columns (pharma-specific)
    _ALLOWED_COLUMNS = {
        "products": {
            # Base fields (inherited)
            "id", "model", "category", "brand", "supplier", 
            "purchase_price", "selling_price", "stock", 
            "reorder_point", "description", "notes", 
            "status", "created_at", "updated_at",
            # Pharma-specific fields
            "batch_number", "expiry_date", "manufacturer",
            "dosage_form", "strength", "prescription_required"
        }
    }
    
    def fetch_products(self, active_only: bool = True) -> List[dict]:
        """Fetch all pharma products."""
        query = "SELECT * FROM products"
        if active_only:
            query += " WHERE status = 'active'"
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            return self.rows_to_dicts(cur.fetchall())
    
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
    
    def fetch_product_by_batch(self, batch_number: str) -> List[dict]:
        """Fetch products by batch number (pharma-specific)."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM products WHERE batch_number = ?", 
                (batch_number,)
            )
            return self.rows_to_dicts(cur.fetchall())
    
    def insert_product(self, data: dict) -> int:
        """Insert a new pharma product."""
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
            logger.info(f"Pharma product created: {data.get('model')} Batch: {data.get('batch_number')} (ID: {product_id})")
            return product_id
    
    def update_product(self, model: str, data: dict) -> bool:
        """Update a pharma product."""
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
                logger.info(f"Pharma product updated: {model}")
            return success
    
    def delete_product(self, model: str) -> bool:
        """Soft-delete a pharma product."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET status = 'deleted', updated_at = CURRENT_TIMESTAMP WHERE model = ?",
                (model,)
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Pharma product soft-deleted: {model}")
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


class PharmaExpiryRepository(BaseRepository):
    """
    PHARMA expiry tracking and alerts.
    Monitor product expiry dates.
    """
    
    def fetch_expiring_products(self, days: int = 30) -> List[dict]:
        """Fetch products expiring within N days."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, model, batch_number, stock, expiry_date, manufacturer,
                       julianday(expiry_date) - julianday('now') as days_until_expiry,
                       CASE 
                           WHEN expiry_date < date('now') THEN 'expired'
                           WHEN expiry_date < date('now', '+7 days') THEN 'critical'
                           WHEN expiry_date < date('now', '+30 days') THEN 'warning'
                           ELSE 'ok'
                       END as expiry_status
                FROM products
                WHERE status = 'active' 
                  AND expiry_date IS NOT NULL
                  AND expiry_date < date('now', '+' || ? || ' days')
                ORDER BY expiry_date ASC
            """, (days,))
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_expired_products(self) -> List[dict]:
        """Fetch products that have already expired."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, model, batch_number, stock, expiry_date, manufacturer,
                       julianday('now') - julianday(expiry_date) as days_expired
                FROM products
                WHERE status = 'active' 
                  AND expiry_date IS NOT NULL
                  AND expiry_date < date('now')
                ORDER BY expiry_date ASC
            """)
            return self.rows_to_dicts(cur.fetchall())
    
    def fetch_batches(self) -> List[dict]:
        """Fetch all active batches with supplier info."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT p.model, p.batch_number, p.stock, p.expiry_date,
                       p.manufacturer, s.name as supplier_name
                FROM products p
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.batch_number IS NOT NULL AND p.status = 'active'
                ORDER BY p.expiry_date ASC
            """)
            return self.rows_to_dicts(cur.fetchall())


class PharmaPrescriptionRepository(BaseRepository):
    """
    PHARMA prescription tracking.
    Manage prescriptions for prescription-required products.
    """
    
    def fetch_prescriptions(self, status: Optional[str] = None) -> List[dict]:
        """Fetch prescriptions, optionally filtered by status."""
        query = "SELECT * FROM prescriptions"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return self.rows_to_dicts(cur.fetchall())
    
    def insert_prescription(self, data: dict) -> int:
        """Create a new prescription."""
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO prescriptions 
                   (patient_name, doctor_name, items, status) 
                   VALUES (?, ?, ?, ?)""",
                (
                    data.get("patient_name"),
                    data.get("doctor_name"),
                    data.get("items"),  # JSON string of items
                    data.get("status", "pending")
                )
            )
            rx_id = cur.lastrowid
            logger.info(f"Prescription created: #{rx_id}")
            return rx_id
    
    def update_prescription_status(self, rx_id: int, status: str) -> bool:
        """Update prescription status."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE prescriptions SET status = ? WHERE id = ?",
                (status, rx_id)
            )
            success = cur.rowcount > 0
            if success:
                logger.info(f"Prescription #{rx_id} status updated: {status}")
            return success


class PharmaStatsRepository(BaseRepository):
    """
    PHARMA statistics and reporting.
    """
    
    def get_stats(self) -> dict:
        """Get pharma dashboard statistics."""
        stats = {}
        
        with self.conn.cursor() as cur:
            # Total products
            cur.execute(
                "SELECT COUNT(*) as count FROM products WHERE status = 'active'"
            )
            stats['total_products'] = cur.fetchone()['count']
            
            # Expired products
            cur.execute("""
                SELECT COUNT(*) as count FROM products 
                WHERE status = 'active' 
                  AND expiry_date IS NOT NULL
                  AND expiry_date < date('now')
            """)
            stats['expired_count'] = cur.fetchone()['count']
            
            # Expiring soon (30 days)
            cur.execute("""
                SELECT COUNT(*) as count FROM products 
                WHERE status = 'active' 
                  AND expiry_date IS NOT NULL
                  AND expiry_date < date('now', '+30 days')
                  AND expiry_date >= date('now')
            """)
            stats['expiring_soon_count'] = cur.fetchone()['count']
            
            # Total batches
            cur.execute("""
                SELECT COUNT(DISTINCT batch_number) as count FROM products 
                WHERE batch_number IS NOT NULL AND status = 'active'
            """)
            stats['total_batches'] = cur.fetchone()['count']
            
            # Pending prescriptions
            cur.execute(
                "SELECT COUNT(*) as count FROM prescriptions WHERE status = 'pending'"
            )
            stats['pending_prescriptions'] = cur.fetchone()['count']
        
        return stats
