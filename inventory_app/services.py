"""
Service Layer — Business Logic
===============================
This module sits between the UI and the database.
UI components call these service methods; services call InventoryDB.

RULES:
  - Services contain VALIDATION and BUSINESS LOGIC only.
  - Services NEVER touch UI (no messagebox, no tkinter).
  - After every write method the caller (UI) is responsible for
    refreshing its display through its own refresh_from_db().
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from database import db, InventoryDB, get_db_cursor
from exceptions import (
    ProductNotFoundError, InsufficientStockError, InvalidProductDataError,
    OrderNotFoundError, InvalidOrderDataError, LocationNotFoundError,
    SupplierNotFoundError, CustomerNotFoundError, validate_not_none,
    validate_positive, validate_non_empty_string
)

logger = logging.getLogger(__name__)


class InventoryService:
    """Business logic for products / inventory."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    # ── Read ──────────────────────────────────────────────

    def get_all_products(self, active_only: bool = True) -> List[dict]:
        return self.db.fetch_products(active_only=active_only)

    def get_product_by_model(self, model: str) -> Optional[dict]:
        return self.db.fetch_product_by_model(model)

    def get_product_by_id(self, product_id: int) -> Optional[dict]:
        product = self.db.fetch_product_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id=product_id)
        return product

    def get_low_stock_products(self) -> List[dict]:
        """Return products at or below reorder point."""
        all_products = self.db.fetch_products(active_only=True)
        return [p for p in all_products if p.get("stock", 0) <= p.get("reorder_point", 5)]

    # ── Write ─────────────────────────────────────────────

    def add_product(self, data: dict, username: str = "system") -> int:
        """Validate and insert a new product. Returns product id."""
        self._validate_product(data)
        # Ensure status defaults
        data.setdefault("status", "active")
        data.setdefault("created_at", datetime.now().isoformat())
        product_id = self.db.insert_product(data)
        self.db.audit_event(username, "create_product", "products", product_id,
                            f"Created product: {data.get('model')}")
        logger.info(f"Product created: {data.get('model')} (id={product_id})")
        return product_id

    def update_product(self, model: str, data: dict, username: str = "system") -> bool:
        """Validate and update an existing product."""
        self._validate_product(data, require_model=False)
        # Remove model from update data if present (used as identifier)
        update_data = {k: v for k, v in data.items() if k != "model"}
        if not update_data:
            return False
        update_data["updated_at"] = datetime.now().isoformat()
        success = self.db.update_product(model, update_data)
        if success:
            self.db.audit_event(username, "update_product", "products", None,
                                f"Updated product: {model}")
            logger.info(f"Product updated: {model}")
        return success

    def upsert_product(self, data: dict, username: str = "system") -> int:
        """Insert or update a product by model name."""
        self._validate_product(data)
        data.setdefault("status", "active")
        product_id = self.db.upsert_product(data)
        self.db.audit_event(username, "upsert_product", "products", product_id,
                            f"Upserted product: {data.get('model')}")
        return product_id

    def delete_product(self, model: str, username: str = "system", hard: bool = False) -> bool:
        """Soft-delete by default. Set hard=True to permanently remove."""
        if hard:
            success = self.db.hard_delete_product(model)
        else:
            success = self.db.delete_product(model)
        if success:
            self.db.audit_event(username, "delete_product", "products", None,
                                f"Deleted product: {model}")
            logger.info(f"Product deleted: {model}")
        return success

    def adjust_stock(self, model: str, delta: int, username: str = "system",
                     reason: str = "") -> bool:
        """Add or subtract from stock. delta can be negative."""
        success = self.db.adjust_stock(model, delta)
        if success:
            self.db.audit_event(username, "adjust_stock", "products", None,
                                f"Stock adjusted: {model} by {delta}. Reason: {reason}")
            logger.info(f"Stock adjusted: {model} by {delta}")
        return success

    def set_stock(self, model: str, quantity: int, username: str = "system",
                  reason: str = "") -> bool:
        """Set absolute stock quantity."""
        success = self.db.set_stock(model, quantity)
        if success:
            self.db.audit_event(username, "set_stock", "products", None,
                                f"Stock set: {model} to {quantity}. Reason: {reason}")
            logger.info(f"Stock set: {model} to {quantity}")
        return success

    # ── Validation ────────────────────────────────────────

    @staticmethod
    def _validate_product(data: dict, require_model: bool = True):
        if require_model and not data.get("model"):
            raise ValueError("Product must have a 'model' field")
        # Numeric field validation
        for field in ("purchase_price", "selling_price"):
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field}: {data[field]}")
        for field in ("stock", "min_stock", "reorder_point", "warranty_months"):
            if field in data and data[field] is not None:
                try:
                    int(data[field])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid {field}: {data[field]}")

    def resolve_category_display(self, category_id) -> str:
        """Return human-friendly category text for tree/form.

        This replaces direct SQL calls in the UI layer.
        """
        if category_id is None:
            return ""
        try:
            cid_int = int(category_id)
            category = self.db.fetch_category_by_id(cid_int)
            if category and category.get("name"):
                return f"{category['name']} (ID: {cid_int})"
        except Exception:
            pass
        return str(category_id)

    def resolve_supplier_display(self, supplier_id) -> str:
        """Return human-friendly supplier text for tree/form.

        This replaces direct SQL calls in the UI layer.
        """
        if supplier_id is None:
            return ""
        try:
            sid_int = int(supplier_id)
            supplier = self.db.fetch_supplier_by_id(sid_int)
            if supplier and supplier.get("name"):
                return f"{supplier['name']} (ID: {sid_int})"
        except Exception:
            pass
        return str(supplier_id)

    def parse_related_id(self, field_name: str, raw_value) -> int:
        """
        Normalize category/supplier input to an integer ID.
        Accepts:
        - "Name (ID: 12)"
        - "12"
        - "Name" (resolved via DB)

        This replaces direct SQL calls in the UI layer.
        """
        if raw_value is None:
            return None

        text = str(raw_value).strip()
        if not text:
            return None

        # Pattern: "Name (ID: 12)"
        if "ID:" in text:
            try:
                import re
                match = re.search(r'ID:\s*(\d+)', text)
                if match:
                    return int(match.group(1))
            except Exception:
                pass

        # Direct numeric ID
        if text.isdigit():
            return int(text)

        # Name lookup fallback - only allow specific known tables (security: prevent SQL injection)
        if field_name == "category_id":
            table = "categories"
        elif field_name == "supplier_id":
            table = "suppliers"
        else:
            raise ValueError(f"Unsupported field for ID resolution: {field_name}")

        try:
            result_id = self.db.fetch_id_by_name(table, text)
            if result_id is not None:
                return int(result_id)
        except Exception:
            pass

        label_text = "Category" if field_name == "category_id" else "Supplier"
        raise ValueError(
            f"{label_text} '{text}' is invalid. Please select a value like 'Name (ID: X)' "
            f"or enter a valid {label_text.lower()} ID."
        )


