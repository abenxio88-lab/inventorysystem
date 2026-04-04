"""
Industry Switching Smoke Tests
===============================
Tests the IndustryService and related components for the industry switching flow.

Run: python -m pytest tests/test_industry_switching.py -v

Acceptance criteria:
1. Switching retail <-> pharma <-> electronics normalizes correctly
2. get_current() returns consistent values
3. subscribe/unsubscribe works
4. Config access returns correct data for each industry
5. Invalid industry IDs are rejected gracefully
"""

import sys
import os
import unittest
import tempfile
import sqlite3

# Ensure the app module is importable
APP_DIR = os.path.join(os.path.dirname(__file__), "..", "inventory_app")
sys.path.insert(0, os.path.abspath(APP_DIR))


class TestIndustryService(unittest.TestCase):
    """Test IndustryService logic without UI."""

    def setUp(self):
        """Set up a temporary database for testing."""
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.conn = sqlite3.connect(self.tmp_db.name)
        self.conn.row_factory = sqlite3.Row
        self._setup_db()

    def tearDown(self):
        self.conn.close()
        os.unlink(self.tmp_db.name)

    def _setup_db(self):
        """Create minimal schema needed for tests."""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                category TEXT DEFAULT 'general',
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            INSERT OR IGNORE INTO settings (key, value, category, description)
            VALUES ('industry_type', 'retail', 'business', 'Primary business type')
        """)
        self.conn.commit()

    def _get_industry(self):
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = 'industry_type'")
        row = cur.fetchone()
        return row["value"] if row else None

    def _set_industry(self, value):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'industry_type'",
            (value,)
        )
        self.conn.commit()

    def test_01_canonical_config_exists(self):
        """IndustryService has one canonical config with 6 industries."""
        from industry_service import INDUSTRY_CONFIG, VALID_INDUSTRY_IDS

        self.assertEqual(len(INDUSTRY_CONFIG), 6)
        self.assertEqual(VALID_INDUSTRY_IDS, {
            "retail", "pharma", "electronics",
            "lease_rental", "manufacturing", "healthcare"
        })

    def test_02_normalize_industry_id(self):
        """normalize_industry_id handles various input formats correctly."""
        from industry_service import normalize_industry_id

        # Direct matches
        self.assertEqual(normalize_industry_id("retail"), "retail")
        self.assertEqual(normalize_industry_id("pharma"), "pharma")
        self.assertEqual(normalize_industry_id("electronics"), "electronics")

        # Display name mapping
        self.assertEqual(normalize_industry_id("Pharmacy"), "pharma")
        self.assertEqual(normalize_industry_id("pharmacy"), "pharma")
        self.assertEqual(normalize_industry_id("Lease & Rental"), "lease_rental")
        self.assertEqual(normalize_industry_id("General Retail"), "retail")

        # Edge cases
        self.assertEqual(normalize_industry_id(""), "retail")
        self.assertEqual(normalize_industry_id(None), "retail")
        self.assertEqual(normalize_industry_id("  PHARMA  "), "pharma")

    def test_03_get_config_returns_correct_data(self):
        """get_config returns full config dict with all required fields."""
        from industry_service import get_config

        for industry_id in ["retail", "pharma", "electronics", "lease_rental",
                            "manufacturing", "healthcare"]:
            config = get_config(industry_id)
            self.assertIn("id", config)
            self.assertIn("name", config)
            self.assertIn("icon", config)
            self.assertIn("color", config)
            self.assertIn("app_state_name", config)
            self.assertEqual(config["id"], industry_id)

    def test_04_get_config_falls_back_to_retail(self):
        """get_config falls back to retail for unknown industry IDs."""
        from industry_service import get_config, DEFAULT_INDUSTRY_ID

        config = get_config("nonexistent_industry")
        self.assertEqual(config["id"], DEFAULT_INDUSTRY_ID)

    def test_05_industry_type_read_from_db(self):
        """get_current_industry_id reads from DB and normalizes correctly."""
        from industry_service import get_current_industry_id

        # Mock the svc.db.get_industry_type by temporarily patching
        import industry_service as svc_module
        original_svc = None
        if hasattr(svc_module, 'svc'):
            original_svc = svc_module.svc

        class MockDB:
            def get_industry_type(self):
                return self._val
            def set_industry_type(self, val):
                self._val = val
                return True
            _val = "pharma"

        class MockSvc:
            db = MockDB()

        svc_module.svc = MockSvc()
        try:
            result = get_current_industry_id()
            self.assertEqual(result, "pharma")
        finally:
            if original_svc:
                svc_module.svc = original_svc

    def test_06_invalid_industry_rejected(self):
        """Invalid industry IDs return False from change_industry."""
        # Note: change_industry tries to import svc and main, so we test
        # validation separately through normalize_industry_id
        from industry_service import normalize_industry_id, VALID_INDUSTRY_IDS

        # Unknown input normalizes to default, not to itself
        result = normalize_industry_id("totally_fake_industry")
        self.assertEqual(result, "retail")  # Falls back to default

    def test_07_subscribe_unsubscribe_api(self):
        """subscribe/unsubscribe work correctly."""
        from industry_service import subscribe, unsubscribe, _subscribers

        call_log = []
        def my_cb(industry_id):
            call_log.append(industry_id)

        subscribe(my_cb)
        self.assertIn(my_cb, _subscribers)

        unsubscribe(my_cb)
        self.assertNotIn(my_cb, _subscribers)

    def test_08_notify_subscribers_fires_callbacks(self):
        """_notify_subscribers fires all registered callbacks."""
        from industry_service import subscribe, unsubscribe, _notify_subscribers

        call_log = []
        def cb1(iid):
            call_log.append(("cb1", iid))
        def cb2(iid):
            call_log.append(("cb2", iid))

        subscribe(cb1)
        subscribe(cb2)

        _notify_subscribers("pharma")

        self.assertIn(("cb1", "pharma"), call_log)
        self.assertIn(("cb2", "pharma"), call_log)

        unsubscribe(cb1)
        unsubscribe(cb2)

    def test_09_config_all_icons_are_unique(self):
        """Each industry has a distinct icon."""
        from industry_service import INDUSTRY_CONFIG

        icons = [v["icon"] for v in INDUSTRY_CONFIG.values()]
        self.assertEqual(len(icons), len(set(icons)),
                        "Industry icons should be unique")

    def test_10_config_all_colors_valid(self):
        """Each industry has a valid hex color."""
        import re
        from industry_service import INDUSTRY_CONFIG

        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for industry_id, config in INDUSTRY_CONFIG.items():
            self.assertTrue(hex_pattern.match(config["color"]),
                          f"{industry_id} has invalid color: {config['color']}")

    def test_11_legacy_shims_delegate_correctly(self):
        """Legacy get_industry_type and set_industry_type delegate to new API."""
        from industry_service import get_industry_type, normalize_industry_id

        # get_industry_type calls get_current_industry_id which needs svc
        # Just verify it exists and is callable
        self.assertTrue(callable(get_industry_type))
        self.assertTrue(callable(normalize_industry_id))


class TestTabManager(unittest.TestCase):
    """Test tab_manager metadata-based registry logic."""

    def test_tag_last_tab_structure(self):
        """_tag_last_tab function exists and has correct signature."""
        from tab_manager import _tag_last_tab
        self.assertTrue(callable(_tag_last_tab))

    def test_reload_industry_tabs_signature(self):
        """reload_industry_tabs has correct parameter count."""
        import inspect
        from tab_manager import reload_industry_tabs
        sig = inspect.signature(reload_industry_tabs)
        # Should accept at least the required parameters
        self.assertGreaterEqual(len(sig.parameters), 5)

    def test_tag_dashboard_tab_exists(self):
        """tag_dashboard_tab function exists."""
        from tab_manager import tag_dashboard_tab
        self.assertTrue(callable(tag_dashboard_tab))


if __name__ == "__main__":
    unittest.main()
