"""
Mintaka Sphere - Development Logging & Reporting System
========================================================
Comprehensive logging and issue tracking for development.

Features:
- Centralized logging with levels
- Issue tracking and reporting
- Development status dashboard
- Error aggregation
- Performance monitoring

Usage:
    from dev_logging import log, report_issue, get_status_report
    
    log("Starting feature", level="info")
    report_issue("Feature X failed", severity="high")
    print(get_status_report())
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Get data directory
try:
    from utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    def get_data_dir():
        return os.path.join(os.path.dirname(__file__), 'data')

# Log levels
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# Issue severities
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]


class DevLogger:
    """Development logger with issue tracking"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Setup logging
        log_dir = os.path.join(get_data_dir(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f'dev_{datetime.now().strftime("%Y%m%d")}.log')
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('MintakaSphere.Dev')
        self.logger.setLevel(logging.DEBUG)
        
        # Issue tracking
        self.issues: List[Dict[str, Any]] = []
        self.issue_counts = defaultdict(int)
        
        # Performance tracking
        self.timings: Dict[str, List[float]] = defaultdict(list)
        
        # Status
        self.status = {
            "start_time": datetime.now().isoformat(),
            "total_logs": 0,
            "total_issues": 0,
            "critical_issues": 0
        }
        
        self.logger.info("=" * 60)
        self.logger.info("Mintaka Sphere Development Logger Initialized")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info("=" * 60)
    
    def log(self, message: str, level: str = "info", module: str = "app"):
        """
        Log a message
        
        Args:
            message: Log message
            level: Log level (debug, info, warning, error, critical)
            module: Module name
        """
        log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
        full_message = f"[{module}] {message}"
        self.logger.log(log_level, full_message)
        self.status["total_logs"] += 1
    
    def debug(self, message: str, module: str = "app"):
        """Debug level log"""
        self.log(message, "debug", module)
    
    def info(self, message: str, module: str = "app"):
        """Info level log"""
        self.log(message, "info", module)
    
    def warning(self, message: str, module: str = "app"):
        """Warning level log"""
        self.log(message, "warning", module)
    
    def error(self, message: str, module: str = "app", exc_info: bool = False):
        """Error level log"""
        self.log(message, "error", module)
        if exc_info:
            self.logger.exception("Exception details:")
    
    def critical(self, message: str, module: str = "app", exc_info: bool = False):
        """Critical level log"""
        self.log(message, "critical", module)
        self.status["critical_issues"] += 1
        if exc_info:
            self.logger.exception("Exception details:")
    
    def report_issue(
        self,
        title: str,
        description: str,
        severity: str = "medium",
        module: str = "app",
        metadata: Optional[Dict] = None
    ):
        """
        Report a development issue
        
        Args:
            title: Issue title
            description: Issue description
            severity: Issue severity (low, medium, high, critical)
            module: Module where issue occurred
            metadata: Additional metadata
        """
        issue = {
            "id": len(self.issues) + 1,
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "description": description,
            "severity": severity,
            "module": module,
            "status": "open",
            "metadata": metadata or {}
        }
        
        self.issues.append(issue)
        self.issue_counts[severity] += 1
        self.status["total_issues"] += 1
        
        self.logger.warning(f"ISSUE #{issue['id']}: {title} [{severity}]")
        
        if severity == "critical":
            self.status["critical_issues"] += 1
    
    def start_timing(self, operation: str):
        """Start timing an operation"""
        self.timings[operation] = self.timings.get(operation, [])
        self.timings[operation].append(datetime.now().timestamp())
    
    def end_timing(self, operation: str) -> Optional[float]:
        """End timing and return duration in seconds"""
        if operation in self.timings and self.timings[operation]:
            start = self.timings[operation].pop()
            duration = datetime.now().timestamp() - start
            self.info(f"Operation '{operation}' took {duration:.3f}s", "performance")
            return duration
        return None
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get current development status report"""
        return {
            "status": self.status,
            "issues_by_severity": dict(self.issue_counts),
            "recent_issues": self.issues[-10:],  # Last 10 issues
            "total_issues": len(self.issues),
            "open_issues": len([i for i in self.issues if i["status"] == "open"]),
            "log_count": self.status["total_logs"]
        }
    
    def save_report(self, filename: str = None):
        """Save status report to file"""
        if filename is None:
            filename = os.path.join(
                get_data_dir(),
                'reports',
                f'dev_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        report = self.get_status_report()
        report["generated_at"] = datetime.now().isoformat()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.info(f"Development report saved: {filename}")
        return filename
    
    def resolve_issue(self, issue_id: int, resolution: str = "fixed"):
        """Mark an issue as resolved"""
        for issue in self.issues:
            if issue["id"] == issue_id:
                issue["status"] = "resolved"
                issue["resolved_at"] = datetime.now().isoformat()
                issue["resolution"] = resolution
                self.info(f"Issue #{issue_id} resolved: {resolution}")
                return True
        return False
    
    def get_issues(self, severity: str = None, status: str = None) -> List[Dict]:
        """Get filtered list of issues"""
        filtered = self.issues
        
        if severity:
            filtered = [i for i in filtered if i["severity"] == severity]
        
        if status:
            filtered = [i for i in filtered if i["status"] == status]
        
        return filtered


# Global instance
_dev_logger: Optional[DevLogger] = None


def get_dev_logger() -> DevLogger:
    """Get or create dev logger instance"""
    global _dev_logger
    if _dev_logger is None:
        _dev_logger = DevLogger()
    return _dev_logger


# Convenience functions
def log(message: str, level: str = "info", module: str = "app"):
    """Log a message"""
    get_dev_logger().log(message, level, module)


def debug(message: str, module: str = "app"):
    """Debug log"""
    get_dev_logger().debug(message, module)


def info(message: str, module: str = "app"):
    """Info log"""
    get_dev_logger().info(message, module)


def warning(message: str, module: str = "app"):
    """Warning log"""
    get_dev_logger().warning(message, module)


def error(message: str, module: str = "app", exc_info: bool = False):
    """Error log"""
    get_dev_logger().error(message, module, exc_info)


def critical(message: str, module: str = "app", exc_info: bool = False):
    """Critical log"""
    get_dev_logger().critical(message, module, exc_info)


def report_issue(title: str, description: str, severity: str = "medium", module: str = "app"):
    """Report an issue"""
    get_dev_logger().report_issue(title, description, severity, module)


def get_status() -> Dict[str, Any]:
    """Get current status report"""
    return get_dev_logger().get_status_report()


def save_report(filename: str = None) -> str:
    """Save status report"""
    return get_dev_logger().save_report(filename)


def start_timing(operation: str):
    """Start timing"""
    get_dev_logger().start_timing(operation)


def end_timing(operation: str) -> Optional[float]:
    """End timing"""
    return get_dev_logger().end_timing(operation)


# Initialize on module import
try:
    get_dev_logger()
except Exception as e:
    print(f"Warning: Dev logger initialization failed: {e}")


__all__ = [
    "DevLogger",
    "get_dev_logger",
    "log",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "report_issue",
    "get_status",
    "save_report",
    "start_timing",
    "end_timing"
]
