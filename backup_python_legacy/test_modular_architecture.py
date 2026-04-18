"""
Modular Industry Architecture Test
====================================
Tests each industry INDEPENDENTLY to verify:
- NO cross-contamination between industries
- Each industry knows ONLY its own operations
- Configuration is industry-specific
- Services work independently
"""

import sys
import os
import unittest
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory_app'))

from db.base import DatabaseConnection
from config import get_industry_config, get_all_industries
from industry_services import get_industry_service
from industry_factory import create_industry, get_current_industry


class TestModularArchitecture(unittest.TestCase):
    """Test the complete modular architecture."""
    
    def setUp(self):
        """Create temporary database for testing."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create connection
        self.conn = DatabaseConnection(self.temp_db_path)
    
    def tearDown(self):
        """Clean up temporary database."""
        self.conn.close_connection()
        try:
            os.unlink(self.temp_db_path)
        except:
            pass
    
    def _init_minimal_schema(self):
        """Create minimal tables for testing."""
        with self.conn.cursor() as cur:
            # Products table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    category TEXT, brand TEXT, supplier TEXT,
                    purchase_price REAL, selling_price REAL,
                    stock INTEGER DEFAULT 0, reorder_point INTEGER DEFAULT 10,
                    description TEXT, notes TEXT,
                    status TEXT DEFAULT 'active', condition TEXT DEFAULT 'new',
                    -- Electronics fields
                    serial_number TEXT, imei TEXT,
                    ram TEXT, storage TEXT, screen_type TEXT,
                    camera TEXT, battery TEXT, color TEXT,
                    warranty_months INTEGER, warranty_expiry TEXT,
                    device_condition TEXT, specifications TEXT,
                    -- Pharma fields
                    batch_number TEXT, expiry_date TEXT,
                    manufacturer TEXT, dosage_form TEXT,
                    strength TEXT, prescription_required INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sales orders
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sales_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number TEXT UNIQUE NOT NULL,
                    customer_name TEXT, order_date TEXT,
                    status TEXT DEFAULT 'confirmed',
                    total_amount REAL DEFAULT 0
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sales_order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    product_id INTEGER,
                    quantity INTEGER DEFAULT 0,
                    unit_price REAL DEFAULT 0,
                    total_price REAL DEFAULT 0
                )
            """)
            
            # Serial numbers (electronics)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS serial_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    serial_number TEXT NOT NULL,
                    status TEXT DEFAULT 'in_stock',
                    warranty_start TEXT, warranty_end TEXT,
                    UNIQUE(product_id, serial_number)
                )
            """)
            
            # Prescriptions (pharma)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS prescriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name TEXT,
                    doctor_name TEXT,
                    items TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)


class TestConfiguration(TestModularArchitecture):
    """Test industry configurations."""
    
    def test_all_industries_available(self):
        """Test that all industries are registered."""
        industries = get_all_industries()
        self.assertIn("retail", industries)
        self.assertIn("electronics", industries)
        self.assertIn("pharma", industries)
    
    def test_retail_config(self):
        """Test RETAIL configuration is independent."""
        config = get_industry_config("retail")
        
        self.assertEqual(config.industry_id, "retail")
        self.assertEqual(config.icon, "🏪")
        
        # Retail should NOT have pharma/electronics fields
        self.assertNotIn("batch_number", config.product_fields)
        self.assertNotIn("serial_number", config.product_fields)
        self.assertNotIn("expiry_date", config.product_fields)
        
        # Retail should have basic fields
        self.assertIn("model", config.product_fields)
        self.assertIn("purchase_price", config.product_fields)
    
    def test_electronics_config(self):
        """Test ELECTRONICS configuration is independent."""
        config = get_industry_config("electronics")
        
        self.assertEqual(config.industry_id, "electronics")
        self.assertEqual(config.icon, "📱")
        self.assertTrue(config.warranty_tracking)
        
        # Electronics should have serial numbers and warranty
        self.assertIn("serial_number", config.product_fields)
        self.assertIn("imei", config.product_fields)
        self.assertIn("warranty_months", config.product_fields)
        
        # Should NOT have pharma fields
        self.assertNotIn("batch_number", config.product_fields)
        self.assertNotIn("expiry_date", config.product_fields)
    
    def test_pharma_config(self):
        """Test PHARMA configuration is independent."""
        config = get_industry_config("pharma")
        
        self.assertEqual(config.industry_id, "pharma")
        self.assertEqual(config.icon, "💊")
        self.assertTrue(config.batch_tracking)
        
        # Pharma should have batch/expiry
        self.assertIn("batch_number", config.product_fields)
        self.assertIn("expiry_date", config.product_fields)
        self.assertIn("dosage_form", config.product_fields)
        
        # Should NOT have electronics fields
        self.assertNotIn("serial_number", config.product_fields)
        self.assertNotIn("imei", config.product_fields)


class TestIndustryServices(TestModularArchitecture):
    """Test industry services work independently."""
    
    def setUp(self):
        super().setUp()
        self._init_minimal_schema()
    
    def test_retail_service_creation(self):
        """Test RETAIL service can be created."""
        service = get_industry_service("retail", self.conn)
        self.assertIsNotNone(service)
        self.assertEqual(service.__class__.__name__, "RetailService")
    
    def test_electronics_service_creation(self):
        """Test ELECTRONICS service can be created."""
        service = get_industry_service("electronics", self.conn)
        self.assertIsNotNone(service)
        self.assertEqual(service.__class__.__name__, "ElectronicsService")
    
    def test_pharma_service_creation(self):
        """Test PHARMA service can be created."""
        service = get_industry_service("pharma", self.conn)
        self.assertIsNotNone(service)
        self.assertEqual(service.__class__.__name__, "PharmaService")
    
    def test_retail_product_operations(self):
        """Test RETAIL product operations work."""
        service = get_industry_service("retail", self.conn)
        
        # Add product
        product_data = {
            "model": "RETAIL-001",
            "purchase_price": 100.0,
            "selling_price": 150.0,
            "stock": 50
        }
        product_id = service.add_product(product_data)
        self.assertGreater(product_id, 0)
        
        # Get product
        product = service.get_product_by_model("RETAIL-001")
        self.assertIsNotNone(product)
        self.assertEqual(product["model"], "RETAIL-001")
        
        # Adjust stock
        service.adjust_stock("RETAIL-001", -10)
        product = service.get_product_by_model("RETAIL-001")
        self.assertEqual(product["stock"], 40)
    
    def test_electronics_product_operations(self):
        """Test ELECTRONICS product operations work."""
        service = get_industry_service("electronics", self.conn)
        
        # Add product with electronics fields
        product_data = {
            "model": "ELEC-001",
            "purchase_price": 500.0,
            "selling_price": 700.0,
            "stock": 20,
            "ram": "8GB",
            "storage": "256GB",
            "warranty_months": 12,
            "device_condition": "new"
        }
        product_id = service.add_product(product_data)
        self.assertGreater(product_id, 0)
        
        # Get product
        product = service.get_product_by_model("ELEC-001")
        self.assertIsNotNone(product)
        self.assertEqual(product["ram"], "8GB")
    
    def test_pharma_product_operations(self):
        """Test PHARMA product operations work."""
        service = get_industry_service("pharma", self.conn)
        
        # Add product with pharma fields
        product_data = {
            "model": "PHARMA-001",
            "purchase_price": 50.0,
            "selling_price": 75.0,
            "stock": 100,
            "batch_number": "BATCH-2026-001",
            "expiry_date": "2027-12-31",
            "manufacturer": "Test Pharma",
            "dosage_form": "tablet"
        }
        product_id = service.add_product(product_data)
        self.assertGreater(product_id, 0)
        
        # Get product
        product = service.get_product_by_model("PHARMA-001")
        self.assertIsNotNone(product)
        self.assertEqual(product["batch_number"], "BATCH-2026-001")


class TestIndustryFactory(TestModularArchitecture):
    """Test the industry factory."""
    
    def test_factory_creates_industry(self):
        """Test factory can create complete industry instances."""
        from industry_factory import get_factory
        
        factory = get_factory()
        industry = factory.create_industry("retail", self.conn)
        
        self.assertIn("config", industry)
        self.assertIn("service", industry)
        self.assertEqual(industry["industry_id"], "retail")
    
    def test_factory_caches_instances(self):
        """Test factory caches industry instances."""
        from industry_factory import get_factory
        
        factory = get_factory()
        industry1 = factory.create_industry("retail", self.conn)
        industry2 = factory.create_industry("retail", self.conn)
        
        # Should be same instance (cached)
        self.assertIs(industry1, industry2)


class TestIndustryIsolation(TestModularArchitecture):
    """Test that industries are truly isolated."""
    
    def test_configs_are_independent(self):
        """Test that each config is a separate instance."""
        retail = get_industry_config("retail")
        electronics = get_industry_config("electronics")
        
        # Should be different instances
        self.assertIsNot(retail, electronics)
        
        # Should have different IDs
        self.assertNotEqual(retail.industry_id, electronics.industry_id)
    
    def test_services_are_independent(self):
        """Test that each service is a separate instance."""
        retail = get_industry_service("retail", self.conn)
        electronics = get_industry_service("electronics", self.conn)
        
        # Should be different instances
        self.assertIsNot(retail, electronics)
        
        # Should be different classes
        self.assertNotEqual(type(retail), type(electronics))


def run_tests():
    """Run all modular architecture tests."""
    print("=" * 70)
    print("Modular Industry Architecture Test Suite")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestIndustryServices))
    suite.addTests(loader.loadTestsFromTestCase(TestIndustryFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestIndustryIsolation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Modular architecture is working perfectly!")
        print("   - Each industry is INDEPENDENT")
        print("   - NO cross-contamination")
        print("   - Configurations are industry-specific")
        print("   - Services work independently")
    else:
        print("❌ TESTS FAILED - Please review the errors above")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
