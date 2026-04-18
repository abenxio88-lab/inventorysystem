"""
License Manager Module
======================
Professional software licensing with device binding and admin approval.

Features:
- Device fingerprinting (hardware ID, MAC address, disk serial)
- License key generation and validation
- Admin hierarchy system (Owner Admin > Secondary Admin > Staff)
- Device change detection (clone detection)
- Admin authorization workflow
"""

import os
import json
import hashlib
import uuid
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import platform
import socket
import base64

try:
    from .database import get_db_cursor, get_connection
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from utils import get_data_dir


# ============================================================================
# LICENSE ENCRYPTION UTILITIES
# ============================================================================

def _get_encryption_key() -> bytes:
    """Derive encryption key from device fingerprint."""
    fingerprint = get_device_fingerprint()
    # Use SHA-256 of fingerprint as encryption key
    return hashlib.sha256(fingerprint.encode()).digest()


def _encrypt_license_data(data: dict) -> str:
    """Encrypt license data using XOR cipher with device fingerprint."""
    json_data = json.dumps(data, indent=2).encode('utf-8')
    key = _get_encryption_key()
    
    # XOR encryption (simple but effective for license files)
    encrypted = bytes([json_data[i] ^ key[i % len(key)] for i in range(len(json_data))])
    return base64.b64encode(encrypted).decode('utf-8')


def _decrypt_license_data(encrypted_data: str) -> dict:
    """Decrypt license data."""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        key = _get_encryption_key()
        
        # XOR decryption
        decrypted = bytes([encrypted_bytes[i] ^ key[i % len(key)] for i in range(len(encrypted_bytes))])
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        logging.error(f"License decryption failed: {e}")
        raise ValueError("Invalid or corrupted license file")


# ============================================================================
# DEVICE FINGERPRINTING
# ============================================================================

def get_device_fingerprint() -> str:
    """Generate device fingerprint from hardware characteristics."""
    fingerprint_parts = []
    
    try:
        mac = uuid.getnode()
        fingerprint_parts.append(str(mac))
    except Exception as e:
        logging.warning(f"Could not get MAC address: {e}")
    
    try:
        hostname = socket.gethostname()
        fingerprint_parts.append(hostname)
    except Exception as e:
        logging.warning(f"Could not get hostname: {e}")
    
    try:
        os_type = platform.system() + platform.release()
        fingerprint_parts.append(os_type)
    except Exception as e:
        logging.warning(f"Could not get OS info: {e}")
    
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(
                ['wmic', 'logicaldisk', 'get', 'volumeserialnumber', '/format:value'],
                text=True
            )
            serial = output.split('=')[-1].strip()
            if serial:
                fingerprint_parts.append(serial)
        except Exception as e:
            logging.warning(f"Could not get disk serial: {e}")
    
    try:
        processor = platform.processor()
        fingerprint_parts.append(processor)
    except Exception as e:
        logging.warning(f"Could not get processor info: {e}")
    
    fingerprint_string = "|".join(fingerprint_parts)
    device_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    return device_hash


def get_device_info() -> Dict:
    """Get detailed device information."""
    return {
        'hostname': socket.gethostname(),
        'os': platform.system(),
        'os_version': platform.release(),
        'processor': platform.processor(),
        'mac_address': format(uuid.getnode(), '012x'),
        'ip_address': socket.gethostbyname(socket.gethostname()),
        'fingerprint': get_device_fingerprint()
    }


# ============================================================================
# LICENSE MANAGER
# ============================================================================

