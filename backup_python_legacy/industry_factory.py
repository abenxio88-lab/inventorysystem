"""
Industry Factory / Router
===========================
Creates and manages industry-specific instances.
Clean separation - NO mixing of industries.

This is the ONLY place that decides which industry to use.
Everything else just asks the factory.
"""

import logging
from typing import Optional

from db.base import DatabaseConnection
from config import get_industry_config, IndustryConfig
from industry_services import get_industry_service, BaseService

logger = logging.getLogger(__name__)


class IndustryFactory:
    """
    Factory for creating industry-specific components.
    ONE factory knows ALL industries - individual industries know only themselves.
    """
    
    def __init__(self):
        """Initialize factory (stateless, no industry preference)."""
        self._cache = {}
    
    def create_industry(
        self, 
        industry_id: str, 
        connection: DatabaseConnection
    ) -> dict:
        """
        Create a complete industry instance with config and service.
        
        Args:
            industry_id: Industry identifier
            connection: DatabaseConnection instance
            
        Returns:
            dict: {
                "config": IndustryConfig,
                "service": BaseService,
                "industry_id": str
            }
        """
        # Check cache first
        cache_key = f"{industry_id}_{id(connection)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Create industry components
        try:
            config = get_industry_config(industry_id)
            service = get_industry_service(industry_id, connection)
            
            industry = {
                "config": config,
                "service": service,
                "industry_id": industry_id
            }
            
            # Cache for future use
            self._cache[cache_key] = industry
            
            logger.info(f"Industry created: {industry_id}")
            return industry
            
        except ValueError as e:
            logger.error(f"Failed to create industry '{industry_id}': {e}")
            raise
    
    def get_config(self, industry_id: str) -> IndustryConfig:
        """Get configuration for an industry (without service)."""
        return get_industry_config(industry_id)
    
    def get_service(
        self, 
        industry_id: str, 
        connection: DatabaseConnection
    ) -> BaseService:
        """Get service for an industry (without config)."""
        return get_industry_service(industry_id, connection)
    
    def get_all_industries(self) -> list:
        """Get list of all available industry IDs."""
        from config import get_all_industries
        return get_all_industries()
    
    def clear_cache(self):
        """Clear cached industry instances."""
        self._cache.clear()
        logger.info("Industry factory cache cleared")


# Singleton factory instance
_factory = IndustryFactory()


def get_factory() -> IndustryFactory:
    """Get the singleton factory instance."""
    return _factory


def create_industry(industry_id: str, connection: DatabaseConnection) -> dict:
    """Convenience function to create an industry instance."""
    return _factory.create_industry(industry_id, connection)


def get_current_industry(connection: DatabaseConnection) -> dict:
    """
    Get the currently active industry from database settings.
    
    Returns:
        dict: Current industry instance with config and service
    """
    from db.core import SettingsRepository
    
    settings = SettingsRepository(connection)
    industry_id = settings.get_industry_type()
    
    return _factory.create_industry(industry_id, connection)
