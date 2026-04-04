"""
Integration Tests for Service Layer
=====================================
Tests the integration between services, repositories, and models.
Run: pytest tests/test_services/ -v

Note: Database tests require the app to have been run at least once
to initialize the database.
"""

import pytest
from pathlib import Path
import sys
import os

# Add src and inventory_app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "inventory_app"))


class TestProductService:
    """Test Product Service integration."""
    
    @pytest.fixture
    def service(self):
        """Create product service instance."""
        from src.services import ProductService
        return ProductService()
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_all_products(self, service):
        """Test getting all products."""
        products = service.get_all_products()
        assert isinstance(products, list)
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_product_by_id(self, service):
        """Test getting product by ID."""
        products = service.get_all_products()
        if products:
            product = service.get_product(products[0].id)
            assert product is not None
            assert product.id == products[0].id
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_search_products(self, service):
        """Test searching products."""
        # Search for common terms
        results = service.search_products("iPhone")
        assert isinstance(results, list)
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_low_stock_products(self, service):
        """Test getting low stock products."""
        low_stock = service.get_low_stock_products(threshold=10)
        assert isinstance(low_stock, list)
        
        # All returned products should have stock <= threshold
        for product in low_stock:
            assert product.stock <= 10
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_check_availability(self, service):
        """Test availability checking."""
        products = service.get_all_products()
        if products:
            product = products[0]
            # Should be available if stock > 0
            available = service.check_availability(product.id, 1)
            assert isinstance(available, bool)


class TestInventoryService:
    """Test Inventory Service integration."""
    
    @pytest.fixture
    def service(self):
        """Create inventory service instance."""
        from src.services import InventoryService
        return InventoryService()
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_stock_status(self, service):
        """Test getting stock status."""
        from src.models import StockStatus
        
        products = service.product_service.get_all_products()
        if products:
            status = service.get_stock_status(products[0].id)
            assert status in [StockStatus.IN_STOCK, StockStatus.LOW_STOCK, 
                            StockStatus.CRITICAL, StockStatus.OUT_OF_STOCK]
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_inventory_summary(self, service):
        """Test getting inventory summary."""
        summary = service.get_inventory_summary()
        
        assert isinstance(summary, dict)
        assert 'total_products' in summary
        assert 'total_stock' in summary
        assert 'low_stock_count' in summary
        assert 'out_of_stock_count' in summary
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_reorder_suggestions(self, service):
        """Test getting reorder suggestions."""
        suggestions = service.get_reorder_suggestions()
        assert isinstance(suggestions, list)
        
        # Each suggestion should have required fields
        for suggestion in suggestions:
            assert 'product_id' in suggestion
            assert 'model' in suggestion
            assert 'current_stock' in suggestion
            assert 'suggested_order_qty' in suggestion


class TestDashboardService:
    """Test Dashboard Service integration."""
    
    @pytest.fixture
    def service(self):
        """Create dashboard service instance."""
        from src.services import DashboardService
        return DashboardService()
    
    @pytest.mark.skip(reason="Requires database initialization")
    def test_get_stats(self, service):
        """Test getting dashboard statistics."""
        from src.models import DashboardStats
        
        stats = service.get_stats()
        
        assert isinstance(stats, DashboardStats)
        assert hasattr(stats, 'total_products')
        assert hasattr(stats, 'total_stock')
        assert hasattr(stats, 'low_stock_count')
        assert hasattr(stats, 'out_of_stock_count')
        assert hasattr(stats, 'total_sales_today')
        assert hasattr(stats, 'total_sales_month')


class TestRepositoryPattern:
    """Test Repository pattern integration."""
    
    def test_repository_factory(self):
        """Test repository factory."""
        from src.repositories import repositories
        
        # Get repositories
        product_repo = repositories.get("product")
        assert product_repo is not None
        
        customer_repo = repositories.get("customer")
        assert customer_repo is not None
        
        supplier_repo = repositories.get("supplier")
        assert supplier_repo is not None
    
    def test_service_factory(self):
        """Test service factory."""
        from src.services import services
        
        # Get services
        product_service = services.get("product")
        assert product_service is not None
        
        inventory_service = services.get("inventory")
        assert inventory_service is not None
        
        sales_service = services.get("sales")
        assert sales_service is not None


