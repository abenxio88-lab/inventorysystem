"""
RETAIL Industry Service Layer
==============================
Business logic for RETAIL operations.
Simple products, basic sales, customers.

This service KNOWS it's for retail - uses retail repository.
ZERO confusion about what it does.
"""

import logging
from typing import List, Optional

from db.base import DatabaseConnection
from db.industries.retail import (
    RetailProductRepository,
    RetailSalesRepository,
    RetailStatsRepository
)
from industry_services.base import BaseService

logger = logging.getLogger(__name__)


class RetailService(BaseService):
    """
    RETAIL business logic.
    ONLY handles retail operations.
    """
    
    def __init__(self, connection: DatabaseConnection):
        super().__init__(connection)
        
        # Initialize retail-specific repositories
        self.products = RetailProductRepository(connection)
        self.sales = RetailSalesRepository(connection)
        self.stats = RetailStatsRepository(connection)
    
    # ── Product Operations ─────────────────────────────
    
    def add_product(self, data: dict, username: str = "system") -> int:
        """Add a new retail product with validation."""
        self._validate_product(data)
        
        # Set defaults for retail
        data.setdefault("status", "active")
        
        product_id = self.products.insert_product(data)
        logger.info(f"Retail product added: {data.get('model')} (ID: {product_id})")
        return product_id
    
    def update_product(self, model: str, data: dict, username: str = "system") -> bool:
        """Update a retail product."""
        self._validate_product(data, require_model=False)
        
        # Remove model from update data (used as identifier)
        update_data = {k: v for k, v in data.items() if k != "model"}
        if not update_data:
            return False
        
        success = self.products.update_product(model, update_data)
        if success:
            logger.info(f"Retail product updated: {model}")
        return success
    
    def delete_product(self, model: str, username: str = "system") -> bool:
        """Soft-delete a retail product."""
        success = self.products.delete_product(model)
        if success:
            logger.info(f"Retail product deleted: {model}")
        return success
    
    def adjust_stock(self, model: str, delta: int, username: str = "system",
                    reason: str = "") -> bool:
        """Adjust retail product stock."""
        self.validate_not_none(delta, "delta")
        
        success = self.products.adjust_stock(model, delta)
        if success:
            logger.info(f"Retail stock adjusted: {model} by {delta}")
        return success
    
    def get_all_products(self, active_only: bool = True) -> List[dict]:
        """Get all retail products."""
        return self.products.fetch_products(active_only=active_only)
    
    def get_product_by_model(self, model: str) -> Optional[dict]:
        """Get a retail product by model."""
        return self.products.fetch_product_by_model(model)
    
    # ── Sales Operations ─────────────────────────────
    
    def create_sale(self, order_data: dict, items: List[dict], 
                   username: str = "system") -> int:
        """Create a retail sale with stock deduction."""
        if not items:
            raise ValueError("Sale must have at least one item")
        
        # Validate stock availability
        for item in items:
            product = self.products.fetch_product_by_id(item.get("product_id", 0))
            if not product:
                raise ValueError(f"Product not found: {item.get('product_id')}")
            
            if product["stock"] < item.get("quantity", 0):
                raise ValueError(
                    f"Insufficient stock for {product['model']}. "
                    f"Available: {product['stock']}, Requested: {item.get('quantity')}"
                )
        
        # Create the sale
        order_data.setdefault("status", "confirmed")
        order_id = self.sales.insert_sales_order(order_data, items)
        
        # Deduct stock
        for item in items:
            product = self.products.fetch_product_by_id(item.get("product_id", 0))
            if product:
                self.products.adjust_stock(
                    product["model"], 
                    -item.get("quantity", 0)
                )
        
        logger.info(f"Retail sale created: #{order_id}")
        return order_id
    
    def get_all_sales(self, status: Optional[str] = None) -> List[dict]:
        """Get all retail sales."""
        return self.sales.fetch_sales_orders(status=status)
    
    # ── Statistics ───────────────────────────────────
    
    def get_stats(self) -> dict:
        """Get retail dashboard statistics."""
        return self.stats.get_stats()
    
    # ── Validation ───────────────────────────────────
    
    @staticmethod
    def _validate_product(data: dict, require_model: bool = True):
        """Validate retail product data."""
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
