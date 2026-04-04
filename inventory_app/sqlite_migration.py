"""
SQLite Migration Module
========================
Centralized data access functions to replace JSON file operations.
All modules should use these functions instead of direct JSON file access.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    from .database import get_db_cursor, get_connection
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection

logger = logging.getLogger(__name__)


# ============================================================================
# PRODUCT/INVENTORY FUNCTIONS
# ============================================================================

def get_all_products() -> List[Dict[str, Any]]:
    """
    Get all products from database.
    Returns list of dictionaries (compatible with old JSON format).
    """
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.status = 'active'
            ORDER BY p.model
        """)
        
        products = []
        for row in cur.fetchall():
            product = dict(row)
            # Convert category_id to category name for backward compatibility
            if product.get('category_name'):
                product['category'] = product['category_name']
            if product.get('supplier_name'):
                product['supplier'] = product['supplier_name']
            products.append(product)
        
        return products


def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """Get single product by ID."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
        """, (product_id,))
        
        row = cur.fetchone()
        if row:
            product = dict(row)
            if product.get('category_name'):
                product['category'] = product['category_name']
            if product.get('supplier_name'):
                product['supplier'] = product['supplier_name']
            return product
        return None


def get_product_by_model(model: str) -> Optional[Dict[str, Any]]:
    """Get product by model name."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.model = ?
        """, (model,))
        
        row = cur.fetchone()
        if row:
            product = dict(row)
            if product.get('category_name'):
                product['category'] = product['category_name']
            if product.get('supplier_name'):
                product['supplier'] = product['supplier_name']
            return product
        return None


