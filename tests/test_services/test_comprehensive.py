"""
Comprehensive Tests for Service Layer
======================================
Tests all service classes with real database (SQLite in-memory).

Run: pytest tests/test_services/test_comprehensive.py -v
"""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add inventory_app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "inventory_app"))

# Import service layer
from services import svc
from database import InventoryDB, get_db_cursor


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(scope="function")
def fresh_db():
    """Create a fresh in-memory database for each test."""
    import sqlite3
    
    # Use in-memory database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Disable foreign key enforcement for testing
    conn.execute("PRAGMA foreign_keys = OFF")
    
    # Store connection in thread-local for get_connection() to find
    import threading
    from database import _local
    _local.connection = conn
    
    # Initialize schema
    from database import init_database
    try:
        init_database()
    except Exception:
        pass  # Schema may already exist from previous test
    
    yield conn
    
    # Cleanup
    conn.close()
    _local.connection = None


@pytest.fixture
def sample_product():
    """Create sample product data."""
    return {
        "model": "TEST-PROD-001",
        "purchase_price": 100.0,
        "selling_price": 150.0,
        "stock": 50,
        "min_stock": 10,
        "reorder_point": 20,
        "status": "active",
        "condition": "new",
    }


@pytest.fixture
def sample_location():
    """Create sample location data."""
    return {
        "code": "TEST-LOC-001",
        "name": "Test Warehouse",
        "type": "warehouse",
        "is_active": 1,
    }


@pytest.fixture
def sample_supplier():
    """Create sample supplier data."""
    return {
        "code": "TEST-SUP-001",
        "name": "Test Supplier Inc.",
        "contact_person": "John Doe",
        "email": "john@testsupplier.com",
        "phone": "123-456-7890",
        "is_active": 1,
    }


# ============================================================
# INVENTORY SERVICE TESTS
# ============================================================

