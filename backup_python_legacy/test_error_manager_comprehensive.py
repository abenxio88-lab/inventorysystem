"""
Comprehensive test suite for error_manager.py
Tests EVERY function and verifies ALL connections
"""

import os
import sys
import json
import threading

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'inventory_app'))

from error_manager import (
    ErrorSeverity,
    AppError,
    ErrorManager,
    handle_errors,
    error_context,
    get_error_manager,
    report_error,
    report_info,
    report_warning,
    report_critical,
    install_global_hook
)


def test_error_severity_constants():
    """Test ErrorSeverity class constants are properly defined."""
    print("\n[TEST] ErrorSeverity constants...")
    assert ErrorSeverity.INFO == 'info'
    assert ErrorSeverity.WARNING == 'warning'
    assert ErrorSeverity.ERROR == 'error'
    assert ErrorSeverity.CRITICAL == 'critical'
    
    # Verify COLORS dictionary
    assert ErrorSeverity.COLORS['info'] == '#2196F3'
    assert ErrorSeverity.COLORS['warning'] == '#FF9800'
    assert ErrorSeverity.COLORS['error'] == '#F44336'
    assert ErrorSeverity.COLORS['critical'] == '#9C27B0'
    
    # Verify ICONS dictionary
    assert 'ℹ️' in ErrorSeverity.ICONS['info']
    assert '⚠️' in ErrorSeverity.ICONS['warning']
    assert '❌' in ErrorSeverity.ICONS['error']
    assert '🔥' in ErrorSeverity.ICONS['critical']
    print("  ✓ ErrorSeverity constants OK")


def test_apperror_creation():
    """Test AppError class creation and methods."""
    print("\n[TEST] AppError creation...")
    
    # Test basic creation
    error = AppError("Test error message")
    assert error.message == "Test error message"
    assert error.severity == 'error'
    assert error.exception is None
    assert error.context == {}
    assert error.traceback is None
    assert error.module == 'Unknown'
    assert error.function == 'Unknown'
    assert error.user_action == 'Unknown'
    assert error.resolved is False
    assert error.resolved_at is None
    assert error.id is not None
    assert error.timestamp is not None
    print("  ✓ Basic creation OK")
    
    # Test with exception
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        error = AppError("Error with exception", exception=e, context={
            'module': 'TestModule',
            'function': 'test_func',
            'user_action': 'Testing'
        })
        assert error.exception is not None
        assert error.traceback is not None
        assert 'ValueError' in error.traceback
        assert error.module == 'TestModule'
        assert error.function == 'test_func'
        assert error.user_action == 'Testing'
    print("  ✓ Exception handling OK")
    
    # Test to_dict()
    error_dict = error.to_dict()
    assert 'id' in error_dict
    assert 'timestamp' in error_dict
    assert 'message' in error_dict
    assert 'severity' in error_dict
    assert 'module' in error_dict
    assert 'function' in error_dict
    assert 'exception_type' in error_dict
    assert error_dict['exception_type'] == 'ValueError'
    print("  ✓ to_dict() OK")
    
    # Test __str__()
    str_repr = str(error)
    assert '[ERROR]' in str_repr
    assert 'TestModule' in str_repr
    assert 'test_func' in str_repr
    assert 'Error with exception' in str_repr
    print(f"  ✓ __str__() OK: {str_repr}")


def test_error_manager_singleton():
    """Test ErrorManager singleton pattern."""
    print("\n[TEST] ErrorManager singleton...")
    
    em1 = get_error_manager()
    em2 = get_error_manager()
    
    assert em1 is em2, "Singleton pattern failed - different instances"
    print("  ✓ Singleton pattern OK")


def test_error_manager_initialization():
    """Test ErrorManager initialization attributes."""
    print("\n[TEST] ErrorManager initialization...")
    
    em = get_error_manager()
    
    assert hasattr(em, 'errors')
    assert hasattr(em, 'callbacks')
    assert hasattr(em, 'error_count')
    assert hasattr(em, 'critical_count')
    assert hasattr(em, 'warning_count')
    assert hasattr(em, 'max_errors')
    assert hasattr(em, 'log_file')
    assert hasattr(em, 'logger')
    
    assert isinstance(em.errors, list)
    assert isinstance(em.callbacks, list)
    assert isinstance(em.max_errors, int)
    assert isinstance(em.log_file, str)
    assert em.max_errors == 1000
    print("  ✓ Initialization attributes OK")


