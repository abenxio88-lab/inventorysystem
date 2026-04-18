import os
import sys
import shutil
import json
import csv
import logging
import threading
import tempfile
from datetime import datetime

def get_data_dir(app_name="inventory_app"):
    """Return a writable data directory.

    - When frozen (PyInstaller), use %LOCALAPPDATA%\\<app_name>\\data.
    - During development, use the package `data/` folder next to source.
    """
    if getattr(sys, "frozen", False):
        base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
        data_dir = os.path.join(base, app_name, "data")
    else:
        data_dir = os.path.join(os.path.dirname(__file__), "data")

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _data_file(name):
    return os.path.join(get_data_dir(), name)


# In-process file lock to avoid concurrent writer races between threads
_file_lock = threading.Lock()


def write_json_atomic(path, data):
    """Write JSON to `path` atomically (write temp then replace) under a thread lock."""
    ddir = os.path.dirname(path)
    os.makedirs(ddir, exist_ok=True)
    with _file_lock:
        # write to a temp file in the same directory then atomically replace
        fd, tmp = tempfile.mkstemp(prefix=".tmp", dir=ddir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass


def load_json_file(path, default=None):
    """Load JSON safely, returning `default` on error or missing file."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logging.exception("Failed to load json file: %s", path)
        return default


def backup_data(backup_dir=None, files=None):
    """Copy important JSON data files into a timestamped backup folder.

    Returns the path to the created backup folder.
    """
    if files is None:
        files = ["inventory.json", "sales.json", "reports.json"]

    data_dir = get_data_dir()
    if backup_dir is None:
        backup_dir = os.path.join(data_dir, "backups")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_folder = os.path.join(backup_dir, timestamp)
    os.makedirs(dest_folder, exist_ok=True)

    for f in files:
        src = os.path.join(data_dir, f)
        if os.path.exists(src):
            try:
                shutil.copy2(src, os.path.join(dest_folder, f))
            except Exception:
                logging.exception("Failed to backup %s", src)
    return dest_folder


def export_inventory_to_csv(csv_path=None):
    """Export current inventory JSON to a CSV file. If csv_path is None,
    a timestamped file is placed in the data directory.
    Returns the path to the written CSV file.
    """
    data_file = _data_file("inventory.json")
    if not os.path.exists(data_file):
        raise FileNotFoundError("inventory.json not found")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if csv_path is None:
        csv_path = os.path.join(get_data_dir(), f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    fieldnames = ["model", "category", "screen_type", "supplier", "purchase_price", "selling_price", "stock", "notes"]
    with open(csv_path, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            row = {k: item.get(k, "") for k in fieldnames}
            writer.writerow(row)

    return csv_path


def import_inventory_from_csv(csv_path, merge=False):
    """Import inventory items from a CSV file. If merge is False the
    CSV replaces the current inventory; if True, rows are merged by
    `model` (existing items are updated, new items added).
    Returns the final inventory list written to disk.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(csv_path)

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        items = []
        for r in reader:
            try:
                item = {
                    "model": str(r.get("model", "")).strip(),
                    "category": str(r.get("category", "")).strip(),
                    "screen_type": str(r.get("screen_type", r.get("screen", ""))).strip(),
                    "supplier": str(r.get("supplier", "")).strip(),
                    "purchase_price": int(float(r.get("purchase_price", 0) or 0)),
                    "selling_price": int(float(r.get("selling_price", 0) or 0)),
                    "stock": int(float(r.get("stock", 0) or 0)),
                    "notes": str(r.get("notes", "")).strip()
                }
            except Exception:
                logging.exception("Skipping invalid row in import: %s", r)
                continue
            if item.get("model"):
                items.append(item)

    dest = _data_file("inventory.json")
    if merge and os.path.exists(dest):
        existing = load_json_file(dest, default=[])
        # Build map by model for quick merge
        emap = {e.get("model"): e for e in existing}
        for it in items:
            emap[it.get("model")] = it
        final = list(emap.values())
    else:
        final = items

    try:
        write_json_atomic(dest, final)
    except Exception:
        logging.exception("Failed to write inventory during import: %s", dest)

    return final


def prune_backups(backup_root=None, keep=30):
    """Prune older backup folders, keeping only the most recent `keep` entries.

    Returns list of removed folder paths.
    """
    if backup_root is None:
        backup_root = os.path.join(get_data_dir(), "backups")
    if not os.path.exists(backup_root):
        return []

    entries = []
    for name in os.listdir(backup_root):
        full = os.path.join(backup_root, name)
        if os.path.isdir(full):
            try:
                # attempt to parse timestamp-like folder names first
                entries.append((os.path.getmtime(full), full))
            except Exception:
                entries.append((0, full))

    # sort by modified time descending
    entries.sort(reverse=True, key=lambda x: x[0])
    to_remove = entries[keep:]
    removed = []
    for _, path in to_remove:
        try:
            shutil.rmtree(path)
            removed.append(path)
        except Exception:
            logging.exception("Failed to remove old backup %s", path)
    return removed


# --------------------- User Management ---------------------
import hashlib
import binascii
import secrets

# Try to import centralized security functions
try:
    from .security import hash_password, verify_password
    SECURITY_MODULE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    try:
        from security import hash_password, verify_password
        SECURITY_MODULE_AVAILABLE = True
    except (ImportError, ModuleNotFoundError):
        SECURITY_MODULE_AVAILABLE = False
        hash_password = None
        verify_password = None

# Optional Argon2 support for stronger password hashing
try:
    from argon2 import PasswordHasher, exceptions as argon2_exceptions
    ARGON2_AVAILABLE = True
    _ph = PasswordHasher()
except Exception:
    ARGON2_AVAILABLE = False

USERS_FILE = _data_file("users.json")


def _ensure_users_file():
    # Ensure the users file exists but do NOT create a default insecure account.
    if not os.path.exists(USERS_FILE):
        try:
            write_json_atomic(USERS_FILE, {})
        except Exception:
            # best-effort fallback
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=4)


