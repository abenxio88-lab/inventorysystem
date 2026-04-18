"""
Base Service Module
====================
Defines the base service class that ALL industry services extend.
Contains common business logic and validation.

NO industry-specific logic here - just shared foundations.
"""

import logging
from typing import Optional
from abc import ABC, abstractmethod

from db.base import DatabaseConnection

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Abstract base class for ALL industry services.
    Every industry service EXTENDS this - no duplication.
    """
    
    def __init__(self, connection: DatabaseConnection):
        """Initialize with database connection."""
        self.conn = connection
    
    @abstractmethod
    def get_stats(self) -> dict:
        """Get industry-specific statistics. Must be implemented by each industry."""
        pass
    
    @staticmethod
    def validate_positive(value, field_name: str):
        """Validate that a value is positive."""
        if value is not None and value < 0:
            raise ValueError(f"{field_name} must be positive, got {value}")
    
    @staticmethod
    def validate_not_none(value, field_name: str):
        """Validate that a value is not None."""
        if value is None:
            raise ValueError(f"{field_name} is required")
    
    @staticmethod
    def validate_non_empty_string(value, field_name: str):
        """Validate that a value is a non-empty string."""
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
