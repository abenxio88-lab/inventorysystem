"""
Sales UI Tab
=============
UI-ONLY layer. All data goes through the service layer.
After every write, refresh_from_db() reloads fresh data.

RULES:
  - No SQL queries here.
  - No direct database access.
  - All reads/writes go through svc.sales and svc.inventory.
"""

import os
import logging
from datetime import datetime

from PySide6 import QtWidgets, QtCore, QtGui

# Project imports
from app_core import app_state, PremiumPopup
from ui_theme import (
    toggle_theme, get_color, make_button, make_card, styled_label, styled_entry,
    frame, label, entry, combobox, treeview,
    COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT_MUTED, COLOR_APP_BG, COLOR_INFO,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, BTN_WIDTH, FONT_BOLD, FONT_HEADING, FONT_REGULAR
)
from services import svc

logger = logging.getLogger(__name__)


def create_sales_tab(parent):
    """Creates the sales management tab."""
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)

    # ── Toolbar ───────────────────────────────────────────
    toolbar = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    search_label = QtWidgets.QLabel("Search:")
    toolbar_layout.addWidget(search_label)

    search_entry = QtWidgets.QLineEdit()
    search_entry.setPlaceholderText("Search sales...")
    toolbar_layout.addWidget(search_entry)

    search_btn = make_button(toolbar, "Search", kind="primary")
    clear_btn = make_button(toolbar, "Clear", kind="secondary")
    fullscreen_btn = make_button(toolbar, "\u26f6 Fullscreen", kind="secondary")

    toolbar_layout.addWidget(search_btn)
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch()
    toolbar_layout.addWidget(fullscreen_btn)

    main_layout.addWidget(toolbar)

    # ── Filter Section ────────────────────────────────────
    filter_heading = label(window, "FILTER SALES", kind="heading")
    main_layout.addWidget(filter_heading)

    filter_card = make_card(window, padx=25, pady=20)
    filter_layout = QtWidgets.QHBoxLayout(filter_card)
    main_layout.addWidget(filter_card)

    model_label = label(filter_card, "Model Name:", kind="bold", foreground=COLOR_TEXT_MUTED)
    filter_layout.addWidget(model_label)

    products = svc.inventory.get_all_products(active_only=True)
    models = ["All"] + sorted({p["model"] for p in products if p.get("model")})

    model_cb = combobox(filter_card, values=models, state="readonly")
    model_cb.setCurrentText("All")
    filter_layout.addWidget(model_cb)

    month_label = label(filter_card, "Month (YYYY-MM):", kind="bold", foreground="#6c757d")
    filter_layout.addWidget(month_label)

    month_entry = QtWidgets.QLineEdit()
    month_entry.setPlaceholderText("YYYY-MM")
    filter_layout.addWidget(month_entry)

    reset_btn = make_button(filter_card, "Reset Filter", kind="secondary")
    filter_layout.addWidget(reset_btn)

    # ── Table Section ─────────────────────────────────────
    table_heading = label(window, "SALES HISTORY", kind="heading")
    main_layout.addWidget(table_heading)

    table_frame = make_card(window, padx=10, pady=10)
    table_layout = QtWidgets.QVBoxLayout(table_frame)
    main_layout.addWidget(table_frame, stretch=1)

    table_widget = QtWidgets.QTableWidget()
    table_widget.setColumnCount(5)
    table_widget.setHorizontalHeaderLabels(["DATE", "MODEL NAME", "QUANTITY", "UNIT PRICE", "TOTAL AMOUNT"])
    table_widget.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
    table_widget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    table_widget.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
    table_widget.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
    table_widget.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
    table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    table_widget.setAlternatingRowColors(False)
    table_layout.addWidget(table_widget)

    # ── Action Bar ────────────────────────────────────────
    actions = QtWidgets.QWidget()
    actions_layout = QtWidgets.QHBoxLayout(actions)
    actions_layout.addStretch()

    record_sale_btn = make_button(actions, "Record New Sale", kind="success")
    actions_layout.addWidget(record_sale_btn)
    actions_layout.addStretch()

    main_layout.addWidget(actions)

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    # ========================================================

    def refresh_from_db(filtered_sales=None):
        """Reload the sales table from the database."""
        table_widget.setRowCount(0)
        orders = filtered_sales if filtered_sales is not None else svc.sales.get_all_orders()
        products_map = {p["model"]: p.get("category", "") for p in svc.inventory.get_all_products()}

        for sale in orders:
            items = svc.sales.get_order_items(sale["id"])
            model = _get_sale_model(sale, items)
            qty = sum(it.get("quantity", 0) for it in items) if items else sale.get("quantity", 0)
            price = items[0].get("unit_price", 0) if items else sale.get("selling_price", 0)
            total = sale.get("total_amount", 0)
            cat = products_map.get(model, "")

            row = table_widget.rowCount()
            table_widget.insertRow(row)
            table_widget.setItem(row, 0, QtWidgets.QTableWidgetItem(sale.get("order_date", "")))
            table_widget.setItem(row, 1, QtWidgets.QTableWidgetItem(model))
            table_widget.setItem(row, 2, QtWidgets.QTableWidgetItem(str(qty)))
            table_widget.setItem(row, 3, QtWidgets.QTableWidgetItem(f"Rs. {price:.2f}"))
            table_widget.setItem(row, 4, QtWidgets.QTableWidgetItem(f"Rs. {total:.2f}"))

            if cat:
                color_map = {
                    "Phone": {"bg": "#DBEAFE", "fg": "#1E40AF"},
                    "Tablet": {"bg": "#FEF3C7", "fg": "#B45309"},
                    "Accessory": {"bg": "#D1FAE5", "fg": "#065F46"},
                }
                colors = color_map.get(cat, {})
                bg = colors.get("bg")
                fg = colors.get("fg")
                if bg:
                    for col in range(5):
                        item = table_widget.item(row, col)
                        if item:
                            item.setBackground(QtGui.QColor(bg))
                            item.setForeground(QtGui.QColor(fg))

        _refresh_filter_models(model_var_holder, model_cb)

    def refresh_filter_models():
        """Refresh the model dropdown with current inventory."""
        _refresh_filter_models(model_var_holder, model_cb)

    def auto_refresh():
        """Auto-refresh table and filter after any change."""
        refresh_from_db()
        refresh_filter_models()

    # ── Connect signals ───────────────────────────────────
    def on_search():
        q = search_entry.text().strip().lower()
        if not q:
            refresh_from_db()
            return
        all_orders = svc.sales.get_all_orders()
        filtered = []
        for s in all_orders:
            items = svc.sales.get_order_items(s["id"])
            model = _get_sale_model(s, items)
            if q in model.lower():
                filtered.append(s)
        refresh_from_db(filtered_sales=filtered)

    search_btn.clicked.connect(on_search)
    search_entry.returnPressed.connect(on_search)

    def on_clear():
        search_entry.clear()
        refresh_from_db()

    clear_btn.clicked.connect(on_clear)

    def on_fullscreen():
        top_level = window.window()
        if top_level:
            if top_level.isFullScreen():
                top_level.showNormal()
            else:
                top_level.showFullScreen()

    fullscreen_btn.clicked.connect(on_fullscreen)

    def on_filter():
        _apply_filter(model_var_holder, month_entry, refresh_from_db)

    model_cb.currentTextChanged.connect(on_filter)
    month_entry.returnPressed.connect(on_filter)

    def on_reset_filter():
        model_cb.setCurrentText("All")
        month_entry.clear()
        refresh_from_db()

    reset_btn.clicked.connect(on_reset_filter)

    record_sale_btn.clicked.connect(lambda: _record_sale(window, auto_refresh))

    # ── Initial load ──────────────────────────────────────
    refresh_from_db()
    return window


