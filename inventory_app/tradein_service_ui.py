"""
Trade-in & Service/Repair Module
=================================
Trade-in valuation and service ticket management.
Phase 5 - Complete Implementation
"""

from PySide6.QtWidgets import (QFrame, QLabel, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QFormLayout, QComboBox, QLineEdit, QTextEdit,
                               QHeaderView, QAbstractItemView, QScrollArea, QWidget)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
import logging
from datetime import datetime

from services import svc
from ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, BTN_WIDTH


def create_trade_ins_tab(parent, current_user=None):
    """Creates the trade-in management tab."""
    window = QFrame()
    window.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_layout, "\U0001f4b1 Trade-In Management", font=FONT_HEADING)

    def open_new_trade_in():
        open_trade_in_dialog(window, current_user=current_user)

    make_button(header_layout, "\u2795 New Trade-In", command=open_new_trade_in, kind="success")

    layout.addWidget(header_frame)

    # Summary
    summary_frame = QFrame()
    summary_layout = QGridLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 0)
    for i in range(3):
        summary_layout.setColumnStretch(i, 1)

    summary_labels = {}

    def create_summary_card(parent_layout, title, value, col):
        card = make_card(parent_layout, padding=12)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        styled_label(card_layout, text=title, font=("Segoe UI", 9), foreground="#6c757d")
        value_label = styled_label(card_layout, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        parent_layout.addWidget(card, 0, col)
        return value_label

    pending_lbl = create_summary_card(summary_layout, "Pending", 0, 0)
    completed_lbl = create_summary_card(summary_layout, "Completed", 0, 1)
    total_value_lbl = create_summary_card(summary_layout, "Total Value", "Rs. 0", 2)

    summary_labels = {'pending': pending_lbl, 'completed': completed_lbl, 'total_value': total_value_lbl}
    layout.addWidget(summary_frame)

    # Table
    table_frame = make_card(window, padding=10)
    table_layout = QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
    tree = QTableWidget()
    columns = ("trade_in_number", "customer", "product", "value", "credit", "status")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in columns])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    table_layout.addWidget(tree)
    layout.addWidget(table_frame)

    def refresh_from_db():
        """Reload trade-in data from the database via services."""
        tree.setRowCount(0)
        trades = svc.tradein.get_all_trade_ins()

        counts = {'pending': 0, 'completed': 0, 'total_value': 0}
        for t in trades:
            status = t.get('status', 'pending')
            if status in counts:
                counts[status] += 1
            counts['total_value'] += t.get('trade_in_value', 0) or 0

            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QTableWidgetItem(t.get('trade_in_number', '')))
            tree.setItem(row, 1, QTableWidgetItem(t.get('customer_name', '')))
            tree.setItem(row, 2, QTableWidgetItem(t.get('product_name', '')))
            tree.setItem(row, 3, QTableWidgetItem(f"Rs. {t.get('trade_in_value', 0):,.2f}"))
            tree.setItem(row, 4, QTableWidgetItem(f"Rs. {t.get('credit_amount', 0):,.2f}"))
            tree.setItem(row, 5, QTableWidgetItem(status.title()))

        summary_labels['pending'].setText(str(counts['pending']))
        summary_labels['completed'].setText(str(counts['completed']))
        summary_labels['total_value'].setText(f"Rs. {counts['total_value']:,.2f}")

    window.refresh = refresh_from_db
    refresh_from_db()

    return window