class LicenseManager:
    """Manages software licensing and device binding."""
    
    LICENSE_FILE = os.path.join(get_data_dir(), 'license.json')
    
    @staticmethod
    def initialize_license(admin_email: str) -> str:
        """Initialize software license on first launch with encryption."""
        device_info = get_device_info()
        
        license_data = {
            'license_key': str(uuid.uuid4()),
            'admin_email': admin_email,
            'device_fingerprint': device_info['fingerprint'],
            'device_info': device_info,
            'licensed_date': datetime.now().isoformat(),
            'status': 'ACTIVE',
            'clone_detected': False,
            'last_verified_date': datetime.now().isoformat()
        }
        
        # Encrypt and save license file
        encrypted_license = _encrypt_license_data(license_data)
        with open(LicenseManager.LICENSE_FILE, 'w') as f:
            json.dump({
                'version': 2,
                'encrypted_data': encrypted_license,
                'created_at': datetime.now().isoformat()
            }, f, indent=2)
        
        with get_db_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS license (
                    id INTEGER PRIMARY KEY,
                    license_key TEXT UNIQUE,
                    admin_email TEXT,
                    device_fingerprint TEXT,
                    status TEXT,
                    licensed_date TEXT
                )
            """)
            cur.execute("""
                INSERT OR REPLACE INTO license 
                (license_key, admin_email, device_fingerprint, status, licensed_date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                license_data['license_key'],
                admin_email,
                device_info['fingerprint'],
                'ACTIVE',
                datetime.now().isoformat()
            ))
        
        logging.info(f"Software licensed to: {admin_email} (encrypted)")
        return license_data['license_key']
    
    @staticmethod
    def verify_license() -> Tuple[bool, str]:
        """Verify if software is licensed and device is authorized."""
        if not os.path.exists(LicenseManager.LICENSE_FILE):
            return False, "NOT_LICENSED"
        
        try:
            with open(LicenseManager.LICENSE_FILE, 'r') as f:
                license_file = json.load(f)
            
            # Support both v1 (plain JSON) and v2 (encrypted) formats
            if license_file.get('version') == 2:
                license_data = _decrypt_license_data(license_file['encrypted_data'])
            else:
                # Legacy format - plain JSON (will be upgraded on next verification)
                license_data = license_file
        except ValueError as e:
            return False, f"INVALID_LICENSE: {str(e)}"
        except Exception as e:
            return False, f"INVALID_LICENSE: {str(e)}"
        
        if license_data.get('status') != 'ACTIVE':
            return False, "LICENSE_INACTIVE"
        
        current_fingerprint = get_device_fingerprint()
        stored_fingerprint = license_data.get('device_fingerprint')
        
        if current_fingerprint != stored_fingerprint:
            license_data['clone_detected'] = True
            license_data['new_device_fingerprint'] = current_fingerprint
            license_data['new_device_info'] = get_device_info()
            license_data['clone_detected_date'] = datetime.now().isoformat()
            
            # Re-encrypt and save with clone detection
            encrypted_license = _encrypt_license_data(license_data)
            with open(LicenseManager.LICENSE_FILE, 'w') as f:
                json.dump({
                    'version': 2,
                    'encrypted_data': encrypted_license,
                    'created_at': license_file.get('created_at', datetime.now().isoformat()),
                    'last_modified': datetime.now().isoformat()
                }, f, indent=2)
            
            logging.warning("CLONE DETECTED: Software running on unauthorized device")
            return False, "CLONE_DETECTED"

        # Upgrade legacy license to encrypted format
        if license_file.get('version') != 2:
            encrypted_license = _encrypt_license_data(license_data)
            with open(LicenseManager.LICENSE_FILE, 'w') as f:
                json.dump({
                    'version': 2,
                    'encrypted_data': encrypted_license,
                    'created_at': license_file.get('licensed_date', datetime.now().isoformat()),
                    'upgraded_at': datetime.now().isoformat()
                }, f, indent=2)
            logging.info("License upgraded to encrypted format")

        return True, "VALID"
    
    @staticmethod
    def update_device_fingerprint():
        """Update stored fingerprint to current device (for development)"""
        if not os.path.exists(LicenseManager.LICENSE_FILE):
            return
        
        try:
            with open(LicenseManager.LICENSE_FILE, 'r') as f:
                license_file = json.load(f)
            
            # Handle encrypted v2 format
            if license_file.get('version') == 2:
                license_data = _decrypt_license_data(license_file['encrypted_data'])
            else:
                license_data = license_file
            
            # Update fingerprint
            current_fingerprint = get_device_fingerprint()
            license_data['device_fingerprint'] = current_fingerprint
            license_data['device_info'] = get_device_info()
            license_data['clone_detected'] = False
            
            # Re-encrypt and save
            encrypted_license = _encrypt_license_data(license_data)
            with open(LicenseManager.LICENSE_FILE, 'w') as f:
                json.dump({
                    'version': 2,
                    'encrypted_data': encrypted_license,
                    'created_at': license_file.get('created_at', datetime.now().isoformat()),
                    'last_modified': datetime.now().isoformat()
                }, f, indent=2)
            
            logging.info("Device fingerprint updated")
        except Exception as e:
            logging.error(f"Error updating fingerprint: {e}")
    
    @staticmethod
    def get_license_info() -> Optional[Dict]:
        """Get current license information (decrypted if v2)."""
        if not os.path.exists(LicenseManager.LICENSE_FILE):
            return None
        
        try:
            with open(LicenseManager.LICENSE_FILE, 'r') as f:
                license_file = json.load(f)
            
            # Return decrypted data for v2 licenses
            if license_file.get('version') == 2:
                try:
                    license_data = _decrypt_license_data(license_file['encrypted_data'])
                    # Add metadata
                    license_data['version'] = 2
                    license_data['created_at'] = license_file.get('created_at')
                    license_data['last_modified'] = license_file.get('last_modified')
                    return license_data
                except ValueError:
                    logging.error("Cannot decrypt license file")
                    return None
            else:
                # Legacy format
                return license_file
        except Exception as e:
            logging.error(f"Error reading license info: {e}")
            return None