class TestInventoryService:
    """Test InventoryService business logic."""

    def test_add_product(self, fresh_db, sample_product):
        """Test adding a new product."""
        product_id = svc.inventory.add_product(sample_product.copy(), username="testuser")
        assert product_id > 0
        
        # Verify product was added
        product = svc.inventory.get_product_by_id(product_id)
        assert product is not None
        assert product["model"] == "TEST-PROD-001"
        assert product["stock"] == 50

    def test_add_product_missing_model(self, fresh_db):
        """Test adding product without model raises error."""
        with pytest.raises(ValueError, match="Product must have a 'model' field"):
            svc.inventory.add_product({}, username="testuser")

    def test_add_product_invalid_price(self, fresh_db):
        """Test adding product with invalid price."""
        data = {"model": "TEST-001", "purchase_price": "invalid"}
        with pytest.raises(ValueError, match="Invalid purchase_price"):
            svc.inventory.add_product(data, username="testuser")

    def test_update_product(self, fresh_db, sample_product):
        """Test updating a product."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        # Update the product
        success = svc.inventory.update_product(
            "TEST-PROD-001",
            {"selling_price": 175.0, "stock": 60},
            username="testuser"
        )
        assert success is True
        
        # Verify update
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        assert product["selling_price"] == 175.0
        assert product["stock"] == 60

    def test_delete_product_soft(self, fresh_db, sample_product):
        """Test soft deleting a product."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        success = svc.inventory.delete_product("TEST-PROD-001", username="testuser")
        assert success is True
        
        # Product should not appear in active list
        active_products = svc.inventory.get_all_products(active_only=True)
        assert len([p for p in active_products if p["model"] == "TEST-PROD-001"]) == 0

    def test_adjust_stock_positive(self, fresh_db, sample_product):
        """Test adding stock."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        success = svc.inventory.adjust_stock("TEST-PROD-001", 10, username="testuser", reason="Restock")
        assert success is True
        
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        assert product["stock"] == 60

    def test_adjust_stock_negative(self, fresh_db, sample_product):
        """Test deducting stock."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        success = svc.inventory.adjust_stock("TEST-PROD-001", -15, username="testuser", reason="Sale")
        assert success is True
        
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        assert product["stock"] == 35

    def test_set_stock(self, fresh_db, sample_product):
        """Test setting absolute stock quantity."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        success = svc.inventory.set_stock("TEST-PROD-001", 100, username="testuser", reason="Inventory count")
        assert success is True
        
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        assert product["stock"] == 100

    def test_get_low_stock_products(self, fresh_db):
        """Test getting low stock products."""
        # Add product with low stock
        product_data = {
            "model": "LOW-STOCK-001",
            "stock": 3,
            "reorder_point": 5,
            "status": "active",
        }
        svc.inventory.add_product(product_data, username="testuser")
        
        low_stock = svc.inventory.get_low_stock_products()
        assert len(low_stock) >= 1
        assert any(p["model"] == "LOW-STOCK-001" for p in low_stock)


# ============================================================
# SALES SERVICE TESTS
# ============================================================

class TestSalesService:
    """Test SalesService business logic."""

    def test_create_order_with_stock_deduction(self, fresh_db, sample_product):
        """Test creating sales order deducts stock."""
        # Add product
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        
        # Create order
        order_data = {
            "order_number": "SO-TEST-001",
            "customer_name": "Test Customer",
            "total_amount": 300.0,
            "status": "confirmed",
            "payment_status": "pending",
        }
        items = [
            {
                "product_id": product["id"],
                "quantity": 2,
                "unit_price": 150.0,
                "total_price": 300.0,
            }
        ]
        
        order_id = svc.sales.create_order(order_data, items, username="testuser")
        assert order_id > 0
        
        # Verify stock was deducted
        updated_product = svc.inventory.get_product_by_id(product["id"])
        assert updated_product["stock"] == 48  # 50 - 2

    def test_create_order_insufficient_stock(self, fresh_db, sample_product):
        """Test creating order with insufficient stock raises error."""
        from exceptions import InsufficientStockError
        
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        
        order_data = {
            "order_number": "SO-TEST-002",
            "customer_name": "Test Customer",
            "total_amount": 15000.0,
        }
        items = [
            {
                "product_id": product["id"],
                "quantity": 1000,  # More than available
                "unit_price": 150.0,
                "total_price": 150000.0,
            }
        ]
        
        with pytest.raises(InsufficientStockError, match="Insufficient stock"):
            svc.sales.create_order(order_data, items, username="testuser")

    def test_create_order_empty_items(self, fresh_db):
        """Test creating order with no items raises error."""
        order_data = {
            "order_number": "SO-TEST-003",
            "customer_name": "Test Customer",
        }
        
        from exceptions import InvalidOrderDataError
        with pytest.raises(InvalidOrderDataError, match="Sales order must have at least one item"):
            svc.sales.create_order(order_data, [], username="testuser")

    def test_delete_order_restores_stock(self, fresh_db, sample_product):
        """Test deleting order restores stock."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        
        # Create and then delete order
        order_data = {
            "order_number": "SO-TEST-004",
            "customer_name": "Test Customer",
            "total_amount": 150.0,
        }
        items = [{"product_id": product["id"], "quantity": 5, "unit_price": 150.0, "total_price": 750.0}]
        
        order_id = svc.sales.create_order(order_data, items, username="testuser")
        svc.sales.delete_order(order_id, username="testuser")
        
        # Stock should be restored
        updated_product = svc.inventory.get_product_by_id(product["id"])
        assert updated_product["stock"] == 50

    def test_update_order_status(self, fresh_db, sample_product):
        """Test updating order status."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        
        order_data = {
            "order_number": "SO-TEST-005",
            "customer_name": "Test Customer",
            "total_amount": 150.0,
            "status": "confirmed",
        }
        items = [{"product_id": product["id"], "quantity": 1, "unit_price": 150.0, "total_price": 150.0}]
        
        order_id = svc.sales.create_order(order_data, items, username="testuser")
        
        # Update status
        success = svc.sales.update_order_status(order_id, "shipped", username="testuser")
        assert success is True
        
        # Verify update
        orders = svc.sales.get_all_orders()
        order = next((o for o in orders if o["id"] == order_id), None)
        assert order is not None
        assert order["status"] == "shipped"


# ============================================================
# LOCATION SERVICE TESTS
# ============================================================

class TestLocationService:
    """Test LocationService business logic."""

    def test_add_location(self, fresh_db, sample_location):
        """Test adding a location."""
        location_id = svc.location.add_location(sample_location.copy(), username="testuser")
        assert location_id > 0
        
        # Verify location was added
        locations = svc.location.get_all_locations()
        assert any(loc["code"] == "TEST-LOC-001" for loc in locations)

    def test_add_location_missing_fields(self, fresh_db):
        """Test adding location without required fields."""
        from exceptions import validate_non_empty_string
        with pytest.raises(ValueError, match="'code' must be a non-empty string"):
            svc.location.add_location({}, username="testuser")

    def test_update_location(self, fresh_db, sample_location):
        """Test updating a location."""
        svc.location.add_location(sample_location.copy(), username="testuser")
        
        success = svc.location.update_location("TEST-LOC-001", {"name": "Updated Warehouse"}, username="testuser")
        assert success is True
        
        locations = svc.location.get_all_locations()
        location = next((loc for loc in locations if loc["code"] == "TEST-LOC-001"), None)
        assert location["name"] == "Updated Warehouse"

    def test_delete_location(self, fresh_db, sample_location):
        """Test soft deleting a location."""
        svc.location.add_location(sample_location.copy(), username="testuser")
        
        success = svc.location.delete_location("TEST-LOC-001", username="testuser")
        assert success is True
        
        # Location should not appear in active list
        active_locations = svc.location.get_all_locations(active_only=True)
        assert not any(loc["code"] == "TEST-LOC-001" for loc in active_locations)


# ============================================================
# SUPPLIER SERVICE TESTS
# ============================================================

class TestSupplierService:
    """Test SupplierService business logic."""

    def test_add_supplier(self, fresh_db, sample_supplier):
        """Test adding a supplier."""
        supplier_id = svc.supplier.add_supplier(sample_supplier.copy(), username="testuser")
        assert supplier_id > 0
        
        # Verify supplier was added
        suppliers = svc.supplier.get_all_suppliers()
        assert any(sup["code"] == "TEST-SUP-001" for sup in suppliers)

    def test_add_supplier_missing_name(self, fresh_db):
        """Test adding supplier without name."""
        with pytest.raises(ValueError, match="'name' must be a non-empty string"):
            svc.supplier.add_supplier({"code": "SUP-001"}, username="testuser")

    def test_update_supplier(self, fresh_db, sample_supplier):
        """Test updating a supplier."""
        svc.supplier.add_supplier(sample_supplier.copy(), username="testuser")
        
        success = svc.supplier.update_supplier("TEST-SUP-001", {"phone": "999-888-7777"}, username="testuser")
        assert success is True
        
        suppliers = svc.supplier.get_all_suppliers()
        supplier = next((sup for sup in suppliers if sup["code"] == "TEST-SUP-001"), None)
        assert supplier["phone"] == "999-888-7777"


# ============================================================
# CUSTOMER SERVICE TESTS
# ============================================================

class TestCustomerService:
    """Test CustomerService business logic."""

    def test_add_customer(self, fresh_db):
        """Test adding a customer."""
        customer_data = {
            "name": "Test Customer",
            "phone": "123-456-7890",
            "email": "customer@test.com",
        }
        customer_id = svc.customer.add_customer(customer_data, username="testuser")
        assert customer_id > 0
        
        # Verify customer was added
        customers = svc.customer.get_all_customers()
        assert any(cust["name"] == "Test Customer" for cust in customers)

    def test_add_customer_missing_name(self, fresh_db):
        """Test adding customer without name."""
        with pytest.raises(ValueError, match="'name' must be a non-empty string"):
            svc.customer.add_customer({"phone": "123-456-7890"}, username="testuser")

    def test_update_customer(self, fresh_db):
        """Test updating a customer."""
        customer_data = {"name": "Test Customer"}
        customer_id = svc.customer.add_customer(customer_data, username="testuser")
        
        success = svc.customer.update_customer(customer_id, {"email": "newemail@test.com"}, username="testuser")
        assert success is True
        
        customers = svc.customer.get_all_customers()
        customer = next((c for c in customers if c["id"] == customer_id), None)
        assert customer["email"] == "newemail@test.com"


# ============================================================
# PURCHASE ORDER SERVICE TESTS
# ============================================================

class TestPurchaseOrderService:
    """Test PurchaseOrderService business logic."""

    def test_create_purchase_order(self, fresh_db, sample_product, sample_supplier):
        """Test creating a purchase order."""
        svc.supplier.add_supplier(sample_supplier.copy(), username="testuser")
        supplier = svc.supplier.get_all_suppliers()[0]
        
        order_data = {
            "po_number": "PO-TEST-001",
            "supplier_id": supplier["id"],
            "total_amount": 1000.0,
            "status": "draft",
        }
        items = [
            {"product_id": 1, "sku": "SKU-001", "quantity_ordered": 10, "unit_price": 100.0, "total_price": 1000.0}
        ]
        
        po_id = svc.purchase_order.create_order(order_data, items, username="testuser")
        assert po_id > 0
        
        # Verify PO was created
        orders = svc.purchase_order.get_all_orders()
        assert any(po["po_number"] == "PO-TEST-001" for po in orders)

    def test_get_order_items(self, fresh_db, sample_product, sample_supplier):
        """Test getting purchase order items."""
        svc.supplier.add_supplier(sample_supplier.copy(), username="testuser")
        supplier = svc.supplier.get_all_suppliers()[0]
        
        order_data = {
            "po_number": "PO-TEST-002",
            "supplier_id": supplier["id"],
        }
        items = [
            {"product_id": 1, "quantity_ordered": 5, "unit_price": 50.0, "total_price": 250.0}
        ]
        
        po_id = svc.purchase_order.create_order(order_data, items, username="testuser")
        po_items = svc.purchase_order.get_order_items(po_id)
        
        assert len(po_items) == 1
        assert po_items[0]["quantity_ordered"] == 5


# ============================================================
# STOCK TRANSFER SERVICE TESTS
# ============================================================

class TestStockTransferService:
    """Test StockTransferService business logic."""

    def test_get_products_with_stock(self, fresh_db, sample_product):
        """Test getting products with stock."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        products = svc.stock_transfer.get_products_with_stock()
        assert len(products) >= 1
        assert any(p["model"] == "TEST-PROD-001" for p in products)

    def test_create_transfer(self, fresh_db, sample_location):
        """Test creating stock transfer."""
        svc.location.add_location(sample_location.copy(), username="testuser")
        loc2 = {"code": "TEST-LOC-002", "name": "Store A", "is_active": 1}
        svc.location.add_location(loc2, username="testuser")
        
        locations = svc.location.get_all_locations()
        
        transfer_data = {
            "transfer_number": "TRF-TEST-001",
            "from_location_id": locations[0]["id"],
            "to_location_id": locations[1]["id"],
            "status": "pending",
        }
        items = [{"product_id": 1, "quantity": 10}]
        
        transfer_id = svc.stock_transfer.create_transfer(transfer_data, items, username="testuser")
        assert transfer_id > 0

    def test_get_categories(self, fresh_db):
        """Test getting categories."""
        categories = svc.stock_transfer.get_categories()
        assert isinstance(categories, list)


