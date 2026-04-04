"""
Custom Exception Classes for Mintaka Sphere Inventory System
=============================================================
Provides domain-specific exceptions for better error handling and debugging.

USAGE:
    from exceptions import (
        InventoryError, InsufficientStockError, ProductNotFoundError,
        handle_inventory_exception
    )

    try:
        svc.sales.create_order(order_data, items)
    except InsufficientStockError as e:
        messagebox.showerror("Stock Error", str(e))
    except InventoryError as e:
        messagebox.showerror("Inventory Error", str(e))
"""


class InventoryBaseError(Exception):
    """Base exception for all inventory system errors."""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


# ── Product/Stock Exceptions ──────────────────────────────

class ProductNotFoundError(InventoryBaseError):
    """Raised when a product cannot be found."""
    def __init__(self, model: str = None, product_id: int = None):
        identifier = f"model='{model}'" if model else f"id={product_id}"
        super().__init__(
            message=f"Product not found: {identifier}",
            error_code="PRODUCT_NOT_FOUND",
            details={"model": model, "product_id": product_id}
        )


class InsufficientStockError(InventoryBaseError):
    """Raised when there's not enough stock for an operation."""
    def __init__(self, model: str, requested: int, available: int):
        super().__init__(
            message=f"Insufficient stock for '{model}': requested {requested}, available {available}",
            error_code="INSUFFICIENT_STOCK",
            details={
                "model": model,
                "requested_quantity": requested,
                "available_quantity": available
            }
        )


class InvalidProductDataError(InventoryBaseError):
    """Raised when product data validation fails."""
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(
            message=message,
            error_code="INVALID_PRODUCT_DATA",
            details={"field": field, "value": value}
        )


class DuplicateProductError(InventoryBaseError):
    """Raised when attempting to create a duplicate product."""
    def __init__(self, model: str):
        super().__init__(
            message=f"Product already exists: model='{model}'",
            error_code="DUPLICATE_PRODUCT",
            details={"model": model}
        )


# ── Sales/Order Exceptions ────────────────────────────────

class OrderNotFoundError(InventoryBaseError):
    """Raised when an order cannot be found."""
    def __init__(self, order_id: int, order_type: str = "sales"):
        super().__init__(
            message=f"{order_type.title()} order not found: id={order_id}",
            error_code="ORDER_NOT_FOUND",
            details={"order_id": order_id, "order_type": order_type}
        )


class InvalidOrderDataError(InventoryBaseError):
    """Raised when order data validation fails."""
    pass


class OrderValidationError(InventoryBaseError):
    """Raised when an order fails business rule validation."""
    pass


# ── Location/Transfer Exceptions ──────────────────────────

class LocationNotFoundError(InventoryBaseError):
    """Raised when a location cannot be found."""
    def __init__(self, code: str = None, location_id: int = None):
        identifier = f"code='{code}'" if code else f"id={location_id}"
        super().__init__(
            message=f"Location not found: {identifier}",
            error_code="LOCATION_NOT_FOUND",
            details={"code": code, "location_id": location_id}
        )


class InvalidTransferError(InventoryBaseError):
    """Raised when a stock transfer is invalid."""
    pass


# ── Supplier/Customer Exceptions ──────────────────────────

class SupplierNotFoundError(InventoryBaseError):
    """Raised when a supplier cannot be found."""
    def __init__(self, code: str = None, supplier_id: int = None):
        identifier = f"code='{code}'" if code else f"id={supplier_id}"
        super().__init__(
            message=f"Supplier not found: {identifier}",
            error_code="SUPPLIER_NOT_FOUND",
            details={"code": code, "supplier_id": supplier_id}
        )


class CustomerNotFoundError(InventoryBaseError):
    """Raised when a customer cannot be found."""
    def __init__(self, customer_id: int = None):
        super().__init__(
            message=f"Customer not found: id={customer_id}",
            error_code="CUSTOMER_NOT_FOUND",
            details={"customer_id": customer_id}
        )