class SalesService:
    """Business logic for sales orders."""

    def __init__(self, database: Optional[InventoryDB] = None,
                 inventory_svc: Optional[InventoryService] = None):
        self.db = database or InventoryDB()
        self.inventory = inventory_svc or InventoryService(database)

    def get_all_orders(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_sales_orders(status=status)

    def get_order_items(self, order_id: int) -> List[dict]:
        return self.db.fetch_sales_order_items(order_id)

    def create_order(self, order_data: dict, items: List[dict],
                     username: str = "system") -> int:
        """Create a sales order and deduct stock."""
        if not items:
            raise InvalidOrderDataError("Sales order must have at least one item")

        # Validate stock availability before creating order
        for item in items:
            product_id = item.get("product_id")
            if not product_id:
                raise InvalidOrderDataError("Order item must have a product_id")
                
            product = self.inventory.get_product_by_id(product_id)
            if not product:
                raise ProductNotFoundError(product_id=product_id)
                
            requested_qty = item.get("quantity", 0)
            if requested_qty <= 0:
                raise InvalidOrderDataError(f"Order quantity must be positive, got {requested_qty}")
                
            if product["stock"] < requested_qty:
                raise InsufficientStockError(
                    model=product["model"],
                    requested=requested_qty,
                    available=product["stock"]
                )

        order_data.setdefault("order_date", datetime.now().isoformat())
        order_data.setdefault("status", "confirmed")
        order_data.setdefault("created_by", username)

        order_id = self.db.insert_sales_order(order_data, items)

        # Deduct stock
        for item in items:
            product = self.inventory.get_product_by_id(item.get("product_id", 0))
            if product:
                self.inventory.adjust_stock(
                    product["model"],
                    -item.get("quantity", 0),
                    username=username,
                    reason=f"Sales order #{order_id}"
                )

        self.db.audit_event(username, "create_sales_order", "sales_orders", order_id,
                            f"Created order with {len(items)} items")
        logger.info(f"Sales order created: #{order_id}")
        return order_id

    def delete_order(self, order_id: int, username: str = "system") -> bool:
        """Delete a sales order and restore stock."""
        items = self.get_order_items(order_id)
        if not items:
            raise OrderNotFoundError(order_id, order_type="sales")
            
        success = self.db.delete_sales_order(order_id)
        if success:
            # Restore stock
            for item in items:
                product = self.inventory.get_product_by_id(item.get("product_id", 0))
                if product:
                    self.inventory.adjust_stock(
                        product["model"],
                        item.get("quantity", 0),
                        username=username,
                        reason=f"Deleted sales order #{order_id}"
                    )
            self.db.audit_event(username, "delete_sales_order", "sales_orders", order_id)
            logger.info(f"Sales order deleted: #{order_id}")
        return success

    def update_order_status(self, order_id: int, status: str,
                            payment_status: Optional[str] = None,
                            username: str = "system") -> bool:
        """Update the status and/or payment status of a sales order."""
        updates: dict = {}
        if status:
            updates["status"] = status
        if payment_status:
            updates["payment_status"] = payment_status
        if not updates:
            return False
        success = self.db.update_sales_order(order_id, updates)
        if success:
            self.db.audit_event(username, "update_sales_order", "sales_orders", order_id,
                                f"Updated order #{order_id}: {updates}")
            logger.info(f"Sales order updated: #{order_id} -> {updates}")
        return success


class LocationService:
    """Business logic for locations/warehouses."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_all_locations(self, active_only: bool = True) -> List[dict]:
        return self.db.fetch_locations(active_only=active_only)

    def add_location(self, data: dict, username: str = "system") -> int:
        validate_non_empty_string(code=data.get("code"), name=data.get("name"))
        location_id = self.db.insert_location(data)
        self.db.audit_event(username, "create_location", "locations", location_id,
                            f"Created location: {data['code']}")
        return location_id

    def update_location(self, code: str, data: dict, username: str = "system") -> bool:
        update_data = {k: v for k, v in data.items() if k != "code"}
        if not update_data:
            return False
        success = self.db.update_location(code, update_data)
        if success:
            self.db.audit_event(username, "update_location", "locations", None,
                                f"Updated location: {code}")
        return success

    def delete_location(self, code: str, username: str = "system") -> bool:
        success = self.db.delete_location(code)
        if success:
            self.db.audit_event(username, "delete_location", "locations", None,
                                f"Deleted location: {code}")
        return success


class SupplierService:
    """Business logic for suppliers."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_all_suppliers(self, active_only: bool = True) -> List[dict]:
        return self.db.fetch_suppliers(active_only=active_only)

    def add_supplier(self, data: dict, username: str = "system") -> int:
        validate_non_empty_string(name=data.get("name"))
        supplier_id = self.db.insert_supplier(data)
        self.db.audit_event(username, "create_supplier", "suppliers", supplier_id,
                            f"Created supplier: {data['name']}")
        return supplier_id

    def update_supplier(self, code: str, data: dict, username: str = "system") -> bool:
        update_data = {k: v for k, v in data.items() if k != "code"}
        if not update_data:
            return False
        success = self.db.update_supplier(code, update_data)
        if success:
            self.db.audit_event(username, "update_supplier", "suppliers", None,
                                f"Updated supplier: {code}")
        return success


class CustomerService:
    """Business logic for customers."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_all_customers(self, active_only: bool = True) -> List[dict]:
        return self.db.fetch_customers(active_only=active_only)

    def add_customer(self, data: dict, username: str = "system") -> int:
        validate_non_empty_string(name=data.get("name"))
        customer_id = self.db.insert_customer(data)
        self.db.audit_event(username, "create_customer", "customers", customer_id,
                            f"Created customer: {data['name']}")
        return customer_id

    def update_customer(self, customer_id: int, data: dict, username: str = "system") -> bool:
        if not data:
            return False
        success = self.db.update_customer(customer_id, data)
        if success:
            self.db.audit_event(username, "update_customer", "customers", customer_id,
                                f"Updated customer: {customer_id}")
        return success

    def create_customer(self, data: dict, username: str = "system") -> int:
        """Alias for add_customer for consistency."""
        return self.add_customer(data, username=username)

    def delete_customer(self, customer_id: int, username: str = "system") -> bool:
        """Delete a customer."""
        success = self.db.delete_customer(customer_id)
        if success:
            self.db.audit_event(username, "delete_customer", "customers", customer_id,
                                f"Deleted customer: {customer_id}")
        return success


class InvoiceService:
    """Business logic for invoices."""

    def __init__(self, database: Optional[InventoryDB] = None,
                 inventory_svc: Optional[InventoryService] = None):
        self.db = database or InventoryDB()
        self.inventory = inventory_svc or InventoryService(database)

    def get_all_invoices(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_invoices(status=status)

    def get_invoice_items(self, invoice_id: int) -> List[dict]:
        return self.db.fetch_invoice_items(invoice_id)

    def create_invoice(self, invoice_data: dict, items: List[dict],
                       username: str = "system") -> int:
        if not items:
            raise ValueError("Invoice must have at least one item")
        invoice_data.setdefault("invoice_date", datetime.now().isoformat())
        invoice_data.setdefault("status", "pending")
        invoice_data.setdefault("created_by", username)
        invoice_id = self.db.insert_invoice(invoice_data, items)
        self.db.audit_event(username, "create_invoice", "invoices", invoice_id,
                            f"Created invoice: {invoice_data.get('invoice_number')}")
        logger.info(f"Invoice created: #{invoice_id}")
        return invoice_id


class LeaseService:
    """Business logic for leases/rentals."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_all_leases(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_leases(status=status)

    def create_lease(self, data: dict, username: str = "system") -> str:
        if not data.get("lease_id") or not data.get("customer_name"):
            raise ValueError("Lease must have 'lease_id' and 'customer_name'")
        data.setdefault("start_date", datetime.now().isoformat())
        data.setdefault("status", "active")
        data.setdefault("created_by", username)
        lease_id = self.db.insert_lease(data)
        self.db.audit_event(username, "create_lease", "leases", None,
                            f"Created lease: {lease_id}")
        return lease_id

    def update_lease(self, lease_id: str, data: dict, username: str = "system") -> bool:
        update_data = {k: v for k, v in data.items() if k != "lease_id"}
        if not update_data:
            return False
        success = self.db.update_lease(lease_id, update_data)
        if success:
            self.db.audit_event(username, "update_lease", "leases", None,
                                f"Updated lease: {lease_id}")
        return success


class SerialNumberService:
    """Business logic for serial numbers (electronics tracking)."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_serial_numbers(self, product_id: Optional[int] = None) -> List[dict]:
        return self.db.fetch_serial_numbers(product_id=product_id)

    def add_serial_number(self, data: dict, username: str = "system") -> int:
        sn_id = self.db.insert_serial_number(data)
        self.db.audit_event(username, "add_serial_number", "serial_numbers", sn_id)
        return sn_id

    def update_serial_status(self, serial_number: str, status: str, username: str = "system") -> bool:
        success = self.db.update_serial_status(serial_number, status)
        if success:
            self.db.audit_event(username, "update_serial_status", "serial_numbers", None,
                                f"Updated serial number {serial_number} status to {status}")
        return success


class PurchaseOrderService:
    """Business logic for purchase orders."""

    def __init__(self, database: Optional[InventoryDB] = None,
                 inventory_svc: Optional[InventoryService] = None):
        self.db = database or InventoryDB()
        self.inventory = inventory_svc or InventoryService(database)

    def get_all_orders(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_purchase_orders(status=status)

    def get_order_items(self, po_id: int) -> List[dict]:
        return self.db.fetch_po_items(po_id)

    def create_order(self, order_data: dict, items: List[dict], username: str = "system") -> int:
        po_id = self.db.insert_purchase_order(order_data, items)
        self.db.audit_event(username, "create_purchase_order", "purchase_orders", po_id)
        return po_id

    def receive_order(self, po_id: int, username: str = "system") -> bool:
        """Receive a PO and add stock."""
        items = self.get_order_items(po_id)
        for item in items:
            product_id = item.get("product_id")
            if product_id:
                product = self.inventory.get_product_by_id(product_id)
                if product:
                    qty_received = item.get("quantity_received", item.get("quantity_ordered", 0))
                    self.inventory.adjust_stock(product["model"], qty_received, username=username,
                                                reason=f"PO #{po_id} received")
        success = self.db.update_purchase_order_status(po_id, "received", received_date=datetime.now().isoformat())
        if success:
            self.db.audit_event(username, "receive_purchase_order", "purchase_orders", po_id)
        return success


class ReturnService:
    """Business logic for returns/RMA."""

    def __init__(self, database: Optional[InventoryDB] = None,
                 inventory_svc: Optional[InventoryService] = None):
        self.db = database or InventoryDB()
        self.inventory = inventory_svc or InventoryService(database)

    def get_all_returns(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_returns(status=status)

    def get_return_items(self, return_id: int) -> List[dict]:
        return self.db.fetch_return_items(return_id)

    def create_return(self, return_data: dict, items: List[dict], username: str = "system") -> int:
        return_id = self.db.insert_return(return_data, items)

        # Restock items if applicable
        for item in items:
            if item.get("restock"):
                product = self.inventory.get_product_by_id(item.get("product_id", 0))
                if product:
                    self.inventory.adjust_stock(product["model"], item.get("quantity", 0),
                                                username=username, reason=f"Return #{return_id}")

        self.db.audit_event(username, "create_return", "returns", return_id)
        return return_id

    def approve_return(self, return_id: int, username: str = "system") -> bool:
        items = self.get_return_items(return_id)
        for item in items:
            if item.get("restock"):
                product = self.inventory.get_product_by_id(item.get("product_id", 0))
                if product:
                    self.inventory.adjust_stock(product["model"], item.get("quantity", 0),
                                                username=username, reason=f"Return #{return_id} approved")
        success = self.db.update_return_status(return_id, "approved")
        if success:
            self.db.audit_event(username, "approve_return", "returns", return_id)
        return success


class TradeInService:
    """Business logic for trade-ins."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_all_trade_ins(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_trade_ins(status=status)

    def create_trade_in(self, data: dict, username: str = "system") -> int:
        trade_in_id = self.db.insert_trade_in(data)
        self.db.audit_event(username, "create_trade_in", "trade_ins", trade_in_id)
        return trade_in_id


class ServiceTicketService:
    """Business logic for service/repair tickets."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_all_tickets(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_service_tickets(status=status)

    def create_ticket(self, data: dict, username: str = "system") -> int:
        ticket_id = self.db.insert_service_ticket(data)
        self.db.audit_event(username, "create_service_ticket", "service_tickets", ticket_id)
        return ticket_id


class ReportService:
    """Business logic for reports and statistics."""

    def __init__(self, database: Optional[InventoryDB] = None,
                 inventory_svc: Optional[InventoryService] = None,
                 sales_svc: Optional[SalesService] = None):
        self.db = database or InventoryDB()
        self.inventory = inventory_svc or InventoryService(database)
        self.sales = sales_svc or SalesService(database)

    def get_dashboard_stats(self) -> dict:
        return self.db.get_stats()

    def get_stock_value_report(self) -> List[dict]:
        products = self.inventory.get_all_products()
        for p in products:
            stock = p.get("stock", 0)
            p["cost_value"] = stock * p.get("purchase_price", 0)
            p["retail_value"] = stock * p.get("selling_price", 0)
            p["potential_profit"] = stock * (p.get("selling_price", 0) - p.get("purchase_price", 0))
        return products

    def get_sales_summary(self) -> dict:
        orders = self.sales.get_all_orders()
        total_revenue = sum(o.get("total_amount", 0) for o in orders)
        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "orders_by_status": self._count_by_field(orders, "status"),
        }

    @staticmethod
    def _count_by_field(items: List[dict], field: str) -> dict:
        counts = {}
        for item in items:
            val = item.get(field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts


# ============================================================
# ServiceFactory — single entry point to get any service
# ============================================================

class PharmacyService:
    """Business logic for pharmacy/pharma inventory."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_pharmacy_inventory(self) -> List[dict]:
        """Get products with pharma-specific fields (expiry, batch, prescription)."""
        return self.db.fetch_pharmacy_inventory()

    def get_pharmacy_stats(self) -> dict:
        """Get pharmacy dashboard stats."""
        return self.db.fetch_pharmacy_stats()

    def get_batches(self) -> List[dict]:
        """Get all active batches with product and supplier info."""
        return self.db.fetch_batches()

    def get_expiring_products(self, days: int = 30) -> List[dict]:
        """Get products expiring within N days."""
        return self.db.fetch_expiring_products(days=days)


class StockTransferService:
    """Business logic for stock transfers between locations."""

    def __init__(self, database: Optional[InventoryDB] = None):
        self.db = database or InventoryDB()

    def get_transfers(self, status: Optional[str] = None) -> List[dict]:
        return self.db.fetch_stock_transfers(status=status)

    def get_transfer_items(self, transfer_id: int) -> List[dict]:
        return self.db.fetch_stock_transfer_items(transfer_id)

    def get_products_with_stock(self) -> List[dict]:
        """Get active products that have stock > 0."""
        return self.db.fetch_products_with_stock()

    def create_transfer(self, transfer_data: dict, items: List[dict], username: str = "system") -> int:
        transfer_id = self.db.insert_stock_transfer(transfer_data, items)
        self.db.audit_event(username, "create_stock_transfer", "stock_transfers", transfer_id)
        return transfer_id

    def complete_transfer(self, transfer_id: int, username: str = "system") -> bool:
        """Complete a transfer: deduct source stock, add to destination."""
        items = self.get_transfer_items(transfer_id)
        locations = self.db.get_transfer_locations(transfer_id)
        if not locations:
            return False

        from_loc, to_loc = locations

        for item in items:
            product_id = item["product_id"]
            qty = item["quantity"]

            # Deduct from source location stock
            self.db.update_product_stock_location(product_id, from_loc, -qty)

            # Add to destination location stock (upsert)
            self.db.upsert_product_stock_location(product_id, to_loc, qty)

            # Update received quantity
            self.db.update_transfer_item_received_quantity(transfer_id, product_id, qty)

        # Mark transfer as completed
        success = self.db.complete_stock_transfer(transfer_id)
        if success:
            self.db.audit_event(username, "complete_stock_transfer", "stock_transfers", transfer_id)
        return success

    # ── Lease payments ────────────────────────────────────
    def get_lease_payments(self, lease_id: Optional[str] = None) -> List[dict]:
        return self.db.fetch_lease_payments(lease_id=lease_id)

    def record_lease_payment(self, data: dict, username: str = "system") -> int:
        payment_id = self.db.insert_lease_payment(data)
        self.db.audit_event(username, "record_lease_payment", "lease_payments", payment_id)
        return payment_id

    # ── Return items ──────────────────────────────────────
    def get_return_items(self, return_id: int) -> List[dict]:
        return self.db.fetch_return_items(return_id)

    # ── Categories ────────────────────────────────────────
    def get_categories(self) -> List[dict]:
        return self.db.fetch_categories()

    def add_category(self, data: dict, username: str = "system") -> int:
        category_id = self.db.insert_category(data)
        self.db.audit_event(username, "create_category", "categories", category_id)
        return category_id


class ServiceFactory:
    """
    Creates and caches service instances so the whole app shares
    one InventoryDB singleton and one set of services.
    """

    def __init__(self):
        self._db = InventoryDB()
        self._inventory = None
        self._sales = None
        self._location = None
        self._supplier = None
        self._customer = None
        self._invoice = None
        self._lease = None
        self._report = None
        self._serial = None
        self._purchase_order = None
        self._return_svc = None
        self._tradein = None
        self._service_ticket = None
        self._pharmacy = None
        self._stock_transfer = None

    @property
    def db(self):
        """Direct access to the database helper for settings/industry."""
        return self._db

    @property
    def inventory(self) -> InventoryService:
        if self._inventory is None:
            self._inventory = InventoryService(self._db)
        return self._inventory

    @property
    def sales(self) -> SalesService:
        if self._sales is None:
            self._sales = SalesService(self._db, self.inventory)
        return self._sales

    @property
    def location(self) -> LocationService:
        if self._location is None:
            self._location = LocationService(self._db)
        return self._location

    @property
    def supplier(self) -> SupplierService:
        if self._supplier is None:
            self._supplier = SupplierService(self._db)
        return self._supplier

    @property
    def customer(self) -> CustomerService:
        if self._customer is None:
            self._customer = CustomerService(self._db)
        return self._customer

    @property
    def invoice(self) -> InvoiceService:
        if self._invoice is None:
            self._invoice = InvoiceService(self._db, self.inventory)
        return self._invoice

    @property
    def lease(self) -> LeaseService:
        if self._lease is None:
            self._lease = LeaseService(self._db)
        return self._lease

    @property
    def report(self) -> ReportService:
        if self._report is None:
            self._report = ReportService(self._db, self.inventory, self.sales)
        return self._report

    @property
    def serial(self) -> SerialNumberService:
        if self._serial is None:
            self._serial = SerialNumberService(self._db)
        return self._serial

    @property
    def purchase_order(self) -> PurchaseOrderService:
        if self._purchase_order is None:
            self._purchase_order = PurchaseOrderService(self._db, self.inventory)
        return self._purchase_order

    @property
    def return_svc(self) -> ReturnService:
        if self._return_svc is None:
            self._return_svc = ReturnService(self._db, self.inventory)
        return self._return_svc

    @property
    def tradein(self) -> TradeInService:
        if self._tradein is None:
            self._tradein = TradeInService(self._db)
        return self._tradein

    @property
    def service_ticket(self) -> ServiceTicketService:
        if self._service_ticket is None:
            self._service_ticket = ServiceTicketService(self._db)
        return self._service_ticket

    @property
    def pharmacy(self) -> PharmacyService:
        if self._pharmacy is None:
            self._pharmacy = PharmacyService(self._db)
        return self._pharmacy

    @property
    def stock_transfer(self) -> StockTransferService:
        if self._stock_transfer is None:
            self._stock_transfer = StockTransferService(self._db)
        return self._stock_transfer


# Module-level singleton
svc = ServiceFactory()
