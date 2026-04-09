"""
ELECTRONICS Industry Configuration
====================================
DEFAULT industry for the system.
Defines ELECTRONICS-specific settings, tabs, and field schemas.
Serial numbers, IMEI, warranty, device specifications.

This is the ONLY source of truth for Electronics industry.
"""

from ..base import IndustryConfig, FieldConfig
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ElectronicsConfig(IndustryConfig):
    """ELECTRONICS industry configuration - DEFAULT INDUSTRY."""
    
    # Core identity
    industry_id: str = "electronics"
    industry_name: str = "Electronics & Devices"
    description: str = "Electronics inventory with serial number and warranty tracking"
    icon: str = "📱"
    color: str = "#8B5CF6"  # Purple
    
    # DEFAULT INDUSTRY FLAG
    is_default: bool = True
    
    # ═══════════════════════════════════════════════════════
    # TAB REGISTRY - Controls exactly what tabs are shown
    # ═══════════════════════════════════════════════════════
    
    # Core tabs ALWAYS shown for this industry
    core_tabs: List[str] = field(default_factory=lambda: [
        "Dashboard",
        "Inventory",
        "Sales",
        "Customers",
        "Suppliers",
        "Reports",
        "Settings"
    ])
    
    # Industry-specific tabs (auto-added)
    industry_tabs: List[str] = field(default_factory=lambda: [
        "Serial Numbers",
        "Warranty"
    ])
    
    # Tabs EXPLICITLY HIDDEN for this industry
    hidden_tabs: List[str] = field(default_factory=lambda: [
        "Batches",
        "Expiry Alerts",
        "Prescriptions",
        "Trade-ins",
        "Service Tickets",
        "Stock Transfers",
        "Purchase Orders",
        "Sales Orders",
        "Invoicing",
        "Returns/RMA",
        "Profit Analysis",
        "Alerts",
        "Smart Analytics",
        "Industry Settings"
    ])
    
    # ═══════════════════════════════════════════════════════
    # FIELD DEFINITIONS - Drives forms and database validation
    # ═══════════════════════════════════════════════════════
    
    # Product fields for electronics
    product_fields: Dict[str, FieldConfig] = field(default_factory=lambda: {
        # Core fields (always shown)
        "model": FieldConfig(label="Model", type="text", required=True, tab="General"),
        "brand": FieldConfig(label="Brand", type="text", required=True, tab="General"),
        "category_id": FieldConfig(label="Category", type="select", source="categories", required=False, tab="General"),
        "purchase_price": FieldConfig(label="Purchase Price", type="number", required=True, min=0, tab="Pricing"),
        "selling_price": FieldConfig(label="Selling Price", type="number", required=True, min=0, tab="Pricing"),
        "stock": FieldConfig(label="Stock", type="number", required=True, min=0, default=0, tab="Inventory"),
        "reorder_point": FieldConfig(label="Reorder Point", type="number", required=False, min=0, default=5, tab="Inventory"),
        
        # Electronics-specific fields
        "serial_number": FieldConfig(label="Serial Number", type="text", required=False, unique=True, tab="Device Info"),
        "imei": FieldConfig(label="IMEI", type="text", required=False, pattern=r"^\d{15}$", tab="Device Info"),
        "ram": FieldConfig(label="RAM", type="select", options=["2GB", "4GB", "6GB", "8GB", "12GB", "16GB", "32GB"], required=False, tab="Specifications"),
        "storage": FieldConfig(label="Storage", type="select", options=["16GB", "32GB", "64GB", "128GB", "256GB", "512GB", "1TB", "2TB"], required=False, tab="Specifications"),
        "screen_size": FieldConfig(label="Screen Size", type="text", required=False, placeholder='e.g., 6.1"', tab="Specifications"),
        "screen_type": FieldConfig(label="Screen Type", type="select", options=["LCD", "OLED", "AMOLED", "IPS", "TFT"], required=False, tab="Specifications"),
        "camera": FieldConfig(label="Camera", type="text", required=False, placeholder='e.g., 48MP Triple', tab="Specifications"),
        "battery": FieldConfig(label="Battery", type="text", required=False, placeholder='e.g., 5000mAh', tab="Specifications"),
        "color": FieldConfig(label="Color", type="text", required=False, tab="Device Info"),
        "device_condition": FieldConfig(label="Condition", type="select", options=["new", "refurbished", "used", "damaged"], required=True, default="new", tab="Device Info"),
        "warranty_months": FieldConfig(label="Warranty (Months)", type="number", required=False, min=0, default=12, tab="Warranty"),
        "warranty_expiry": FieldConfig(label="Warranty Expiry", type="date", required=False, tab="Warranty"),
        
        # Optional fields
        "supplier_id": FieldConfig(label="Supplier", type="select", source="suppliers", required=False, tab="General"),
        "description": FieldConfig(label="Description", type="textarea", required=False, tab="Details"),
        "notes": FieldConfig(label="Notes", type="textarea", required=False, tab="Details"),
        "specifications": FieldConfig(label="Full Specifications", type="textarea", required=False, tab="Specifications"),
        "barcode": FieldConfig(label="Barcode", type="text", required=False, unique=True, tab="General"),
        "sku": FieldConfig(label="SKU", type="text", required=False, unique=True, tab="General"),
    })
    
    # Supplier fields
    supplier_fields: Dict[str, FieldConfig] = field(default_factory=lambda: {
        "name": FieldConfig(label="Name", type="text", required=True),
        "contact_person": FieldConfig(label="Contact Person", type="text", required=False),
        "email": FieldConfig(label="Email", type="email", required=False),
        "phone": FieldConfig(label="Phone", type="text", required=False),
        "address": FieldConfig(label="Address", type="textarea", required=False),
        "city": FieldConfig(label="City", type="text", required=False),
        "country": FieldConfig(label="Country", type="text", required=False, default="Pakistan"),
        "notes": FieldConfig(label="Notes", type="textarea", required=False),
    })
    
    # Customer fields
    customer_fields: Dict[str, FieldConfig] = field(default_factory=lambda: {
        "name": FieldConfig(label="Name", type="text", required=True),
        "phone": FieldConfig(label="Phone", type="text", required=False),
        "email": FieldConfig(label="Email", type="email", required=False),
        "address": FieldConfig(label="Address", type="textarea", required=False),
        "notes": FieldConfig(label="Notes", type="textarea", required=False),
    })
    
    # Business rules
    default_tax_rate: float = 0.16
    low_stock_threshold: int = 5
    
    # Electronics-specific settings
    warranty_tracking: bool = True
    serial_number_required: bool = False  # Optional but available
    imei_validation: bool = True
    device_condition_options: List[str] = field(default_factory=lambda: [
        "new", "refurbished", "used", "damaged"
    ])
