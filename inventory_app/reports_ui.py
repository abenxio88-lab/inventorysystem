"""
Reports UI Tab
===============
UI-ONLY layer. All data goes through the service layer.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    styled_label(header_frame, "📊 Reports", font=FONT_BOLD).pack(side=tk.LEFT)

    # Report type selector
    report_var = tk.StringVar(value="stock_summary")

    report_types = [
        ("stock_summary", "📦 Stock Summary"),
        ("low_stock", "⚠️ Low Stock Report"),
        ("profit_analysis", "💵 Profit Analysis"),
        ("supplier_performance", "🏭 Supplier Performance"),
        ("inventory_valuation", "💼 Inventory Valuation"),
        ("sales_summary", "💰 Sales Summary"),
    ]

    selector_frame = ttk.Frame(window)
    selector_frame.pack(fill="x", pady=(0, 10))

    type_cb = combobox(selector_frame, values=[rt[1] for rt in report_types],
                       textvariable=report_var, state="readonly")
    type_cb.pack(side=tk.LEFT, padx=(0, 10))

    make_button(selector_frame, "Generate Report", command=lambda: _generate_report(report_var, tree, report_types),
                kind="primary").pack(side=tk.LEFT)

    # Table
    table_frame = make_card(window, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(table_frame, show="headings")
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    try:
        style = ttk.Style()
        style.configure("Treeview", font=FONT_REGULAR, rowheight=28)
        style.configure("Treeview.Heading", font=FONT_BOLD)
    except Exception:
        pass

    # Initial report
    _generate_report(report_var, tree, report_types)
    return window


def _generate_report(report_var, tree, report_types):
    """Generate and display the selected report type."""
    report_type = report_var.get()
    # Map display name back to key
    type_map = {rt[1]: rt[0] for rt in report_types}
    actual_type = type_map.get(report_type, report_type)

    tree.delete(*tree.get_children())

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
    tree["columns"] = ("model", "category", "stock", "purchase", "selling", "stock_value", "retail_value")
    for col in tree["columns"]:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=100)

    for p in products:
        stock = p.get("stock", 0)
        tree.insert("", "end", values=(
            p.get("model", ""),
            p.get("category", ""),
            stock,
            f"{p.get('purchase_price', 0):.2f}",
            f"{p.get('selling_price', 0):.2f}",
            f"{stock * p.get('purchase_price', 0):.2f}",
            f"{stock * p.get('selling_price', 0):.2f}",
        ))


def _report_low_stock(tree):
    products = svc.inventory.get_low_stock_products()
    tree["columns"] = ("model", "category", "stock", "reorder_point", "min_stock")
    for col in tree["columns"]:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=120)

    for p in products:
        tree.insert("", "end", values=(
            p.get("model", ""),
            p.get("category", ""),
            p.get("stock", 0),
            p.get("reorder_point", 10),
            p.get("min_stock", 5),
        ))


def _report_profit_analysis(tree):
    products = svc.inventory.get_all_products()
    tree["columns"] = ("model", "category", "margin", "margin_pct")
    for col in tree["columns"]:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=120)

    for p in products:
        purchase = p.get("purchase_price", 0)
        selling = p.get("selling_price", 0)
        margin = selling - purchase
        margin_pct = (margin / selling * 100) if selling > 0 else 0
        tree.insert("", "end", values=(
            p.get("model", ""),
            p.get("category", ""),
            f"{margin:.2f}",
            f"{margin_pct:.1f}%",
        ))


def _report_supplier_performance(tree):
    suppliers = svc.supplier.get_all_suppliers()
    products = svc.inventory.get_all_products()

    tree["columns"] = ("name", "rating", "lead_time", "product_count", "avg_margin")
    for col in tree["columns"]:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=120)

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
        tree.insert("", "end", values=(
            s.get("name", ""),
            s.get("rating", 5),
            s.get("lead_time_days", 7),
            product_count,
            f"{avg_margin:.2f}",
        ))


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

    tree["columns"] = ("category", "item_count", "total_units", "total_cost", "total_retail", "potential_profit")
    for col in tree["columns"]:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=120)

    for cat, data in categories.items():
        data["potential_profit"] = data["total_retail"] - data["total_cost"]
        tree.insert("", "end", values=(
            cat,
            data["item_count"],
            data["total_units"],
            f"{data['total_cost']:.2f}",
            f"{data['total_retail']:.2f}",
            f"{data['potential_profit']:.2f}",
        ))


def _report_sales_summary(tree):
    orders = svc.sales.get_all_orders()
    tree["columns"] = ("order_number", "customer", "date", "total", "status")
    for col in tree["columns"]:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=140)

    for o in orders:
        tree.insert("", "end", values=(
            o.get("order_number", ""),
            o.get("customer_name", ""),
            o.get("order_date", "")[:10],
            f"{o.get('total_amount', 0):.2f}",
            o.get("status", ""),
        ))