# ============================================================
# TRADE-IN SERVICE TESTS
# ============================================================

class TestTradeInService:
    """Test TradeInService business logic."""

    def test_create_trade_in(self, fresh_db):
        """Test creating a trade-in."""
        trade_in_data = {
            "trade_in_number": "TI-TEST-001",
            "customer_name": "John Doe",
            "customer_phone": "123-456-7890",
            "product_name": "Old iPhone",
            "product_condition": "good",
            "trade_in_value": 300.0,
            "status": "pending",
        }
        
        trade_in_id = svc.tradein.create_trade_in(trade_in_data, username="testuser")
        assert trade_in_id > 0
        
        # Verify trade-in was created
        trade_ins = svc.tradein.get_all_trade_ins()
        assert any(ti["trade_in_number"] == "TI-TEST-001" for ti in trade_ins)


# ============================================================
# SERVICE TICKET TESTS
# ============================================================

class TestServiceTicketService:
    """Test ServiceTicketService business logic."""

    def test_create_ticket(self, fresh_db):
        """Test creating a service ticket."""
        ticket_data = {
            "ticket_number": "ST-TEST-001",
            "customer_name": "Jane Doe",
            "customer_phone": "987-654-3210",
            "device_type": "Laptop",
            "device_brand": "Dell",
            "issue_description": "Screen not working",
            "status": "received",
        }
        
        ticket_id = svc.service_ticket.create_ticket(ticket_data, username="testuser")
        assert ticket_id > 0
        
        # Verify ticket was created
        tickets = svc.service_ticket.get_all_tickets()
        assert any(t["ticket_number"] == "ST-TEST-001" for t in tickets)


