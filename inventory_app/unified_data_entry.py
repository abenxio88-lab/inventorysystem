"""
Unified Data Entry System - Industry Specific
==============================================
Single entry point for all data, with industry-specific fields.

Key Features:
- Enter data ONCE → Available everywhere in that industry
- Dynamic form fields based on industry type
- Industry-specific database columns
- Smart data linking across modules
- Automatic context propagation

Industry Types:
- Electronics: IMEI, Serial, Warranty, Specs
- Pharmacy: Batch, Expiry, Dosage, Prescription
- Toy Shop: Age Range, Safety Certs
- Fashion: Size, Material, Gender, Season
- Food & Beverage: Ingredients, Allergens, Nutrition
- General Retail: Basic fields only
"""

import tkinter as tk
from tkinter import ttk
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

try:
    import customtkinter as ctk
    CTk_AVAILABLE = True
except ImportError:
    CTk_AVAILABLE = False

from error_manager import get_error_manager, report_error, handle_errors

logger = logging.getLogger(__name__)


# ============================================================================
# INDUSTRY CONFIGURATIONS
# ============================================================================

class IndustryConfig:
    """Configuration for each industry type."""
    
    INDUSTRIES = {
        'electronics': {
            'name': 'Electronics & Mobile',
            'icon': '📱',
            'fields': {
                'products': [
                    # Basic Fields (All Industries)
                    {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
                    {'name': 'model', 'type': 'text', 'label': 'Model Name', 'required': True},
                    {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
                    {'name': 'category_id', 'type': 'select', 'label': 'Category', 'required': False},
                    {'name': 'supplier_id', 'type': 'select', 'label': 'Supplier', 'required': False},
                    {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
                    {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
                    {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},

                    # Electronics-Specific Fields
                    {'name': 'serial_number', 'type': 'text', 'label': 'Serial Number', 'required': False, 'industry_only': True},
                    {'name': 'imei', 'type': 'text', 'label': 'IMEI', 'required': False, 'industry_only': True},
                    {'name': 'ram_gb', 'type': 'select', 'label': 'RAM (GB)', 'options': [2, 3, 4, 6, 8, 12, 16, 24, 32, 64], 'required': False, 'industry_only': True},
                    {'name': 'storage_gb', 'type': 'select', 'label': 'Storage (GB)', 'options': [16, 32, 64, 128, 256, 512, 1024, 2048], 'required': False, 'industry_only': True},
                    {'name': 'screen_type', 'type': 'select', 'label': 'Screen Type', 'options': ['OLED', 'AMOLED', 'Super AMOLED', 'Dynamic AMOLED', 'TFT', 'TFT LCD', 'IPS LCD', 'PLS LCD', 'LED', 'QLED', 'Mini-LED', 'MicroLED', 'E Ink', 'CRT', 'Other'], 'required': False, 'industry_only': True},
                    {'name': 'screen_size', 'type': 'text', 'label': 'Screen Size (inches)', 'required': False, 'industry_only': True},
                    {'name': 'camera_mp', 'type': 'select', 'label': 'Camera (MP)', 'options': [2, 5, 8, 12, 13, 16, 20, 24, 32, 48, 50, 64, 108, 200], 'required': False, 'industry_only': True},
                    {'name': 'battery_mah', 'type': 'select', 'label': 'Battery (mAh)', 'options': [1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 10000, 20000], 'required': False, 'industry_only': True},
                    {'name': 'color', 'type': 'select', 'label': 'Color', 'options': ['Black', 'White', 'Silver', 'Gold', 'Space Gray', 'Blue', 'Red', 'Green', 'Purple', 'Pink', 'Orange', 'Yellow', 'Gray', 'Rose Gold', 'Midnight Green', 'Pacific Blue', 'Sierra Blue', 'Alpine Green', 'Starlight', 'Graphite', 'Other'], 'required': False, 'industry_only': True},
                    {'name': 'warranty_months', 'type': 'select', 'label': 'Warranty (Months)', 'options': [3, 6, 12, 18, 24, 36], 'required': False, 'industry_only': True},
                    {'name': 'warranty_expiry_date', 'type': 'date', 'label': 'Warranty Expiry', 'required': False, 'industry_only': True},
                    {'name': 'device_condition', 'type': 'select', 'label': 'Condition', 'options': ['New', 'Refurbished', 'Used', 'Like New', 'Good', 'Fair', 'Poor', 'Damaged', 'For Parts'], 'required': False, 'industry_only': True},
                ]
            },
            'features': ['warranty_tracking', 'serial_tracking', 'imei_tracking', 'service_management']
        },
        
        'pharmacy': {
            'name': 'Pharmacy & Medical',
            'icon': '💊',
            'fields': {
                'products': [
                    # Basic Fields
                    {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
                    {'name': 'model', 'type': 'text', 'label': 'Product Name', 'required': True},
                    {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
                    {'name': 'category_id', 'type': 'select', 'label': 'Category', 'required': False},
                    {'name': 'supplier_id', 'type': 'select', 'label': 'Supplier', 'required': False},
                    {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
                    {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
                    {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},

                    # Pharmacy-Specific Fields
                    {'name': 'batch_number', 'type': 'text', 'label': 'Batch Number', 'required': False, 'industry_only': True},
                    {'name': 'expiry_date', 'type': 'date', 'label': 'Expiry Date', 'required': False, 'industry_only': True},
                    {'name': 'manufacturer', 'type': 'text', 'label': 'Manufacturer', 'required': False, 'industry_only': True},
                    {'name': 'dosage', 'type': 'text', 'label': 'Dosage', 'required': False, 'industry_only': True},
                    {'name': 'form', 'type': 'select', 'label': 'Form', 'options': ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Cream', 'Ointment', 'Powder', 'Drop', 'Spray', 'Patch', 'Suppository', 'Inhaler', 'Liquid', 'Gel', 'Lozenge'], 'required': False, 'industry_only': True},
                    {'name': 'requires_prescription', 'type': 'select', 'label': 'Requires Prescription', 'options': ['Yes', 'No'], 'required': False, 'industry_only': True},
                    {'name': 'storage_temp', 'type': 'select', 'label': 'Storage Temperature', 'options': ['Room Temp (15-25°C)', 'Refrigerated (2-8°C)', 'Freezer (-20°C)', 'Cool (8-15°C)', 'Controlled Room (20-25°C)'], 'required': False, 'industry_only': True},
                    {'name': 'generic_name', 'type': 'text', 'label': 'Generic Name', 'required': False, 'industry_only': True},
                ]
            },
            'features': ['expiry_tracking', 'batch_tracking', 'prescription_management']
        },
        
        'toy_shop': {
            'name': 'Toy Shop',
            'icon': '🧸',
            'fields': {
                'products': [
                    # Basic Fields
                    {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
                    {'name': 'model', 'type': 'text', 'label': 'Product Name', 'required': True},
                    {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
                    {'name': 'category_id', 'type': 'select', 'label': 'Category', 'required': False},
                    {'name': 'supplier_id', 'type': 'select', 'label': 'Supplier', 'required': False},
                    {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
                    {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
                    {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},
                    
                    # Toy-Specific Fields
                    {'name': 'age_range', 'type': 'text', 'label': 'Age Range', 'required': False, 'industry_only': True},
                    {'name': 'safety_certs', 'type': 'text', 'label': 'Safety Certifications', 'required': False, 'industry_only': True},
                    {'name': 'battery_required', 'type': 'boolean', 'label': 'Batteries Required', 'required': False, 'industry_only': True},
                    {'name': 'assembly_required', 'type': 'boolean', 'label': 'Assembly Required', 'required': False, 'industry_only': True},
                ]
            },
            'features': ['age_tracking', 'safety_compliance']
        },
        
        'fashion': {
            'name': 'Fashion & Apparel',
            'icon': '👕',
            'fields': {
                'products': [
                    # Basic Fields
                    {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
                    {'name': 'model', 'type': 'text', 'label': 'Product Name', 'required': True},
                    {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
                    {'name': 'category_id', 'type': 'select', 'label': 'Category', 'required': False},
                    {'name': 'supplier_id', 'type': 'select', 'label': 'Supplier', 'required': False},
                    {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
                    {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
                    {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},
                    
                    # Fashion-Specific Fields
                    {'name': 'size', 'type': 'select', 'label': 'Size', 'options': ['XS', 'S', 'M', 'L', 'XL', 'XXL'], 'required': False, 'industry_only': True},
                    {'name': 'material', 'type': 'text', 'label': 'Material', 'required': False, 'industry_only': True},
                    {'name': 'gender', 'type': 'select', 'label': 'Gender', 'options': ['Men', 'Women', 'Unisex', 'Kids'], 'required': False, 'industry_only': True},
                    {'name': 'season', 'type': 'select', 'label': 'Season', 'options': ['Spring', 'Summer', 'Fall', 'Winter', 'All Season'], 'required': False, 'industry_only': True},
                    {'name': 'care_instructions', 'type': 'text', 'label': 'Care Instructions', 'required': False, 'industry_only': True},
                ]
            },
            'features': ['size_variants', 'seasonal_tracking']
        },
        
        'food_beverage': {
            'name': 'Food & Beverage',
            'icon': '🍔',
            'fields': {
                'products': [
                    # Basic Fields
                    {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
                    {'name': 'model', 'type': 'text', 'label': 'Product Name', 'required': True},
                    {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
                    {'name': 'category_id', 'type': 'select', 'label': 'Category', 'required': False},
                    {'name': 'supplier_id', 'type': 'select', 'label': 'Supplier', 'required': False},
                    {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
                    {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
                    {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},
                    
                    # Food & Beverage-Specific Fields
                    {'name': 'ingredients', 'type': 'text', 'label': 'Ingredients', 'required': False, 'industry_only': True},
                    {'name': 'allergens', 'type': 'text', 'label': 'Allergens', 'required': False, 'industry_only': True},
                    {'name': 'nutritional_info', 'type': 'text', 'label': 'Nutritional Info', 'required': False, 'industry_only': True},
                    {'name': 'best_before_date', 'type': 'date', 'label': 'Best Before', 'required': False, 'industry_only': True},
                ]
            },
            'features': ['expiry_tracking', 'allergen_tracking', 'nutrition_labeling']
        },
        
        'general': {
            'name': 'General Retail',
            'icon': '🏪',
            'fields': {
                'products': [
                    # Basic Fields Only
                    {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
                    {'name': 'model', 'type': 'text', 'label': 'Product Name', 'required': True},
                    {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
                    {'name': 'category_id', 'type': 'select', 'label': 'Category', 'required': False},
                    {'name': 'supplier_id', 'type': 'select', 'label': 'Supplier', 'required': False},
                    {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
                    {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
                    {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},
                ]
            },
            'features': []
        }
    }
    
    @classmethod
    def get_industry(cls, industry_type: str) -> Dict:
        """Get industry configuration."""
        return cls.INDUSTRIES.get(industry_type, cls.INDUSTRIES['general'])
    
    @classmethod
    def get_all_industries(cls) -> List[Dict]:
        """Get all industry configurations."""
        return [
            {'type': key, 'name': config['name'], 'icon': config['icon']}
            for key, config in cls.INDUSTRIES.items()
        ]
    
    @classmethod
    def get_fields(cls, industry_type: str, form_type: str = 'products') -> List[Dict]:
        """Get fields for specific industry and form type."""
        industry = cls.get_industry(industry_type)
        return industry['fields'].get(form_type, [])
    
    @classmethod
    def get_basic_fields(cls) -> List[Dict]:
        """Get fields common to all industries."""
        return [
            {'name': 'sku', 'type': 'text', 'label': 'SKU', 'required': True},
            {'name': 'model', 'type': 'text', 'label': 'Product Name', 'required': True},
            {'name': 'barcode', 'type': 'text', 'label': 'Barcode', 'required': False},
            {'name': 'stock', 'type': 'number', 'label': 'Initial Stock', 'required': True, 'default': 0},
            {'name': 'purchase_price', 'type': 'number', 'label': 'Purchase Price', 'required': True},
            {'name': 'selling_price', 'type': 'number', 'label': 'Selling Price', 'required': True},
        ]
    
    @classmethod
    def get_industry_fields(cls, industry_type: str) -> List[Dict]:
        """Get ONLY industry-specific fields (not basic fields)."""
        all_fields = cls.get_fields(industry_type)
        return [f for f in all_fields if f.get('industry_only', False)]


# ============================================================================
# DYNAMIC FORM BUILDER
# ============================================================================

class DynamicFormBuilder:
    """Builds dynamic forms based on industry configuration."""
    
    def __init__(self, parent, industry_type: str, form_type: str = 'products'):
        """
        Initialize dynamic form builder.
        
        Args:
            parent: Parent widget
            industry_type: Current industry type
            form_type: Type of form (products, supplier, etc.)
        """
        self.parent = parent
        self.industry_type = industry_type
        self.form_type = form_type
        self.fields = {}
        self.widgets = {}
        self._boolean_vars = {}  # Track BooleanVars for checkbuttons

        self.config = IndustryConfig.get_industry(industry_type)
        self.field_configs = IndustryConfig.get_fields(industry_type, form_type)
    
    def build_form(self, scrollable_frame: Optional = None) -> Dict[str, Any]:
        """
        Build dynamic form with all fields.
        
        Returns:
            Dictionary of field widgets
        """
        if not CTk_AVAILABLE:
            return self._build_tkinter_form()
        
        container = scrollable_frame if scrollable_frame else self.parent
        
        row = 0
        for field in self.field_configs:
            # get_fields() already returns only fields for this industry
            # No need to filter again
            widget = self._create_field_widget(container, field, row)
            if widget:
                self.widgets[field['name']] = widget
                row += 1
        
        return self.widgets
    
    def _create_field_widget(self, parent, field: Dict, row: int):
        """Create widget for specific field."""
        label = ctk.CTkLabel(
            parent,
            text=field['label'],
            font=ctk.CTkFont(size=12),
            justify='left'
        )
        label.grid(row=row, column=0, padx=10, pady=5, sticky='w')
        
        # Create widget based on field type
        if field['type'] == 'text':
            widget = ctk.CTkEntry(parent, width=300)
            if field.get('default'):
                widget.insert(0, str(field['default']))
        
        elif field['type'] == 'number':
            widget = ctk.CTkEntry(parent, width=300)
            if field.get('default'):
                widget.insert(0, str(field['default']))
        
        elif field['type'] == 'select':
            options = field.get('options', [])

            # Keep CTk behavior aligned with tkinter fallback:
            # category/supplier options should come from DB, not static config.
            if field['name'] in ('category_id', 'supplier_id'):
                try:
                    from database import get_db_cursor
                    with get_db_cursor() as cur:
                        if field['name'] == 'category_id':
                            cur.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name")
                        else:
                            cur.execute("SELECT id, name FROM suppliers WHERE is_active = 1 ORDER BY name")
                        rows = cur.fetchall()
                        options = [f"{row['name']} (ID: {row['id']})" for row in rows]
                except Exception as e:
                    logger.debug(f"Failed to load {field['name']} options for CTk form: {e}")

            # CTkOptionMenu expects at least one value; use empty sentinel if none.
            if not options:
                options = [""]

            if field['name'] in ('category_id', 'supplier_id'):
                # Editable combo for better UX on relation fields.
                widget = ctk.CTkComboBox(
                    parent,
                    values=options,
                    width=300
                )
            else:
                widget = ctk.CTkOptionMenu(
                    parent,
                    values=options,
                    width=300
                )
            if field.get('default'):
                widget.set(field['default'])
        
        elif field['type'] == 'date':
            widget = ctk.CTkEntry(parent, width=300, placeholder_text='YYYY-MM-DD')
        
        elif field['type'] == 'boolean':
            widget = ctk.CTkSwitch(parent, text='')
            if field.get('default'):
                widget.select()
        
        else:
            widget = ctk.CTkEntry(parent, width=300)
        
        widget.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
        
        return widget
    
    def _build_tkinter_form(self, container: Optional = None) -> Dict:
        """Fallback for standard tkinter using ui_theme helpers."""
        from ui_theme import styled_label, styled_entry, combobox
        from database import get_db_cursor

        parent = container if container else self.parent
        row = 0

        for field in self.field_configs:
            # All fields already filtered by industry type via get_fields()

            # Label
            lbl = styled_label(parent, text=f"{field['label']}:")
            lbl.grid(row=row, column=0, padx=10, pady=5, sticky='w')

            # Widget
            if field['type'] == 'select':
                # Populate options from database for category/supplier fields
                options = field.get('options', [])
                
                if field['name'] == 'category_id':
                    try:
                        with get_db_cursor() as cur:
                            cur.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name")
                            categories = cur.fetchall()
                            options = [f"{cat['name']} (ID: {cat['id']})" for cat in categories]
                    except Exception as e:
                        import logging
                        logging.debug(f"Failed to load categories: {e}")
                
                elif field['name'] == 'supplier_id':
                    try:
                        with get_db_cursor() as cur:
                            cur.execute("SELECT id, name FROM suppliers WHERE is_active = 1 ORDER BY name")
                            suppliers = cur.fetchall()
                            options = [f"{sup['name']} (ID: {sup['id']})" for sup in suppliers]
                    except Exception as e:
                        import logging
                        logging.debug(f"Failed to load suppliers: {e}")

                widget = combobox(parent, values=options)
                if field.get('default'):
                    widget.set(field['default'])
            elif field['type'] == 'boolean':
                var = tk.BooleanVar(value=bool(field.get('default', False)))
                self._boolean_vars[field['name']] = var
                widget = ttk.Checkbutton(parent, variable=var, text=field['label'])
            else:
                widget = styled_entry(parent)
                if field.get('default'):
                    widget.insert(0, str(field['default']))
            
            widget.grid(row=row, column=1, padx=10, pady=5, sticky='ew')
            self.widgets[field['name']] = widget
            row += 1
            
        return self.widgets
    
    def get_values(self) -> Dict[str, Any]:
        """Get all form values, supporting both CTk and standard TK widgets."""
        values = {}

        for name, widget in self.widgets.items():
            try:
                # Check if this is a tracked boolean field
                if name in self._boolean_vars:
                    values[name] = self._boolean_vars[name].get()
                elif hasattr(widget, 'get'):
                    values[name] = widget.get()
                elif hasattr(widget, 'curselection'):  # listbox if needed
                    values[name] = widget.get(widget.curselection())
                else:
                    # Fallback for complex widgets or vars
                    pass
            except Exception as e:
                logging.debug(f"Error getting value for {name}: {e}")
                values[name] = ""

        return values
    
    def set_values(self, values: Dict[str, Any]):
        """Set form values (for editing)."""
        for name, value in values.items():
            if name in self.widgets:
                widget = self.widgets[name]
                # Handle boolean fields via BooleanVar
                if name in self._boolean_vars:
                    self._boolean_vars[name].set(bool(value))
                elif isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, 'end')
                    widget.insert(0, str(value))
                elif isinstance(widget, ctk.CTkOptionMenu):
                    widget.set(value)
                elif isinstance(widget, ctk.CTkSwitch):
                    if value:
                        widget.select()
                    else:
                        widget.deselect()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_industry_config(industry_type: str) -> Dict:
    """Get industry configuration."""
    return IndustryConfig.get_industry(industry_type)


def get_industry_fields(industry_type: str) -> List[Dict]:
    """Get fields for specific industry."""
    return IndustryConfig.get_fields(industry_type)


def create_dynamic_form(parent, industry_type: str, form_type: str = 'products'):
    """Create dynamic form for specific industry."""
    return DynamicFormBuilder(parent, industry_type, form_type)


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Unified Data Entry System - Test")
    print("="*60)
    
    # Show all industries
    print("\n📊 Available Industries:")
    for industry in IndustryConfig.get_all_industries():
        print(f"  {industry['icon']} {industry['name']} ({industry['type']})")
    
    # Show fields for each industry
    print("\n📝 Industry-Specific Fields:")
    for industry_type in ['electronics', 'pharmacy', 'toy_shop', 'general']:
        config = IndustryConfig.get_industry(industry_type)
        fields = IndustryConfig.get_industry_fields(industry_type)
        print(f"\n  {config['icon']} {config['name']}:")
        if fields:
            for field in fields:
                print(f"    - {field['label']} ({field['type']})")
        else:
            print(f"    (Basic fields only)")
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)