def load_users():
    _ensure_users_file()
    return load_json_file(USERS_FILE, default={})


def save_users(users):
    try:
        write_json_atomic(USERS_FILE, users)
    except Exception:
        logging.exception("Failed to save users file")


def _hash_password_pbkdf2(password, salt=None, iterations=100_000):
    if salt is None:
        salt = secrets.token_bytes(16)
    if isinstance(salt, str):
        salt = binascii.unhexlify(salt)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return binascii.hexlify(dk).decode("ascii"), binascii.hexlify(salt).decode("ascii")


def _verify_pbkdf2(stored_hash, password, salt, iterations=100_000):
    try:
        h, _ = _hash_password_pbkdf2(password, salt=salt, iterations=iterations)
        return h == stored_hash
    except Exception:
        return False


def _hash_password_argon2(password):
    # Returns the encoded argon2 hash string
    return _ph.hash(password)


def _verify_argon2(stored_hash, password):
    try:
        return _ph.verify(stored_hash, password)
    except Exception:
        return False


def create_user(username, password, role="staff"):
    users = load_users()
    if username in users:
        raise ValueError("User already exists")
    
    # Use centralized security module if available
    if SECURITY_MODULE_AVAILABLE and hash_password:
        try:
            h = hash_password(password)
            users[username] = {"role": role, "algo": "pbkdf2", "hash": h}
        except Exception as e:
            logging.warning(f"Failed to use security module, falling back to Argon2/PBKDF2: {e}")
            # Fallback to Argon2/PBKDF2 logic below
            if ARGON2_AVAILABLE:
                try:
                    h = _hash_password_argon2(password)
                    users[username] = {"role": role, "algo": "argon2", "hash": h}
                except Exception:
                    h, s = _hash_password_pbkdf2(password)
                    users[username] = {"role": role, "algo": "pbkdf2", "hash": h, "salt": s, "iterations": 100_000}
            else:
                h, s = _hash_password_pbkdf2(password)
                users[username] = {"role": role, "algo": "pbkdf2", "hash": h, "salt": s, "iterations": 100_000}
    # Prefer Argon2 when available for new users; fall back to PBKDF2 for compatibility
    elif ARGON2_AVAILABLE:
        try:
            h = _hash_password_argon2(password)
            users[username] = {"role": role, "algo": "argon2", "hash": h}
        except Exception:
            # fallback
            h, s = _hash_password_pbkdf2(password)
            users[username] = {"role": role, "algo": "pbkdf2", "hash": h, "salt": s, "iterations": 100_000}
    else:
        h, s = _hash_password_pbkdf2(password)
        users[username] = {"role": role, "algo": "pbkdf2", "hash": h, "salt": s, "iterations": 100_000}
    save_users(users)
    return True


def verify_user(username, password):
    users = load_users()
    u = users.get(username)
    if not u:
        return False, None

    algo = u.get("algo", "pbkdf2")
    stored = u.get("hash")

    # Always try security module verification first (handles full hash format)
    if verify_password:
        try:
            if verify_password(password, stored):
                return (True, u.get("role"))
            else:
                return (False, None)
        except Exception as e:
            logging.debug(f"Security module verification failed: {e}, falling back to local verification")
            # Fall through to local verification logic

    # Fallback to local verification for argon2
    if algo == "argon2":
        if not ARGON2_AVAILABLE:
            return False, None
        ok = False
        try:
            ok = _verify_argon2(stored, password)
        except Exception:
            ok = False
        return (True, u.get("role")) if ok else (False, None)
    else:
        # Local pbkdf2 verification (expects separate salt)
        salt = u.get("salt")
        iterations = int(u.get("iterations", 100_000))
        if stored is None or salt is None:
            return False, None
        ok = _verify_pbkdf2(stored, password, salt, iterations=iterations)
        return (True, u.get("role")) if ok else (False, None)


def list_users():
    users = load_users()
    return [{"username": k, "role": v.get("role")} for k, v in users.items()]


def delete_user(username):
    users = load_users()
    if username in users:
        users.pop(username)
        save_users(users)
        return True
    return False


