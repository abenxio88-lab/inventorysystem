"""
Alerts & Notifications Module
==============================
Real-time alerts for low stock, system events, and notifications.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict

try:
    from .database import get_db_cursor, get_connection
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection


class AlertManager:
    """
    Manages system alerts and notifications.
    """
    
    def __init__(self):
        pass
    
    def create_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "medium",
        record_type: str = None,
        record_id: int = None
    ) -> int:
        """
        Create a new alert.
        
        Args:
            alert_type: Type of alert (low_stock, expiry, etc.)
            title: Alert title
            message: Alert message
            severity: low, medium, high, critical
            record_type: Related table name
            record_id: Related record ID
        
        Returns:
            Alert ID
        """
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO alerts 
                (alert_type, severity, title, message, record_type, record_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (alert_type, severity, title, message, record_type, record_id))
            
            alert_id = cur.lastrowid
            logging.info(f"Alert created: {alert_type} - {title}")
            return alert_id
    
    def get_unread_alerts(self, limit: int = 50) -> List[Dict]:
        """Get all unread alerts."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, alert_type, severity, title, message, 
                       record_type, record_id, created_at
                FROM alerts
                WHERE is_read = 0
                ORDER BY 
                    CASE severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END,
                    created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_all_alerts(self, limit: int = 100) -> List[Dict]:
        """Get all alerts (read and unread)."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, alert_type, severity, title, message,
                       record_type, record_id, is_read, is_acknowledged,
                       acknowledged_by, acknowledged_at, created_at
                FROM alerts
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cur.fetchall()]
    
    def mark_as_read(self, alert_id: int) -> bool:
        """Mark an alert as read."""
        with get_db_cursor() as cur:
            cur.execute("""
                UPDATE alerts SET is_read = 1 WHERE id = ?
            """, (alert_id,))
            return cur.rowcount > 0
    
    def mark_all_as_read(self) -> int:
        """Mark all alerts as read."""
        with get_db_cursor() as cur:
            cur.execute("UPDATE alerts SET is_read = 1")
            return cur.rowcount
    
    def acknowledge_alert(self, alert_id: int, user_id: int) -> bool:
        """Acknowledge an alert."""
        with get_db_cursor() as cur:
            cur.execute("""
                UPDATE alerts 
                SET is_acknowledged = 1, 
                    acknowledged_by = ?,
                    acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id, alert_id))
            return cur.rowcount > 0
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert."""
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            return cur.rowcount > 0
    
    def delete_old_alerts(self, days: int = 30) -> int:
        """Delete alerts older than specified days."""
        with get_db_cursor() as cur:
            cur.execute("""
                DELETE FROM alerts 
                WHERE created_at < datetime('now', ?)
                AND is_acknowledged = 1
            """, (f'-{days} days',))
            return cur.rowcount
    
    def get_alert_count(self, unread_only: bool = False) -> int:
        """Get alert count."""
        with get_db_cursor() as cur:
            if unread_only:
                cur.execute("SELECT COUNT(*) as count FROM alerts WHERE is_read = 0")
            else:
                cur.execute("SELECT COUNT(*) as count FROM alerts")
            
            row = cur.fetchone()
            return row['count'] if row else 0
    
    def check_low_stock_alerts(self) -> List[int]:
        """
        Check for low stock and create alerts.
        Returns list of product IDs that triggered alerts.
        """
        alerted = []
        
        with get_db_cursor() as cur:
            # Get products below reorder point
            cur.execute("""
                SELECT id, model, stock, reorder_point, min_stock
                FROM products
                WHERE stock <= reorder_point
                AND status = 'active'
            """)
            
            products = cur.fetchall()
            
            for product in products:
                # Check if alert already exists (unread)
                cur.execute("""
                    SELECT id FROM alerts
                    WHERE alert_type = 'low_stock'
                    AND record_type = 'products'
                    AND record_id = ?
                    AND is_read = 0
                """, (product['id'],))
                
                if cur.fetchone():
                    continue  # Alert already exists
                
                # Determine severity
                if product['stock'] <= 0:
                    severity = 'critical'
                    title = "Out of Stock"
                    message = f"Product '{product['model']}' is out of stock"
                elif product['stock'] <= product['min_stock']:
                    severity = 'high'
                    title = "Critical Stock Level"
                    message = f"Product '{product['model']}' has only {product['stock']} units (min: {product['min_stock']})"
                else:
                    severity = 'medium'
                    title = "Low Stock Alert"
                    message = f"Product '{product['model']}' is below reorder point ({product['stock']} <= {product['reorder_point']})"
                
                # Create alert
                self.create_alert(
                    alert_type='low_stock',
                    title=title,
                    message=message,
                    severity=severity,
                    record_type='products',
                    record_id=product['id']
                )
                
                alerted.append(product['id'])
        
        return alerted
    
    def check_expiry_alerts(self, days_warning: int = 30) -> List[int]:
        """
        Check for expiring warranties.
        Returns list of product IDs with expiring warranties.
        """
        alerted = []
        
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, model, warranty_expiry
                FROM products
                WHERE warranty_expiry IS NOT NULL
                AND warranty_expiry <= date('now', ?)
                AND warranty_expiry >= date('now')
                AND status = 'active'
            """, (f'+{days_warning} days',))
            
            products = cur.fetchall()
            
            for product in products:
                # Check if alert already exists
                cur.execute("""
                    SELECT id FROM alerts
                    WHERE alert_type = 'warranty_expiry'
                    AND record_type = 'products'
                    AND record_id = ?
                    AND is_read = 0
                """, (product['id'],))
                
                if cur.fetchone():
                    continue
                
                # Create alert
                self.create_alert(
                    alert_type='warranty_expiry',
                    title="Warranty Expiring Soon",
                    message=f"Product '{product['model']}' warranty expires on {product['warranty_expiry']}",
                    severity='medium',
                    record_type='products',
                    record_id=product['id']
                )
                
                alerted.append(product['id'])
        
        return alerted
    
    def get_alert_settings(self, alert_type: str) -> Optional[Dict]:
        """Get settings for a specific alert type."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT * FROM alert_settings
                WHERE alert_type = ?
            """, (alert_type,))
            
            row = cur.fetchone()
            return dict(row) if row else None
    
    def update_alert_setting(
        self,
        alert_type: str,
        enabled: bool = None,
        threshold_value: int = None,
        email_enabled: bool = None,
        in_app_enabled: bool = None
    ) -> bool:
        """Update alert settings."""
        with get_db_cursor() as cur:
            updates = []
            values = []
            
            if enabled is not None:
                updates.append("enabled = ?")
                values.append(1 if enabled else 0)
            
            if threshold_value is not None:
                updates.append("threshold_value = ?")
                values.append(threshold_value)
            
            if email_enabled is not None:
                updates.append("email_enabled = ?")
                values.append(1 if email_enabled else 0)
            
            if in_app_enabled is not None:
                updates.append("in_app_enabled = ?")
                values.append(1 if in_app_enabled else 0)
            
            if not updates:
                return False
            
            values.append(alert_type)

            # Security: All column names below are hardcoded (enabled, threshold_value, etc.)
            # No user input is used for column names, so this is NOT vulnerable to SQL injection.
            cur.execute(f"""
                UPDATE alert_settings
                SET {', '.join(updates)}
                WHERE alert_type = ?
            """, values)
            
            return cur.rowcount > 0


# Global alert manager instance
alert_manager = AlertManager()


def check_all_alerts() -> Dict:
    """Run all alert checks and return summary."""
    results = {
        'low_stock': alert_manager.check_low_stock_alerts(),
        'warranty_expiry': alert_manager.check_expiry_alerts(),
        'unread_count': alert_manager.get_alert_count(unread_only=True)
    }
    return results


def get_unread_alerts() -> List[Dict]:
    """Get unread alerts (convenience function)."""
    return alert_manager.get_unread_alerts()


def create_alert(alert_type: str, title: str, message: str, severity: str = "medium") -> int:
    """Create an alert (convenience function)."""
    return alert_manager.create_alert(alert_type, title, message, severity)
