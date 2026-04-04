"""
Security Module
================
Centralized security functions for the entire application.
Protects against SQL injection, XSS, path traversal, and other threats.
"""

import hashlib
import secrets
import re
import os
import logging
from typing import Optional, Any

# Try to import Argon2 for strong password hashing
try:
    from argon2 import PasswordHasher, exceptions as argon2_exceptions
    ARGON2_AVAILABLE = True
    _ph = PasswordHasher()
except ImportError:
    ARGON2_AVAILABLE = False
    logging.warning("Argon2 not available - using PBKDF2 fallback")

# Try to import bleach for HTML sanitization
try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    logging.warning("Bleach not available - XSS protection limited")


# ============================================================================
# PASSWORD SECURITY
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using Argon2 (preferred) or PBKDF2 (fallback).
    
    Args:
        password: Plain text password
    
    Returns:
        Secure password hash
    """
    if ARGON2_AVAILABLE:
        return _ph.hash(password)
    else:
        # Fallback to PBKDF2 with strong parameters
        salt = secrets.token_bytes(32)
        dk = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # Iterations
        )
        return f"pbkdf2:sha256:100000${salt.hex()}${dk.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against hash.

    Args:
        password: Plain text password
        password_hash: Stored hash

    Returns:
        True if password matches
    """
    if ARGON2_AVAILABLE and not password_hash.startswith('pbkdf2:'):
        try:
            return _ph.verify(password_hash, password)
        except Exception:
            return False
    else:
        # PBKDF2 verification - format: pbkdf2:sha256:iterations$salt$hash
        try:
            # Split off the prefix (pbkdf2:sha256:iterations)
            prefix, salt_hex, dk_hex = password_hash.split('$')
            # Parse prefix
            parts = prefix.split(':')
            algorithm = parts[1]  # sha256
            iterations = int(parts[2])  # 100000
            
            salt = bytes.fromhex(salt_hex)

            dk = hashlib.pbkdf2_hmac(
                algorithm,
                password.encode('utf-8'),
                salt,
                iterations
            )
            return secrets.compare_digest(dk.hex(), dk_hex)
        except Exception as e:
            return False


# ============================================================================
# SQL INJECTION PREVENTION
# ============================================================================

def sanitize_table_name(table_name: str) -> str:
    """
    Sanitize table name for dynamic queries.
    
    Args:
        table_name: Table name to sanitize
    
    Returns:
        Sanitized table name
    
    Raises:
        ValueError: If table name contains invalid characters
    """
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    
    return table_name


def sanitize_column_name(column_name: str) -> str:
    """
    Sanitize column name for dynamic queries.
    
    Args:
        column_name: Column name to sanitize
    
    Returns:
        Sanitized column name
    
    Raises:
        ValueError: If column name contains invalid characters
    """
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
        raise ValueError(f"Invalid column name: {column_name}")
    
    return column_name


def validate_limit(limit: Any, default: int = 100, max_limit: int = 1000) -> int:
    """
    Validate LIMIT clause to prevent SQL injection.
    
    Args:
        limit: Limit value to validate
        default: Default limit if None
        max_limit: Maximum allowed limit
    
    Returns:
        Validated limit value
    """
    if limit is None:
        return default
    
    try:
        limit_int = int(limit)
        return min(max(0, limit_int), max_limit)
    except (ValueError, TypeError):
        return default


# ============================================================================
# XSS PREVENTION
# ============================================================================

def sanitize_html(text: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text safe for HTML display
    """
    if not BLEACH_AVAILABLE:
        # Fallback: escape HTML entities
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;'))
    
    # Use bleach for proper sanitization
    return bleach.clean(text, tags=[], attributes={}, strip=True)


def sanitize_for_display(text: str) -> str:
    """
    Sanitize text for safe display in UI.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text
    """
    if text is None:
        return ''
    
    # Convert to string
    text = str(text)
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Sanitize HTML
    return sanitize_html(text)


# ============================================================================
# PATH TRAVERSAL PREVENTION
# ============================================================================

def sanitize_file_path(file_path: str, base_directory: Optional[str] = None) -> str:
    """
    Sanitize file path to prevent path traversal attacks.
    
    Args:
        file_path: File path to sanitize
        base_directory: Base directory to restrict access to
    
    Returns:
        Sanitized absolute path
    
    Raises:
        ValueError: If path attempts to escape base directory
    """
    # Normalize path
    file_path = os.path.normpath(os.path.expanduser(file_path))
    
    # If base directory specified, ensure path is within it
    if base_directory:
        base_directory = os.path.normpath(os.path.abspath(base_directory))
        file_path = os.path.abspath(file_path)
        
        # Check if path is within base directory
        if not file_path.startswith(base_directory):
            raise ValueError(f"Path traversal attempt detected: {file_path}")
    
    return file_path


def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: Filename to validate
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.png'])
    
    Returns:
        True if extension is allowed
    """
    if not filename:
        return False
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in [e.lower() for e in allowed_extensions]


# ============================================================================
# INPUT VALIDATION
# ============================================================================

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email to validate
    
    Returns:
        True if valid email format
    """
    if not email:
        return False
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid phone format
    """
    if not phone:
        return False
    
    # Remove common separators
    phone = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if remaining characters are digits (with optional +)
    return bool(re.match(r'^\+?[0-9]{7,15}$', phone))


def validate_username(username: str) -> bool:
    """
    Validate username format.
    
    Args:
        username: Username to validate
    
    Returns:
        True if valid username format
    """
    if not username:
        return False
    
    # 3-50 characters, alphanumeric and underscore only
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,49}$', username):
        return False
    
    return True