# ============================================================================
# ADMIN HIERARCHY MANAGER
# ============================================================================

class AdminHierarchyManager:
    """Manages the admin hierarchy system."""
    
    @staticmethod
    def create_owner_admin(admin_username: str, admin_name: str, admin_email: str, password_hash: str, pin_hash: str = None) -> str:
        """Create the OWNER ADMIN (only called once, on first setup)."""
        owner_admin_id = str(uuid.uuid4())
        device_info = get_device_info()

        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO users
                (user_id, username, email, password_hash, security_pin_hash, role, status, full_name,
                 device_fingerprint, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                owner_admin_id,
                admin_username,  # User's chosen username
                admin_email,
                password_hash,
                pin_hash,
                'OWNER_ADMIN',
                'ACTIVE',
                admin_name,  # Store full name
                device_info['fingerprint'],
                device_info['ip_address'],
                datetime.now().isoformat()
            ))

            cur.execute("""
                INSERT INTO admin_hierarchy
                (user_id, role_level, can_authorize_admins, can_authorize_staff,
                 can_deactivate_users, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                owner_admin_id,
                1,  # OWNER_ADMIN level
                1,  # Can authorize admins
                1,  # Can authorize staff
                1,  # Can deactivate users
                datetime.now().isoformat()
            ))

        # ALSO add to JSON users file for login to work
        try:
            from .utils import save_users, load_users
        except (ImportError, ModuleNotFoundError):
            from utils import save_users, load_users
        
        users = load_users()
        users[admin_username] = {
            'hash': password_hash,
            'pin_hash': pin_hash,
            'salt': '',
            'algo': 'pbkdf2',
            'role': 'OWNER_ADMIN',
            'iterations': 100000
        }
        save_users(users)

        logging.info(f"OWNER ADMIN created: {admin_username} ({admin_email})")
        return owner_admin_id
    
    @staticmethod
    def authorize_secondary_admin(requesting_admin_id: str, new_admin_name: str, 
                                   new_admin_email: str) -> bool:
        """OWNER ADMIN authorizes a SECONDARY ADMIN."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT role FROM users WHERE user_id = ?
            """, (requesting_admin_id,))
            
            requesting_user = cur.fetchone()
            if not requesting_user or requesting_user['role'] != 'OWNER_ADMIN':
                logging.warning(f"Non-owner tried to authorize admin: {requesting_admin_id}")
                return False
        
        new_admin_id = str(uuid.uuid4())
        
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO users
                (user_id, username, email, role, status, authorized_by, authorized_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                new_admin_id,
                new_admin_name,
                new_admin_email,
                'ADMIN',
                'PENDING_PASSWORD',
                requesting_admin_id,
                datetime.now().isoformat()
            ))
            
            cur.execute("""
                INSERT INTO admin_hierarchy
                (user_id, role_level, can_authorize_admins, can_authorize_staff,
                 can_deactivate_users, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                new_admin_id,
                2,  # SECONDARY ADMIN level
                0,  # Cannot authorize admins
                1,  # Can authorize staff
                1,  # Can deactivate users
                datetime.now().isoformat()
            ))
            
            cur.execute("""
                INSERT INTO authorization_log
                (authorized_by, authorized_user, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                requesting_admin_id,
                new_admin_id,
                'CREATED',
                datetime.now().isoformat()
            ))
        
        logging.info(f"SECONDARY ADMIN authorized: {new_admin_email}")
        return True
    
    @staticmethod
    def authorize_staff(admin_id: str, staff_name: str, staff_email: str, 
                       staff_role: str) -> bool:
        """ADMIN authorizes STAFF."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT can_authorize_staff FROM admin_hierarchy WHERE user_id = ?
            """, (admin_id,))
            
            admin_record = cur.fetchone()
            if not admin_record or admin_record['can_authorize_staff'] != 1:
                logging.warning(f"Non-admin tried to authorize staff: {admin_id}")
                return False
        
        staff_id = str(uuid.uuid4())
        
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO users
                (user_id, username, email, role, status, authorized_by, authorized_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                staff_id,
                staff_name,
                staff_email,
                staff_role,
                'PENDING_PASSWORD',
                admin_id,
                datetime.now().isoformat()
            ))
            
            cur.execute("""
                INSERT INTO authorization_log
                (authorized_by, authorized_user, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                admin_id,
                staff_id,
                'CREATED',
                datetime.now().isoformat()
            ))
        
        logging.info(f"{staff_role} authorized: {staff_email}")
        return True
    
    @staticmethod
    def deactivate_user(requesting_admin_id: str, user_to_deactivate_id: str) -> bool:
        """Deactivate a user (OWNER_ADMIN can deactivate anyone)."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT role FROM users WHERE user_id = ?
            """, (requesting_admin_id,))
            
            requesting_user = cur.fetchone()
            if not requesting_user or requesting_user['role'] not in ('OWNER_ADMIN', 'ADMIN'):
                return False
            
            cur.execute("""
                SELECT role FROM users WHERE user_id = ?
            """, (user_to_deactivate_id,))
            
            user_to_deactivate = cur.fetchone()
            
            if user_to_deactivate['role'] == 'OWNER_ADMIN':
                logging.warning(f"Attempt to deactivate OWNER_ADMIN")
                return False
            
            cur.execute("""
                UPDATE users SET status = 'INACTIVE' WHERE user_id = ?
            """, (user_to_deactivate_id,))
            
            cur.execute("""
                INSERT INTO authorization_log
                (authorized_by, authorized_user, action, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                requesting_admin_id,
                user_to_deactivate_id,
                'DEACTIVATED',
                datetime.now().isoformat()
            ))
        
        logging.info(f"User deactivated: {user_to_deactivate_id}")
        return True
    
    @staticmethod
    def get_admin_permissions(user_id: str) -> dict:
        """Get the permissions for an admin user."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT u.user_id, u.role, ah.role_level, 
                       ah.can_authorize_admins, ah.can_authorize_staff
                FROM users u
                LEFT JOIN admin_hierarchy ah ON u.user_id = ah.user_id
                WHERE u.user_id = ?
            """, (user_id,))
            
            result = cur.fetchone()
            
            if not result:
                return {'role': 'STAFF', 'can_authorize_admins': 0, 'can_authorize_staff': 0}
            
            return {
                'user_id': result['user_id'],
                'role': result['role'],
                'role_level': result['role_level'],
                'can_authorize_admins': result['can_authorize_admins'],
                'can_authorize_staff': result['can_authorize_staff']
            }
    
    @staticmethod
    def get_pending_user_requests() -> list:
        """Get all users pending password setup."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email, role, authorized_date
                FROM users
                WHERE status = 'PENDING_PASSWORD'
                ORDER BY authorized_date ASC
            """)
            
            return cur.fetchall()
    
    @staticmethod
    def get_all_users() -> list:
        """Get all users (for admin dashboard)."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email, role, status, authorized_date
                FROM users
                ORDER BY authorized_date DESC
            """)
            
            return cur.fetchall()
    
    @staticmethod
    def get_authorization_log() -> list:
        """Get authorization log."""
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT authorized_by, authorized_user, action, timestamp
                FROM authorization_log
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            return cur.fetchall()


def verify_software_activation() -> Tuple[bool, str]:
    """Main verification function called on startup."""
    is_valid, message = LicenseManager.verify_license()
    
    if not is_valid:
        if message == "NOT_LICENSED":
            return False, "FIRST_TIME_SETUP"
        elif message == "CLONE_DETECTED":
            return False, "CLONE_DETECTED"
        else:
            return False, f"LICENSE_ERROR: {message}"
    
    return True, "ACTIVE"
