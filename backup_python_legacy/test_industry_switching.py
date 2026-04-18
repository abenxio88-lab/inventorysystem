"""
Industry Switching Flow Test
==============================
Tests config-driven tab selection and isolation.
Does NOT require actual UI modules to exist.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory_app'))

from config import get_industry_config, get_all_industries, TAB_REGISTRY
from tab_manager import get_industry_tab_count


class TestIndustrySwitchingFlow(unittest.TestCase):
    """Test industry switching configuration and flow."""
    
    def test_all_industries_exist(self):
        """Test that all industries are registered."""
        industries = get_all_industries()
        self.assertIn("electronics", industries)
        self.assertIn("retail", industries)
        self.assertIn("pharma", industries)
        self.assertGreaterEqual(len(industries), 3)
    
    def test_electronics_is_default(self):
        """Test that electronics is the default industry."""
        config = get_industry_config()  # No args = default
        self.assertEqual(config.industry_id, "electronics")
    
    def test_tab_registry_complete(self):
        """Test that tab registry has all necessary mappings."""
        # Core tabs
        self.assertIn("Dashboard", TAB_REGISTRY)
        self.assertIn("Inventory", TAB_REGISTRY)
        self.assertIn("Sales", TAB_REGISTRY)
        self.assertIn("Customers", TAB_REGISTRY)
        self.assertIn("Suppliers", TAB_REGISTRY)
        self.assertIn("Reports", TAB_REGISTRY)
        self.assertIn("Settings", TAB_REGISTRY)
        
        # Electronics tabs
        self.assertIn("Serial Numbers", TAB_REGISTRY)
        self.assertIn("Warranty", TAB_REGISTRY)
        
        # Pharma tabs
        self.assertIn("Batches", TAB_REGISTRY)
        self.assertIn("Expiry Alerts", TAB_REGISTRY)
        self.assertIn("Prescriptions", TAB_REGISTRY)
    
    def test_electronics_tab_isolation(self):
        """Test electronics tabs are isolated from other industries."""
        config = get_industry_config("electronics")
        visible = config.get_visible_tabs()
        
        # Should have electronics-specific tabs
        self.assertIn("Serial Numbers", visible)
        self.assertIn("Warranty", visible)
        
        # Should NOT have pharma tabs
        self.assertNotIn("Batches", visible)
        self.assertNotIn("Expiry Alerts", visible)
        self.assertNotIn("Prescriptions", visible)
        
        # Should have core tabs
        self.assertIn("Dashboard", visible)
        self.assertIn("Inventory", visible)
        self.assertIn("Sales", visible)
    
    def test_pharma_tab_isolation(self):
        """Test pharma tabs are isolated from other industries."""
        config = get_industry_config("pharma")
        visible = config.get_visible_tabs()
        
        # Should have pharma-specific tabs
        self.assertIn("Batches", visible)
        self.assertIn("Expiry Alerts", visible)
        self.assertIn("Prescriptions", visible)
        
        # Should NOT have electronics tabs
        self.assertNotIn("Serial Numbers", visible)
        self.assertNotIn("Warranty", visible)
        
        # Should have core tabs
        self.assertIn("Dashboard", visible)
        self.assertIn("Inventory", visible)
    
    def test_retail_tab_isolation(self):
        """Test retail has only basic tabs."""
        config = get_industry_config("retail")
        visible = config.get_visible_tabs()
        
        # Should have core tabs
        self.assertIn("Dashboard", visible)
        self.assertIn("Inventory", visible)
        self.assertIn("Sales", visible)
        
        # Should NOT have industry-specific tabs
        self.assertNotIn("Serial Numbers", visible)
        self.assertNotIn("Warranty", visible)
        self.assertNotIn("Batches", visible)
        self.assertNotIn("Expiry Alerts", visible)
        self.assertNotIn("Prescriptions", visible)
    
    def test_tab_counts_are_correct(self):
        """Test that each industry has expected tab count."""
        # Electronics: 7 core + 2 industry = 9
        self.assertEqual(get_industry_tab_count("electronics"), 9)
        
        # Retail: 7 core = 7
        self.assertEqual(get_industry_tab_count("retail"), 7)
        
        # Pharma: 7 core + 3 industry = 10
        self.assertEqual(get_industry_tab_count("pharma"), 10)
    
    def test_config_field_isolation(self):
        """Test that product fields are isolated per industry."""
        electronics = get_industry_config("electronics")
        pharma = get_industry_config("pharma")
        retail = get_industry_config("retail")
        
        # Electronics fields
        self.assertIn("serial_number", electronics.product_fields)
        self.assertIn("imei", electronics.product_fields)
        self.assertIn("warranty_months", electronics.product_fields)
        self.assertNotIn("batch_number", electronics.product_fields)
        self.assertNotIn("expiry_date", electronics.product_fields)
        
        # Pharma fields
        self.assertIn("batch_number", pharma.product_fields)
        self.assertIn("expiry_date", pharma.product_fields)
        self.assertIn("dosage_form", pharma.product_fields)
        self.assertNotIn("serial_number", pharma.product_fields)
        self.assertNotIn("imei", pharma.product_fields)
        
        # Retail fields (basic only)
        self.assertIn("model", retail.product_fields)
        self.assertIn("purchase_price", retail.product_fields)
        self.assertNotIn("serial_number", retail.product_fields)
        self.assertNotIn("batch_number", retail.product_fields)
    
    def test_hidden_tabs_are_correct(self):
        """Test that hidden tabs are correctly excluded."""
        electronics = get_industry_config("electronics")
        pharma = get_industry_config("pharma")
        retail = get_industry_config("retail")
        
        # Electronics hides pharma tabs
        self.assertIn("Batches", electronics.hidden_tabs)
        self.assertIn("Expiry Alerts", electronics.hidden_tabs)
        self.assertIn("Prescriptions", electronics.hidden_tabs)
        
        # Pharma hides electronics tabs
        self.assertIn("Serial Numbers", pharma.hidden_tabs)
        self.assertIn("Warranty", pharma.hidden_tabs)
        
        # Retail hides both
        self.assertIn("Serial Numbers", retail.hidden_tabs)
        self.assertIn("Batches", retail.hidden_tabs)
    
    def test_get_visible_tabs_filters_correctly(self):
        """Test that get_visible_tabs() removes hidden tabs."""
        electronics = get_industry_config("electronics")
        visible = electronics.get_visible_tabs()
        
        # Should not contain hidden tabs
        for hidden in electronics.hidden_tabs:
            self.assertNotIn(hidden, visible, f"Hidden tab '{hidden}' should not be visible")
        
        # Should contain core tabs
        for core in electronics.core_tabs:
            self.assertIn(core, visible, f"Core tab '{core}' should be visible")


def run_tests():
    """Run all industry switching tests."""
    print("=" * 70)
    print("Industry Switching Flow Test Suite")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestIndustrySwitchingFlow))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("   - Tab registry complete")
        print("   - Industry isolation verified")
        print("   - Field isolation verified")
        print("   - Hidden tabs correctly excluded")
        print("   - Config-driven switching works")
    else:
        print("❌ TESTS FAILED")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
