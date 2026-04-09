"""
RETAIL Industry Configuration
===============================
Defines RETAIL-specific settings and field schemas.
Simple products, basic sales, no serial numbers or batches.
"""

from ..base import IndustryConfig, FieldConfig
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class RetailConfig(IndustryConfig):
    """RETAIL industry configuration."""
    
    # Core identity
    industry_id: str = "retail"
    industry_name: str = "Retail & General Trade"
    description: str = "General retail inventory management"
    icon: str = "🏪"
    color: str = "#3B82F6"  # Blue
    
    is_default: bool = False
    
    # Tab registry
    core_tabs: List[str] = field(default_factory=lambda: [
        "Dashboard",
        "Inventory",
        "Sales",
        "Customers",
        "Suppliers",
        "Reports",
        "Settings"
    ])
    
    industry_tabs: List[str] = field(default_factory=lambda: [])
    
    hidden_tabs: List[str] = field(default_factory=lambda: [
        "Serial Numbers",
        "Warranty",
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
    
    # Product fields (SIMPLE - no serial, batch, expiry)
    product_fields: Dict[str, FieldConfig] = field(default_factory=lambda: {
        "model": FieldConfig(label="Model", type="text", required=True, tab="General"),
        "brand": FieldConfig(label="Brand", type="text", required=False, tab="General"),
        "category_id": FieldConfig(label="Category", type="select", source="categories", required=False, tab="General"),
        "purchase_price": FieldConfig(label="Purchase Price", type="number", required=True, min=0, tab="Pricing"),
        "selling_price": FieldConfig(label="Selling Price", type="number", required=True, min=0, tab="Pricing"),
        "stock": FieldConfig(label="Stock", type="number", required=True, min=0, default=0, tab="Inventory"),
        "reorder_point": FieldConfig(label="Reorder Point", type="number", required=False, min=0, default=10, tab="Inventory"),
        "supplier_id": FieldConfig(label="Supplier", type="select", source="suppliers", required=False, tab="General"),
        "description": FieldConfig(label="Description", type="textarea", required=False, tab="Details"),
        "notes": FieldConfig(label="Notes", type="textarea", required=False, tab="Details"),
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
    default_tax_rate: float = 0.0
    low_stock_threshold: int = 10
