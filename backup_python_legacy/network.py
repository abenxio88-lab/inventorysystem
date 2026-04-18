"""
Network Connectivity & Offline Detection Module
================================================
Detects online/offline status and manages connection state.
Works entirely offline - no external dependencies required.
"""

import socket
import threading
import time
import logging
from datetime import datetime
from typing import Callable, Optional

# Check interval in seconds
CHECK_INTERVAL = 30

# Known reliable DNS servers (for connectivity check)
DNS_SERVERS = [
    ("8.8.8.8", 53),       # Google DNS
    ("1.1.1.1", 53),       # Cloudflare DNS
    ("9.9.9.9", 53),       # Quad9 DNS
]

# Fallback: Try to resolve a common domain
DOMAIN_CHECK = "www.google.com"


class ConnectivityMonitor:
    """
    Monitors internet connectivity status.
    Runs in background thread, updates status periodically.
    """
    
    def __init__(self):
        self._is_online = False
        self._last_check = None
        self._last_error = None
        self._running = False
        self._thread = None
        self._callbacks = []
        self._lock = threading.Lock()
    
    def start(self):
        """Start background monitoring thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        
        # Do initial check
        self.check_connection()
        
        logging.info("Connectivity monitor started")
    
    def stop(self):
        """Stop background monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logging.info("Connectivity monitor stopped")
    
    def check_connection(self, timeout=3) -> bool:
        """
        Check if internet connection is available.
        Uses multiple methods to verify connectivity.
        """
        self._last_check = datetime.now()
        
        # Method 1: Try to connect to DNS servers
        for host, port in DNS_SERVERS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    self._update_status(True, None)
                    return True
            except Exception as e:
                self._last_error = str(e)
                continue
        
        # Method 2: Try DNS resolution
        try:
            socket.gethostbyname(DOMAIN_CHECK)
            self._update_status(True, None)
            return True
        except Exception as e:
            self._last_error = str(e)
        
        # All methods failed
        self._update_status(False, self._last_error)
        return False
    
    def _update_status(self, is_online: bool, error: Optional[str]):
        """Update status and notify callbacks if changed."""
        with self._lock:
            changed = self._is_online != is_online
            self._is_online = is_online
            self._last_error = error
        
        if changed:
            status = "ONLINE" if is_online else "OFFLINE"
            logging.info(f"Connectivity status changed: {status}")
            
            # Notify all callbacks
            for callback in self._callbacks:
                try:
                    callback(is_online)
                except Exception as e:
                    logging.error(f"Callback error: {e}")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                self.check_connection()
            except Exception as e:
                logging.error(f"Connectivity check error: {e}")
            
            # Sleep in small increments to allow quick stop
            for _ in range(CHECK_INTERVAL * 10):
                if not self._running:
                    break
                time.sleep(0.1)
    
    def add_callback(self, callback: Callable[[bool], None]):
        """Add a callback to be notified on status change."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[bool], None]):
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    @property
    def is_online(self) -> bool:
        """Get current online status."""
        return self._is_online
    
    @property
    def status_text(self) -> str:
        """Get human-readable status text."""
        return "Online" if self._is_online else "Offline"
    
    @property
    def status_icon(self) -> str:
        """Get status icon emoji."""
        return "🟢" if self._is_online else "🔴"
    
    @property
    def last_check(self) -> Optional[datetime]:
        """Get time of last connectivity check."""
        return self._last_check
    
    @property
    def last_error(self) -> Optional[str]:
        """Get last error message if offline."""
        return self._last_error


# Global connectivity monitor instance
connectivity_monitor = ConnectivityMonitor()


def get_connectivity_monitor() -> ConnectivityMonitor:
    """Get the global connectivity monitor instance."""
    return connectivity_monitor


def is_online() -> bool:
    """Quick check if system is online."""
    return connectivity_monitor.is_online


def check_now() -> bool:
    """Force an immediate connectivity check."""
    return connectivity_monitor.check_connection()