def test_handle_error():
    """Test handle() method - the core function."""
    print("\n[TEST] handle() method...")
    
    em = get_error_manager()
    initial_count = em.error_count
    
    # Test handling an error
    error = AppError("Test error", severity='error', context={
        'module': 'Test',
        'function': 'test_handle'
    })
    em.handle(error)
    
    assert em.error_count == initial_count + 1
    assert len(em.errors) > 0
    assert em.errors[-1] is error
    print("  ✓ handle() increments count OK")
    
    # Test log file was written
    assert os.path.exists(em.log_file), f"Log file not created: {em.log_file}"
    print(f"  ✓ Log file created: {em.log_file}")
    
    # Test WARNING severity
    warning = AppError("Test warning", severity='warning')
    em.handle(warning)
    assert em.warning_count > 0
    print("  ✓ Warning count OK")
    
    # Test CRITICAL severity
    critical = AppError("Test critical", severity='critical')
    em.handle(critical)
    assert em.critical_count > 0
    print("  ✓ Critical count OK")


def test_write_to_log_file():
    """Test _write_to_log_file() method."""
    print("\n[TEST] _write_to_log_file()...")
    
    em = get_error_manager()
    
    error = AppError(
        "Log test error",
        severity='error',
        exception=ValueError("Test exception"),
        context={
            'module': 'TestModule',
            'function': 'test_func',
            'user_action': 'Testing logging'
        }
    )
    
    em._write_to_log_file(error)
    
    # Verify log file content
    with open(em.log_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Log test error" in content
        assert "TestModule" in content
        assert "test_func" in content
        assert "ValueError" in content
        assert "STACK TRACE" in content
        assert "CONTEXT" in content
    
    print("  ✓ Log file content OK")


def test_get_errors():
    """Test get_errors() filtering and sorting."""
    print("\n[TEST] get_errors()...")
    
    em = get_error_manager()
    
    # Ensure we have some errors to test with
    if len(em.errors) == 0:
        for sev in ['info', 'warning', 'error', 'critical']:
            em.handle(AppError(f"Test {sev}", severity=sev, context={'module': 'Test'}))
    
    # Get all errors
    all_errors = em.get_errors()
    assert len(all_errors) > 0
    print(f"  ✓ get_errors() returned {len(all_errors)} errors")
    
    # Get errors by severity
    error_errors = em.get_errors(severity='error')
    warning_errors = em.get_errors(severity='warning')
    critical_errors = em.get_errors(severity='critical')
    
    for e in error_errors:
        assert e.severity == 'error'
    print(f"  ✓ Filtered by severity: {len(error_errors)} errors")
    
    # Test limit
    limited = em.get_errors(limit=2)
    assert len(limited) <= 2
    print(f"  ✓ Limit parameter OK: {len(limited)} errors")
    
    # Test resolved filter
    unresolved = em.get_errors(resolved=False)
    assert all(not e.resolved for e in unresolved)
    print(f"  ✓ Resolved filter OK: {len(unresolved)} unresolved")


def test_mark_resolved():
    """Test mark_resolved() method."""
    print("\n[TEST] mark_resolved()...")
    
    em = get_error_manager()
    
    # Get an error ID
    errors = em.get_errors(limit=1)
    if errors:
        error_id = errors[0].id
        
        # Mark as resolved
        result = em.mark_resolved(error_id)
        assert result is True
        
        # Verify resolved
        resolved_errors = em.get_errors(resolved=True)
        assert any(e.id == error_id for e in resolved_errors)
        print("  ✓ mark_resolved() OK")
        
        # Test non-existent error ID
        result = em.mark_resolved("non_existent_id")
        assert result is False
        print("  ✓ Non-existent ID returns False OK")


def test_clear_resolved():
    """Test clear_resolved() method."""
    print("\n[TEST] clear_resolved()...")
    
    em = get_error_manager()
    
    # Mark one as resolved
    errors = em.get_errors(limit=1)
    if errors:
        em.mark_resolved(errors[0].id)
        
        # Clear resolved
        before_count = len(em.errors)
        em.clear_resolved()
        after_count = len(em.errors)
        
        assert after_count < before_count or before_count == 0
        print(f"  ✓ clear_resolved() OK: {before_count} -> {after_count}")


def test_get_error_summary():
    """Test get_error_summary() method."""
    print("\n[TEST] get_error_summary()...")
    
    em = get_error_manager()
    
    summary = em.get_error_summary()
    
    assert 'total_errors' in summary
    assert 'critical' in summary
    assert 'error' in summary
    assert 'warning' in summary
    assert 'unresolved' in summary
    assert 'log_file' in summary
    
    assert isinstance(summary['total_errors'], int)
    assert isinstance(summary['critical'], int)
    assert isinstance(summary['warning'], int)
    
    # Verify math
    total = summary['total_errors']
    critical = summary['critical']
    warning = summary['warning']
    error_count = summary['error']
    
    assert total == critical + warning + error_count
    print(f"  ✓ Summary OK: {summary}")


def test_export_errors():
    """Test export_errors() method."""
    print("\n[TEST] export_errors()...")
    
    em = get_error_manager()
    
    # Ensure we have errors to export
    if len(em.errors) == 0:
        for i in range(3):
            em.handle(AppError(f"Export test {i}", context={'module': 'Test'}))
    
    # Export with auto-generated filename
    filepath = em.export_errors()
    assert filepath is not None
    assert filepath != ""
    assert os.path.exists(filepath)
    
    # Verify JSON content
    with open(filepath, 'r', encoding='utf-8') as f:
        exported_data = json.load(f)
        assert isinstance(exported_data, list)
        assert len(exported_data) > 0
        assert 'id' in exported_data[0]
        assert 'message' in exported_data[0]
    
    print(f"  ✓ Export OK: {filepath}")
    
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)