def open_trade_in_dialog(parent, current_user=None):
    """Dialog to create a new trade-in."""
    from PySide6.QtWidgets import QDialog
    dlg = QDialog(parent)
    dlg.setWindowTitle("New Trade-In")
    dlg.resize(700, 750)
    dlg.setMinimumSize(600, 650)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    styled_label(content_layout, "\U0001f4b1 New Trade-In", font=FONT_HEADING)

    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(1, 1)

    # Customer
    form_layout.addWidget(styled_label(None, "Customer Name *:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)
    customer_var = QLineEdit()
    form_layout.addWidget(customer_var, 1, 0, 1, 2)

    # Phone
    form_layout.addWidget(styled_label(None, "Phone:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    phone_var = QLineEdit()
    form_layout.addWidget(phone_var, 3, 0, 1, 2)

    # Product
    form_layout.addWidget(styled_label(None, "Product Name *:", font=FONT_BOLD), 4, 0, alignment=Qt.AlignLeft)
    product_var = QLineEdit()
    form_layout.addWidget(product_var, 5, 0, 1, 2)

    # Condition
    form_layout.addWidget(styled_label(None, "Condition:", font=FONT_BOLD), 6, 0, alignment=Qt.AlignLeft)
    condition_var = QComboBox()
    condition_var.addItems(["excellent", "good", "fair", "poor", "damaged"])
    condition_var.setCurrentText("good")
    form_layout.addWidget(condition_var, 7, 0, 1, 2)

    # Value
    form_layout.addWidget(styled_label(None, "Trade-In Value (Rs.):", font=FONT_BOLD), 8, 0, alignment=Qt.AlignLeft)
    value_var = QLineEdit("0")
    form_layout.addWidget(value_var, 9, 0)

    # Credit
    form_layout.addWidget(styled_label(None, "Credit Amount (Rs.):", font=FONT_BOLD), 8, 1, alignment=Qt.AlignLeft)
    credit_var = QLineEdit("0")
    form_layout.addWidget(credit_var, 9, 1)

    # Notes
    form_layout.addWidget(styled_label(None, "Notes:", font=FONT_BOLD), 10, 0, alignment=Qt.AlignLeft)
    notes_text = QTextEdit()
    notes_text.setMaximumHeight(60)
    form_layout.addWidget(notes_text, 11, 0, 1, 2)

    content_layout.addWidget(form_frame)

    from PySide6.QtWidgets import QMessageBox
    def save():
        customer = customer_var.text().strip()
        product = product_var.text().strip()

        if not customer or not product:
            QMessageBox.critical(dlg, "Error", "Customer name and product required")
            return

        try:
            value = float(value_var.text())
            credit = float(credit_var.text())
        except (ValueError, TypeError):
            QMessageBox.critical(dlg, "Error", "Invalid value/credit amount")
            return

        trade_number = f"TI-{datetime.now().strftime('%Y%m%d%H%M')}"

        data = {
            'trade_in_number': trade_number,
            'customer_name': customer,
            'customer_phone': phone_var.text(),
            'product_name': product,
            'product_condition': condition_var.currentText(),
            'trade_in_value': value,
            'credit_amount': credit,
            'status': 'pending',
            'created_by': current_user,
        }

        try:
            svc.tradein.create_trade_in(data, current_user)
            QMessageBox.information(dlg, "Success", f"Trade-in created: {trade_number}")
            dlg.accept()
            if hasattr(parent, 'refresh'):
                parent.refresh()
        except Exception as e:
            logging.exception("Failed to create trade-in")
            QMessageBox.critical(dlg, "Error", f"Failed: {e}")

    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    make_button(btn_layout, "\U0001f4be Create", command=save, kind="success", width=BTN_WIDTH['action'])
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary", width=BTN_WIDTH['dialog'])
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()


def create_service_tab(parent, current_user=None):
    """Creates the service/repair management tab."""
    window = QFrame()
    window.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_layout, "\U0001f527 Service & Repair", font=FONT_HEADING)

    def open_new_ticket():
        open_service_ticket_dialog(window, current_user=current_user)

    make_button(header_layout, "\u2795 New Service Ticket", command=open_new_ticket, kind="warning")

    layout.addWidget(header_frame)

    # Summary
    summary_frame = QFrame()
    summary_layout = QGridLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 0)
    for i in range(4):
        summary_layout.setColumnStretch(i, 1)

    def create_summary_card(parent_layout, title, value, col):
        card = make_card(parent_layout, padding=12)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        styled_label(card_layout, text=title, font=("Segoe UI", 9), foreground="#6c757d")
        value_label = styled_label(card_layout, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        parent_layout.addWidget(card, 0, col)
        return value_label

    received_lbl = create_summary_card(summary_layout, "Received", 0, 0)
    in_progress_lbl = create_summary_card(summary_layout, "In Progress", 0, 1)
    completed_lbl = create_summary_card(summary_layout, "Completed", 0, 2)
    revenue_lbl = create_summary_card(summary_layout, "Revenue", "Rs. 0", 3)

    summary_labels = {'received': received_lbl, 'in_progress': in_progress_lbl,
                      'completed': completed_lbl, 'revenue': revenue_lbl}
    layout.addWidget(summary_frame)

    # Table
    table_frame = make_card(window, padding=10)
    table_layout = QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
    tree = QTableWidget()
    columns = ("ticket_number", "customer", "device", "status", "estimated", "received_date")
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in columns])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    table_layout.addWidget(tree)
    layout.addWidget(table_frame)

    def refresh_from_db():
        """Reload service tickets from the database via services."""
        tree.setRowCount(0)
        tickets = svc.service_ticket.get_all_tickets()

        counts = {'received': 0, 'in_progress': 0, 'completed': 0, 'revenue': 0}
        for t in tickets:
            status = t.get('status', 'received')
            if status in counts:
                counts[status] += 1
            if status == 'completed':
                counts['revenue'] += t.get('final_cost', 0) or 0

            device = f"{t.get('device_brand', '')} {t.get('device_model', '')}".strip()
            if not device:
                device = t.get('device_type', '')

            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QTableWidgetItem(t.get('ticket_number', '')))
            tree.setItem(row, 1, QTableWidgetItem(t.get('customer_name', '')))
            tree.setItem(row, 2, QTableWidgetItem(device))
            tree.setItem(row, 3, QTableWidgetItem(status.replace('_', ' ').title()))
            tree.setItem(row, 4, QTableWidgetItem(f"Rs. {t.get('estimated_cost', 0):,.2f}"))
            tree.setItem(row, 5, QTableWidgetItem(t.get('received_date', 'N/A')[:10] if t.get('received_date') else 'N/A'))

        summary_labels['received'].setText(str(counts['received']))
        summary_labels['in_progress'].setText(str(counts['in_progress']))
        summary_labels['completed'].setText(str(counts['completed']))
        summary_labels['revenue'].setText(f"Rs. {counts['revenue']:,.2f}")

    window.refresh = refresh_from_db
    refresh_from_db()

    return window


