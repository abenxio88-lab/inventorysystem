"""
Centralized Error Manager
==========================
Complete error handling system with:
- Real-time UI notifications
- File logging with details
- Developer dashboard integration
- Auto-recovery suggestions
- Color-coded severity levels

NO MORE SILENT ERRORS!
"""

import os
import sys
import json
import logging
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager


# ============================================================================
# ERROR SEVERITY LEVELS
# ============================================================================

class ErrorSeverity:
    """Error severity levels with color codes."""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'
    
    COLORS = {
        'info': '#2196F3',      # Blue
        'warning': '#FF9800',   # Orange
        'error': '#F44336',     # Red
        'critical': '#9C27B0'   # Purple
    }
    
    ICONS = {
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❌',
        'critical': '🔥'
    }


# ============================================================================
# ERROR DATA CLASS
# ============================================================================

class AppError:
    """Represents an application error with full context."""
    
    def __init__(self, message: str, severity: str = 'error',
                 exception: Optional[Exception] = None,
                 context: Optional[Dict] = None):
        self.id = datetime.now().strftime('%Y%m%d%H%M%S%f')
        self.timestamp = datetime.now()
        self.message = message
        self.severity = severity
        self.exception = exception
        self.context = context if context is not None else {}
        self.traceback = traceback.format_exc() if exception else None
        self.module = self.context.get('module', 'Unknown')
        self.function = self.context.get('function', 'Unknown')
        self.user_action = self.context.get('user_action', 'Unknown')
        self.resolved = False
        self.resolved_at = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'severity': self.severity,
            'module': self.module,
            'function': self.function,
            'user_action': self.user_action,
            'exception_type': type(self.exception).__name__ if self.exception else None,
            'exception_message': str(self.exception) if self.exception else None,
            'traceback': self.traceback,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.timestamp.strftime('%H:%M:%S')} {self.module}.{self.function}: {self.message}"


# ============================================================================
# ERROR MANAGER CLASS
# ============================================================================