def set_password(username, new_password):
    users = load_users()
    if username not in users:
        raise KeyError("User not found")
    
    # Use centralized security module if available
    if SECURITY_MODULE_AVAILABLE and hash_password:
        try:
            h = hash_password(new_password)
            users[username]["algo"] = "pbkdf2"
            users[username]["hash"] = h
            users[username].pop("salt", None)
            users[username].pop("iterations", None)
        except Exception as e:
            logging.warning(f"Failed to use security module, falling back: {e}")
            # Fallback to Argon2/PBKDF2 logic
            if ARGON2_AVAILABLE:
                try:
                    h = _hash_password_argon2(new_password)
                    users[username]["algo"] = "argon2"
                    users[username]["hash"] = h
                    users[username].pop("salt", None)
                    users[username].pop("iterations", None)
                except Exception:
                    h, s = _hash_password_pbkdf2(new_password)
                    users[username]["algo"] = "pbkdf2"
                    users[username]["hash"] = h
                    users[username]["salt"] = s
                    users[username]["iterations"] = 100_000
            else:
                h, s = _hash_password_pbkdf2(new_password)
                users[username]["algo"] = "pbkdf2"
                users[username]["hash"] = h
                users[username]["salt"] = s
                users[username]["iterations"] = 100_000
    elif ARGON2_AVAILABLE:
        try:
            h = _hash_password_argon2(new_password)
            users[username]["algo"] = "argon2"
            users[username]["hash"] = h
            users[username].pop("salt", None)
            users[username].pop("iterations", None)
        except Exception:
            h, s = _hash_password_pbkdf2(new_password)
            users[username]["algo"] = "pbkdf2"
            users[username]["hash"] = h
            users[username]["salt"] = s
            users[username]["iterations"] = 100_000
    else:
        h, s = _hash_password_pbkdf2(new_password)
        users[username]["algo"] = "pbkdf2"
        users[username]["hash"] = h
        users[username]["salt"] = s
        users[username]["iterations"] = 100_000
    save_users(users)
    return True


# Ensure users file exists on import
_ensure_users_file()


# --------------------- Audit Logging ---------------------
# Place audit log inside the writable data directory so it is persisted
# and consistent with other data files.
audit_dir = os.path.join(get_data_dir(), "logs")
os.makedirs(audit_dir, exist_ok=True)
AUDIT_LOG = os.path.join(audit_dir, "audit.log")


def audit_event(user, action, target=None, details=None):
    """Append an audit event to logs/audit.log as a JSON line."""
    try:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "target": target,
            "details": details
        }
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        logging.exception("Failed to write audit event: %s %s", user, action)


# --------------------- Settings ---------------------
SETTINGS_FILE = _data_file("settings.json")


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        defaults = {"backup_hour": 2, "backup_minute": 0, "backup_retention": 30}
        save_settings(defaults)
        return defaults
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logging.exception("Failed to load settings; returning defaults")
        return {"backup_hour": 2, "backup_minute": 0, "backup_retention": 30}


def save_settings(settings):
    try:
        write_json_atomic(SETTINGS_FILE, settings)
        return settings
    except Exception:
        logging.exception("Failed to save settings")
        return settings


def _bundle_data_path():
    """Return path to bundled 'data' directory inside frozen bundle or source tree."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts bundled files into _MEIPASS
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return os.path.join(base, "data")
    return os.path.join(os.path.dirname(__file__), "data")


def ensure_default_data(files=None):
    """Ensure default JSON files from the bundled `data/` folder exist in the
    writable data directory (used when the app is frozen). This copies defaults
    on first run so the frozen app has persistent, writable copies in
    `%LOCALAPPDATA%\\<app_name>\\data`.
    """
    if files is None:
        files = ["inventory.json", "sales.json", "reports.json", "settings.json", "users.json"]

    data_dir = get_data_dir()
    bundle_dir = _bundle_data_path()

    for name in files:
        dest = os.path.join(data_dir, name)
        if not os.path.exists(dest):
            src = os.path.join(bundle_dir, name)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, dest)
                except Exception:
                    logging.exception("Failed to copy default data file %s", name)
    return True


# When imported in a frozen application, ensure default data files exist.
try:
    ensure_default_data()
except Exception:
    logging.exception("ensure_default_data failed")


# ============================================================================
# LOGIN RATE LIMITING HELPER
# ============================================================================

_login_rate_limiter = None

def get_login_rate_limiter(max_attempts: int = 5, window_seconds: int = 300):
    """
    Get the singleton login rate limiter.
    
    Args:
        max_attempts: Maximum login attempts before lockout (default: 5)
        window_seconds: Lockout duration in seconds (default: 300 = 5 min)
    
    Returns:
        RateLimiter instance for login attempts
    """
    global _login_rate_limiter
    if _login_rate_limiter is None:
        from security import RateLimiter
        _login_rate_limiter = RateLimiter(max_attempts=max_attempts, window_seconds=window_seconds)
    return _login_rate_limiter
