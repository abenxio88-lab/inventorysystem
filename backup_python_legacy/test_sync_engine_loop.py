"""
Sync Engine Loop Test
=====================
Verifies that the SyncEngine background loop runs without AttributeError.
Tests the fix for _last_sync_time -> _last_sync bug.
"""

import sys
import os
import time
import threading
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'inventory_app'))

from sync_engine import SyncEngine


class TestSyncEngineLoop(unittest.TestCase):
    """Test the sync engine background loop."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = SyncEngine()
        self.engine._sync_interval = 2  # Short interval for testing (2 seconds)

    def tearDown(self):
        """Clean up resources."""
        self.engine.stop()

    @patch('sync_engine.is_online')
    @patch('sync_engine.get_connectivity_monitor')
    def test_sync_loop_no_attribute_error(self, mock_monitor, mock_is_online):
        """Test that sync loop doesn't raise AttributeError on _last_sync_time."""
        # Mock network to be online
        mock_is_online.return_value = True
        
        # Mock auto-sync to be enabled
        self.engine._is_auto_sync_enabled = MagicMock(return_value=True)
        
        # Mock _perform_sync to avoid actual sync operations
        self.engine._perform_sync = MagicMock()
        
        # Start the engine
        self.engine.start()
        
        # Let it run for a few seconds
        time.sleep(3)
        
        # Stop the engine
        self.engine.stop()
        
        # If we got here without an AttributeError, the test passes
        self.assertIsNone(self.engine._last_error)

    @patch('sync_engine.is_online')
    def test_sync_loop_with_offline_network(self, mock_is_online):
        """Test that sync loop handles offline network gracefully."""
        # Mock network to be offline
        mock_is_online.return_value = False
        
        # Start the engine
        self.engine.start()
        
        # Let it run for a few seconds
        time.sleep(2)
        
        # Stop the engine
        self.engine.stop()
        
        # Should not have any errors
        self.assertIsNone(self.engine._last_error)

    @patch('sync_engine.is_online')
    def test_sync_loop_performs_sync_when_online(self, mock_is_online):
        """Test that sync loop performs sync when network is online."""
        # Mock network to be online
        mock_is_online.return_value = True
        
        # Mock auto-sync to be enabled
        self.engine._is_auto_sync_enabled = MagicMock(return_value=True)
        
        # Track if _perform_sync was called
        perform_sync_called = threading.Event()
        
        def mock_perform_sync():
            perform_sync_called.set()
        
        self.engine._perform_sync = mock_perform_sync
        
        # Start the engine
        self.engine.start()
        
        # Wait for sync to be called
        performed = perform_sync_called.wait(timeout=5)
        
        # Stop the engine
        self.engine.stop()
        
        # Verify sync was attempted
        self.assertTrue(performed, "Sync should have been attempted when online")

    def test_last_sync_attribute_exists(self):
        """Test that _last_sync attribute exists and is accessible."""
        # This verifies the fix for the AttributeError bug
        self.assertIsNone(self.engine._last_sync)
        
        # Set it to a value
        self.engine._last_sync = time.time()
        self.assertIsNotNone(self.engine._last_sync)
        
        # Verify it's a timestamp
        self.assertIsInstance(self.engine._last_sync, float)

    @patch('sync_engine.is_online')
    def test_sync_loop_error_handling(self, mock_is_online):
        """Test that sync loop handles errors gracefully."""
        # Mock network to be online
        mock_is_online.return_value = True
        
        # Mock auto-sync to be enabled
        self.engine._is_auto_sync_enabled = MagicMock(return_value=True)
        
        # Mock _perform_sync to raise an exception
        self.engine._perform_sync = MagicMock(side_effect=Exception("Test error"))
        
        # Start the engine
        self.engine.start()
        
        # Let it run for a few seconds
        time.sleep(3)
        
        # Stop the engine
        self.engine.stop()
        
        # Should have recorded the error
        self.assertIsNotNone(self.engine._last_error)
        self.assertIn("Test error", self.engine._last_error)

    def test_sync_interval_setting(self):
        """Test that sync interval can be set correctly."""
        self.assertEqual(self.engine._sync_interval, 2)
        
        # Change interval
        self.engine.set_sync_interval(5)
        self.assertEqual(self.engine._sync_interval, 5 * 60)  # 5 minutes in seconds
        
        # Test minimum interval (should not be less than 1 minute)
        self.engine.set_sync_interval(0)
        self.assertEqual(self.engine._sync_interval, 60)  # Minimum 1 minute


class TestSyncEngineProperties(unittest.TestCase):
    """Test sync engine property accessors."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = SyncEngine()

    def test_last_sync_property(self):
        """Test last_sync property returns datetime or None."""
        from datetime import datetime
        
        # Initially should be None
        self.assertIsNone(self.engine.last_sync)
        
        # Set a timestamp
        self.engine._last_sync = time.time()
        last_sync = self.engine.last_sync
        self.assertIsInstance(last_sync, datetime)

    def test_last_error_property(self):
        """Test last_error property."""
        # Initially should be None
        self.assertIsNone(self.engine.last_error)
        
        # Set an error
        self.engine._last_error = "Test error"
        self.assertEqual(self.engine.last_error, "Test error")

    def test_is_syncing_property(self):
        """Test is_syncing property."""
        # Initially should be False
        self.assertFalse(self.engine.is_syncing)
        
        # Set syncing flag
        self.engine._sync_in_progress = True
        self.assertTrue(self.engine.is_syncing)


def run_tests():
    """Run all sync engine tests."""
    print("=" * 60)
    print("Sync Engine Loop Test Suite")
    print("=" * 60)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestSyncEngineLoop))
    suite.addTests(loader.loadTestsFromTestCase(TestSyncEngineProperties))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Sync engine is stable and working correctly!")
    else:
        print("❌ TESTS FAILED - Please review the errors above")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
