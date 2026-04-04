"""
Expiry Alert System
====================
Automated alerts for expiring products (Pharmacy & Food/Beverage)
Runs on application startup and periodically in background.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict

try:
    from .database import get_db_cursor
    from .alerts import create_alert
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor
    try:
        from alerts import create_alert
    except:
        def create_alert(alert_type, severity, title, message, **kwargs):
            logging.info(f"ALERT: [{severity}] {title} - {message}")

logger = logging.getLogger(__name__)


def check_expiry_alerts():
    """
    Check for expiring products and create alerts.
    Call this on application startup and periodically.
    """
    logger.info("Running expiry alert check...")
    
    with get_db_cursor() as cur:
        # Get products expiring within 30 days
        cur.execute("""
            SELECT 
                p.id,
                p.model,
                p.batch_number,
                p.expiry_date,
                p.stock,
                p.manufacturer,
                p.requires_prescription,
                julianday(p.expiry_date) - julianday('now') as days_until_expiry
            FROM products p
            WHERE p.expiry_date IS NOT NULL 
            AND p.expiry_date != ''
            AND p.status = 'active'
            AND julianday(p.expiry_date) - julianday('now') <= 30
            ORDER BY p.expiry_date ASC
        """)
        
        expiring_products = cur.fetchall()
        
        # Categorize by urgency
        expired = []
        critical = []  # <= 7 days
        warning = []   # <= 30 days
        
        for product in expiring_products:
            days = product['days_until_expiry']
            
            if days < 0:
                expired.append(product)
            elif days <= 7:
                critical.append(product)
            else:
                warning.append(product)
        
        # Create alerts
        if expired:
            create_expired_alert(expired)
        
        if critical:
            create_critical_alert(critical)
        
        if warning:
            create_warning_alert(warning)
        
        logger.info(f"Expiry check complete: {len(expired)} expired, {len(critical)} critical, {len(warning)} warning")
        
        return {
            'expired': len(expired),
            'critical': len(critical),
            'warning': len(warning),
            'total': len(expiring_products)
        }


def create_expired_alert(products: List):
    """Create alert for expired products."""
    total_products = len(products)
    
    product_list = "\n".join([
        f"  • {p['model']} (Batch: {p['batch_number'] or 'N/A'}) - Expired: {p['expiry_date']}"
        for p in products[:10]  # Show first 10
    ])
    
    if total_products > 10:
        product_list += f"\n  ... and {total_products - 10} more"
    
    title = f"🔴 EXPIRED PRODUCTS - {total_products} items"
    message = f"The following products have expired and should be removed from inventory:\n\n{product_list}"
    
    create_alert(
        alert_type='expired_products',
        severity='critical',
        title=title,
        message=message,
        record_type='products',
        record_ids=[p['id'] for p in products]
    )


def create_critical_alert(products: List):
    """Create alert for products expiring within 7 days."""
    total_products = len(products)
    
    product_list = "\n".join([
        f"  • {p['model']} - Expires: {p['expiry_date']} ({int(p['days_until_expiry'])} days left)"
        for p in products[:10]
    ])
    
    if total_products > 10:
        product_list += f"\n  ... and {total_products - 10} more"
    
    title = f"🟠 CRITICAL: Expiring Soon - {total_products} items"
    message = f"The following products expire within 7 days:\n\n{product_list}"
    
    create_alert(
        alert_type='expiry_critical',
        severity='high',
        title=title,
        message=message,
        record_type='products',
        record_ids=[p['id'] for p in products]
    )


def create_warning_alert(products: List):
    """Create alert for products expiring within 30 days."""
    total_products = len(products)
    
    product_list = "\n".join([
        f"  • {p['model']} - Expires: {p['expiry_date']} ({int(p['days_until_expiry'])} days left)"
        for p in products[:15]
    ])
    
    if total_products > 15:
        product_list += f"\n  ... and {total_products - 15} more"
    
    title = f"🟡 WARNING: Expiring Within 30 Days - {total_products} items"
    message = f"Plan to sell or return these products before they expire:\n\n{product_list}"
    
    create_alert(
        alert_type='expiry_warning',
        severity='medium',
        title=title,
        message=message,
        record_type='products',
        record_ids=[p['id'] for p in products]
    )


def check_batch_expiry():
    """Check batch-level expiry (more granular than product-level)."""
    logger.info("Running batch expiry check...")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                b.id,
                b.batch_number,
                p.model as product_name,
                b.quantity_remaining,
                b.expiry_date,
                julianday(b.expiry_date) - julianday('now') as days_until_expiry
            FROM batches b
            LEFT JOIN products p ON b.product_id = p.id
            WHERE b.status = 'active'
            AND b.expiry_date IS NOT NULL
            AND julianday(b.expiry_date) - julianday('now') <= 30
            ORDER BY b.expiry_date ASC
        """)
        
        expiring_batches = cur.fetchall()
        
        if expiring_batches:
            batch_list = "\n".join([
                f"  • {b['product_name']} - Batch {b['batch_number']} ({b['quantity_remaining']} units) - Expires: {b['expiry_date']}"
                for b in expiring_batches[:10]
            ])
            
            if len(expiring_batches) > 10:
                batch_list += f"\n  ... and {len(expiring_batches) - 10} more batches"
            
            create_alert(
                alert_type='batch_expiry',
                severity='medium',
                title=f"📋 Batches Expiring Soon - {len(expiring_batches)} batches",
                message=f"Monitor these batches closely:\n\n{batch_list}",
                record_type='batches',
                record_ids=[b['id'] for b in expiring_batches]
            )


