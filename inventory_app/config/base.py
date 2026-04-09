"""
Base Configuration Module
==========================
Defines the configuration structure that ALL industries follow.
Each industry EXTENDS this base config.

NO duplication - just the base structure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FieldConfig:
    """
    Configuration for a single form field.
    Drives form building and database validation.
    """
    label: str                          # Display label
    type: str                           # text, number, select, date, boolean, email, textarea
    required: bool = False              # Is field required?
    default: any = None                 # Default value
    min: float = None                   # Min value (for numbers)
    max: float = None                   # Max value (for numbers)
    options: List[str] = None           # Options for select fields
    source: str = None                  # Database table for dynamic options
    pattern: str = None                 # Regex pattern for validation
    placeholder: str = None             # Placeholder text
    unique: bool = False                # Must be unique in database?
    tab: str = "General"                # Which tab in multi-tab form?


@dataclass
class IndustryConfig:
    """
    Base configuration for ALL industries.
    Each industry inherits from this and adds its specific settings.
    """
    
    # Core settings (all industries have these)
    industry_id: str
    industry_name: str
    description: str
    icon: str
    color: str
    
    # Tab control (NO optional - tabs are shown or hidden)
    core_tabs: List[str] = field(default_factory=list)
    industry_tabs: List[str] = field(default_factory=list)
    hidden_tabs: List[str] = field(default_factory=list)
    
    # Field definitions (drives forms and validation)
    product_fields: Dict[str, FieldConfig] = field(default_factory=dict)
    supplier_fields: Dict[str, FieldConfig] = field(default_factory=dict)
    customer_fields: Dict[str, FieldConfig] = field(default_factory=dict)
    
    # Business rules
    default_tax_rate: float = 0.0
    default_currency: str = "PKR"
    low_stock_threshold: int = 10
    
    def validate(self) -> bool:
        """Validate configuration completeness."""
        if not self.industry_id:
            raise ValueError("industry_id is required")
        if not self.industry_name:
            raise ValueError("industry_name is required")
        if not self.icon:
            raise ValueError("icon is required")
        if not self.color:
            raise ValueError("color is required")
        return True
    
    def get_visible_tabs(self) -> List[str]:
        """Get list of tabs that should be shown for this industry."""
        all_tabs = self.core_tabs + self.industry_tabs
        # Remove hidden tabs
        return [tab for tab in all_tabs if tab not in self.hidden_tabs]
    
    def is_tab_visible(self, tab_name: str) -> bool:
        """Check if a specific tab should be visible."""
        return tab_name not in self.hidden_tabs and tab_name in (self.core_tabs + self.industry_tabs)
