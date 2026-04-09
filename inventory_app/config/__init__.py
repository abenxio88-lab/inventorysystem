"""
Configuration Package
======================
Industry configuration system.
Each industry has its own config - completely independent.

Usage:
    from config import get_industry_config
    
    config = get_industry_config("electronics")
    print(config.industry_name)  # "Electronics & Devices"
    print(config.get_visible_tabs())  # List of visible tabs
"""

from .base import IndustryConfig, FieldConfig
from .industries.electronics import ElectronicsConfig
from .industries.retail import RetailConfig
from .industries.pharma import PharmaConfig

# Registry of all industry configs (Electronics is DEFAULT)
_INDUSTRY_REGISTRY = {
    "electronics": ElectronicsConfig,  # DEFAULT
    "retail": RetailConfig,
    "pharma": PharmaConfig,
}


def get_industry_config(industry_id: str = None) -> IndustryConfig:
    """
    Get configuration for a specific industry.
    If no industry_id provided, returns DEFAULT (Electronics).
    
    Args:
        industry_id: Industry identifier (e.g., "electronics", "retail", "pharma")
        
    Returns:
        IndustryConfig: Configuration instance for the industry
    """
    # If no industry specified, return DEFAULT (Electronics)
    if industry_id is None:
        industry_id = "electronics"
    
    if industry_id not in _INDUSTRY_REGISTRY:
        raise ValueError(
            f"Unknown industry: {industry_id}. "
            f"Available: {list(_INDUSTRY_REGISTRY.keys())}"
        )
    
    return _INDUSTRY_REGISTRY[industry_id]()


def get_default_industry() -> str:
    """Get the default industry ID."""
    return "electronics"


def get_all_industries() -> list:
    """Get list of all available industry IDs."""
    return list(_INDUSTRY_REGISTRY.keys())


def register_industry_config(industry_id: str, config_class):
    """
    Register a new industry configuration.
    
    Args:
        industry_id: Unique industry identifier
        config_class: Configuration class (inherits IndustryConfig)
    """
    if not issubclass(config_class, IndustryConfig):
        raise ValueError("config_class must inherit from IndustryConfig")
    
    _INDUSTRY_REGISTRY[industry_id] = config_class


# Tab registry - maps tab names to module/function
# This is the SINGLE source of truth for all available tabs
TAB_REGISTRY = {
    "Dashboard": {"module": "dashboard_ui", "function": "create_dashboard_tab"},
    "Inventory": {"module": "inventory_ui", "function": "create_inventory_tab"},
    "Sales": {"module": "sales_ui", "function": "create_sales_tab"},
    "Customers": {"module": "customers_ui", "function": "create_customers_tab"},
    "Suppliers": {"module": "suppliers_ui", "function": "create_suppliers_tab"},
    "Serial Numbers": {"module": "electronics_ui", "function": "create_serial_numbers_tab"},
    "Warranty": {"module": "electronics_ui", "function": "create_warranty_tab"},
    "Batches": {"module": "pharmacy_ui", "function": "create_batches_tab"},
    "Expiry Alerts": {"module": "pharmacy_ui", "function": "create_expiry_monitor_tab"},
    "Prescriptions": {"module": "pharmacy_ui", "function": "create_prescriptions_tab"},
    "Reports": {"module": "reports_ui", "function": "create_reports_tab"},
    "Settings": {"module": "industry_ui", "function": "create_industry_settings_tab"},
    # Hidden/optional tabs (only shown if enabled for industry)
    "Trade-ins": {"module": "tradein_service_ui", "function": "create_trade_ins_tab"},
    "Service Tickets": {"module": "tradein_service_ui", "function": "create_service_tab"},
    "Stock Transfers": {"module": "stock_transfer_ui", "function": "create_stock_transfers_tab"},
    "Purchase Orders": {"module": "purchase_orders_ui", "function": "create_purchase_orders_tab"},
    "Sales Orders": {"module": "sales_orders_ui", "function": "create_sales_orders_tab"},
    "Invoicing": {"module": "invoicing_ui", "function": "create_invoicing_tab"},
    "Returns/RMA": {"module": "returns_ui", "function": "create_returns_tab"},
    "Profit Analysis": {"module": "profit_ui", "function": "create_profit_tab"},
    "Alerts": {"module": "alerts_ui", "function": "create_alerts_tab"},
    "Smart Analytics": {"module": "smart_analytics_ui", "function": "create_smart_analytics_tab"},
    "Industry Settings": {"module": "industry_ui", "function": "create_industry_settings_tab"},
}


def get_tab_function(tab_name: str):
    """
    Get the function that creates a tab.
    
    Args:
        tab_name: Tab name from registry
        
    Returns:
        Function reference or None if not found
    """
    if tab_name not in TAB_REGISTRY:
        return None
    
    tab_info = TAB_REGISTRY[tab_name]
    try:
        import importlib
        module = importlib.import_module(tab_info["module"])
        return getattr(module, tab_info["function"])
    except ImportError:
        return None