def open_service_ticket_dialog(parent, current_user=None):
    """Dialog to create a new service ticket."""
    from PySide6.QtWidgets import QDialog, QMessageBox
    dlg = QDialog(parent)
    dlg.setWindowTitle("New Service Ticket")
    dlg.resize(800, 850)
    dlg.setMinimumSize(650, 700)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    styled_label(content_layout, "\U0001f527 New Service Ticket", font=FONT_HEADING)

    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(1, 1)

    # Customer
    form_layout.addWidget(styled_label(None, "Customer Name *:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)
    customer_var = QLineEdit()
    form_layout.addWidget(customer_var, 1, 0, 1, 2)

    # Phone
    form_layout.addWidget(styled_label(None, "Phone:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    phone_var = QLineEdit()
    form_layout.addWidget(phone_var, 3, 0, 1, 2)

    # Email
    form_layout.addWidget(styled_label(None, "Email:", font=FONT_BOLD), 4, 0, alignment=Qt.AlignLeft)
    email_var = QLineEdit()
    form_layout.addWidget(email_var, 5, 0, 1, 2)

    # Device
    form_layout.addWidget(styled_label(None, "Device Type:", font=FONT_BOLD), 6, 0, alignment=Qt.AlignLeft)
    device_type_var = QLineEdit()
    form_layout.addWidget(device_type_var, 7, 0, 1, 2)

    form_layout.addWidget(styled_label(None, "Brand:", font=FONT_BOLD), 8, 0, alignment=Qt.AlignLeft)
    brand_var = QLineEdit()
    form_layout.addWidget(brand_var, 9, 0)

    form_layout.addWidget(styled_label(None, "Model:", font=FONT_BOLD), 8, 1, alignment=Qt.AlignLeft)
    model_var = QLineEdit()
    form_layout.addWidget(model_var, 9, 1)

    # Serial
    form_layout.addWidget(styled_label(None, "Serial Number:", font=FONT_BOLD), 10, 0, alignment=Qt.AlignLeft)
    serial_var = QLineEdit()
    form_layout.addWidget(serial_var, 11, 0, 1, 2)

    # Issue
    form_layout.addWidget(styled_label(None, "Issue Description *:", font=FONT_BOLD), 12, 0, alignment=Qt.AlignLeft)
    issue_text = QTextEdit()
    issue_text.setMaximumHeight(60)
    form_layout.addWidget(issue_text, 13, 0, 1, 2)

    # Estimated cost
    form_layout.addWidget(styled_label(None, "Estimated Cost (Rs.):", font=FONT_BOLD), 14, 0, alignment=Qt.AlignLeft)
    cost_var = QLineEdit("0")
    form_layout.addWidget(cost_var, 15, 0)

    content_layout.addWidget(form_frame)

    def save():
        customer = customer_var.text().strip()
        issue = issue_text.toPlainText().strip()

        if not customer or not issue:
            QMessageBox.critical(dlg, "Error", "Customer name and issue description required")
            return

        ticket_number = f"SVC-{datetime.now().strftime('%Y%m%d%H%M')}"

        data = {
            'ticket_number': ticket_number,
            'customer_name': customer,
            'customer_phone': phone_var.text(),
            'customer_email': email_var.text(),
            'device_type': device_type_var.text(),
            'device_brand': brand_var.text(),
            'device_model': model_var.text(),
            'serial_number': serial_var.text(),
            'issue_description': issue,
            'estimated_cost': float(cost_var.text()),
            'status': 'received',
            'created_by': current_user,
        }

        try:
            svc.service_ticket.create_ticket(data, current_user)
            QMessageBox.information(dlg, "Success", f"Service ticket created: {ticket_number}")
            dlg.accept()
            if hasattr(parent, 'refresh'):
                parent.refresh()
        except Exception as e:
            logging.exception("Failed to create service ticket")
            QMessageBox.critical(dlg, "Error", f"Failed: {e}")

    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    make_button(btn_layout, "\U0001f4be Create Ticket", command=save, kind="warning", width=BTN_WIDTH['action'])
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary", width=BTN_WIDTH['dialog'])
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()
