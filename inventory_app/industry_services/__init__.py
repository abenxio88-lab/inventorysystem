"""
Services Package
=================
Industry-specific service layers.
Each industry has its own service - completely independent.

Usage:
    from services import get_industry_service
    
    service = get_industry_service("electronics", connection)
    products = service.get_all_products()
"""

from db.base import DatabaseConnection
from .base import BaseService
from .industries.retail import RetailService
from .industries.electronics import ElectronicsService
from .industries.pharma import PharmaService

# Registry of all industry services
_SERVICE_REGISTRY = {
    "retail": RetailService,
    "electronics": ElectronicsService,
    "pharma": PharmaService,
}


def get_industry_service(industry_id: str, connection: DatabaseConnection) -> BaseService:
    """
    Get service instance for a specific industry.
    
    Args:
        industry_id: Industry identifier (e.g., "retail", "electronics", "pharma")
        connection: DatabaseConnection instance
        
    Returns:
        BaseService: Service instance for the industry
        
    Raises:
        ValueError: If industry_id is not found
    """
    if industry_id not in _SERVICE_REGISTRY:
        raise ValueError(
            f"Unknown industry: {industry_id}. "
            f"Available: {list(_SERVICE_REGISTRY.keys())}"
        )
    
    # Create a NEW service instance
    return _SERVICE_REGISTRY[industry_id](connection)


def get_all_industry_services() -> list:
    """Get list of all available industry service IDs."""
    return list(_SERVICE_REGISTRY.keys())


# ============================================================
# BACKWARD COMPATIBILITY - Import legacy svc singleton
# ============================================================
# The old services.py module exports a 'svc' singleton.
# We re-export it here so existing imports continue to work.
# Gradual migration path: update imports to use new system.
try:
    from services import svc  # This will import from the OLD services.py
except ImportError:
    # If old services.py doesn't exist, create a placeholder
    class _ServicePlaceholder:
        """Placeholder until full migration to new service architecture."""
        pass
    svc = _ServicePlaceholder()
