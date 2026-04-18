"""
Reports UI Tab
===============
UI-ONLY layer. All data goes through the service layer.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
from datetime import datetime, timedelta

from ui_theme import (
    make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED,
    label, frame, combobox
)
from services import svc


def create_reports_tab(parent, current_user=None):
    """Creates the advanced reports tab."""
    window = QtWidgets.QWidget()
    window.setContentsMargins(15, 15, 15, 15)

    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    header_label = QtWidgets.QLabel("Reports")
    header_label.setFont(FONT_BOLD)
    header_layout.addWidget(header_label)
    main_layout.addWidget(header_frame)

    # Report type selector
    report_types = [
        ("stock_summary", "Stock Summary"),
        ("low_stock", "Low Stock Report"),
        ("profit_analysis", "Profit Analysis"),
        ("supplier_performance", "Supplier Performance"),
        ("inventory_valuation", "Inventory Valuation"),
        ("sales_summary", "Sales Summary"),
    ]

    selector_frame = QtWidgets.QWidget()
    selector_layout = QtWidgets.QHBoxLayout(selector_frame)
    selector_layout.setContentsMargins(0, 0, 0, 0)

    type_cb = QtWidgets.QComboBox()
    type_cb.addItems([rt[1] for rt in report_types])
    selector_layout.addWidget(type_cb)

    # Store references for the generate function
    tree = QtWidgets.QTableWidget()

    def generate_report():
        _generate_report(type_cb, tree, report_types)

    generate_btn = QtWidgets.QPushButton("Generate Report")
    generate_btn.clicked.connect(generate_report)
    generate_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    selector_layout.addWidget(generate_btn)

    main_layout.addWidget(selector_frame)

    # Table
    table_frame = QtWidgets.QWidget()
    table_layout = QtWidgets.QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    tree = QtWidgets.QTableWidget()
    table_layout.addWidget(tree)
    main_layout.addWidget(table_frame, stretch=1)

    # Initial report
    _generate_report(type_cb, tree, report_types)
    return window


def _generate_report(combo_box, tree, report_types):
    """Generate and display the selected report type."""
    report_type = combo_box.currentText()
    # Map display name back to key
    type_map = {rt[1]: rt[0] for rt in report_types}
    actual_type = type_map.get(report_type, report_type)

    tree.setRowCount(0)

    if actual_type == "stock_summary":
        _report_stock_summary(tree)
    elif actual_type == "low_stock":
        _report_low_stock(tree)
    elif actual_type == "profit_analysis":
        _report_profit_analysis(tree)
    elif actual_type == "supplier_performance":
        _report_supplier_performance(tree)
    elif actual_type == "inventory_valuation":
        _report_inventory_valuation(tree)
    elif actual_type == "sales_summary":
        _report_sales_summary(tree)


def _report_stock_summary(tree):
    products = svc.inventory.get_all_products()
    columns = ("model", "category", "stock", "purchase", "selling", "stock_value", "retail_value")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in columns])
    for i in range(len(columns)):
        tree.horizontalHeader().resizeSection(i, 100)

    for p in products:
        row = tree.rowCount()
        tree.insertRow(row)
        stock = p.get("stock", 0)
        for col, val in enumerate([
            p.get("model", ""),
            p.get("category", ""),
            str(stock),
            f"{p.get('purchase_price', 0):.2f}",
            f"{p.get('selling_price', 0):.2f}",
            f"{stock * p.get('purchase_price', 0):.2f}",
            f"{stock * p.get('selling_price', 0):.2f}",
        ]):
            tree.setItem(row, col, QtWidgets.QTableWidgetItem(val))


def _report_low_stock(tree):
    products = svc.inventory.get_low_stock_products()
    columns = ("model", "category", "stock", "reorder_point", "min_stock")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in columns])
    for i in range(len(columns)):
        tree.horizontalHeader().resizeSection(i, 120)

    for p in products:
        row = tree.rowCount()
        tree.insertRow(row)
        for col, val in enumerate([
            p.get("model", ""),
            p.get("category", ""),
            str(p.get("stock", 0)),
            str(p.get("reorder_point", 10)),
            str(p.get("min_stock", 5)),
        ]):
            tree.setItem(row, col, QtWidgets.QTableWidgetItem(val))


def _report_profit_analysis(tree):
    products = svc.inventory.get_all_products()
    columns = ("model", "category", "margin", "margin_pct")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in columns])
    for i in range(len(columns)):
        tree.horizontalHeader().resizeSection(i, 120)

    for p in products:
        purchase = p.get("purchase_price", 0)
        selling = p.get("selling_price", 0)
        margin = selling - purchase
        margin_pct = (margin / selling * 100) if selling > 0 else 0
        row = tree.rowCount()
        tree.insertRow(row)
        for col, val in enumerate([
            p.get("model", ""),
            p.get("category", ""),
            f"{margin:.2f}",
            f"{margin_pct:.1f}%",
        ]):
            tree.setItem(row, col, QtWidgets.QTableWidgetItem(val))


def _report_supplier_performance(tree):
    suppliers = svc.supplier.get_all_suppliers()
    products = svc.inventory.get_all_products()

    columns = ("name", "rating", "lead_time", "product_count", "avg_margin")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in columns])
    for i in range(len(columns)):
        tree.horizontalHeader().resizeSection(i, 120)

    for s in suppliers:
        supplier_products = [p for p in products if p.get("supplier") == s.get("id")]
        product_count = len(supplier_products)
        if supplier_products:
            avg_margin = sum(
                p.get("selling_price", 0) - p.get("purchase_price", 0)
                for p in supplier_products
            ) / product_count
        else:
            avg_margin = 0
        row = tree.rowCount()
        tree.insertRow(row)
        for col, val in enumerate([
            s.get("name", ""),
            str(s.get("rating", 5)),
            str(s.get("lead_time_days", 7)),
            str(product_count),
            f"{avg_margin:.2f}",
        ]):
            tree.setItem(row, col, QtWidgets.QTableWidgetItem(val))


def _report_inventory_valuation(tree):
    products = svc.inventory.get_all_products()
    # Group by category
    categories = {}
    for p in products:
        cat = p.get("category", "Uncategorized")
        if cat not in categories:
            categories[cat] = {"item_count": 0, "total_units": 0, "total_cost": 0, "total_retail": 0}
        stock = p.get("stock", 0)
        categories[cat]["item_count"] += 1
        categories[cat]["total_units"] += stock
        categories[cat]["total_cost"] += stock * p.get("purchase_price", 0)
        categories[cat]["total_retail"] += stock * p.get("selling_price", 0)

    columns = ("category", "item_count", "total_units", "total_cost", "total_retail", "potential_profit")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in columns])
    for i in range(len(columns)):
        tree.horizontalHeader().resizeSection(i, 120)

    for cat, data in categories.items():
        data["potential_profit"] = data["total_retail"] - data["total_cost"]
        row = tree.rowCount()
        tree.insertRow(row)
        for col, val in enumerate([
            cat,
            str(data["item_count"]),
            str(data["total_units"]),
            f"{data['total_cost']:.2f}",
            f"{data['total_retail']:.2f}",
            f"{data['potential_profit']:.2f}",
        ]):
            tree.setItem(row, col, QtWidgets.QTableWidgetItem(val))


def _report_sales_summary(tree):
    orders = svc.sales.get_all_orders()
    columns = ("order_number", "customer", "date", "total", "status")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([c.replace("_", " ").title() for c in columns])
    for i in range(len(columns)):
        tree.horizontalHeader().resizeSection(i, 140)

    for o in orders:
        row = tree.rowCount()
        tree.insertRow(row)
        for col, val in enumerate([
            o.get("order_number", ""),
            o.get("customer_name", ""),
            o.get("order_date", "")[:10],
            f"{o.get('total_amount', 0):.2f}",
            o.get("status", ""),
        ]):
            tree.setItem(row, col, QtWidgets.QTableWidgetItem(val))