# Model variable holder (replaces tk.StringVar)
model_var_holder = {"value": "All"}


# ============================================================
#  Helper functions
# ============================================================

def _get_sale_model(sale: dict, items: list) -> str:
    """Extract model name from a sale record."""
    if items:
        product_id = items[0].get("product_id")
        if product_id:
            product = svc.inventory.get_product_by_id(product_id)
            if product:
                return product.get("model", "Unknown")
    return sale.get("customer_name", "Unknown")


def _refresh_filter_models(model_var_holder, model_cb):
    """Refresh the model dropdown with current inventory."""
    products = svc.inventory.get_all_products(active_only=True)
    models = ["All"] + sorted({p["model"] for p in products if p.get("model")})
    current = model_cb.currentText()
    model_cb.blockSignals(True)
    model_cb.clear()
    model_cb.addItems(models)
    if current in models:
        model_cb.setCurrentText(current)
    else:
        model_cb.setCurrentText("All")
        model_var_holder["value"] = "All"
    model_cb.blockSignals(False)


def _apply_filter(model_var_holder, month_entry, refresh_cb):
    """Apply model + month filter to sales."""
    m = model_var_holder.get("value", "All")
    month = month_entry.text().strip()
    all_orders = svc.sales.get_all_orders()
    filtered = []
    for s in all_orders:
        items = svc.sales.get_order_items(s["id"])
        sale_model = _get_sale_model(s, items)
        if m == "All" or sale_model == m:
            if not month:
                filtered.append(s)
            else:
                sale_date = s.get("order_date", "")
                sale_month = sale_date[:7] if sale_date else ""
                if sale_month == month:
                    filtered.append(s)
    refresh_cb(filtered_sales=filtered)