# ── User/Auth Exceptions ──────────────────────────────────

class UserNotFoundError(InventoryBaseError):
    """Raised when a user cannot be found."""
    def __init__(self, username: str = None, user_id: int = None):
        identifier = f"username='{username}'" if username else f"id={user_id}"
        super().__init__(
            message=f"User not found: {identifier}",
            error_code="USER_NOT_FOUND",
            details={"username": username, "user_id": user_id}
        )


class AuthenticationError(InventoryBaseError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED"
        )


class PermissionDeniedError(InventoryBaseError):
    """Raised when user lacks required permissions."""
    def __init__(self, permission: str = None, action: str = None):
        super().__init__(
            message=f"Permission denied: {permission or action}",
            error_code="PERMISSION_DENIED",
            details={"permission": permission, "action": action}
        )


# ── Invoice/Payment Exceptions ────────────────────────────

class InvoiceNotFoundError(InventoryBaseError):
    """Raised when an invoice cannot be found."""
    def __init__(self, invoice_id: int = None, invoice_number: str = None):
        identifier = f"number='{invoice_number}'" if invoice_number else f"id={invoice_id}"
        super().__init__(
            message=f"Invoice not found: {identifier}",
            error_code="INVOICE_NOT_FOUND",
            details={"invoice_id": invoice_id, "invoice_number": invoice_number}
        )


class PaymentError(InventoryBaseError):
    """Raised when a payment operation fails."""
    pass


# ── Return/RMA Exceptions ─────────────────────────────────

class ReturnNotFoundError(InventoryBaseError):
    """Raised when a return/RMA cannot be found."""
    def __init__(self, return_id: int = None):
        super().__init__(
            message=f"Return not found: id={return_id}",
            error_code="RETURN_NOT_FOUND",
            details={"return_id": return_id}
        )


class InvalidReturnError(InventoryBaseError):
    """Raised when a return fails validation."""
    pass


# ── Database/Infrastructure Exceptions ────────────────────

class DatabaseError(InventoryBaseError):
    """Raised when a database operation fails."""
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details={"original_error": str(original_exception) if original_exception else None}
        )
        self.original_exception = original_exception


class ConnectionError(InventoryBaseError):
    """Raised when database connection fails."""
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR"
        )


class MigrationError(InventoryBaseError):
    """Raised when schema migration fails."""
    def __init__(self, message: str, from_version: int = None, to_version: int = None):
        super().__init__(
            message=message,
            error_code="MIGRATION_ERROR",
            details={"from_version": from_version, "to_version": to_version}
        )


# ── Validation Helpers ────────────────────────────────────

def validate_not_none(**kwargs):
    """Validate that specified kwargs are not None.
    
    Usage:
        validate_not_none(product_id=product_id, quantity=quantity)
    """
    for name, value in kwargs.items():
        if value is None:
            raise ValueError(f"'{name}' cannot be None")


def validate_positive(**kwargs):
    """Validate that numeric kwargs are positive.
    
    Usage:
        validate_positive(quantity=quantity, price=price)
    """
    for name, value in kwargs.items():
        if value is not None and value <= 0:
            raise ValueError(f"'{name}' must be positive, got {value}")


def validate_non_empty_string(**kwargs):
    """Validate that string kwargs are not empty.
    
    Usage:
        validate_non_empty_string(model=model, name=name)
    """
    for name, value in kwargs.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"'{name}' must be a non-empty string")


# ── Exception Handler Decorator ───────────────────────────

def handle_inventory_exception(func):
    """Decorator to catch and log inventory exceptions uniformly.
    
    Usage:
        @handle_inventory_exception
        def create_product(data):
            ...
    """
    import logging
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InventoryBaseError as e:
            logging.error(
                f"Inventory Error [{e.error_code}]: {e.message}",
                extra={"details": e.details}
            )
            raise
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise DatabaseError(f"Unexpected error in {func.__name__}: {e}", original_exception=e)
    
    return wrapper