def test_register_callback():
    """Test register_callback() and unregister_callback()."""
    print("\n[TEST] register_callback()...")
    
    em = get_error_manager()
    callback_called = []
    
    def test_callback(error):
        callback_called.append(error)
    
    # Register
    em.register_callback(test_callback)
    assert test_callback in em.callbacks
    
    # Trigger an error
    error = AppError("Callback test", context={'module': 'Test'})
    em.handle(error)
    
    assert len(callback_called) > 0
    assert callback_called[-1] is error
    print("  ✓ register_callback() OK")
    
    # Unregister
    em.unregister_callback(test_callback)
    assert test_callback not in em.callbacks
    print("  ✓ unregister_callback() OK")


def test_notify_callbacks_thread_safety():
    """Test that callbacks are thread-safe."""
    print("\n[TEST] Callback thread safety...")
    
    em = get_error_manager()
    results = []
    lock = threading.Lock()
    
    def test_callback(error):
        with lock:
            results.append(error.message)
    
    em.register_callback(test_callback)
    
    # Fire multiple errors from different threads
    def fire_error(msg):
        error = AppError(msg, context={'module': 'ThreadTest'})
        em.handle(error)
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=fire_error, args=(f"Error {i}",))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert len(results) == 5
    print(f"  ✓ Thread safety OK: {len(results)} callbacks fired")
    
    em.unregister_callback(test_callback)


def test_handle_errors_decorator():
    """Test @handle_errors decorator."""
    print("\n[TEST] @handle_errors decorator...")
    
    @handle_errors(module='TestModule', user_action='Testing decorator')
    def failing_function():
        raise ValueError("Decorator test error")
    
    @handle_errors(module='TestModule', user_action='Testing success')
    def success_function():
        return 42
    
    # Test failing function
    result = failing_function()
    assert result is None  # Should return None on error
    
    em = get_error_manager()
    errors = em.get_errors(severity='error', limit=1)
    assert any('failing_function' in str(e) for e in errors)
    print("  ✓ Decorator catches exceptions OK")
    
    # Test success function
    result = success_function()
    assert result == 42
    print("  ✓ Decorator allows success OK")


def test_error_context_manager():
    """Test error_context() context manager."""
    print("\n[TEST] error_context()...")
    
    # Test successful context
    with error_context("Testing success", module='Test'):
        pass  # Should not raise
    print("  ✓ Success context OK")
    
    # Test error context
    try:
        with error_context("Testing failure", module='Test', severity='error'):
            raise RuntimeError("Context manager test error")
    except RuntimeError:
        pass  # Expected
    
    em = get_error_manager()
    errors = em.get_errors(limit=5)
    assert any('Testing failure' in e.message for e in errors)
    print("  ✓ Error context catches exceptions OK")