# ============================================================
# REPORT SERVICE TESTS
# ============================================================

class TestReportService:
    """Test ReportService business logic."""

    def test_get_dashboard_stats(self, fresh_db):
        """Test getting dashboard statistics."""
        stats = svc.report.get_dashboard_stats()
        assert isinstance(stats, dict)
        assert "total_products" in stats
        assert "low_stock_count" in stats

    def test_get_stock_value_report(self, fresh_db, sample_product):
        """Test stock value report."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        report = svc.report.get_stock_value_report()
        assert isinstance(report, list)
        
        if report:
            product = report[0]
            assert "cost_value" in product
            assert "retail_value" in product
            assert "potential_profit" in product

    def test_get_sales_summary(self, fresh_db, sample_product):
        """Test sales summary report."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        product = svc.inventory.get_product_by_model("TEST-PROD-001")
        
        # Create a sales order
        order_data = {
            "order_number": "SO-REPORT-001",
            "customer_name": "Test Customer",
            "total_amount": 150.0,
        }
        items = [{"product_id": product["id"], "quantity": 1, "unit_price": 150.0, "total_price": 150.0}]
        svc.sales.create_order(order_data, items, username="testuser")
        
        summary = svc.report.get_sales_summary()
        assert isinstance(summary, dict)
        assert summary["total_orders"] >= 1
        assert summary["total_revenue"] >= 150.0


