"""
Lease & Rental Management Module
=================================
Complete lease/rental system with tracking, payments, and returns.
"""

from PySide6.QtWidgets import (QFrame, QLabel, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QComboBox, QLineEdit, QTextEdit, QHeaderView,
                               QAbstractItemView, QTableWidget, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import Qt
import logging
from datetime import datetime, timedelta

from services import svc
from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING


def create_lease_management_tab(parent, current_user=None):
    """
    Creates the lease management tab.
    """
    window = QFrame()
    window.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_layout, "🎯 Lease & Rental Management", font=FONT_BOLD)

    def open_new_lease():
        open_create_lease_dialog(window, current_user=current_user)

    make_button(header_layout, "➕ New Lease", command=open_new_lease, kind="success")

    layout.addWidget(header_frame)

    # Summary cards
    summary_frame = QFrame()
    summary_layout = QGridLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 0)
    for i in range(5):
        summary_layout.setColumnStretch(i, 1)

    def create_summary_card(parent_layout, title, value, col):
        card = make_card(parent_layout, padding=12)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        styled_label(card_layout, text=title, font=("Segoe UI", 9), foreground="#6c757d")
        value_label = styled_label(card_layout, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        parent_layout.addWidget(card, 0, col)
        return value_label

    active_lbl = create_summary_card(summary_layout, "Active Leases", 0, 0)
    expiring_lbl = create_summary_card(summary_layout, "Expiring Soon", 0, 1)
    overdue_lbl = create_summary_card(summary_layout, "Overdue Payments", 0, 2)
    pending_lbl = create_summary_card(summary_layout, "Pending Return", 0, 3)
    revenue_lbl = create_summary_card(summary_layout, "Monthly Revenue", "Rs. 0", 4)

    summary_labels = {
        'active': active_lbl,
        'expiring': expiring_lbl,
        'overdue': overdue_lbl,
        'pending': pending_lbl,
        'revenue': revenue_lbl
    }
    layout.addWidget(summary_frame)

    # Filter toolbar
    toolbar_frame = QFrame()
    toolbar_layout = QHBoxLayout(toolbar_frame)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(toolbar_layout, "Status:")

    status_combo = QComboBox()
    status_combo.addItems(["all", "active", "completed", "defaulted", "expired"])
    status_combo.setCurrentText("all")
    toolbar_layout.addWidget(status_combo)

    def apply_filter():
        refresh_from_db()

    make_button(toolbar_layout, "Apply", command=apply_filter, kind="primary")
    make_button(toolbar_layout, "Clear", command=lambda: (status_combo.setCurrentText("all"), refresh_from_db()), kind="secondary")

    layout.addWidget(toolbar_frame)

    # Leases table
    table_frame = make_card(window, padding=10)
    table_layout = QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    columns = ("lease_id", "customer", "product", "start_date", "end_date", "monthly_amount", "status", "last_payment")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([
        "Lease #", "Customer", "Product", "Start Date", "End Date", "Monthly", "Status", "Last Payment"
    ])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    table_layout.addWidget(tree)
    layout.addWidget(table_frame)

    # Action buttons
    action_frame = QFrame()
    action_layout = QHBoxLayout(action_frame)
    action_layout.setContentsMargins(0, 0, 0, 0)

    def on_view_details():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(window, "Select", "Please select a lease")
            return

        row = sel[0].row()
        lease_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if lease_id:
            open_lease_details(window, lease_id=int(lease_id), current_user=current_user)

    def on_record_payment():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(window, "Select", "Please select a lease")
            return

        row = sel[0].row()
        lease_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if lease_id:
            open_record_payment_dialog(window, lease_id=int(lease_id), current_user=current_user)

    def on_return_item():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(window, "Select", "Please select a lease")
            return

        row = sel[0].row()
        lease_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if lease_id:
            open_return_item_dialog(window, lease_id=int(lease_id))

    make_button(action_layout, "👁️ View Details", command=on_view_details, kind="primary")
    make_button(action_layout, "💰 Record Payment", command=on_record_payment, kind="success")
    make_button(action_layout, "📦 Return Item", command=on_return_item, kind="warning")

    layout.addWidget(action_frame)

    # Store state
    window.status_combo = status_combo
    window.tree = tree
    window.summary_labels = summary_labels

    def refresh_from_db():
        """Refresh leases list from database through services."""
        tree.setRowCount(0)

        status_filter = status_combo.currentText() if status_combo.currentText() != "all" else None
        today = datetime.now().strftime('%Y-%m-%d')

        # Fetch leases through service
        leases = svc.lease.get_all_leases(status=status_filter)

        # Fetch lease payments for summary calculations
        all_payments = svc.stock_transfer.get_lease_payments()

        # Build payment aggregates per lease
        payment_totals = {}
        for p in all_payments:
            lid = p['lease_id']
            if lid not in payment_totals:
                payment_totals[lid] = {'total_paid': 0, 'last_payment_date': None}
            payment_totals[lid]['total_paid'] += p['amount_paid'] or 0
            if p['payment_date']:
                if payment_totals[lid]['last_payment_date'] is None or p['payment_date'] > payment_totals[lid]['last_payment_date']:
                    payment_totals[lid]['last_payment_date'] = p['payment_date']

        # Update summary
        active_count = sum(1 for l in leases if l['status'] == 'active')
        expiring_count = sum(1 for l in leases if l['status'] == 'active' and l.get('end_date') and
                            datetime.strptime(l['end_date'], '%Y-%m-%d').date() <= (datetime.now() + timedelta(days=7)).date())
        overdue_count = sum(1 for l in leases if l['status'] == 'active' and l.get('last_payment_date') and
                           datetime.strptime(l['last_payment_date'], '%Y-%m-%d').date() < (datetime.now() - timedelta(days=7)).date())
        pending_count = sum(1 for l in leases if l['status'] == 'active' and l.get('end_date') and
                           datetime.strptime(l['end_date'], '%Y-%m-%d').date() <= datetime.now().date())

        # Calculate monthly revenue from payments
        monthly_revenue = sum(p['amount_paid'] or 0 for p in all_payments
                             if p['payment_date'] and p['payment_date'] >= (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))

        summary_labels['active'].setText(str(active_count))
        summary_labels['expiring'].setText(str(expiring_count))
        summary_labels['overdue'].setText(str(overdue_count))
        summary_labels['pending'].setText(str(pending_count))
        summary_labels['revenue'].setText(f"Rs. {monthly_revenue:,.2f}")

        # Populate table
        for lease in leases:
            lease_id = lease.get('lease_id')
            payment_info = payment_totals.get(lease_id, {'total_paid': 0, 'last_payment_date': None})

            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QTableWidgetItem(str(lease_id)))
            tree.setItem(row, 1, QTableWidgetItem(lease.get('customer_name', '')))
            tree.setItem(row, 2, QTableWidgetItem(lease.get('product_name', '')))
            tree.setItem(row, 3, QTableWidgetItem(lease.get('start_date', 'N/A')[:10] if lease.get('start_date') else 'N/A'))
            tree.setItem(row, 4, QTableWidgetItem(lease.get('end_date', 'N/A')[:10] if lease.get('end_date') else 'N/A'))
            tree.setItem(row, 5, QTableWidgetItem(f"Rs. {lease.get('monthly_amount', 0):,.2f}"))
            tree.setItem(row, 6, QTableWidgetItem(lease.get('status', 'unknown').replace('_', ' ').title()))
            tree.setItem(row, 7, QTableWidgetItem(payment_info['last_payment_date'][:10] if payment_info['last_payment_date'] else 'Never'))

    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_create_lease_dialog(parent, current_user=None):
    """Dialog to create a new lease."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Create New Lease")
    dlg.resize(950, 900)
    dlg.setMinimumSize(750, 700)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    # Heading
    styled_label(content_layout, "New Lease Agreement", font=FONT_BOLD)

    # Form
    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(0, 0)
    form_layout.setColumnMinimumWidth(0, 150)
    form_layout.setColumnStretch(1, 1)

    # Customer
    form_layout.addWidget(styled_label(None, "Customer Name *:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)
    customer_var = QLineEdit()
    form_layout.addWidget(customer_var, 1, 0, 1, 2)

    # Product
    form_layout.addWidget(styled_label(None, "Product *:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    product_var = QComboBox()
    form_layout.addWidget(product_var, 3, 0, 1, 2)

    # Load products through service
    products = svc.inventory.get_all_products(active_only=True)
    products = [p for p in products if p.get('stock', 0) > 0]

    product_data = [(p['id'], f"{p['model']} (Price: Rs. {p['selling_price']}, Stock: {p['stock']})") for p in products]
    product_var.addItems([p[1] for p in product_data])

    # Lease terms
    form_layout.addWidget(styled_label(None, "Lease Duration (months) *:", font=FONT_BOLD), 4, 0, alignment=Qt.AlignLeft)
    duration_var = QLineEdit("12")
    form_layout.addWidget(duration_var, 5, 0)

    form_layout.addWidget(styled_label(None, "Monthly Amount (Rs.) *:", font=FONT_BOLD), 4, 1, alignment=Qt.AlignLeft)
    monthly_var = QLineEdit("0")
    form_layout.addWidget(monthly_var, 5, 1)

    # Dates
    form_layout.addWidget(styled_label(None, "Start Date *:", font=FONT_BOLD), 6, 0, alignment=Qt.AlignLeft)
    start_var = QLineEdit(datetime.now().strftime('%Y-%m-%d'))
    form_layout.addWidget(start_var, 7, 0)

    form_layout.addWidget(styled_label(None, "End Date:", font=FONT_BOLD), 6, 1, alignment=Qt.AlignLeft)
    end_var = QLineEdit()
    form_layout.addWidget(end_var, 7, 1)

    # Security deposit
    form_layout.addWidget(styled_label(None, "Security Deposit (Rs.):", font=FONT_BOLD), 8, 0, alignment=Qt.AlignLeft)
    deposit_var = QLineEdit("0")
    form_layout.addWidget(deposit_var, 9, 0)

    # Notes
    form_layout.addWidget(styled_label(None, "Notes:", font=FONT_BOLD), 10, 0, alignment=Qt.AlignLeft)
    notes_text = QTextEdit()
    notes_text.setMaximumHeight(60)
    form_layout.addWidget(notes_text, 11, 0, 1, 2)

    content_layout.addWidget(form_frame)

    def save_lease():
        customer = customer_var.text().strip()
        product_sel = product_var.currentText()
        duration = duration_var.text().strip()
        monthly = monthly_var.text().strip()
        start_date = start_var.text().strip()
        end_date = end_var.text().strip()
        deposit = deposit_var.text().strip()
        notes = notes_text.toPlainText().strip()

        if not customer:
            QMessageBox.critical(dlg, "Error", "Customer name required")
            return

        if not product_sel:
            QMessageBox.critical(dlg, "Error", "Please select a product")
            return

        try:
            duration_months = int(duration)
            monthly_amount = float(monthly)
            security_deposit = float(deposit) if deposit else 0

            if duration_months <= 0 or monthly_amount <= 0:
                raise ValueError("Duration and amount must be positive")
        except ValueError as e:
            QMessageBox.critical(dlg, "Error", f"Invalid duration or amount: {e}")
            return

        # Get product ID
        product_id = None
        product_name = None
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                break

        # Calculate end date if not provided
        if not end_date:
            end_dt = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=duration_months * 30)
            end_date = end_dt.strftime('%Y-%m-%d')

        # Generate lease ID
        lease_id = f"LEASE-{datetime.now().strftime('%Y%m%d%H%M')}"

        try:
            # Create lease through service
            lease_data = {
                'lease_id': lease_id,
                'customer_name': customer,
                'product_id': product_id,
                'product_name': product_name,
                'start_date': start_date,
                'end_date': end_date,
                'monthly_amount': monthly_amount,
                'duration_months': duration_months,
                'security_deposit': security_deposit,
                'status': 'active',
                'notes': notes,
                'created_by': current_user,
            }
            svc.lease.create_lease(lease_data, username=current_user)

            # Deduct from stock through service
            product = svc.inventory.get_product_by_id(product_id)
            if product:
                svc.inventory.adjust_stock(product['model'], -1, username=current_user, reason=f"Lease {lease_id}")

            QMessageBox.information(dlg, "Success", f"Lease created: {lease_id}")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to create lease")
            QMessageBox.critical(dlg, "Error", f"Failed to create lease: {e}")

    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    make_button(btn_layout, "💾 Create Lease", command=save_lease, kind="success")
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary")
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()


def open_lease_details(parent, lease_id, current_user=None):
    """View lease details."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Lease Details")
    dlg.resize(950, 850)
    dlg.setMinimumSize(750, 700)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    # Get lease through service
    leases = svc.lease.get_all_leases()
    lease = None
    for l in leases:
        if str(l.get('lease_id')) == str(lease_id):
            lease = l
            break

    if not lease:
        QMessageBox.critical(dlg, "Error", "Lease not found")
        dlg.reject()
        return

    # Header
    styled_label(content_layout, f"Lease: {lease['lease_id']}", font=FONT_BOLD)
    styled_label(content_layout, f"Status: {lease['status'].title()}", foreground=COLOR_PRIMARY)

    # Info
    info_frame = make_card(content, padding=15)
    info_layout = QVBoxLayout(info_frame)

    info = [
        ("Customer:", lease.get('customer_name', 'N/A')),
        ("Product:", lease.get('product_name', 'N/A')),
        ("Start Date:", lease.get('start_date', 'N/A')[:10] if lease.get('start_date') else 'N/A'),
        ("End Date:", lease.get('end_date', 'N/A')[:10] if lease.get('end_date') else 'N/A'),
        ("Monthly Amount:", f"Rs. {lease.get('monthly_amount', 0):,.2f}"),
        ("Duration:", f"{lease.get('duration_months', 0)} months"),
        ("Security Deposit:", f"Rs. {lease.get('security_deposit', 0):,.2f}"),
    ]

    for label, value in info:
        frame = QFrame()
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        styled_label(frame_layout, f"{label}", font=("Segoe UI", 10, "bold"))
        styled_label(frame_layout, f"{value}")
        info_layout.addWidget(frame)

    content_layout.addWidget(info_frame)

    # Payment history
    styled_label(content_layout, "Payment History:", font=FONT_BOLD)

    payments_frame = make_card(content, padding=10)
    payments_layout = QVBoxLayout(payments_frame)

    columns = ("date", "amount", "method", "notes")
    payments_tree = QTableWidget()
    payments_tree.setColumnCount(len(columns))
    payments_tree.setHorizontalHeaderLabels([col.title() for col in columns])
    payments_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    payments_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    payments_tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    payments_tree.verticalHeader().setVisible(False)
    payments_tree.setMaximumHeight(150)

    payments_layout.addWidget(payments_tree)

    # Fetch payments through service
    payments = svc.stock_transfer.get_lease_payments(lease_id=lease_id)

    for row_data in payments:
        row = payments_tree.rowCount()
        payments_tree.insertRow(row)
        payments_tree.setItem(row, 0, QTableWidgetItem(row_data['payment_date'][:10] if row_data['payment_date'] else 'N/A'))
        payments_tree.setItem(row, 1, QTableWidgetItem(f"Rs. {row_data['amount_paid']:,.2f}"))
        payments_tree.setItem(row, 2, QTableWidgetItem(row_data['payment_method'] or 'Cash'))
        payments_tree.setItem(row, 3, QTableWidgetItem(row_data['notes'] or ''))

    if not payments:
        styled_label(payments_layout, "No payments recorded yet", foreground=COLOR_WARNING)

    content_layout.addWidget(payments_frame)

    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dlg.reject)
    content_layout.addWidget(close_btn)

    dlg.setLayout(content_layout)
    dlg.exec()


