"""
Industry Service — Single Source of Truth
==========================================
Centralizes:
  1. Industry configuration (one canonical dict)
  2. Industry state management (DB + AppState sync)
  3. Industry change event emission
  4. Tab rebuild triggering

All modules MUST read industry config/state from here.
No module should define its own industry dict anymore.

Allowed industry IDs (canonical):
  retail, pharma, electronics, lease_rental, manufacturing, healthcare
"""

import logging
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

# ============================================================
# CANONICAL INDUSTRY CONFIGURATION (Single Source of Truth)
# ============================================================

INDUSTRY_CONFIG: Dict[str, Dict[str, Any]] = {
    "retail": {
        "id": "retail",
        "name": "General Retail",
        "icon": "🛒",
        "color": "#2563EB",
        "description": "Standard retail inventory and POS",
        "app_state_name": "Retail",
        "features": {"track_expiry": False, "track_serial": False, "track_batch": False,
                     "track_prescription": False, "track_repairs": False, "track_trade_in": False},
        "custom_fields": [],
        "default_categories": ["General", "Sale Items", "New Arrivals"],
    },
    "pharma": {
        "id": "pharma",
        "name": "Pharmacy",
        "icon": "💊",
        "color": "#10B981",
        "description": "Medical supplies and batch tracking",
        "app_state_name": "Pharma",
        "features": {"track_expiry": True, "track_serial": False, "track_batch": True,
                     "track_prescription": True, "track_repairs": False, "track_trade_in": False},
        "custom_fields": [
            ("generic_name", "Generic Name", "text"), ("manufacturer", "Manufacturer", "text"),
            ("batch_number", "Batch Number", "text"), ("expiry_date", "Expiry Date", "date"),
            ("dosage", "Dosage", "text"), ("form", "Form (Tablet/Syrup/etc)", "text"),
            ("requires_prescription", "Requires Prescription", "boolean"),
            ("storage_temp", "Storage Temperature", "text"),
        ],
        "default_categories": ["Prescription", "OTC", "Medical Supplies", "Vitamins", "First Aid"],
    },
    "electronics": {
        "id": "electronics",
        "name": "Electronics",
        "icon": "📱",
        "color": "#8B5CF6",
        "description": "IMEI/Serial tracking and repairs",
        "app_state_name": "Electronics",
        "features": {"track_expiry": False, "track_serial": True, "track_batch": False,
                     "track_prescription": False, "track_repairs": True, "track_trade_in": True},
        "custom_fields": [
            ("brand", "Brand", "text"), ("ram", "RAM", "text"), ("storage", "Storage", "text"),
            ("screen_size", "Screen Size", "text"), ("camera", "Camera", "text"),
            ("battery", "Battery", "text"), ("color", "Color", "text"),
            ("warranty_months", "Warranty (Months)", "number"),
        ],
        "default_categories": ["Phones", "Tablets", "Laptops", "Accessories", "Audio"],
    },
    "lease_rental": {
        "id": "lease_rental",
        "name": "Lease & Rental",
        "icon": "📋",
        "color": "#F59E0B",
        "description": "Equipment and property rental",
        "app_state_name": "Lease & Rental",
        "features": {"track_expiry": False, "track_serial": False, "track_batch": False,
                     "track_prescription": False, "track_repairs": False, "track_trade_in": False},
        "custom_fields": [],
        "default_categories": ["Leases", "Contracts", "Properties", "Equipment"],
    },
    "manufacturing": {
        "id": "manufacturing",
        "name": "Manufacturing",
        "icon": "🏭",
        "color": "#F59E0B",
        "description": "BOM and production tracking",
        "app_state_name": "Manufacturing",
        "features": {"track_expiry": False, "track_serial": False, "track_batch": True,
                     "track_prescription": False, "track_repairs": False, "track_trade_in": False},
        "custom_fields": [],
        "default_categories": ["Raw Materials", "Work in Progress", "Finished Goods"],
    },
    "healthcare": {
        "id": "healthcare",
        "name": "Healthcare",
        "icon": "🏥",
        "color": "#EF4444",
        "description": "Patient billing and medical records",
        "app_state_name": "Healthcare",
        "features": {"track_expiry": False, "track_serial": False, "track_batch": False,
                     "track_prescription": True, "track_repairs": False, "track_trade_in": False},
        "custom_fields": [],
        "default_categories": ["Medical Supplies", "Equipment", "Pharmaceuticals", "Consumables"],
    },
}

VALID_INDUSTRY_IDS = set(INDUSTRY_CONFIG.keys())
DEFAULT_INDUSTRY_ID = "retail"

# Subscriber callbacks: fired when industry changes
_subscribers: List[Callable[[str], None]] = []

# Tab reload callback — registered by main.py at startup to avoid inverted dependency
_tab_reload_fn: Optional[Callable[[], bool]] = None


def set_tab_reload_fn(fn: Callable[[], bool]):
    """Register the tab reload function. Called by main.py at startup."""
    global _tab_reload_fn
    _tab_reload_fn = fn