# ============================================================
# EXCEPTION HANDLING TESTS
# ============================================================

class TestExceptionHandling:
    """Test exception handling in services."""

    def test_invalid_product_data_raises_value_error(self, fresh_db):
        """Test that invalid product data raises ValueError."""
        with pytest.raises(ValueError):
            svc.inventory.add_product({"purchase_price": "not_a_number"}, username="testuser")

    def test_empty_sales_order_raises_value_error(self, fresh_db):
        """Test that empty sales order raises ValueError."""
        from exceptions import InvalidOrderDataError
        with pytest.raises(InvalidOrderDataError):
            svc.sales.create_order({"order_number": "SO-001"}, [], username="testuser")

    def test_missing_location_fields_raises_value_error(self, fresh_db):
        """Test that missing location fields raises ValueError."""
        with pytest.raises(ValueError):
            svc.location.add_location({}, username="testuser")


# ============================================================
# AUDIT LOG TESTS
# ============================================================

class TestAuditLogging:
    """Test audit logging functionality."""

    def test_product_creation_logs_audit(self, fresh_db, sample_product):
        """Test that creating a product logs an audit event."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        
        # Check audit log (directly in database)
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM audit_log WHERE action = 'create_product'")
            result = cur.fetchone()
            assert result["count"] >= 1

    def test_product_update_logs_audit(self, fresh_db, sample_product):
        """Test that updating a product logs an audit event."""
        svc.inventory.add_product(sample_product.copy(), username="testuser")
        svc.inventory.update_product("TEST-PROD-001", {"stock": 60}, username="testuser")
        
        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM audit_log WHERE action = 'update_product'")
            result = cur.fetchone()
            assert result["count"] >= 1
