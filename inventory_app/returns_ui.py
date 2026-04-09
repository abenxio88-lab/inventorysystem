"""
RMA/Returns Management Module
==============================
Return Merchandise Authorization and returns processing.
Phase 5 - Complete Implementation
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
from datetime import datetime

from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED
)

from services import svc


def create_returns_tab(parent, current_user=None):
    """
    Creates the returns/RMA management tab.
    """
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 15)
    styled_label(header_frame, "Returns & RMA", font=FONT_HEADING)
    header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
    main_layout.addWidget(header_frame)

    # New Return button
    def open_new_return():
        open_create_return_dialog(window, current_user=current_user)

    new_btn = make_button(header_frame, "New Return", command=open_new_return, kind="warning")
    header_layout.addStretch()
    header_layout.addWidget(new_btn)

    # Summary cards
    summary_frame = QtWidgets.QWidget()
    summary_layout = QtWidgets.QHBoxLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 15)
    summary_layout.setSpacing(8)
    main_layout.addWidget(summary_frame)

    def create_summary_card(parent, title, value):
        card = make_card(parent, padding=12)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        title_lbl = styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d")
        card_layout.addWidget(title_lbl)
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        card_layout.addWidget(value_label)
        card_layout.addStretch()
        summary_layout.addWidget(card)
        return value_label

    pending_lbl = create_summary_card(summary_frame, "Pending", 0)
    approved_lbl = create_summary_card(summary_frame, "Approved", 0)
    refunded_lbl = create_summary_card(summary_frame, "Refunded", 0)
    total_lbl = create_summary_card(summary_frame, "Total Returns", 0)

    window.summary_labels = {
        'pending': pending_lbl,
        'approved': approved_lbl,
        'refunded': refunded_lbl,
        'total': total_lbl
    }

    # Filter toolbar
    toolbar_frame = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar_frame)
    toolbar_layout.setContentsMargins(0, 0, 0, 10)
    main_layout.addWidget(toolbar_frame)

    styled_label(toolbar_frame, "Status:")
    status_combo = QtWidgets.QComboBox()
    status_combo.addItems(["all", "pending", "approved", "refunded", "rejected"])
    toolbar_layout.addWidget(status_combo)

    def apply_filter():
        refresh_returns()

    apply_btn = make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary")
    toolbar_layout.addWidget(apply_btn)
    clear_btn = make_button(toolbar_frame, "Clear", command=lambda: (status_combo.setCurrentText("all"), refresh_returns()), kind="secondary")
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch()

    # Returns table
    table_frame = make_card(window, padding=10)
    table_layout = QtWidgets.QHBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(table_frame)

    columns = ("return_number", "customer", "date", "reason", "amount", "status")
    column_map = {
        "return_number": ("Return #", 120),
        "customer": ("Customer", 200),
        "date": ("Date", 100),
        "reason": ("Reason", 250),
        "amount": ("Refund Amount", 120),
        "status": ("Status", 100)
    }

    tree = QtWidgets.QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([column_map[c][0] for c in columns])
    tree.horizontalHeader().setStretchLastSection(True)
    tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

    for i, col in enumerate(columns):
        tree.setColumnWidth(i, column_map[col][1])

    table_layout.addWidget(tree)

    # Action buttons
    action_frame = QtWidgets.QWidget()
    action_layout = QtWidgets.QHBoxLayout(action_frame)
    action_layout.setContentsMargins(0, 10, 0, 0)
    main_layout.addWidget(action_frame)

    def on_view_details():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select a return")
            return

        row = selected_rows[0].row()
        return_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if return_id:
            open_return_details(window, return_number=return_id, current_user=current_user)

    def on_approve():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select a return")
            return

        row = selected_rows[0].row()
        return_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if return_id:
            approve_return(return_id, refresh_callback=refresh_returns)

    view_btn = make_button(action_frame, "View Details", command=on_view_details, kind="primary")
    action_layout.addWidget(view_btn)
    approve_btn = make_button(action_frame, "Approve Return", command=on_approve, kind="success")
    action_layout.addWidget(approve_btn)
    action_layout.addStretch()

    # Store state
    window.status_combo = status_combo
    window.tree = tree

    def refresh_returns():
        """Refresh returns list from database through services."""
        tree.setRowCount(0)

        status_filter = status_combo.currentText()
        status_arg = None if status_filter == 'all' else status_filter
        returns = svc.return_svc.get_all_returns(status=status_arg)

        # Update summary
        status_counts = {'pending': 0, 'approved': 0, 'refunded': 0, 'total': len(returns)}
        for ret in returns:
            if ret['status'] in status_counts:
                status_counts[ret['status']] += 1

        window.summary_labels['pending'].setText(str(status_counts['pending']))
        window.summary_labels['approved'].setText(str(status_counts['approved']))
        window.summary_labels['refunded'].setText(str(status_counts['refunded']))
        window.summary_labels['total'].setText(str(status_counts['total']))

        # Populate table
        for row_idx, ret in enumerate(returns):
            status_text = ret['status'].replace('_', ' ').title()
            tree.insertRow(row_idx)
            tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(ret['return_number']))
            tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(ret['customer_name']))
            tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(ret['return_date'][:10] if ret['return_date'] else 'N/A'))
            reason_text = ret['reason'][:50] + ('...' if len(ret['reason'] or '') > 50 else '')
            tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(reason_text))
            tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(f"Rs. {ret['total_refund']:,.2f}" if ret['total_refund'] else "Rs. 0.00"))
            tree.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(status_text))

    window.refresh_returns = refresh_returns
    refresh_returns()

    return window


def open_create_return_dialog(parent, current_user=None):
    """Dialog to create a new return."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Create Return/RMA")
    dlg.resize(900, 800)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Heading
    styled_label(dlg, "New Return/RMA", font=FONT_HEADING)

    # Customer info
    customer_frame = QtWidgets.QGroupBox("Customer Information")
    customer_layout = QtWidgets.QFormLayout(customer_frame)
    customer_layout.setSpacing(5)
    main_layout.addWidget(customer_frame)

    customer_name_entry = QtWidgets.QLineEdit()
    customer_layout.addRow(styled_label(customer_frame, "Customer Name *:", font=FONT_BOLD), customer_name_entry)

    customer_email_entry = QtWidgets.QLineEdit()
    customer_layout.addRow(styled_label(customer_frame, "Email:", font=FONT_BOLD), customer_email_entry)

    customer_phone_entry = QtWidgets.QLineEdit()
    customer_layout.addRow(styled_label(customer_frame, "Phone:", font=FONT_BOLD), customer_phone_entry)

    # Return details
    details_frame = QtWidgets.QGroupBox("Return Details")
    details_layout = QtWidgets.QFormLayout(details_frame)
    details_layout.setSpacing(5)
    main_layout.addWidget(details_frame)

    # Return number (auto-generated)
    return_number = f"RMA-{datetime.now().strftime('%Y%m%d%H%M')}"
    return_number_edit = QtWidgets.QLineEdit(return_number)
    return_number_edit.setReadOnly(True)
    details_layout.addRow(styled_label(details_frame, "Return Number:", font=FONT_BOLD), return_number_edit)

    # Return date
    return_date_edit = QtWidgets.QLineEdit(datetime.now().strftime('%Y-%m-%d'))
    details_layout.addRow(styled_label(details_frame, "Return Date *:", font=FONT_BOLD), return_date_edit)

    # Reason
    reason_combo = QtWidgets.QComboBox()
    reason_combo.addItems([
        "Defective Product", "Wrong Item", "Damaged in Shipping",
        "Not as Described", "Changed Mind", "Other"
    ])
    details_layout.addRow(styled_label(details_frame, "Reason *:", font=FONT_BOLD), reason_combo)

    # Items section
    styled_label(dlg, "Return Items:", font=FONT_BOLD)

    items_frame = make_card(dlg, padding=10)
    items_main_layout = QtWidgets.QVBoxLayout(items_frame)
    main_layout.addWidget(items_frame)

    # Add item row
    add_frame = QtWidgets.QWidget()
    add_layout = QtWidgets.QHBoxLayout(add_frame)
    add_layout.setContentsMargins(0, 0, 0, 10)
    items_main_layout.addWidget(add_frame)

    styled_label(add_frame, "Product:")

    product_combo = QtWidgets.QComboBox()
    add_layout.addWidget(product_combo, stretch=1)

    # Load products via service
    products = svc.inventory.get_all_products(active_only=True)
    product_data = [(p['id'], f"{p['model']} (Rs. {p['selling_price']})") for p in products]
    product_combo.addItems([p[1] for p in product_data])

    styled_label(add_frame, "Qty:")
    qty_edit = QtWidgets.QLineEdit("1")
    qty_edit.setFixedWidth(60)
    add_layout.addWidget(qty_edit)

    # Items tree
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(5)
    items_tree.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price", "Total", "Actions"])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    items_tree.setColumnWidth(0, 200)
    for i in range(1, 5):
        items_tree.setColumnWidth(i, 100)
    items_main_layout.addWidget(items_tree)

    # Return items storage
    return_items = []

    def add_item():
        product_sel = product_combo.currentText()
        qty = qty_edit.text()

        if not product_sel:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please select a product")
            return

        try:
            qty_int = int(qty)
            if qty_int <= 0:
                raise ValueError("must be positive")
        except ValueError as e:
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Invalid quantity: {e}")
            return

        # Find product
        product_id = None
        product_name = None
        unit_price = 0
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                unit_price = float(pname.split('Rs. ')[1].replace(')', '')) if 'Rs. ' in pname else 0
                break

        if not product_id:
            return

        line_total = qty_int * unit_price

        return_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': qty_int,
            'unit_price': unit_price,
            'line_total': line_total
        })

        # Update tree
        row = items_tree.rowCount()
        items_tree.insertRow(row)
        items_tree.setItem(row, 0, QtWidgets.QTableWidgetItem(product_name))
        items_tree.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty_int)))
        items_tree.setItem(row, 2, QtWidgets.QTableWidgetItem(f"Rs. {unit_price:,.2f}"))
        items_tree.setItem(row, 3, QtWidgets.QTableWidgetItem(f"Rs. {line_total:,.2f}"))
        items_tree.setItem(row, 4, QtWidgets.QTableWidgetItem("Remove"))

        product_combo.setCurrentIndex(-1)
        qty_edit.setText("1")
        update_total()

    def on_item_click(index):
        row = index.row()
        col = index.column()
        if col == 4:
            if 0 <= row < len(return_items):
                return_items.pop(row)
                items_tree.removeRow(row)
                update_total()

    items_tree.clicked.connect(on_item_click)

    add_btn = make_button(add_frame, "Add Item", command=add_item, kind="primary")
    add_layout.addWidget(add_btn)

    # Total
    total_label = styled_label(items_frame, "Total Refund: Rs. 0.00", font=("Segoe UI", 12, "bold"), foreground=COLOR_DANGER)
    total_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
    items_main_layout.addWidget(total_label)

    def update_total():
        total = sum(item['line_total'] for item in return_items)
        total_label.setText(f"Total Refund: Rs. {total:,.2f}")

    # Notes
    styled_label(dlg, "Notes:", font=FONT_BOLD)
    notes_edit = QtWidgets.QTextEdit()
    notes_edit.setMaximumHeight(80)
    main_layout.addWidget(notes_edit)

    # Buttons
    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 10, 0, 0)
    main_layout.addWidget(btn_frame)

    def save_return():
        customer_name = customer_name_entry.text().strip()
        customer_email = customer_email_entry.text().strip()
        customer_phone = customer_phone_entry.text().strip()
        return_date = return_date_edit.text().strip()
        reason = reason_combo.currentText()
        notes = notes_edit.toPlainText().strip()

        if not customer_name:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Customer name required")
            return

        if not reason:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please select a reason")
            return

        if not return_items:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please add at least one item")
            return

        total_refund = sum(item['line_total'] for item in return_items)

        try:
            return_data = {
                'return_number': return_number_edit.text(),
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'return_date': return_date,
                'reason': reason,
                'total_refund': total_refund,
                'notes': notes,
                'status': 'pending',
                'created_by': current_user,
            }

            svc.return_svc.create_return(return_data, return_items, username=current_user)

            QtWidgets.QMessageBox.information(dlg, "Success", f"Return created: {return_number_edit.text()}")
            dlg.accept()

            if hasattr(parent, 'refresh_returns'):
                parent.refresh_returns()

        except Exception as e:
            logging.exception("Failed to create return")
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Failed to create return: {e}")

    save_btn = make_button(btn_frame, "Create Return", command=save_return, kind="warning")
    btn_layout.addWidget(save_btn)
    cancel_btn = make_button(btn_frame, "Cancel", command=dlg.reject, kind="secondary")
    btn_layout.addWidget(cancel_btn)
    btn_layout.addStretch()