def validate_security_pin(pin: str) -> bool:
    """
    Validate security PIN format (4-8 digits).
    
    Args:
        pin: PIN to validate
    
    Returns:
        True if valid PIN format
    """
    if not pin:
        return False
    
    # 4-8 digits only
    return bool(re.match(r'^[0-9]{4,8}$', pin))


def validate_password_strength(password: str) -> tuple:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, ""


# ============================================================================
# CSRF PROTECTION
# ============================================================================

def generate_csrf_token() -> str:
    """
    Generate CSRF token for form protection.
    
    Returns:
        Random CSRF token
    """
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, stored_token: str) -> bool:
    """
    Validate CSRF token.
    
    Args:
        token: Submitted token
        stored_token: Stored token to compare against
    
    Returns:
        True if tokens match
    """
    if not token or not stored_token:
        return False
    
    return secrets.compare_digest(token, stored_token)


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """
    Simple rate limiter to prevent brute-force attacks.
    """
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        """
        Initialize rate limiter.
        
        Args:
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}  # key -> list of timestamps
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if action is allowed for given key (e.g., IP, username).
        
        Args:
            key: Identifier (IP address, username, etc.)
        
        Returns:
            True if action is allowed
        """
        import time
        current_time = time.time()
        
        # Clean old attempts
        if key in self.attempts:
            self.attempts[key] = [
                t for t in self.attempts[key]
                if current_time - t < self.window_seconds
            ]
        else:
            self.attempts[key] = []
        
        # Check if limit exceeded
        if len(self.attempts[key]) >= self.max_attempts:
            return False
        
        # Record attempt
        self.attempts[key].append(current_time)
        return True
    
    def reset(self, key: str):
        """
        Reset attempts for given key.

        Args:
            key: Identifier to reset
        """
        if key in self.attempts:
            del self.attempts[key]

    def get_remaining_attempts(self, key: str) -> int | None:
        """
        Get remaining attempts before lockout.

        Args:
            key: Identifier (username, etc.)

        Returns:
            Number of remaining attempts, or None if not tracking this key
        """
        import time
        current_time = time.time()
        if key not in self.attempts:
            return self.max_attempts
        # Clean expired attempts
        self.attempts[key] = [
            t for t in self.attempts[key]
            if current_time - t < self.window_seconds
        ]
        return max(0, self.max_attempts - len(self.attempts[key]))

    def get_wait_time(self, key: str) -> int:
        """
        Get seconds until lockout expires.

        Args:
            key: Identifier (username, etc.)

        Returns:
            Seconds to wait, or 0 if not locked out
        """
        import time
        current_time = time.time()
        if key not in self.attempts:
            return 0
        # Find oldest attempt in current window
        valid_attempts = [
            t for t in self.attempts[key]
            if current_time - t < self.window_seconds
        ]
        if not valid_attempts or len(valid_attempts) < self.max_attempts:
            return 0
        # Wait until oldest attempt expires
        oldest = min(valid_attempts)
        return max(0, int(self.window_seconds - (current_time - oldest)))


# ============================================================================
# LOGGING SECURITY EVENTS
# ============================================================================

def log_security_event(event_type: str, details: dict, user_id: Optional[str] = None):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        details: Event details
        user_id: User ID if applicable
    """
    import logging
    from datetime import datetime
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details
    }
    
    logging.warning(f"SECURITY EVENT: {log_entry}")


# ============================================================================
# SECURE RANDOM GENERATION
# ============================================================================

def generate_secure_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token.
    
    Args:
        length: Token length in bytes
    
    Returns:
        Secure random token (hex encoded)
    """
    return secrets.token_hex(length)


def generate_api_key() -> str:
    """
    Generate secure API key.
    
    Returns:
        Secure API key
    """
    return f"sk_{secrets.token_urlsafe(32)}"