def _record_sale(master, on_refresh):
    """Open dialog to record a new sale through the service layer."""
    dlg = PremiumPopup(master, "Record New Sale", width=700, height=550, resizable=True)
    content = dlg.get_content_frame()

    # Main layout for content
    content_layout = QtWidgets.QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(10)

    # Header
    header_card = make_card(content, padx=30, pady=20)
    header_layout = QtWidgets.QVBoxLayout(header_card)
    industry_config = app_state.get_industry_config()
    icon = industry_config.get("icon", "\U0001f4b0")
    heading = label(header_card, f"{icon} Record Sale", kind="heading", foreground=COLOR_PRIMARY)
    header_layout.addWidget(heading)
    content_layout.addWidget(header_card)

    # Form
    form_card = make_card(content, padx=30, pady=25)
    form_layout = QtWidgets.QFormLayout(form_card)
    form_layout.setSpacing(15)
    content_layout.addWidget(form_card, stretch=1)

    # Product selection
    model_label = label(form_card, "Select Product Model", kind="bold", foreground=COLOR_TEXT_MAIN)
    form_layout.addRow(model_label, None)

    model_sel_holder = {"widget": None, "product_map": {}}

    products = svc.inventory.get_all_products(active_only=True)
    available = [(p["model"], p["stock"], p["selling_price"]) for p in products if p.get("stock", 0) > 0]
    model_names = [p[0] for p in available] if available else ["No products available"]

    model_sel = combobox(form_card, values=model_names, state="readonly")
    form_layout.addRow("Product:", model_sel)
    model_sel_holder["widget"] = model_sel

    # Stock info display
    stock_frame = make_card(form_card, padx=15, pady=10)
    stock_layout = QtWidgets.QHBoxLayout(stock_frame)
    stock_info = label(stock_frame, "Available: \u2014 | Unit Price: 0.00",
                       foreground=COLOR_TEXT_MUTED, size=12)
    stock_alert = label(stock_frame, "", foreground=COLOR_DANGER, size=11, bold=True)
    stock_layout.addWidget(stock_info)
    stock_layout.addWidget(stock_alert)
    stock_layout.addStretch()
    form_layout.addRow(stock_frame)

    # Quantity
    qty_spin = QtWidgets.QSpinBox()
    qty_spin.setRange(1, 10000)
    qty_spin.setValue(1)
    form_layout.addRow("Quantity:", qty_spin)

    # Total display
    total_frame = make_card(form_card, padx=20, pady=15)
    total_layout = QtWidgets.QVBoxLayout(total_frame)
    total_lbl = label(total_frame, "Total Amount: Rs. 0.00", kind="heading", foreground=COLOR_SUCCESS)
    total_layout.addWidget(total_lbl)
    form_layout.addRow(total_frame)

    # Product info lookup
    product_map = {p["model"]: p for p in available}
    model_sel_holder["product_map"] = product_map

    def update_info(event=None):
        sel = model_sel.currentText()
        if not sel or sel == "No products available":
            return
        product = product_map.get(sel)
        if not product:
            return
        s = product.get("stock", 0)
        p = product.get("selling_price", 0)
        stock_info.setText(f"Available: {s} | Unit Price: Rs. {p:.2f}")
        try:
            qty = qty_spin.value()
            if qty > s:
                stock_alert.setText(f"\u26a0\ufe0f Only {s} in stock!")
                total_lbl.setText(f"Total Amount: Rs. {s * p:.2f}")
                qty_spin.setValue(s)
            else:
                stock_alert.setText("")
                total_lbl.setText(f"Total Amount: Rs. {qty * p:.2f}")
        except Exception:
            total_lbl.setText(f"Total Amount: Rs. {p:.2f}")

    model_sel.currentTextChanged.connect(update_info)

    if model_names and model_names[0] != "No products available":
        model_sel.setCurrentText(model_names[0])
        update_info()

    # Buttons
    button_frame = QtWidgets.QWidget()
    button_layout = QtWidgets.QHBoxLayout(button_frame)
    button_layout.setContentsMargins(0, 0, 0, 0)

    cancel_btn = make_button(button_frame, "Cancel", kind="secondary", width=15)
    confirm_btn = make_button(button_frame, "\u2713 Confirm Sale", kind="success", width=15)

    button_layout.addStretch()
    button_layout.addWidget(confirm_btn)
    button_layout.addWidget(cancel_btn)

    cancel_btn.clicked.connect(dlg.destroy)

    def save_sale_action():
        model = model_sel.currentText()
        qty = qty_spin.value()

        if not model or model == "No products available":
            QtWidgets.QMessageBox.critical(master, "Error", "Please select a valid product")
            return

        if qty <= 0:
            QtWidgets.QMessageBox.critical(master, "Error", "Quantity must be positive")
            return

        product = product_map.get(model)
        if not product:
            QtWidgets.QMessageBox.critical(master, "Error", "Product not found")
            return

        s = product.get("stock", 0)
        if qty > s:
            QtWidgets.QMessageBox.critical(master, "Error", f"Only {s} units available")
            return

        try:
            username = getattr(app_state, "username", "system")
            price = product.get("selling_price", 0)
            total = qty * price

            order_data = {
                "order_number": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "customer_name": "Walk-in Customer",
                "order_date": datetime.now().isoformat(),
                "status": "confirmed",
                "total_amount": total,
                "paid_amount": total,
                "payment_status": "paid",
            }

            items = [{
                "product_id": product.get("id"),
                "quantity": qty,
                "unit_price": price,
                "total_price": total,
            }]

            svc.sales.create_order(order_data, items, username=username)
            QtWidgets.QMessageBox.information(master, "Success", "Sale recorded successfully!")
            dlg.destroy()
            on_refresh()
        except Exception as e:
            logger.error(f"Failed to record sale: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(master, "Error", f"Failed to record sale: {e}")

    confirm_btn.clicked.connect(save_sale_action)

    content_layout.addWidget(button_frame)
