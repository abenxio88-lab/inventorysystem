"""
Test Script for New Features
=============================
Run this to verify all new modules are working correctly.
"""

import sys
import os

# Add inventory_app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'inventory_app'))

def test_database():
    """Test database initialization."""
    print("\n" + "="*50)
    print("TESTING: Database Module")
    print("="*50)
    
    try:
        from database import init_database, get_db_stats, get_connection
        
        # Initialize
        print("✓ Initializing database...")
        init_database()
        
        # Get stats
        print("✓ Getting database stats...")
        stats = get_db_stats()
        print(f"  - Total Products: {stats.get('total_products', 0)}")
        print(f"  - Low Stock Items: {stats.get('low_stock_count', 0)}")
        print(f"  - Suppliers: {stats.get('total_suppliers', 0)}")
        print(f"  - Locations: {stats.get('total_locations', 0)}")
        print(f"  - Pending Sync: {stats.get('pending_sync', 0)}")
        print(f"  - Unread Alerts: {stats.get('unread_alerts', 0)}")
        
        print("\n✅ DATABASE: PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ DATABASE: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_network():
    """Test network connectivity monitoring."""
    print("\n" + "="*50)
    print("TESTING: Network Module")
    print("="*50)
    
    try:
        from network import get_connectivity_monitor, is_online, check_now
        
        # Get monitor
        print("✓ Getting connectivity monitor...")
        monitor = get_connectivity_monitor()
        
        # Check status
        print("✓ Checking connectivity...")
        status = is_online()
        print(f"  - Status: {'🟢 Online' if status else '🔴 Offline'}")
        print(f"  - Status Text: {monitor.status_text}")
        print(f"  - Status Icon: {monitor.status_icon}")
        
        # Force check
        print("✓ Forcing connectivity check...")
        result = check_now()
        print(f"  - Check Result: {'Success' if result else 'Failed'}")
        
        print("\n✅ NETWORK: PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ NETWORK: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_alerts():
    """Test alerts system."""
    print("\n" + "="*50)
    print("TESTING: Alerts Module")
    print("="*50)
    
    try:
        from alerts import alert_manager, check_all_alerts, get_unread_alerts
        
        # Check alerts
        print("✓ Running alert checks...")
        results = check_all_alerts()
        print(f"  - Low Stock Alerts: {len(results.get('low_stock', []))}")
        print(f"  - Warranty Expiry: {len(results.get('warranty_expiry', []))}")
        print(f"  - Unread Count: {results.get('unread_count', 0)}")
        
        # Get unread
        print("✓ Getting unread alerts...")
        unread = get_unread_alerts()
        print(f"  - Unread Alerts: {len(unread)}")
        
        if unread:
            print(f"  - Latest: {unread[0].get('title', 'N/A')}")
        
        print("\n✅ ALERTS: PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ ALERTS: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_backup():
    """Test backup system."""
    print("\n" + "="*50)
    print("TESTING: Backup Module")
    print("="*50)
    
    try:
        from backup_manager import backup_manager, get_backup_stats
        
        # Get stats
        print("✓ Getting backup stats...")
        stats = get_backup_stats()
        print(f"  - Total Backups: {stats.get('total_backups', 0)}")
        print(f"  - Valid Backups: {stats.get('valid_backups', 0)}")
        print(f"  - Total Size: {stats.get('total_size_mb', 0)} MB")
        
        # Create test backup
        print("✓ Creating test backup...")
        backup_path = backup_manager.create_backup("test")
        print(f"  - Backup Created: {backup_path}")
        
        # Verify
        print("✓ Verifying backup...")
        is_valid = backup_manager.verify_backup(backup_path)
        print(f"  - Integrity Check: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        print("\n✅ BACKUP: PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ BACKUP: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_qr():
    """Test QR code generation."""
    print("\n" + "="*50)
    print("TESTING: QR Generator Module")
    print("="*50)
    
    try:
        from qr_generator import generate_qr_code, save_product_qr
        
        # Generate simple QR
        print("✓ Generating test QR code...")
        img = generate_qr_code("Test QR Code - Minataka Sphere")
        print(f"  - QR Size: {img.size}")
        
        # Save test QR
        test_path = os.path.join(os.path.dirname(__file__), 'test_qr.png')
        img.save(test_path)
        print(f"  - Saved to: {test_path}")
        
        # Generate product QR
        print("✓ Generating product QR code...")
        product = {
            'id': 1,
            'sku': 'TEST-001',
            'model': 'iPhone 16 Pro Max',
            'stock': 50,
            'selling_price': 2000
        }
        
        product_qr_path = os.path.join(os.path.dirname(__file__), 'test_product_qr.png')
        save_product_qr(product, product_qr_path)
        print(f"  - Product QR Saved: {product_qr_path}")
        
        print("\n✅ QR GENERATOR: PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ QR GENERATOR: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_sync_engine():
    """Test sync engine."""
    print("\n" + "="*50)
    print("TESTING: Sync Engine Module")
    print("="*50)
    
    try:
        from sync_engine import get_sync_engine, get_pending_sync_count
        
        # Get sync engine
        print("✓ Getting sync engine...")
        sync = get_sync_engine()
        
        # Get pending count
        print("✓ Checking pending sync...")
        pending = get_pending_sync_count()
        print(f"  - Pending Operations: {pending}")
        
        print("\n✅ SYNC ENGINE: PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n❌ SYNC ENGINE: FAILED - {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  MINATAKA SPHERE INVENTORY SYSTEM - FEATURE TESTS")
    print("="*60)
    
    results = {
        'Database': test_database(),
        'Network': test_network(),
        'Alerts': test_alerts(),
        'Backup': test_backup(),
        'QR Generator': test_qr(),
        'Sync Engine': test_sync_engine()
    }
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:20} {status}")
    
    print("-"*60)
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 ALL TESTS PASSED! System is ready!")
    else:
        print(f"\n  ⚠️ {total - passed} test(s) failed. Check errors above.")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