def check_prescription_expiry():
    """Check for expiring prescriptions."""
    logger.info("Running prescription expiry check...")
    
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                prescription_number,
                patient_name,
                doctor_name,
                expiry_date,
                julianday(expiry_date) - julianday('now') as days_until_expiry
            FROM prescriptions
            WHERE status IN ('active', 'verified')
            AND expiry_date IS NOT NULL
            AND julianday(expiry_date) - julianday('now') BETWEEN 0 AND 7
            ORDER BY expiry_date ASC
        """)
        
        expiring_rx = cur.fetchall()
        
        if expiring_rx:
            rx_list = "\n".join([
                f"  • RX-{r['prescription_number']} - Patient: {r['patient_name']} - Expires: {r['expiry_date']} ({int(r['days_until_expiry'])} days)"
                for r in expiring_rx
            ])
            
            create_alert(
                alert_type='prescription_expiry',
                severity='high',
                title=f"📝 Prescriptions Expiring - {len(expiring_rx)} prescriptions",
                message=f"Follow up with patients before these prescriptions expire:\n\n{rx_list}",
                record_type='prescriptions',
                record_ids=[r['prescription_number'] for r in expiring_rx]
            )


def get_expiry_dashboard_stats() -> Dict:
    """Get statistics for expiry dashboard."""
    with get_db_cursor() as cur:
        stats = {}
        
        # Total products with expiry dates
        cur.execute("""
            SELECT COUNT(*) as total
            FROM products
            WHERE expiry_date IS NOT NULL AND status = 'active'
        """)
        stats['total_tracked'] = cur.fetchone()['total']
        
        # Expired
        cur.execute("""
            SELECT COUNT(*) as total
            FROM products
            WHERE expiry_date < date('now') AND status = 'active'
        """)
        stats['expired'] = cur.fetchone()['total']
        
        # Critical (<= 7 days)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM products
            WHERE expiry_date BETWEEN date('now') AND date('now', '+7 days')
            AND status = 'active'
        """)
        stats['critical'] = cur.fetchone()['total']
        
        # Warning (<= 30 days)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM products
            WHERE expiry_date BETWEEN date('now', '+7 days') AND date('now', '+30 days')
            AND status = 'active'
        """)
        stats['warning'] = cur.fetchone()['total']
        
        # Batches expiring
        cur.execute("""
            SELECT COUNT(*) as total
            FROM batches
            WHERE expiry_date BETWEEN date('now') AND date('now', '+30 days')
            AND status = 'active'
        """)
        stats['expiring_batches'] = cur.fetchone()['total']
        
        # Active prescriptions
        cur.execute("""
            SELECT COUNT(*) as total
            FROM prescriptions
            WHERE status IN ('active', 'verified')
        """)
        stats['active_prescriptions'] = cur.fetchone()['total']
        
        return stats


def run_all_expiry_checks():
    """Run all expiry-related checks."""
    logger.info("Running comprehensive expiry checks...")
    
    results = {
        'product_expiry': check_expiry_alerts(),
        'batch_expiry': None,
        'prescription_expiry': None,
        'stats': None
    }
    
    try:
        check_batch_expiry()
        results['batch_expiry'] = 'completed'
    except Exception as e:
        logger.error(f"Batch expiry check failed: {e}")
        results['batch_expiry'] = f'failed: {e}'
    
    try:
        check_prescription_expiry()
        results['prescription_expiry'] = 'completed'
    except Exception as e:
        logger.error(f"Prescription expiry check failed: {e}")
        results['prescription_expiry'] = f'failed: {e}'
    
    try:
        results['stats'] = get_expiry_dashboard_stats()
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
    
    return results


if __name__ == "__main__":
    # Test run
    logging.basicConfig(level=logging.INFO)
    
    print("Running expiry alert system test...")
    results = run_all_expiry_checks()
    
    print("\n" + "=" * 60)
    print("EXPIRY CHECK RESULTS")
    print("=" * 60)
    print(f"Product Expiry: {results['product_expiry']}")
    print(f"Batch Expiry: {results['batch_expiry']}")
    print(f"Prescription Expiry: {results['prescription_expiry']}")
    print(f"\nDashboard Stats: {results['stats']}")
    print("=" * 60)
