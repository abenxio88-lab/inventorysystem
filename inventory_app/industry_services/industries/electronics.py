"""
ELECTRONICS Industry Service Layer
===================================
Business logic for ELECTRONICS operations.
Serial numbers, IMEI, warranty, device specs.

This service KNOWS it's for electronics - uses electronics repository.
ZERO confusion about what it does.
"""

import logging
from typing import List, Optional
import re

from db.base import DatabaseConnection
from db.industries.electronics import (
    ElectronicsProductRepository,
    ElectronicsSerialRepository,
    ElectronicsWarrantyRepository,
    ElectronicsStatsRepository
)
from industry_services.base import BaseService

logger = logging.getLogger(__name__)


class ElectronicsService(BaseService):
    """
    ELECTRONICS business logic.
    ONLY handles electronics operations.
    """
    
    def __init__(self, connection: DatabaseConnection):
        super().__init__(connection)
        
        # Initialize electronics-specific repositories
        self.products = ElectronicsProductRepository(connection)
        self.serials = ElectronicsSerialRepository(connection)
        self.warranty = ElectronicsWarrantyRepository(connection)
        self.stats = ElectronicsStatsRepository(connection)
    
    # ── Product Operations ─────────────────────────────
    
    def add_product(self, data: dict, username: str = "system") -> int:
        """Add a new electronics product with validation."""
        self._validate_product(data)
        
        # Set defaults for electronics
        data.setdefault("status", "active")
        data.setdefault("device_condition", "new")
        
        product_id = self.products.insert_product(data)
        logger.info(f"Electronics product added: {data.get('model')} (ID: {product_id})")
        return product_id
    
    def update_product(self, model: str, data: dict, username: str = "system") -> bool:
        """Update an electronics product."""
        self._validate_product(data, require_model=False)
        
        update_data = {k: v for k, v in data.items() if k != "model"}
        if not update_data:
            return False
        
        success = self.products.update_product(model, update_data)
        if success:
            logger.info(f"Electronics product updated: {model}")
        return success
    
    def delete_product(self, model: str, username: str = "system") -> bool:
        """Soft-delete an electronics product."""
        success = self.products.delete_product(model)
        if success:
            logger.info(f"Electronics product deleted: {model}")
        return success
    
    def adjust_stock(self, model: str, delta: int, username: str = "system",
                    reason: str = "") -> bool:
        """Adjust electronics product stock."""
        self.validate_not_none(delta, "delta")
        
        success = self.products.adjust_stock(model, delta)
        if success:
            logger.info(f"Electronics stock adjusted: {model} by {delta}")
        return success
    
    def get_all_products(self, active_only: bool = True) -> List[dict]:
        """Get all electronics products."""
        return self.products.fetch_products(active_only=active_only)
    
    def get_product_by_model(self, model: str) -> Optional[dict]:
        """Get an electronics product by model."""
        return self.products.fetch_product_by_model(model)
    
    # ── Serial Number Operations ─────────────────────
    
    def register_serial_number(self, product_id: int, serial_number: str,
                              warranty_months: int = None) -> int:
        """Register a new serial number for a product."""
        self.validate_not_none(product_id, "product_id")
        self.validate_non_empty_string(serial_number, "serial_number")
        
        data = {
            "product_id": product_id,
            "serial_number": serial_number,
            "status": "in_stock"
        }
        
        # Calculate warranty end date if months provided
        if warranty_months:
            from datetime import datetime, timedelta
            start_date = datetime.now()
            end_date = start_date + timedelta(days=warranty_months * 30)
            data["warranty_start"] = start_date.isoformat()
            data["warranty_end"] = end_date.isoformat()
        
        sn_id = self.serials.insert_serial_number(data)
        logger.info(f"Serial number registered: {serial_number}")
        return sn_id
    
    def get_serial_number(self, serial_number: str) -> Optional[dict]:
        """Get serial number details."""
        return self.serials.fetch_by_serial(serial_number)
    
    def update_serial_status(self, serial_number: str, status: str) -> bool:
        """Update serial number status."""
        valid_statuses = ["in_stock", "sold", "returned", "warranty", "disposed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        success = self.serials.update_serial_status(serial_number, status)
        if success:
            logger.info(f"Serial number status updated: {serial_number} -> {status}")
        return success
    
    # ── Warranty Operations ──────────────────────────
    
    def get_expiring_warranties(self, days: int = 30) -> List[dict]:
        """Get products with warranties expiring soon."""
        return self.warranty.fetch_expiring_warranties(days)
    
    def get_expired_warranties(self) -> List[dict]:
        """Get products with expired warranties."""
        return self.warranty.fetch_expired_warranties()
    
    # ── Sales Operations ─────────────────────────────
    # (Electronics uses same sales structure as retail, but with serial tracking)
    
    # ── Statistics ───────────────────────────────────
    
    def get_stats(self) -> dict:
        """Get electronics dashboard statistics."""
        return self.stats.get_stats()
    
    # ── Validation ───────────────────────────────────
    
    @staticmethod
    def _validate_product(data: dict, require_model: bool = True):
        """Validate electronics product data."""
        if require_model and not data.get("model"):
            raise ValueError("Product must have a 'model' field")
        
        # Validate numeric fields
        for field in ("purchase_price", "selling_price"):
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field}: {data[field]}")
        
        for field in ("stock", "reorder_point", "warranty_months"):
            if field in data and data[field] is not None:
                try:
                    int(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field}: {data[field]}")
        
        # Validate IMEI format if provided (15 digits)
        if "imei" in data and data["imei"]:
            imei = str(data["imei"])
            if not re.match(r'^\d{15}$', imei):
                raise ValueError(f"Invalid IMEI: {imei}. Must be 15 digits")
        
        # Validate device condition if provided
        if "device_condition" in data and data["device_condition"]:
            valid_conditions = ["new", "refurbished", "used", "damaged"]
            if data["device_condition"] not in valid_conditions:
                raise ValueError(
                    f"Invalid condition: {data['device_condition']}. "
                    f"Must be one of {valid_conditions}"
                )