# ============================================================
# PUBLIC API
# ============================================================

def get_config(industry_id: str) -> Dict[str, Any]:
    """Get industry config by canonical ID. Falls back to retail."""
    return INDUSTRY_CONFIG.get(industry_id, INDUSTRY_CONFIG[DEFAULT_INDUSTRY_ID])


def get_all_configs() -> Dict[str, Dict[str, Any]]:
    """Get all industry configurations."""
    return INDUSTRY_CONFIG


def get_valid_ids() -> set:
    """Return set of valid industry IDs."""
    return VALID_INDUSTRY_IDS


def normalize_industry_id(raw: str) -> str:
    """
    Normalize any input string to a canonical industry ID.
    Handles: 'Retail' -> 'retail', 'Pharmacy' -> 'pharma',
             'pharmacy' -> 'pharma', 'Electronics' -> 'electronics', etc.
    """
    if not raw:
        return DEFAULT_INDUSTRY_ID

    cleaned = raw.strip().lower().replace(" ", "_").replace("&", "").replace("__", "_")

    # Direct match
    if cleaned in VALID_INDUSTRY_IDS:
        return cleaned

    # Map common display names to IDs
    name_to_id = {
        "general_retail": "retail",
        "pharmacy": "pharma",
        "electronics_&_mobile": "electronics",
        "electronics__mobile": "electronics",
        "lease_&_rental": "lease_rental",
        "lease__rental": "lease_rental",
    }
    return name_to_id.get(cleaned, DEFAULT_INDUSTRY_ID)


def get_current_industry_id() -> str:
    """Get current industry ID from database via service layer."""
    try:
        from services import svc
        raw = svc.db.get_industry_type()
        return normalize_industry_id(raw)
    except Exception as e:
        logger.warning(f"Failed to read industry from DB: {e}")
        return DEFAULT_INDUSTRY_ID


def get_app_state_industry_name() -> str:
    """Get the industry name as used by AppState (capitalized display name)."""
    current_id = get_current_industry_id()
    config = get_config(current_id)
    return config.get("app_state_name", config["name"])


def change_industry(industry_id: str) -> bool:
    """
    Atomically change the industry:
      1. Validate input
      2. Write to DB
      3. Update AppState
      4. Emit industry_changed event (triggers tab rebuild)

    This is the ONLY function that should be called when switching industries.
    All UI entry points (dashboard selector, settings tab, wizard, shortcuts)
    must call this function.

    Returns True on success, False on failure.
    """
    canonical_id = normalize_industry_id(industry_id)

    if canonical_id not in VALID_INDUSTRY_IDS:
        logger.error(f"Invalid industry ID: '{industry_id}' (normalized to '{canonical_id}')")
        return False

    # Step 1: Write to DB
    try:
        from services import svc
        success = svc.db.set_industry_type(canonical_id)
        if not success:
            logger.error(f"Failed to write industry '{canonical_id}' to DB")
            return False
    except Exception as e:
        logger.error(f"DB error setting industry '{canonical_id}': {e}")
        return False

    # Step 2: Update AppState
    try:
        from app_core import app_state
        config = get_config(canonical_id)
        app_state_name = config.get("app_state_name", config["name"])
        app_state.industry_type = app_state_name
    except Exception as e:
        logger.error(f"Failed to update AppState: {e}")
        # Continue anyway — DB is the source of truth

    # Step 3: Trigger tab rebuild via registered callback (no import from main)
    if _tab_reload_fn:
        try:
            _tab_reload_fn()
        except Exception as e:
            logger.warning(f"Tab reload failed after industry change: {e}")

    # Step 4: Notify subscribers
    _notify_subscribers(canonical_id)

    logger.info(f"✅ Industry changed to: {canonical_id}")
    return True


def subscribe(callback: Callable[[str], None]):
    """Subscribe to industry change events. Callback receives the new industry ID."""
    if callback not in _subscribers:
        _subscribers.append(callback)


def unsubscribe(callback: Callable[[str], None]):
    """Unsubscribe from industry change events."""
    if callback in _subscribers:
        _subscribers.remove(callback)


def _notify_subscribers(industry_id: str):
    """Fire all subscriber callbacks."""
    for cb in list(_subscribers):
        try:
            cb(industry_id)
        except Exception as e:
            logger.error(f"Industry subscriber error: {e}")


# ============================================================
# LEGACY COMPATIBILITY SHIMS
# ============================================================
# These functions wrap the old API names so existing imports don't
# break immediately. They delegate to the canonical functions above.

def get_industry_type() -> str:
    """Legacy shim — use get_current_industry_id() instead."""
    return get_current_industry_id()


def set_industry_type(industry_id: str) -> bool:
    """Legacy shim — use change_industry() instead."""
    return change_industry(industry_id)


def get_industry_metadata(industry_id: str = None) -> dict:
    """Legacy shim — returns config dict for backward compatibility."""
    if industry_id is None:
        return get_all_configs()
    return get_config(industry_id)
