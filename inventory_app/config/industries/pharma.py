"""
PHARMA Industry Configuration
===============================
Defines PHARMACY-specific settings and field schemas.
Batch tracking, expiry dates, prescriptions, dosage information.
"""

from ..base import IndustryConfig, FieldConfig
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class PharmaConfig(IndustryConfig):
    """PHARMA industry configuration."""
    
    # Core identity
    industry_id: str = "pharma"
    industry_name: str = "Pharmacy & Healthcare"
    description: str = "Pharmaceutical inventory with batch and expiry tracking"
    icon: str = "💊"
    color: str = "#EF4444"  # Red
    
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
    
    industry_tabs: List[str] = field(default_factory=lambda: [
        "Batches",
        "Expiry Alerts",
        "Prescriptions"
    ])
    
    hidden_tabs: List[str] = field(default_factory=lambda: [
        "Serial Numbers",
        "Warranty",
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
    
    # Product fields (batch, expiry, dosage)
    product_fields: Dict[str, FieldConfig] = field(default_factory=lambda: {
        "model": FieldConfig(label="Model", type="text", required=True, tab="General"),
        "brand": FieldConfig(label="Brand", type="text", required=False, tab="General"),
        "category_id": FieldConfig(label="Category", type="select", source="categories", required=False, tab="General"),
        "purchase_price": FieldConfig(label="Purchase Price", type="number", required=True, min=0, tab="Pricing"),
        "selling_price": FieldConfig(label="Selling Price", type="number", required=True, min=0, tab="Pricing"),
        "stock": FieldConfig(label="Stock", type="number", required=True, min=0, default=0, tab="Inventory"),
        "reorder_point": FieldConfig(label="Reorder Point", type="number", required=False, min=0, default=20, tab="Inventory"),
        
        # Pharma-specific
        "batch_number": FieldConfig(label="Batch Number", type="text", required=True, tab="Batch Info"),
        "expiry_date": FieldConfig(label="Expiry Date", type="date", required=True, tab="Batch Info"),
        "manufacturer": FieldConfig(label="Manufacturer", type="text", required=False, tab="Batch Info"),
        "dosage_form": FieldConfig(label="Dosage Form", type="select", options=["tablet", "capsule", "syrup", "injection", "cream", "ointment", "drops", "inhaler"], required=False, tab="Details"),
        "strength": FieldConfig(label="Strength", type="text", required=False, placeholder='e.g., 500mg', tab="Details"),
        "prescription_required": FieldConfig(label="Prescription Required", type="boolean", required=False, default=False, tab="Details"),
        
        "supplier_id": FieldConfig(label="Supplier", type="select", source="suppliers", required=False, tab="General"),
        "description": FieldConfig(label="Description", type="textarea", required=False, tab="Details"),
        "notes": FieldConfig(label="Notes", type="textarea", required=False, tab="Details"),
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
    low_stock_threshold: int = 20
    
    # Pharma-specific settings
    batch_tracking: bool = True
    expiry_monitoring: bool = True
    expiry_alert_days: int = 30
    dosage_form_options: List[str] = field(default_factory=lambda: [
        "tablet", "capsule", "syrup", "injection",
        "cream", "ointment", "drops", "inhaler"
    ])
