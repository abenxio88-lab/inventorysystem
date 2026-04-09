"""
Core Database Module
====================
Handles SHARED functionality that ALL industries use:
- User authentication
- Audit logging
- System settings
- Database initialization/migration

This module is INDEPENDENT of any industry.
Every industry uses the same users, auth, and settings.
"""

import hashlib
import secrets
import logging
from typing import Optional, List, Dict
from datetime import datetime

from .base import DatabaseConnection, BaseRepository

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    User management and authentication.
    Shared across ALL industries - no duplication.
    """
    
    def create_user(self, username: str, password: str, role: str = "staff",
                   email: str = None, full_name: str = None, 
                   created_by: int = None) -> int:
        """
        Create a new user with secure password hashing.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role (admin, staff, etc.)
            email: User's email address
            full_name: User's full name
            created_by: ID of user who created this account
            
        Returns:
            int: The new user's ID
            
        Raises:
            ValueError: If user already exists
        """
        # Hash the password
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100_000
        ).hex()
        
        with self.conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cur.fetchone():
                raise ValueError(f"User '{username}' already exists")
            
            # Insert new user
            cur.execute("""
                INSERT INTO users (username, password_hash, password_salt, password_algo,
                                 role, email, full_name, is_active, status, created_by)
                VALUES (?, ?, ?, 'pbkdf2', ?, ?, ?, 1, 'ACTIVE', ?)
            """, (username, password_hash, salt, role, email, full_name, created_by))
            
            user_id = cur.lastrowid
            logger.info(f"User '{username}' created with ID {user_id}, role: {role}")
            return user_id
    
    def verify_user(self, username: str, password: str) -> tuple:
        """
        Verify user credentials.
        
        Returns:
            tuple: (success: bool, role: str|None, user_id: int|None)
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, password_hash, password_salt, password_algo,
                       role, is_active, status
                FROM users
                WHERE username = ?
            """, (username,))
            
            user = cur.fetchone()
            if not user:
                logger.warning(f"Login attempt for non-existent user: {username}")
                return False, None, None
            
            # Check if user is active
            if not user['is_active'] or user['status'] != 'ACTIVE':
                logger.warning(f"Login attempt for inactive user: {username}")
                return False, None, None
            
            # Verify password
            stored_hash = user['password_hash']
            salt = user['password_salt']
            
            try:
                computed_hash = hashlib.pbkdf2_hmac(
                    'sha256',
                    password.encode('utf-8'),
                    salt.encode('utf-8'),
                    100_000
                ).hex()
                
                if computed_hash != stored_hash:
                    logger.warning(f"Invalid password for user: {username}")
                    return False, None, None
                
                # Update last login timestamp
                cur.execute("""
                    UPDATE users
                    SET last_login = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), user['id']))
                
                logger.info(f"User '{username}' authenticated successfully")
                return True, user['role'], user['id']
                
            except Exception as e:
                logger.error(f"Password verification failed: {e}")
                return False, None, None
    
    def fetch_user(self, username: str) -> Optional[dict]:
        """Fetch user by username."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE username = ? AND is_active = 1", 
                (username,)
            )
            row = cur.fetchone()
            return self.row_to_dict(row) if row else None
    
    def list_users(self, active_only: bool = True) -> List[dict]:
        """List all users."""
        query = """
            SELECT id, username, role, email, full_name, is_active, 
                   status, last_login, created_at 
            FROM users
        """
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY username"
        
        with self.conn.cursor() as cur:
            cur.execute(query)
            return self.rows_to_dicts(cur.fetchall())
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user fields."""
        allowed_fields = {
            'role', 'email', 'full_name', 'is_active', 'status',
            'password_hash', 'password_salt'
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            raise ValueError(f"No valid fields to update. Allowed: {allowed_fields}")
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [user_id]
        
        with self.conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            logger.info(f"User {user_id} updated: {list(updates.keys())}")
            return cur.rowcount > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Soft-delete a user."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET is_active = 0, status = 'INACTIVE' WHERE id = ?", 
                (user_id,)
            )
            logger.info(f"User {user_id} soft-deleted")
            return cur.rowcount > 0
    
    def ensure_default_admin(self) -> bool:
        """Create default admin user if it doesn't exist."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = 'admin'")
            if cur.fetchone():
                return False  # Admin already exists
        
        try:
            self.create_user(
                "admin", 
                "admin123", 
                role="admin", 
                full_name="System Administrator"
            )
            logger.info("Default admin user created")
            return True
        except ValueError:
            logger.info("Admin user already exists (race condition)")
            return False


class AuditRepository(BaseRepository):
    """
    Audit logging system.
    Shared across ALL industries - tracks all database changes.
    """
    
    def log_event(self, username: str, action: str, table_name: str = "",
                  record_id: int = None, details: str = "") -> None:
        """
        Log an audit event.
        
        Args:
            username: User who performed the action
            action: Type of action (create, update, delete, etc.)
            table_name: Table affected
            record_id: Record ID affected
            details: Additional details
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO audit_log 
                   (username, action, table_name, record_id, details) 
                   VALUES (?, ?, ?, ?, ?)""",
                (username, action, table_name, record_id, details)
            )
        
        # Notify UI of database changes
        self._notify_ui(table_name, action)
    
    def fetch_audit_log(self, username: str = None, 
                       start_date: str = None,
                       end_date: str = None,
                       limit: int = 100) -> List[dict]:
        """Fetch audit log entries with optional filters."""
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if username:
            query += " AND username = ?"
            params.append(username)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return self.rows_to_dicts(cur.fetchall())
    
    def _notify_ui(self, table_name: str, action: str):
        """Notify UI of database changes (optional, handles missing imports)."""
        try:
            from app_core import app_state
            app_state.notify_ui_updates(
                "db_changed", 
                {"table": table_name, "action": action}
            )
        except ImportError:
            pass


class SettingsRepository(BaseRepository):
    """
    System settings and configuration storage.
    Key-value store shared across ALL industries.
    """
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row["value"] if row else None
    
    def set_setting(self, key: str, value: str, 
                   category: str = "general", 
                   description: str = "") -> bool:
        """Set a setting value (insert or update)."""
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO settings 
                   (key, value, category, description, updated_at) 
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP) 
                   ON CONFLICT(key) DO UPDATE 
                   SET value = excluded.value, 
                       updated_at = CURRENT_TIMESTAMP""",
                (key, value, category, description)
            )
            return True
    
    def get_all_settings(self, category: str = None) -> Dict[str, str]:
        """Get all settings, optionally filtered by category."""
        query = "SELECT key, value, category FROM settings"
        params = []
        
        if category:
            query += " WHERE category = ?"
            params.append(category)
        
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return {row["key"]: row["value"] for row in rows}
    
    def get_industry_type(self) -> str:
        """Get the current active industry."""
        val = self.get_setting("industry_type")
        return val if val else "retail"  # Default to retail
    
    def set_industry_type(self, industry: str) -> bool:
        """Set the current active industry."""
        return self.set_setting(
            "industry_type", 
            industry, 
            "general", 
            "Current industry type"
        )
