"""
PHARMA Industry Service Layer
==============================
Business logic for PHARMACY operations.
Batch tracking, expiry dates, prescriptions, dosage.

This service KNOWS it's for pharma - uses pharma repository.
ZERO confusion about what it does.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from db.base import DatabaseConnection
from db.industries.pharma import (
    PharmaProductRepository,
    PharmaExpiryRepository,
    PharmaPrescriptionRepository,
    PharmaStatsRepository
)
from industry_services.base import BaseService

logger = logging.getLogger(__name__)


class PharmaService(BaseService):
    """
    PHARMA business logic.
    ONLY handles pharmacy operations.
    """
    
    def __init__(self, connection: DatabaseConnection):
        super().__init__(connection)
        
        # Initialize pharma-specific repositories
        self.products = PharmaProductRepository(connection)
        self.expiry = PharmaExpiryRepository(connection)
        self.prescriptions = PharmaPrescriptionRepository(connection)
        self.stats = PharmaStatsRepository(connection)
    
    # ── Product Operations ─────────────────────────────
    
    def add_product(self, data: dict, username: str = "system") -> int:
        """Add a new pharma product with validation."""
        self._validate_product(data)
        
        # Set defaults for pharma
        data.setdefault("status", "active")
        
        product_id = self.products.insert_product(data)
        logger.info(f"Pharma product added: {data.get('model')} Batch: {data.get('batch_number')} (ID: {product_id})")
        return product_id
    
    def update_product(self, model: str, data: dict, username: str = "system") -> bool:
        """Update a pharma product."""
        self._validate_product(data, require_model=False)
        
        update_data = {k: v for k, v in data.items() if k != "model"}
        if not update_data:
            return False
        
        success = self.products.update_product(model, update_data)
        if success:
            logger.info(f"Pharma product updated: {model}")
        return success
    
    def delete_product(self, model: str, username: str = "system") -> bool:
        """Soft-delete a pharma product."""
        success = self.products.delete_product(model)
        if success:
            logger.info(f"Pharma product deleted: {model}")
        return success
    
    def adjust_stock(self, model: str, delta: int, username: str = "system",
                    reason: str = "") -> bool:
        """Adjust pharma product stock."""
        self.validate_not_none(delta, "delta")
        
        success = self.products.adjust_stock(model, delta)
        if success:
            logger.info(f"Pharma stock adjusted: {model} by {delta}")
        return success
    
    def get_all_products(self, active_only: bool = True) -> List[dict]:
        """Get all pharma products."""
        return self.products.fetch_products(active_only=active_only)
    
    def get_product_by_model(self, model: str) -> Optional[dict]:
        """Get a pharma product by model."""
        return self.products.fetch_product_by_model(model)
    
    # ── Expiry Operations ────────────────────────────
    
    def get_expiring_products(self, days: int = 30) -> List[dict]:
        """Get products expiring within N days."""
        return self.expiry.fetch_expiring_products(days)
    
    def get_expired_products(self) -> List[dict]:
        """Get products that have already expired."""
        return self.expiry.fetch_expired_products()
    
    def get_batches(self) -> List[dict]:
        """Get all active batches."""
        return self.expiry.fetch_batches()
    
    def check_expiry_alerts(self, alert_days: int = 30) -> dict:
        """
        Check for expiry alerts and return summary.
        
        Returns:
            dict: Summary of expiry status
        """
        expiring = self.get_expiring_products(alert_days)
        expired = self.get_expired_products()
        
        return {
            "expiring_count": len(expiring),
            "expiring_products": expiring,
            "expired_count": len(expired),
            "expired_products": expired,
            "alert_date": datetime.now().isoformat()
        }
    
    # ── Prescription Operations ──────────────────────
    
    def create_prescription(self, patient_name: str, doctor_name: str,
                           items: List[dict], status: str = "pending") -> int:
        """Create a new prescription."""
        self.validate_non_empty_string(patient_name, "patient_name")
        self.validate_non_empty_string(doctor_name, "doctor_name")
        
        if not items:
            raise ValueError("Prescription must have at least one item")
        
        import json
        data = {
            "patient_name": patient_name,
            "doctor_name": doctor_name,
            "items": json.dumps(items),
            "status": status
        }
        
        rx_id = self.prescriptions.insert_prescription(data)
        logger.info(f"Prescription created: #{rx_id}")
        return rx_id
    
    def get_prescriptions(self, status: Optional[str] = None) -> List[dict]:
        """Get prescriptions, optionally filtered by status."""
        return self.prescriptions.fetch_prescriptions(status=status)
    
    def update_prescription_status(self, rx_id: int, status: str) -> bool:
        """Update prescription status."""
        valid_statuses = ["pending", "approved", "rejected", "completed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        success = self.prescriptions.update_prescription_status(rx_id, status)
        if success:
            logger.info(f"Prescription #{rx_id} status updated: {status}")
        return success
    
    # ── Sales Operations ─────────────────────────────
    # (Pharma uses same sales structure as retail)
    
    # ── Statistics ───────────────────────────────────
    
    def get_stats(self) -> dict:
        """Get pharma dashboard statistics."""
        return self.stats.get_stats()
    
    # ── Validation ───────────────────────────────────
    
    @staticmethod
    def _validate_product(data: dict, require_model: bool = True):
        """Validate pharma product data."""
        if require_model and not data.get("model"):
            raise ValueError("Product must have a 'model' field")
        
        # Validate numeric fields
        for field in ("purchase_price", "selling_price"):
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field}: {data[field]}")
        
        for field in ("stock", "reorder_point"):
            if field in data and data[field] is not None:
                try:
                    int(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field}: {data[field]}")
        
        # Validate expiry date format if provided
        if "expiry_date" in data and data["expiry_date"]:
            try:
                datetime.strptime(str(data["expiry_date"]), "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid expiry_date: {data['expiry_date']}. "
                    f"Must be YYYY-MM-DD format"
                )
        
        # Validate dosage form if provided
        if "dosage_form" in data and data["dosage_form"]:
            valid_forms = [
                "tablet", "capsule", "syrup", "injection",
                "cream", "ointment", "drops", "inhaler"
            ]
            if data["dosage_form"].lower() not in valid_forms:
                raise ValueError(
                    f"Invalid dosage form: {data['dosage_form']}. "
                    f"Must be one of {valid_forms}"
                )
