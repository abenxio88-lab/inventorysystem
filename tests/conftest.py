"""
Pytest Configuration and Fixtures
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_config():
    """Create test configuration."""
    from src.core import AppConfig
    
    config = AppConfig(
        app_name="MS Inventory Test",
        debug=True,
        database_path=":memory:",
        log_level="DEBUG",
    )
    return config


@pytest.fixture
def sample_product():
    """Create sample product data."""
    from src.models import Product
    
    return Product(
        sku="TEST-001",
        model="Test Product",
        category="Electronics",
        stock=100,
        purchase_price=50.0,
        selling_price=75.0,
    )


@pytest.fixture
def sample_customer():
    """Create sample customer data."""
    from src.models import Customer
    
    return Customer(
        name="Test Customer",
        phone="1234567890",
        email="test@example.com",
        city="Karachi",
    )


@pytest.fixture
def sample_supplier():
    """Create sample supplier data."""
    from src.models import Supplier
    
    return Supplier(
        name="Test Supplier",
        contact_person="John Doe",
        phone="0987654321",
        email="supplier@example.com",
        city="Lahore",
    )