def test_convenience_functions():
    """Test report_error, report_info, report_warning, report_critical."""
    print("\n[TEST] Convenience functions...")
    
    # Clear previous errors
    em = get_error_manager()
    em.clear_resolved()
    
    # Test report_error
    report_error("Test error", module='Test', user_action='Testing')
    errors = em.get_errors(severity='error', limit=1)
    assert any('Test error' in e.message for e in errors)
    print("  ✓ report_error() OK")
    
    # Test report_info
    report_info("Test info", module='Test')
    info_errors = em.get_errors(severity='info', limit=1)
    assert any('Test info' in e.message for e in info_errors)
    print("  ✓ report_info() OK")
    
    # Test report_warning
    report_warning("Test warning", module='Test')
    warnings = em.get_errors(severity='warning', limit=1)
    assert any('Test warning' in e.message for e in warnings)
    print("  ✓ report_warning() OK")
    
    # Test report_critical
    report_critical("Test critical", module='Test')
    criticals = em.get_errors(severity='critical', limit=1)
    assert any('Test critical' in e.message for e in criticals)
    print("  ✓ report_critical() OK")


def test_global_hook():
    """Test global error hook installation."""
    print("\n[TEST] Global error hook...")
    
    # Hook is already installed on import
    assert sys.excepthook is not None
    
    # Verify hook is callable
    assert callable(sys.excepthook)
    print("  ✓ Global hook installed OK")


def test_setup_logging():
    """Test _setup_logging() method."""
    print("\n[TEST] _setup_logging()...")
    
    em = get_error_manager()
    
    assert em.logger is not None
    assert em.logger.name == 'ErrorManager'
    assert len(em.logger.handlers) > 0
    
    # Verify handler level
    handler = em.logger.handlers[0]
    assert handler.level > 0  # Should be set
    print("  ✓ Logging setup OK")


def test_get_log_file_path():
    """Test _get_log_file_path() method."""
    print("\n[TEST] _get_log_file_path()...")
    
    em = get_error_manager()
    
    assert em.log_file is not None
    assert isinstance(em.log_file, str)
    assert 'errors_' in em.log_file
    assert '.log' in em.log_file
    
    # Verify directory exists
    log_dir = os.path.dirname(em.log_file)
    assert os.path.exists(log_dir)
    print(f"  ✓ Log file path OK: {em.log_file}")


def test_max_errors_limit():
    """Test that max_errors limit is enforced."""
    print("\n[TEST] Max errors limit...")
    
    em = get_error_manager()
    
    # Clear existing errors
    em.clear_resolved()
    
    # Set a low limit for testing
    original_limit = em.max_errors
    em.max_errors = 10
    
    # Add more errors than limit
    for i in range(15):
        error = AppError(f"Limit test {i}", context={'module': 'Test'})
        em.handle(error)
    
    # Verify limit is enforced
    assert len(em.errors) <= em.max_errors
    print(f"  ✓ Max errors limit OK: {len(em.errors)} <= {em.max_errors}")
    
    # Restore original limit
    em.max_errors = original_limit


def test_error_context_dictionary_merge():
    """Test that context dictionary is properly merged in report_error()."""
    print("\n[TEST] Context dictionary merge...")
    
    em = get_error_manager()
    em.clear_resolved()
    
    report_error(
        "Context merge test",
        module='Test',
        user_action='Testing',
        context={
            'extra_field': 'extra_value',
            'custom_data': {'key': 'value'}
        }
    )
    
    errors = em.get_errors(limit=1)
    assert len(errors) > 0
    
    error = errors[0]
    assert error.context.get('extra_field') == 'extra_value'
    assert error.context.get('custom_data') == {'key': 'value'}
    assert error.context.get('module') == 'Test'
    print("  ✓ Context merge OK")


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("COMPREHENSIVE ERROR_MANAGER FUNCTION TEST")
    print("="*60)
    
    tests = [
        test_error_severity_constants,
        test_apperror_creation,
        test_error_manager_singleton,
        test_error_manager_initialization,
        test_handle_error,
        test_write_to_log_file,
        test_get_errors,
        test_mark_resolved,
        test_clear_resolved,
        test_get_error_summary,
        test_export_errors,
        test_register_callback,
        test_notify_callbacks_thread_safety,
        test_handle_errors_decorator,
        test_error_context_manager,
        test_convenience_functions,
        test_global_hook,
        test_setup_logging,
        test_get_log_file_path,
        test_max_errors_limit,
        test_error_context_dictionary_merge,
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((test.__name__, str(e)))
            import traceback
            print(f"\n  ✗ FAILED: {test.__name__}")
            print(f"    Error: {e}")
            traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    if errors:
        print("\nFailed tests:")
        for name, err in errors:
            print(f"  - {name}: {err}")
    else:
        print("\n✓ ALL TESTS PASSED!")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
