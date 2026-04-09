"""
Base Database Infrastructure
=============================
Provides base classes and utilities for ALL industry databases.
NO industry-specific logic here - just common foundations.

Every industry database EXTENDS these classes.
"""

import sqlite3
import os
import logging
import threading
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Thread-safe database connection manager.
    Handles connection pooling, retries, and error recovery.
    
    This is the ONLY connection manager in the entire system.
    All industries use this - no duplication.
    """
    
    def __init__(self, db_path: str):
        """Initialize with database file path."""
        self.db_path = db_path
        self._local = threading.local()
        
    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            self._local.connection.row_factory = sqlite3.Row
            
            # Performance optimizations (apply to ALL connections)
            optimizations = [
                "PRAGMA journal_mode = WAL",
                "PRAGMA busy_timeout = 5000",
                "PRAGMA synchronous = NORMAL",
                "PRAGMA cache_size = -64000",
                "PRAGMA foreign_keys = ON",
                "PRAGMA wal_autocheckpoint = 1000",
            ]
            for pragma in optimizations:
                self._local.connection.execute(pragma)
                
            logger.debug(f"Database connection opened: {self.db_path}")
        return self._local.connection
    
    def close_connection(self):
        """Close thread-local database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Database connection closed")
    
    @contextmanager
    def cursor(self, retries: int = 3, retry_delay: float = 0.1):
        """
        Context manager for database operations with retry logic.
        Handles locked database gracefully with exponential backoff.
        
        Usage:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM products")
                results = cur.fetchall()
        """
        import time
        
        conn = self.get_connection()
        cursor = conn.cursor()
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                yield cursor
                conn.commit()
                return  # Success
            except sqlite3.OperationalError as e:
                last_error = e
                if "locked" in str(e).lower() and attempt < retries:
                    logger.warning(f"Database locked, retry {attempt + 1}/{retries}")
                    conn.rollback()
                    time.sleep(retry_delay * (attempt + 1))
                    cursor = conn.cursor()
                else:
                    conn.rollback()
                    logger.error(f"Database operation failed: {e}")
                    raise
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
        
        if last_error:
            raise last_error


class BaseRepository:
    """
    Base class for ALL database operations.
    Provides common utilities that ALL industries need.
    
    Every industry repository EXTENDS this class.
    NO duplication of helper methods.
    """
    
    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection manager."""
        self.conn = connection
    
    @staticmethod
    def row_to_dict(row) -> dict:
        """Convert sqlite3.Row to dict. Handles None safely."""
        if row is None:
            return {}
        return dict(row)
    
    @staticmethod
    def rows_to_dicts(rows) -> List[dict]:
        """Convert list of sqlite3.Row to list of dicts."""
        return [dict(r) for r in rows]
    
    def sanitize_keys(self, keys, table: str = None, whitelist: Dict[str, set] = None):
        """
        Validate column names to prevent SQL injection.
        Uses whitelist for defense-in-depth.
        
        Args:
            keys: Column names to validate
            table: Table name for whitelist lookup
            whitelist: Dict of {table_name: set(allowed_columns)}
        """
        for k in keys:
            if not str(k).isidentifier():
                raise ValueError(f"Invalid column name: {k}")
            
            if whitelist and table and table in whitelist:
                if k not in whitelist[table]:
                    raise ValueError(f"Unknown column '{k}' for table '{table}'")
