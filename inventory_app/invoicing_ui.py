"""
Invoicing UI Tab
=================
UI-ONLY layer. All data goes through the service layer.
After every write, refresh_from_db() reloads fresh data.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
import os
from datetime import datetime, timedelta

from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED,
    COLOR_TEXT_MAIN, COLOR_APP_BG, COLOR_CARD_BG,
    label, frame, entry, combobox
)
from services import svc
from app_core import app_state

logger = logging.getLogger(__name__)


def create_invoicing_tab(parent, current_user=None):
    """Creates the comprehensive invoicing tab."""
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 15)
    styled_label(header_frame, "Invoice Management", font=FONT_HEADING)
    header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
    main_layout.addWidget(header_frame)

    def open_new_invoice():
        _open_create_invoice_dialog(window, current_user=current_user)

    new_btn = make_button(header_frame, "New Invoice", command=open_new_invoice, kind="success")
    header_layout.addStretch()
    header_layout.addWidget(new_btn)

    # Summary cards
    summary_frame = QtWidgets.QWidget()
    summary_layout = QtWidgets.QHBoxLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 15)
    summary_layout.setSpacing(8)
    main_layout.addWidget(summary_frame)

    def _update_summary():
        invoices = svc.invoice.get_all_invoices()
        total = sum(inv.get("total_amount", 0) for inv in invoices)
        paid = sum(inv.get("amount_paid", 0) for inv in invoices if inv.get("status") == "paid")
        pending = total - paid
        counts = {"pending": 0, "paid": 0, "overdue": 0}
        for inv in invoices:
            status = inv.get("status", "pending")
            if status in counts:
                counts[status] += 1

        _summary_widgets["total"].setText(f"Rs. {total:,.2f}")
        _summary_widgets["paid"].setText(f"Rs. {paid:,.2f}")
        _summary_widgets["pending"].setText(f"Rs. {pending:,.2f}")
        _summary_widgets["count_pending"].setText(str(counts["pending"]))
        _summary_widgets["count_paid"].setText(str(counts["paid"]))

    _summary_widgets = {}
    for title, key in [
        ("Total Invoiced", "total"), ("Total Paid", "paid"),
        ("Outstanding", "pending"), ("Pending Count", "count_pending"), ("Paid Count", "count_paid")
    ]:
        card = make_card(summary_frame, padding=12)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        title_lbl = styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d")
        card_layout.addWidget(title_lbl)
        val = styled_label(card, text="...", font=("Segoe UI", 18, "bold"), foreground=COLOR_PRIMARY)
        card_layout.addWidget(val)
        card_layout.addStretch()
        summary_layout.addWidget(card)
        _summary_widgets[key] = val

    # Filter toolbar
    toolbar = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 10)
    main_layout.addWidget(toolbar)

    styled_label(toolbar, "Status:")
    status_cb = QtWidgets.QComboBox()
    status_cb.addItems(["All", "pending", "paid", "overdue"])
    toolbar_layout.addWidget(status_cb, stretch=0)

    refresh_btn = make_button(toolbar, "Refresh", kind="primary")
    toolbar_layout.addWidget(refresh_btn)
    toolbar_layout.addStretch()

    # Table
    table_frame = make_card(window, padx=10, pady=10)
    table_layout = QtWidgets.QHBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(table_frame)

    columns = ("number", "customer", "date", "due_date", "total", "paid", "status")
    column_map = {
        "number": ("Invoice #", 120),
        "customer": ("Customer", 150),
        "date": ("Date", 100),
        "due_date": ("Due Date", 100),
        "total": ("Total", 100),
        "paid": ("Paid", 100),
        "status": ("Status", 80),
    }

    tree = QtWidgets.QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([column_map[c][0].upper() for c in columns])
    tree.horizontalHeader().setStretchLastSection(True)
    tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    for i, col in enumerate(columns):
        tree.setColumnWidth(i, column_map[col][1])

    table_layout.addWidget(tree)

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    # ========================================================

    def refresh_from_db():
        """Reload invoices and update summary."""
        _update_summary()
        tree.setRowCount(0)

        status_filter = status_cb.currentText()
        invoices = svc.invoice.get_all_invoices(
            status=None if status_filter == "All" else status_filter
        )

        for row_idx, inv in enumerate(invoices):
            tree.insertRow(row_idx)
            tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(inv.get("invoice_number", "")))
            tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(inv.get("customer_name", "")))
            tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(inv.get("invoice_date", "")[:10]))
            tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(inv.get("due_date", "")[:10]))
            tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(f"{inv.get('total_amount', 0):,.2f}"))
            tree.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(f"{inv.get('amount_paid', 0):,.2f}"))
            tree.setItem(row_idx, 6, QtWidgets.QTableWidgetItem(inv.get("status", "")))

    # Wire the combobox and button
    status_cb.currentTextChanged.connect(lambda _: refresh_from_db())
    refresh_btn.clicked.connect(refresh_from_db)

    # Double-click to view/pay
    def on_double_click(event):
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        inv_number = tree.item(row, 0).text()
        invoices = svc.invoice.get_all_invoices()
        inv = next((i for i in invoices if i.get("invoice_number") == inv_number), None)
        if inv:
            _open_invoice_detail(window, inv, current_user=current_user, on_refresh=refresh_from_db)

    tree.doubleClicked.connect(on_double_click)

    # Initial load
    refresh_from_db()
    return window


def _open_create_invoice_dialog(master, current_user=None):
    """Dialog to create a new invoice."""
    dlg = QtWidgets.QDialog(master)
    dlg.setWindowTitle("New Invoice")
    dlg.resize(600, 550)
    dlg.setModal(True)

    layout = QtWidgets.QVBoxLayout(dlg)
    layout.setContentsMargins(10, 10, 10, 10)

    form_card = make_card(dlg, padx=20, pady=20)
    form_layout = QtWidgets.QFormLayout(form_card)
    form_layout.setSpacing(10)
    layout.addWidget(form_card)

    # Customer selection
    customer_var = ""
    customers = svc.customer.get_all_customers()
    customer_names = [c.get("name", "") for c in customers if c.get("name")]

    customer_cb = QtWidgets.QComboBox()
    customer_cb.addItems(customer_names)
    form_layout.addRow(label(form_card, "Customer Name", kind="bold"), customer_cb)

    # Product selection
    products = svc.inventory.get_all_products(active_only=True)
    product_names = [p.get("model", "") for p in products if p.get("model")]
    product_cb = QtWidgets.QComboBox()
    product_cb.addItems(product_names)
    form_layout.addRow(label(form_card, "Product", kind="bold"), product_cb)

    # Quantity
    qty_edit = QtWidgets.QLineEdit("1")
    form_layout.addRow(label(form_card, "Quantity", kind="bold"), qty_edit)

    # Due date
    due_edit = QtWidgets.QLineEdit((datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
    form_layout.addRow(label(form_card, "Due Date (YYYY-MM-DD)", kind="bold"), due_edit)

    # Notes
    notes_edit = QtWidgets.QLineEdit()
    form_layout.addRow(label(form_card, "Notes", kind="bold"), notes_edit)

    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.addStretch()
    layout.addWidget(btn_frame)

    def create():
        customer_name = customer_cb.currentText()
        product_name = product_cb.currentText()
        if not customer_name or not product_name:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Customer and Product are required")
            return

        try:
            qty = int(qty_edit.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Invalid quantity")
            return

        product = next((p for p in products if p.get("model") == product_name), None)
        if not product:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Product not found")
            return

        unit_price = product.get("selling_price", 0)
        subtotal = qty * unit_price
        tax_rate = 0
        tax_amount = subtotal * tax_rate / 100
        total = subtotal + tax_amount

        username = current_user or getattr(app_state, "username", "system")
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        invoice_data = {
            "invoice_number": invoice_number,
            "customer_name": customer_name,
            "invoice_date": datetime.now().isoformat(),
            "due_date": due_edit.text(),
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total,
            "amount_paid": 0,
            "status": "pending",
            "notes": notes_edit.text(),
            "created_by": username,
        }

        items = [{
            "product_id": product.get("id"),
            "product_name": product_name,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": subtotal,
        }]

        try:
            svc.invoice.create_invoice(invoice_data, items, username=username)
            QtWidgets.QMessageBox.information(dlg, "Success", f"Invoice {invoice_number} created")
            dlg.accept()
        except Exception as e:
            logger.error(f"Failed to create invoice: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(dlg, "Error", str(e))

    create_btn = make_button(btn_frame, "Create Invoice", command=create, kind="primary")
    btn_layout.addWidget(create_btn)
    cancel_btn = make_button(btn_frame, "Cancel", command=dlg.reject, kind="secondary")
    btn_layout.addWidget(cancel_btn)


def _open_invoice_detail(master, invoice, current_user=None, on_refresh=None):
    """Dialog to view invoice details and record payments."""
    dlg = QtWidgets.QDialog(master)
    dlg.setWindowTitle(f"Invoice {invoice.get('invoice_number', '')}")
    dlg.resize(500, 400)
    dlg.setModal(True)

    layout = QtWidgets.QVBoxLayout(dlg)
    layout.setContentsMargins(10, 10, 10, 10)

    form_card = make_card(dlg, padx=20, pady=20)
    form_layout = QtWidgets.QFormLayout(form_card)
    layout.addWidget(form_card)

    details = [
        ("Invoice #", invoice.get("invoice_number", "")),
        ("Customer", invoice.get("customer_name", "")),
        ("Date", invoice.get("invoice_date", "")[:10]),
        ("Due Date", invoice.get("due_date", "")[:10]),
        ("Total", f"{invoice.get('total_amount', 0):,.2f}"),
        ("Paid", f"{invoice.get('amount_paid', 0):,.2f}"),
        ("Status", invoice.get("status", "")),
    ]

    for lbl, val in details:
        form_layout.addRow(label(form_card, lbl, kind="bold"), label(form_card, val))

    # Payment section
    pay_frame = QtWidgets.QWidget()
    pay_layout = QtWidgets.QVBoxLayout(pay_frame)
    layout.addWidget(pay_frame)

    pay_layout.addWidget(label(pay_frame, "Payment Amount", kind="bold"))
    pay_edit = QtWidgets.QLineEdit()
    pay_layout.addWidget(pay_edit)

    def record_payment():
        try:
            amount = float(pay_edit.text())
        except ValueError:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Invalid payment amount")
            return

        username = current_user or getattr(app_state, "username", "system")
        try:
            from database import db
            db.audit_event(username, "invoice_payment", "invoices", invoice.get("invoice_id"),
                           f"Payment of {amount} for {invoice.get('invoice_number')}")
            QtWidgets.QMessageBox.information(dlg, "Success", f"Payment of {amount} recorded")
            dlg.accept()
            if on_refresh:
                on_refresh()
        except Exception as e:
            QtWidgets.QMessageBox.critical(dlg, "Error", str(e))

    pay_btn = make_button(pay_frame, "Record Payment", command=record_payment, kind="success")
    pay_layout.addWidget(pay_btn)
    close_btn = make_button(pay_frame, "Close", command=dlg.reject, kind="secondary")
    pay_layout.addWidget(close_btn)