def open_record_payment_dialog(parent, lease_id, current_user=None):
    """Dialog to record a lease payment."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Record Lease Payment")
    dlg.resize(800, 700)
    dlg.setMinimumSize(650, 550)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    styled_label(content_layout, "Record Payment", font=FONT_BOLD)

    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(0, 0)
    form_layout.setColumnMinimumWidth(0, 150)
    form_layout.setColumnStretch(1, 1)

    # Amount
    form_layout.addWidget(styled_label(None, "Amount (Rs.) *:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)
    amount_var = QLineEdit()
    form_layout.addWidget(amount_var, 1, 0)

    # Payment method
    form_layout.addWidget(styled_label(None, "Payment Method:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    method_var = QComboBox()
    method_var.addItems(["cash", "check", "bank_transfer", "card", "other"])
    method_var.setCurrentText("cash")
    form_layout.addWidget(method_var, 3, 0)

    # Payment date
    form_layout.addWidget(styled_label(None, "Payment Date:", font=FONT_BOLD), 4, 0, alignment=Qt.AlignLeft)
    date_var = QLineEdit(datetime.now().strftime('%Y-%m-%d'))
    form_layout.addWidget(date_var, 5, 0)

    # Notes
    form_layout.addWidget(styled_label(None, "Notes:", font=FONT_BOLD), 6, 0, alignment=Qt.AlignLeft)
    notes_text = QTextEdit()
    notes_text.setMaximumHeight(60)
    form_layout.addWidget(notes_text, 7, 0)

    content_layout.addWidget(form_frame)

    def save_payment():
        amount = amount_var.text().strip()
        method = method_var.currentText()
        payment_date = date_var.text().strip()
        notes = notes_text.toPlainText().strip()

        if not amount:
            QMessageBox.critical(dlg, "Error", "Amount required")
            return

        try:
            amount_paid = float(amount)
            if amount_paid <= 0:
                raise ValueError("Amount must be positive")
        except ValueError as e:
            QMessageBox.critical(dlg, "Error", f"Invalid amount: {e}")
            return

        try:
            # Record payment through service
            payment_data = {
                "lease_id": lease_id,
                "payment_date": payment_date,
                "amount_paid": amount_paid,
                "payment_method": method,
                "notes": notes,
                "recorded_by": current_user
            }
            svc.stock_transfer.record_lease_payment(payment_data, username=current_user)

            # Update lease last payment date through service
            svc.lease.update_lease(str(lease_id), {'last_payment_date': payment_date}, username=current_user)

            QMessageBox.information(dlg, "Success", "Payment recorded")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to record payment")
            QMessageBox.critical(dlg, "Error", f"Failed to record payment: {e}")

    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    make_button(btn_layout, "💾 Record Payment", command=save_payment, kind="success")
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary")
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()


def open_return_item_dialog(parent, lease_id):
    """Dialog to process lease item return."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Return Lease Item")
    dlg.resize(850, 750)
    dlg.setMinimumSize(700, 600)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    styled_label(content_layout, "Return Lease Item", font=FONT_BOLD)

    # Get lease info through service
    leases = svc.lease.get_all_leases()
    lease = None
    for l in leases:
        if str(l.get('lease_id')) == str(lease_id):
            lease = l
            break

    if not lease:
        QMessageBox.critical(dlg, "Error", "Lease not found")
        dlg.reject()
        return

    styled_label(content_layout, f"Product: {lease.get('product_name', 'N/A')}", font=FONT_BOLD)
    styled_label(content_layout, f"Customer: {lease.get('customer_name', 'N/A')}", foreground=COLOR_PRIMARY)

    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(0, 0)
    form_layout.setColumnMinimumWidth(0, 150)
    form_layout.setColumnStretch(1, 1)

    # Condition
    form_layout.addWidget(styled_label(None, "Item Condition:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)
    condition_var = QComboBox()
    condition_var.addItems(["good", "fair", "damaged", "needs_repair"])
    condition_var.setCurrentText("good")
    form_layout.addWidget(condition_var, 1, 0)

    # Return date
    form_layout.addWidget(styled_label(None, "Return Date:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    date_var = QLineEdit(datetime.now().strftime('%Y-%m-%d'))
    form_layout.addWidget(date_var, 3, 0)

    # Notes
    form_layout.addWidget(styled_label(None, "Return Notes:", font=FONT_BOLD), 4, 0, alignment=Qt.AlignLeft)
    notes_text = QTextEdit()
    notes_text.setMaximumHeight(60)
    form_layout.addWidget(notes_text, 5, 0)

    # Deduct from security
    deduct_var = QLineEdit("0")
    form_layout.addWidget(styled_label(None, "Deduction from Security (Rs.):", font=FONT_BOLD), 6, 0, alignment=Qt.AlignLeft)
    form_layout.addWidget(deduct_var, 7, 0)

    content_layout.addWidget(form_frame)

    def process_return():
        condition = condition_var.currentText()
        return_date = date_var.text().strip()
        notes = notes_text.toPlainText().strip()
        deduction = deduct_var.text().strip()

        try:
            # Update lease status through service
            svc.lease.update_lease(str(lease_id), {
                'status': 'completed',
                'return_date': return_date,
                'return_condition': condition,
                'return_notes': notes,
                'security_deduction': float(deduction) if deduction else 0,
            }, username="system")

            # Add product back to stock through service
            product_name = lease.get('product_name')
            if product_name:
                product = svc.inventory.get_product_by_model(product_name)
                if product:
                    svc.inventory.adjust_stock(product['model'], 1, username="system", reason=f"Lease {lease_id} returned")

            QMessageBox.information(dlg, "Success", "Item returned successfully")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to process return")
            QMessageBox.critical(dlg, "Error", f"Failed to process return: {e}")

    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    make_button(btn_layout, "📦 Process Return", command=process_return, kind="warning")
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary")
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()