class TestConfiguration:
    """Test configuration system."""
    
    def test_load_config(self):
        """Test loading configuration."""
        from src.core import get_config
        
        config = get_config()
        assert config is not None
        assert hasattr(config, 'app_name')
        assert hasattr(config, 'low_stock_threshold')
        assert hasattr(config, 'theme')
    
    def test_config_values(self):
        """Test configuration values."""
        from src.core import get_config
        
        config = get_config()
        
        # Check default values
        assert config.low_stock_threshold > 0
        assert config.critical_stock_threshold > 0
        assert config.currency_symbol


class TestModelMethods:
    """Test model business logic."""
    
    def test_product_stock_status(self):
        """Test product stock status calculation."""
        from src.models import Product, StockStatus
        
        # In stock
        product = Product(stock=50)
        assert product.stock_status == StockStatus.IN_STOCK
        
        # Low stock
        product = Product(stock=8)
        assert product.stock_status == StockStatus.LOW_STOCK
        
        # Critical
        product = Product(stock=3)
        assert product.stock_status == StockStatus.CRITICAL
        
        # Out of stock
        product = Product(stock=0)
        assert product.stock_status == StockStatus.OUT_OF_STOCK
    
    def test_product_profit_margin(self):
        """Test profit margin calculation."""
        from src.models import Product
        
        # 50% margin
        product = Product(purchase_price=50.0, selling_price=75.0)
        assert abs(product.profit_margin - 50.0) < 0.01
        
        # Zero cost
        product = Product(purchase_price=0, selling_price=75.0)
        assert product.profit_margin == 0.0
    
    def test_invoice_balance(self):
        """Test invoice balance calculation."""
        from src.models import Invoice
        
        invoice = Invoice(total_amount=1000.0, amount_paid=400.0)
        assert invoice.balance == 600.0
        
        # Fully paid
        invoice = Invoice(total_amount=1000.0, amount_paid=1000.0)
        assert invoice.balance == 0.0
    
    def test_invoice_overdue(self):
        """Test invoice overdue detection."""
        from src.models import Invoice
        
        # Past due date
        invoice = Invoice(
            total_amount=1000.0,
            due_date="2020-01-01",
            status="pending"
        )
        assert invoice.is_overdue is True
        
        # Paid invoice
        invoice = Invoice(
            total_amount=1000.0,
            due_date="2020-01-01",
            status="paid"
        )
        assert invoice.is_overdue is False


class TestServiceLayerAvailability:
    """Test service layer availability in UI modules."""
    
    @pytest.mark.skip(reason="UI modules require tkinter environment")
    def test_inventory_ui_service_layer(self):
        """Test inventory UI has service layer."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "inventory_ui",
            "inventory_app/inventory_ui.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check service layer is available
        assert hasattr(module, 'SERVICE_LAYER_AVAILABLE')
    
    @pytest.mark.skip(reason="UI modules require tkinter environment")
    def test_sales_ui_service_layer(self):
        """Test sales UI has service layer."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "sales_ui",
            "inventory_app/sales_ui.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check service layer is available
        assert hasattr(module, 'SERVICE_LAYER_AVAILABLE')


class TestFallbackMechanism:
    """Test fallback mechanism works correctly."""
    
    @pytest.mark.skip(reason="UI modules require tkinter environment")
    def test_load_inventory_fallback(self):
        """Test load_inventory has fallback."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "inventory_ui",
            "inventory_app/inventory_ui.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check load_inventory function exists
        assert hasattr(module, 'load_inventory')
        
        # Should be callable
        assert callable(module.load_inventory)
    
    @pytest.mark.skip(reason="UI modules require tkinter environment")
    def test_save_inventory_fallback(self):
        """Test save_inventory has fallback."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "inventory_ui",
            "inventory_app/inventory_ui.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check save_inventory function exists
        assert hasattr(module, 'save_inventory')
        
        # Should be callable
        assert callable(module.save_inventory)
