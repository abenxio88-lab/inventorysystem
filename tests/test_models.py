"""
Tests for Data Models
"""

import pytest
from src.models import Product, StockStatus, Customer, Invoice, InvoiceStatus


class TestProduct:
    """Test Product model."""
    
    def test_stock_status_in_stock(self):
        """Test stock status when well stocked."""
        product = Product(stock=50)
        assert product.stock_status == StockStatus.IN_STOCK
    
    def test_stock_status_low_stock(self):
        """Test stock status when low."""
        product = Product(stock=8)
        assert product.stock_status == StockStatus.LOW_STOCK
    
    def test_stock_status_critical(self):
        """Test stock status when critical."""
        product = Product(stock=3)
        assert product.stock_status == StockStatus.CRITICAL
    
    def test_stock_status_out_of_stock(self):
        """Test stock status when out of stock."""
        product = Product(stock=0)
        assert product.stock_status == StockStatus.OUT_OF_STOCK
    
    def test_profit_margin(self):
        """Test profit margin calculation."""
        product = Product(purchase_price=50.0, selling_price=75.0)
        assert product.profit_margin == 50.0
    
    def test_profit_margin_zero_cost(self):
        """Test profit margin with zero cost."""
        product = Product(purchase_price=0, selling_price=75.0)
        assert product.profit_margin == 0.0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        product = Product(id=1, model="Test", stock=10)
        data = product.to_dict()
        
        assert data['id'] == 1
        assert data['model'] == "Test"
        assert data['stock'] == 10


class TestCustomer:
    """Test Customer model."""
    
    def test_default_country(self):
        """Test default country is Pakistan."""
        customer = Customer(name="Test")
        assert customer.country == "Pakistan"


class TestInvoice:
    """Test Invoice model."""
    
    def test_balance_calculation(self):
        """Test balance calculation."""
        invoice = Invoice(total_amount=1000.0, amount_paid=400.0)
        assert invoice.balance == 600.0
    
    def test_balance_fully_paid(self):
        """Test balance when fully paid."""
        invoice = Invoice(total_amount=1000.0, amount_paid=1000.0)
        assert invoice.balance == 0.0
    
    def test_is_overdue(self):
        """Test overdue detection."""
        invoice = Invoice(
            total_amount=1000.0,
            due_date="2020-01-01",
            status="pending"
        )
        assert invoice.is_overdue is True
    
    def test_is_not_overdue_paid(self):
        """Test not overdue when paid."""
        invoice = Invoice(
            total_amount=1000.0,
            due_date="2020-01-01",
            status="paid"
        )
        assert invoice.is_overdue is False
    
    def test_is_not_overdue_future(self):
        """Test not overdue with future date."""
        future_date = "2030-12-31"
        invoice = Invoice(
            total_amount=1000.0,
            due_date=future_date,
            status="pending"
        )
        assert invoice.is_overdue is False