class ErrorManager:
    """
    Centralized error management system.
    Catches, logs, displays, and tracks all errors.
    """

    _instance: Optional['ErrorManager'] = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()

    def __new__(cls) -> 'ErrorManager':
        """Singleton pattern - only one error manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self):
        with self._init_lock:
            if self._initialized:
                return

            self._initialized = True
            self.errors: List[AppError] = []
            self.callbacks: List[Callable[[AppError], None]] = []
            self.error_count = 0
            self.critical_count = 0
            self.warning_count = 0

            # Setup logging
            self._setup_logging()

            # Max errors to keep in memory
            self.max_errors = 1000

            # Error log file
            self.log_file = self._get_log_file_path()

            logging.info(f"Error Manager initialized - Log file: {self.log_file}")
    
    def _setup_logging(self):
        """Setup dedicated error logging."""
        self.logger = logging.getLogger('ErrorManager')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '🔴 %(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def _get_log_file_path(self) -> str:
        """Get error log file path."""
        try:
            from utils import get_data_dir
            data_dir = get_data_dir()
        except (ImportError, ModuleNotFoundError):
            try:
                from .utils import get_data_dir
                data_dir = get_data_dir()
            except (ImportError, ModuleNotFoundError):
                data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        os.makedirs(data_dir, exist_ok=True)
        
        log_file = os.path.join(data_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log')
        return log_file
    
    def _write_to_log_file(self, error: AppError):
        """Write error to log file with full details."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n" + "="*80 + "\n")
                f.write(f"ERROR ID: {error.id}\n")
                f.write(f"Timestamp: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')}\n")
                f.write(f"Severity: {error.severity.upper()}\n")
                f.write(f"Module: {error.module}\n")
                f.write(f"Function: {error.function}\n")
                f.write(f"User Action: {error.user_action}\n")
                f.write(f"Message: {error.message}\n")
                
                if error.exception:
                    f.write(f"Exception Type: {type(error.exception).__name__}\n")
                    f.write(f"Exception Message: {str(error.exception)}\n")
                
                if error.traceback:
                    f.write("\n--- STACK TRACE ---\n")
                    f.write(error.traceback)
                    f.write("\n--- END TRACE ---\n")
                
                if error.context:
                    f.write("\n--- CONTEXT ---\n")
                    for key, value in error.context.items():
                        f.write(f"{key}: {value}\n")
                
                f.write("="*80 + "\n")

        except Exception as e:
            logging.error(f"Failed to write error to log file: {e}")
    
    def handle(self, error: AppError):
        """
        Handle an error - log, display, and notify.

        This is the MAIN method to report errors.
        """
        with self._lock:
            # Add to error list
            self.errors.append(error)
            self.error_count += 1

            if error.severity == ErrorSeverity.CRITICAL:
                self.critical_count += 1
            elif error.severity == ErrorSeverity.WARNING:
                self.warning_count += 1

            # Keep only recent errors
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[-self.max_errors:]
        
        # Write to log file
        self._write_to_log_file(error)
        
        # Log to console
        log_message = f"{ErrorSeverity.ICONS.get(error.severity, '❌')} [{error.severity.upper()}] {error.message}"
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        # Notify callbacks (for dashboard widget)
        self._notify_callbacks(error)

    def _notify_callbacks(self, error: AppError):
        """Notify all registered callbacks."""
        with self._lock:
            callbacks_copy = self.callbacks[:]

        for callback in callbacks_copy:
            try:
                callback(error)
            except Exception as e:
                logging.error(f"Error callback failed: {e}")

    def register_callback(self, callback: Callable[[AppError], None]):
        """Register a callback to be notified of errors."""
        with self._lock:
            self.callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[AppError], None]):
        """Unregister a callback."""
        with self._lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
    
    def get_errors(self, severity: Optional[str] = None,
                   resolved: Optional[bool] = None,
                   limit: int = 50) -> List[AppError]:
        """Get errors with optional filtering."""
        with self._lock:
            filtered = self.errors[:]

        if severity:
            filtered = [e for e in filtered if e.severity == severity]

        if resolved is not None:
            filtered = [e for e in filtered if e.resolved == resolved]

        # Sort by timestamp (newest first)
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        return filtered[:limit]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self._lock:
            unresolved = sum(1 for e in self.errors if not e.resolved)
            total = self.error_count
            critical = self.critical_count
            warning = self.warning_count

        return {
            'total_errors': total,
            'critical': critical,
            'error': total - warning - critical,
            'warning': warning,
            'unresolved': unresolved,
            'log_file': self.log_file
        }
    
    def mark_resolved(self, error_id: str):
        """Mark an error as resolved."""
        with self._lock:
            for error in self.errors:
                if error.id == error_id:
                    error.resolved = True
                    error.resolved_at = datetime.now()
                    logging.info(f"Error {error_id} marked as resolved")
                    return True
        return False

    def clear_resolved(self):
        """Clear all resolved errors from memory."""
        with self._lock:
            self.errors = [e for e in self.errors if not e.resolved]
        logging.info("Cleared resolved errors")

    def export_errors(self, filepath: Optional[str] = None) -> str:
        """Export errors to JSON file."""
        if filepath is None:
            filepath = os.path.join(
                os.path.dirname(self.log_file),
                f'errors_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )

        with self._lock:
            errors_copy = self.errors[:]

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([e.to_dict() for e in errors_copy], f, indent=2)

            logging.info(f"Exported {len(self.errors)} errors to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to export errors: {e}")
            return ""


# ============================================================================
# DECORATOR FOR AUTO ERROR HANDLING
# ============================================================================

def handle_errors(severity: str = 'error', module: str = 'Unknown',
                  user_action: str = 'Unknown'):
    """
    Decorator to automatically handle errors in functions.
    
    Usage:
        @handle_errors(module='Inventory', user_action='Adding product')
        def add_product(self, data):
            # Your code here
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = AppError(
                    message=f"{func.__name__}: {str(e)}",
                    severity=severity,
                    exception=e,
                    context={
                        'module': module,
                        'function': func.__name__,
                        'user_action': user_action,
                        'args': str(args)[:200],
                        'kwargs': str(kwargs)[:200]
                    }
                )
                get_error_manager().handle(error)
                return None
        return wrapper
    return decorator


# ============================================================================
# CONTEXT MANAGER FOR ERROR HANDLING
# ============================================================================

@contextmanager
def error_context(message: str, severity: str = 'error',
                  module: str = 'Unknown', user_action: str = 'Unknown'):
    """
    Context manager for error handling.
    
    Usage:
        with error_context("Loading data", module='Dashboard'):
            # Your code here
    """
    try:
        yield
    except Exception as e:
        error = AppError(
            message=f"{message}: {str(e)}",
            severity=severity,
            exception=e,
            context={
                'module': module,
                'user_action': user_action
            }
        )
        get_error_manager().handle(error)
        raise


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_error_manager() -> ErrorManager:
    """Get the singleton error manager instance."""
    return ErrorManager()


def report_error(message: str, severity: str = 'error',
                 exception: Optional[Exception] = None,
                 module: str = 'Unknown', user_action: str = 'Unknown',
                 context: Optional[Dict] = None):
    """Quick way to report an error."""
    error = AppError(
        message=message,
        severity=severity,
        exception=exception,
        context={
            'module': module,
            'user_action': user_action,
            **(context or {})
        }
    )
    get_error_manager().handle(error)


def report_info(message: str, module: str = 'Unknown'):
    """Report an info message."""
    report_error(message, severity='info', module=module)


def report_warning(message: str, module: str = 'Unknown'):
    """Report a warning."""
    report_error(message, severity='warning', module=module)


def report_critical(message: str, exception: Optional[Exception] = None,
                    module: str = 'Unknown'):
    """Report a critical error."""
    report_error(message, severity='critical', exception=exception, module=module)


# ============================================================================
# GLOBAL ERROR HOOK
# ============================================================================

def install_global_hook():
    """Install global exception hook to catch unhandled errors."""
    original_hook = sys.excepthook
    
    def global_hook(exc_type, exc_value, exc_traceback):
        # Don't handle KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            original_hook(exc_type, exc_value, exc_traceback)
            return

        error = AppError(
            message=f"Unhandled exception: {str(exc_value)}",
            severity='critical',
            exception=exc_value,
            context={
                'module': 'Global',
                'user_action': 'Unhandled exception'
            }
        )

        # Format traceback
        error.traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        get_error_manager().handle(error)
        
        # Call original hook
        original_hook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = global_hook
    logging.info("Global error hook installed")


# ============================================================================
# INITIALIZATION
# ============================================================================

# Auto-install global hook when module is imported
install_global_hook()


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Error Manager - Test/Demo")
    print("="*60)
    
    # Get error manager
    em = get_error_manager()
    
    # Test info
    print("\n[INFO] Testing INFO...")
    report_info("This is an info message", module='Test')
    
    # Test warning
    print("\n[WARN] Testing WARNING...")
    report_warning("This is a warning", module='Test')
    
    # Test error
    print("\n[ERROR] Testing ERROR...")
    try:
        1 / 0
    except Exception as e:
        report_error("Division by zero test", exception=e, module='Test')
    
    # Test critical
    print("\n🔥 Testing CRITICAL...")
    try:
        raise ValueError("Critical test error")
    except Exception as e:
        report_critical("System critical failure", exception=e, module='Test')
    
    # Show summary
    print("\n📊 Error Summary:")
    summary = em.get_error_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Export errors
    print("\n💾 Exporting errors...")
    em.export_errors()
    
    print("\n" + "="*60)
    print("Test complete! Check the log file for details.")
    print("="*60)