def open_return_details(parent, return_number, current_user=None):
    """View return details."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Return Details")
    dlg.resize(850, 750)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    returns = svc.return_svc.get_all_returns()
    ret = next((r for r in returns if r['return_number'] == return_number), None)

    if not ret:
        styled_label(dlg, "Return not found", foreground=COLOR_DANGER)
        close_btn = QtWidgets.QPushButton("Close", dlg)
        close_btn.clicked.connect(dlg.reject)
        main_layout.addWidget(close_btn)
        return

    # Header
    styled_label(dlg, f"Return: {ret['return_number']}", font=FONT_HEADING)
    styled_label(dlg, f"Status: {ret['status'].title()}", foreground=COLOR_PRIMARY)

    # Info
    info_frame = make_card(dlg, padding=15)
    info_layout = QtWidgets.QFormLayout(info_frame)
    main_layout.addWidget(info_frame)

    info = [
        ("Customer:", ret['customer_name']),
        ("Email:", ret['customer_email'] or 'N/A'),
        ("Phone:", ret['customer_phone'] or 'N/A'),
        ("Return Date:", ret['return_date'][:10] if ret['return_date'] else 'N/A'),
        ("Reason:", ret['reason']),
        ("Refund Amount:", f"Rs. {ret['total_refund']:,.2f}"),
    ]

    for lbl, val in info:
        info_layout.addRow(label(info_frame, lbl, kind="bold"), label(info_frame, val))

    # Items
    styled_label(dlg, "Return Items:", font=FONT_BOLD)

    items_frame = make_card(dlg, padding=10)
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    main_layout.addWidget(items_frame)

    columns = ("product", "quantity", "unit_price", "total")
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(len(columns))
    items_tree.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in columns])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    for i in range(4):
        items_tree.setColumnWidth(i, 120)
    items_layout.addWidget(items_tree)

    # Load return items through service
    return_items = svc.return_svc.get_return_items_by_number(return_number)
    for row_idx, row in enumerate(return_items):
        items_tree.insertRow(row_idx)
        items_tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(row['product_name']))
        items_tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row['quantity'])))
        items_tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"Rs. {row['unit_price']:,.2f}"))
        items_tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"Rs. {row['line_total']:,.2f}"))

    # Close button
    close_btn = QtWidgets.QPushButton("Close", dlg)
    close_btn.clicked.connect(dlg.reject)
    main_layout.addWidget(close_btn)


def approve_return(return_number, refresh_callback=None):
    """Approve a return."""
    reply = QtWidgets.QMessageBox.question(None, "Confirm", "Approve this return and process refund?",
                                           QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    if reply == QtWidgets.QMessageBox.StandardButton.Yes:
        try:
            svc.return_svc.approve_return(return_number, username="system")
            QtWidgets.QMessageBox.information(None, "Success", "Return approved")

            if refresh_callback:
                refresh_callback()

        except Exception as e:
            logging.exception("Failed to approve return")
            QtWidgets.QMessageBox.critical(None, "Error", f"Failed to approve return: {e}")