def search_products(query: str) -> List[Dict[str, Any]]:
    """Search products by model, SKU, barcode, or category."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.status = 'active'
            AND (
                p.model LIKE ? OR
                p.sku LIKE ? OR
                p.barcode LIKE ? OR
                p.brand LIKE ? OR
                c.name LIKE ?
            )
            ORDER BY p.model
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        products = []
        for row in cur.fetchall():
            product = dict(row)
            if product.get('category_name'):
                product['category'] = product['category_name']
            if product.get('supplier_name'):
                product['supplier'] = product['supplier_name']
            products.append(product)
        
        return products


def create_product(product_data: Dict[str, Any], created_by: str = None) -> int:
    """
    Create new product.
    Returns product ID.
    """
    with get_db_cursor() as cur:
        # Get or create category
        category_id = None
        if product_data.get('category'):
            cur.execute("SELECT id FROM categories WHERE name = ?", (product_data['category'],))
            cat_row = cur.fetchone()
            if cat_row:
                category_id = cat_row['id']
            else:
                cur.execute("INSERT INTO categories (name) VALUES (?)", (product_data['category'],))
                category_id = cur.lastrowid
        
        # Get supplier ID if provided
        supplier_id = None
        if product_data.get('supplier_id'):
            supplier_id = product_data['supplier_id']
        
        cur.execute("""
            INSERT INTO products (
                model, category_id, supplier_id, sku, barcode,
                purchase_price, selling_price, stock, min_stock, reorder_point,
                brand, serial_number, ram, storage, screen_size, camera, battery,
                color, warranty_months, warranty_expiry, status, condition,
                default_location_id, rack_location, shelf_location,
                description, notes, specifications, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_data.get('model', ''),
            category_id,
            supplier_id,
            product_data.get('sku', ''),
            product_data.get('barcode', ''),
            float(product_data.get('purchase_price', 0)),
            float(product_data.get('selling_price', 0)),
            int(product_data.get('stock', 0)),
            int(product_data.get('min_stock', 5)),
            int(product_data.get('reorder_point', 10)),
            product_data.get('brand', ''),
            product_data.get('serial_number', ''),
            product_data.get('ram', ''),
            product_data.get('storage', ''),
            product_data.get('screen_size', ''),
            product_data.get('camera', ''),
            product_data.get('battery', ''),
            product_data.get('color', ''),
            product_data.get('warranty_months'),
            product_data.get('warranty_expiry'),
            product_data.get('status', 'active'),
            product_data.get('condition', 'new'),
            product_data.get('default_location_id'),
            product_data.get('rack_location', ''),
            product_data.get('shelf_location', ''),
            product_data.get('description', ''),
            product_data.get('notes', ''),
            product_data.get('specifications'),
            created_by
        ))
        
        product_id = cur.lastrowid
        
        # Create initial stock record for default location
        if product_data.get('stock', 0) > 0:
            cur.execute("""
                INSERT INTO product_stock (product_id, location_id, quantity)
                VALUES (?, 1, ?)
                ON CONFLICT(product_id, location_id) 
                DO UPDATE SET quantity = quantity + ?
            """, (product_id, product_data['stock'], product_data['stock']))
        
        # Audit log
        cur.execute("""
            INSERT INTO audit_log (username, action, table_name, record_id, new_values, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (created_by, 'CREATE', 'products', product_id, 
              str(product_data), f'Created product: {product_data.get("model")}'))
        
        logger.info(f"Product created: ID={product_id}, Model={product_data.get('model')}")
        return product_id


def update_product(product_id: int, product_data: Dict[str, Any], updated_by: str = None) -> bool:
    """Update existing product."""
    with get_db_cursor() as cur:
        # Get current product for audit
        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        old_product = cur.fetchone()
        
        if not old_product:
            logger.error(f"Product not found: {product_id}")
            return False
        
        # Get or create category
        category_id = None
        if product_data.get('category'):
            cur.execute("SELECT id FROM categories WHERE name = ?", (product_data['category'],))
            cat_row = cur.fetchone()
            if cat_row:
                category_id = cat_row['id']
            else:
                cur.execute("INSERT INTO categories (name) VALUES (?)", (product_data['category'],))
                category_id = cur.lastrowid
        
        cur.execute("""
            UPDATE products SET
                model = ?, category_id = ?, supplier_id = ?, sku = ?, barcode = ?,
                purchase_price = ?, selling_price = ?, stock = ?, min_stock = ?, reorder_point = ?,
                brand = ?, serial_number = ?, ram = ?, storage = ?, screen_size = ?, camera = ?,
                battery = ?, color = ?, warranty_months = ?, warranty_expiry = ?,
                status = ?, condition = ?, default_location_id = ?, rack_location = ?,
                shelf_location = ?, description = ?, notes = ?, specifications = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            product_data.get('model', ''),
            category_id,
            product_data.get('supplier_id'),
            product_data.get('sku', ''),
            product_data.get('barcode', ''),
            float(product_data.get('purchase_price', 0)),
            float(product_data.get('selling_price', 0)),
            int(product_data.get('stock', 0)),
            int(product_data.get('min_stock', 5)),
            int(product_data.get('reorder_point', 10)),
            product_data.get('brand', ''),
            product_data.get('serial_number', ''),
            product_data.get('ram', ''),
            product_data.get('storage', ''),
            product_data.get('screen_size', ''),
            product_data.get('camera', ''),
            product_data.get('battery', ''),
            product_data.get('color', ''),
            product_data.get('warranty_months'),
            product_data.get('warranty_expiry'),
            product_data.get('status', 'active'),
            product_data.get('condition', 'new'),
            product_data.get('default_location_id'),
            product_data.get('rack_location', ''),
            product_data.get('shelf_location', ''),
            product_data.get('description', ''),
            product_data.get('notes', ''),
            product_data.get('specifications'),
            product_id
        ))
        
        # Audit log
        cur.execute("""
            INSERT INTO audit_log (username, action, table_name, record_id, old_values, new_values, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (updated_by, 'UPDATE', 'products', product_id, 
              str(dict(old_product)), str(product_data), 
              f'Updated product: {product_data.get("model")}'))
        
        logger.info(f"Product updated: ID={product_id}")
        return True


def delete_product(product_id: int, deleted_by: str = None) -> bool:
    """Soft delete product (set status to inactive)."""
    with get_db_cursor() as cur:
        cur.execute("""
            UPDATE products SET status = 'inactive', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (product_id,))
        
        # Audit log
        cur.execute("""
            INSERT INTO audit_log (username, action, table_name, record_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (deleted_by, 'DELETE', 'products', product_id, f'Deleted product ID: {product_id}'))
        
        logger.info(f"Product deleted: ID={product_id}")
        return True


def adjust_stock(product_id: int, quantity_change: int, reason: str, user: str = None) -> bool:
    """
    Adjust product stock level.
    quantity_change: positive for increase, negative for decrease
    """
    with get_db_cursor() as cur:
        # Get current stock
        cur.execute("SELECT stock, model FROM products WHERE id = ?", (product_id,))
        product = cur.fetchone()
        
        if not product:
            logger.error(f"Product not found: {product_id}")
            return False
        
        new_stock = product['stock'] + quantity_change
        if new_stock < 0:
            logger.error(f"Cannot reduce stock below zero: {product['model']}")
            return False
        
        # Update product stock
        cur.execute("""
            UPDATE products SET stock = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_stock, product_id))
        
        # Update location-specific stock (default location)
        cur.execute("""
            INSERT INTO product_stock (product_id, location_id, quantity)
            VALUES (?, 1, ?)
            ON CONFLICT(product_id, location_id) 
            DO UPDATE SET quantity = quantity + ?, last_updated = CURRENT_TIMESTAMP
        """, (product_id, quantity_change, quantity_change))
        
        # Create stock movement record
        cur.execute("""
            INSERT INTO audit_log (username, action, table_name, record_id, new_values, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user, 'STOCK_ADJUSTMENT', 'products', product_id, 
              str({'old': product['stock'], 'new': new_stock, 'change': quantity_change}),
              f'{reason}: {quantity_change:+d}'))
        
        logger.info(f"Stock adjusted: ID={product_id}, Change={quantity_change:+d}, New={new_stock}")
        return True


# ============================================================================
# SALES FUNCTIONS
# ============================================================================

def get_all_sales() -> List[Dict[str, Any]]:
    """Get all sales records."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                so.id, so.order_number, so.customer_name, so.customer_phone,
                so.order_date, so.delivery_date, so.status, so.total_amount,
                so.paid_amount, so.payment_status, so.notes,
                soi.product_id, soi.quantity, soi.unit_price, soi.total_price,
                p.model, p.sku, p.barcode
            FROM sales_orders so
            LEFT JOIN sales_order_items soi ON so.id = soi.order_id
            LEFT JOIN products p ON soi.product_id = p.id
            ORDER BY so.order_date DESC
        """)
        
        sales = []
        current_sale = None
        
        for row in cur.fetchall():
            if current_sale is None or current_sale['id'] != row['id']:
                if current_sale:
                    sales.append(current_sale)
                
                current_sale = {
                    'id': row['id'],
                    'order_number': row['order_number'],
                    'customer_name': row['customer_name'],
                    'customer_phone': row['customer_phone'],
                    'order_date': row['order_date'],
                    'delivery_date': row['delivery_date'],
                    'status': row['status'],
                    'total_amount': row['total_amount'],
                    'paid_amount': row['paid_amount'],
                    'payment_status': row['payment_status'],
                    'notes': row['notes'],
                    'items': []
                }
            
            if row['product_id']:
                current_sale['items'].append({
                    'product_id': row['product_id'],
                    'model': row['model'],
                    'sku': row['sku'],
                    'quantity': row['quantity'],
                    'unit_price': row['unit_price'],
                    'total_price': row['total_price']
                })
        
        if current_sale:
            sales.append(current_sale)
        
        return sales


def create_sale(sale_data: Dict[str, Any], created_by: str = None) -> int:
    """
    Create new sale.
    Returns sale ID.
    """
    with get_db_cursor() as cur:
        # Generate order number
        order_number = f"SO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cur.execute("""
            INSERT INTO sales_orders (
                order_number, customer_name, customer_phone, customer_email,
                order_date, delivery_date, status, total_amount, paid_amount,
                payment_status, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_number,
            sale_data.get('customer_name', 'Walk-in Customer'),
            sale_data.get('customer_phone', ''),
            sale_data.get('customer_email', ''),
            sale_data.get('order_date', datetime.now().strftime('%Y-%m-%d')),
            sale_data.get('delivery_date'),
            sale_data.get('status', 'completed'),
            float(sale_data.get('total_amount', 0)),
            float(sale_data.get('paid_amount', 0)),
            sale_data.get('payment_status', 'paid'),
            sale_data.get('notes', ''),
            created_by
        ))
        
        sale_id = cur.lastrowid
        
        # Add sale items and update stock
        for item in sale_data.get('items', []):
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            unit_price = item.get('unit_price', 0)
            
            # Add order item
            cur.execute("""
                INSERT INTO sales_order_items (order_id, product_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (sale_id, product_id, quantity, unit_price, quantity * unit_price))
            
            # Reduce stock
            if item.get('reduce_stock', True):
                cur.execute("""
                    UPDATE products SET stock = stock - ? WHERE id = ?
                """, (quantity, product_id))
                
                # Update location stock
                cur.execute("""
                    UPDATE product_stock SET quantity = quantity - ?
                    WHERE product_id = ? AND location_id = 1
                """, (quantity, product_id))
        
        # Audit log
        cur.execute("""
            INSERT INTO audit_log (username, action, table_name, record_id, new_values, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (created_by, 'CREATE', 'sales_orders', sale_id, 
              str(sale_data), f'Created sale: {order_number}'))
        
        logger.info(f"Sale created: ID={sale_id}, Order={order_number}")
        return sale_id


def get_sales_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get sales within date range."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                so.id, so.order_number, so.customer_name, so.total_amount,
                so.order_date, so.status, so.payment_status
            FROM sales_orders so
            WHERE so.order_date BETWEEN ? AND ?
            ORDER BY so.order_date DESC
        """, (start_date, end_date))
        
        return [dict(row) for row in cur.fetchall()]


def get_profit_data() -> Dict[str, Any]:
    """Get profit/loss data from sales."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                so.order_date,
                so.total_amount as revenue,
                SUM(soi.quantity * p.purchase_price) as cost,
                (so.total_amount - SUM(soi.quantity * p.purchase_price)) as profit
            FROM sales_orders so
            LEFT JOIN sales_order_items soi ON so.id = soi.order_id
            LEFT JOIN products p ON soi.product_id = p.id
            WHERE so.status = 'completed'
            GROUP BY so.id
            ORDER BY so.order_date
        """)
        
        total_revenue = 0
        total_cost = 0
        monthly_data = {}
        
        for row in cur.fetchall():
            revenue = row['revenue'] or 0
            cost = row['cost'] or 0
            profit = row['profit'] or 0
            
            total_revenue += revenue
            total_cost += cost
            
            # Group by month
            if row['order_date']:
                month = row['order_date'][:7]  # YYYY-MM
                if month not in monthly_data:
                    monthly_data[month] = {'revenue': 0, 'cost': 0, 'profit': 0}
                monthly_data[month]['revenue'] += revenue
                monthly_data[month]['cost'] += cost
                monthly_data[month]['profit'] += profit
        
        return {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'total_profit': total_revenue - total_cost,
            'monthly_data': monthly_data
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_low_stock_products(threshold: int = 10) -> List[Dict[str, Any]]:
    """Get products with low stock."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.stock <= ? AND p.status = 'active'
            ORDER BY p.stock ASC
        """, (threshold,))
        
        return [dict(row) for row in cur.fetchall()]


def get_out_of_stock_products() -> List[Dict[str, Any]]:
    """Get products with zero stock."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.*, s.name as supplier_name
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.stock = 0 AND p.status = 'active'
            ORDER BY p.model
        """)
        
        return [dict(row) for row in cur.fetchall()]


def get_stock_value_report() -> Dict[str, Any]:
    """Get total inventory value report."""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT 
                COUNT(*) as total_products,
                SUM(stock) as total_units,
                SUM(stock * purchase_price) as total_cost_value,
                SUM(stock * selling_price) as total_retail_value,
                SUM(stock * (selling_price - purchase_price)) as potential_profit
            FROM products
            WHERE status = 'active' AND stock > 0
        """)
        
        row = cur.fetchone()
        return {
            'total_products': row['total_products'] or 0,
            'total_units': row['total_units'] or 0,
            'total_cost_value': row['total_cost_value'] or 0,
            'total_retail_value': row['total_retail_value'] or 0,
            'potential_profit': row['potential_profit'] or 0
        }


def export_products_to_dict() -> List[Dict[str, Any]]:
    """
    Export all products to dictionary format.
    Useful for backups and data migration.
    """
    return get_all_products()


def import_products_from_dict(products: List[Dict[str, Any]], created_by: str = None) -> int:
    """
    Import products from dictionary format.
    Returns number of products imported.
    """
    count = 0
    for product in products:
        try:
            # Check if product exists (by SKU or model)
            existing = None
            if product.get('sku'):
                existing = get_product_by_model(product['sku'])
            if not existing and product.get('model'):
                existing = get_product_by_model(product['model'])
            
            if existing:
                update_product(existing['id'], product, created_by)
            else:
                create_product(product, created_by)
            
            count += 1
        except Exception as e:
            logger.error(f"Failed to import product {product.get('model')}: {e}")
    
    return count
