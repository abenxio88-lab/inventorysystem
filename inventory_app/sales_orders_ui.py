"""
Sales Orders Module
====================
Complete sales order management system.
Create orders, track delivery, manage customers, and process payments.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
from datetime import datetime, timedelta

from ui_theme import (
    make_card, styled_label, make_button, label,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED
)
from services import svc


def create_sales_orders_tab(parent, current_user=None):
    """
    Creates the sales orders management tab.
    """
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 15)
    styled_label(header_frame, "Sales Orders", font=FONT_BOLD)
    header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
    main_layout.addWidget(header_frame)

    # New Order button
    def open_new_order():
        open_create_order_dialog(window, current_user=current_user)

    new_btn = make_button(header_frame, "New Sales Order", command=open_new_order, kind="success")
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

    confirmed_lbl = create_summary_card(summary_frame, "Confirmed", 0)
    processing_lbl = create_summary_card(summary_frame, "Processing", 0)
    shipped_lbl = create_summary_card(summary_frame, "Shipped", 0)
    delivered_lbl = create_summary_card(summary_frame, "Delivered", 0)
    total_lbl = create_summary_card(summary_frame, "Total Orders", 0)

    window.summary_labels = {
        'confirmed': confirmed_lbl,
        'processing': processing_lbl,
        'shipped': shipped_lbl,
        'delivered': delivered_lbl,
        'total': total_lbl
    }

    # Filter toolbar
    toolbar_frame = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar_frame)
    toolbar_layout.setContentsMargins(0, 0, 0, 10)
    main_layout.addWidget(toolbar_frame)

    styled_label(toolbar_frame, "Status:")
    status_combo = QtWidgets.QComboBox()
    status_combo.addItems(["all", "confirmed", "processing", "shipped", "delivered", "cancelled"])
    toolbar_layout.addWidget(status_combo)

    def apply_filter():
        refresh_orders()

    apply_btn = make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary")
    toolbar_layout.addWidget(apply_btn)
    clear_btn = make_button(toolbar_frame, "Clear", command=lambda: (status_combo.setCurrentText("all"), refresh_orders()), kind="secondary")
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch()

    # Orders table
    table_frame = make_card(window, padding=10)
    table_layout = QtWidgets.QHBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(table_frame)

    columns = ("order_number", "customer", "order_date", "delivery_date", "status", "total_amount", "payment")
    column_map = {
        "order_number": ("Order #", 120),
        "customer": ("Customer", 200),
        "order_date": ("Order Date", 100),
        "delivery_date": ("Delivery", 100),
        "status": ("Status", 100),
        "total_amount": ("Total", 120),
        "payment": ("Payment", 100)
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
            QtWidgets.QMessageBox.information(window, "Select", "Please select an order")
            return

        row = selected_rows[0].row()
        order_id_text = tree.item(row, 0).text() if tree.item(row, 0) else None

        if order_id_text:
            open_order_details(window, order_number=order_id_text, current_user=current_user)

    def on_update_status():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select an order")
            return

        row = selected_rows[0].row()
        order_id_text = tree.item(row, 0).text() if tree.item(row, 0) else None

        if order_id_text:
            open_update_status_dialog(window, order_number=order_id_text)

    view_btn = make_button(action_frame, "View Details", command=on_view_details, kind="primary")
    action_layout.addWidget(view_btn)
    update_btn = make_button(action_frame, "Update Status", command=on_update_status, kind="warning")
    action_layout.addWidget(update_btn)
    action_layout.addStretch()

    # Store state
    window.status_combo = status_combo
    window.tree = tree

    def refresh_from_db():
        """Reload all data from the database through services and refresh the UI."""
        tree.setRowCount(0)

        status_filter = status_combo.currentText()
        status_arg = None if status_filter == 'all' else status_filter
        orders = svc.sales.get_all_orders(status=status_arg)

        # Update summary
        status_counts = {'confirmed': 0, 'processing': 0, 'shipped': 0, 'delivered': 0, 'total': len(orders)}
        for order in orders:
            if order['status'] in status_counts:
                status_counts[order['status']] += 1

        window.summary_labels['confirmed'].setText(str(status_counts['confirmed']))
        window.summary_labels['processing'].setText(str(status_counts['processing']))
        window.summary_labels['shipped'].setText(str(status_counts['shipped']))
        window.summary_labels['delivered'].setText(str(status_counts['delivered']))
        window.summary_labels['total'].setText(str(status_counts['total']))

        # Populate table
        for row_idx, order in enumerate(orders):
            payment_status = order['payment_status'].replace('_', ' ').title()
            tree.insertRow(row_idx)
            tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(order['order_number']))
            tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(order['customer_name'] or 'Walk-in Customer'))
            tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(order['order_date'][:10] if order['order_date'] else 'N/A'))
            tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(order['delivery_date'][:10] if order['delivery_date'] else 'N/A'))
            tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(order['status'].replace('_', ' ').title()))
            tree.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(f"Rs. {order['total_amount']:,.2f}" if order['total_amount'] else 'Rs. 0.00'))
            tree.setItem(row_idx, 6, QtWidgets.QTableWidgetItem(payment_status))

    def refresh_orders():
        """Refresh sales orders list."""
        refresh_from_db()

    window.refresh_orders = refresh_orders
    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_create_order_dialog(parent, current_user=None):
    """Dialog to create a new sales order."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Create Sales Order")
    dlg.resize(950, 800)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Heading
    styled_label(dlg, "New Sales Order", font=FONT_BOLD)

    # Customer info frame
    customer_frame = QtWidgets.QGroupBox("Customer Information")
    customer_layout = QtWidgets.QFormLayout(customer_frame)
    customer_layout.setSpacing(5)
    main_layout.addWidget(customer_frame)

    # Customer fields
    customer_name_edit = QtWidgets.QLineEdit()
    customer_layout.addRow(styled_label(customer_frame, "Customer Name:"), customer_name_edit)

    customer_phone_edit = QtWidgets.QLineEdit()
    customer_layout.addRow(styled_label(customer_frame, "Phone:"), customer_phone_edit)

    customer_email_edit = QtWidgets.QLineEdit()
    customer_layout.addRow(styled_label(customer_frame, "Email:"), customer_email_edit)

    # Set default delivery date (3 days from now)
    default_delivery = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    delivery_edit = QtWidgets.QLineEdit(default_delivery)
    customer_layout.addRow(styled_label(customer_frame, "Delivery Date:"), delivery_edit)

    # Products list
    styled_label(dlg, "Add Products:", font=FONT_BOLD)

    products_frame = make_card(dlg, padding=10)
    products_main_layout = QtWidgets.QVBoxLayout(products_frame)
    main_layout.addWidget(products_frame)

    # Product selection row
    select_frame = QtWidgets.QWidget()
    select_layout = QtWidgets.QHBoxLayout(select_frame)
    select_layout.setContentsMargins(0, 0, 0, 10)
    products_main_layout.addWidget(select_frame)

    product_combo = QtWidgets.QComboBox()
    product_combo.setMinimumWidth(250)
    select_layout.addWidget(styled_label(select_frame, "Product:"), stretch=0)
    select_layout.addWidget(product_combo, stretch=1)

    # Load products with stock via service
    products = svc.inventory.get_all_products(active_only=True)
    products = [p for p in products if p.get('stock', 0) > 0]
    products.sort(key=lambda p: p.get('model', ''))

    product_data = [(p['id'], f"{p['model']} (Stock: {p['stock']}, Price: Rs. {p['selling_price']})") for p in products]
    product_combo.addItems([p[1] for p in product_data])

    qty_edit = QtWidgets.QLineEdit("1")
    qty_edit.setFixedWidth(60)
    select_layout.addWidget(styled_label(select_frame, "Qty:"))
    select_layout.addWidget(qty_edit)

    # Items list
    styled_label(dlg, "Order Items:", font=FONT_BOLD)

    items_frame = QtWidgets.QWidget()
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    items_layout.setContentsMargins(0, 0, 0, 0)
    products_main_layout.addWidget(items_frame)

    columns = ("product", "quantity", "unit_price", "total", "actions")
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(len(columns))
    items_tree.setHorizontalHeaderLabels([col.title() for col in columns])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    items_tree.setColumnWidth(0, 300)
    for i in range(1, 5):
        items_tree.setColumnWidth(i, 120)
    items_layout.addWidget(items_tree)

    # Order items storage
    order_items = []

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
        available_stock = 0

        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                # Get price from original products list
                for p in products:
                    if p['id'] == pid:
                        unit_price = p['selling_price']
                        available_stock = p['stock']
                        break
                break

        if not product_id:
            return

        # Check stock
        if qty_int > available_stock:
            reply = QtWidgets.QMessageBox.question(dlg, "Low Stock", f"Only {available_stock} in stock. Continue anyway?",
                                                     QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return

        total = qty_int * unit_price

        # Add to list
        order_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': qty_int,
            'unit_price': unit_price,
            'total': total
        })

        # Update tree
        row = items_tree.rowCount()
        items_tree.insertRow(row)
        items_tree.setItem(row, 0, QtWidgets.QTableWidgetItem(product_name))
        items_tree.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty_int)))
        items_tree.setItem(row, 2, QtWidgets.QTableWidgetItem(f"Rs. {unit_price:,.2f}"))
        items_tree.setItem(row, 3, QtWidgets.QTableWidgetItem(f"Rs. {total:,.2f}"))
        items_tree.setItem(row, 4, QtWidgets.QTableWidgetItem("Remove"))

        # Clear selection
        product_combo.setCurrentIndex(-1)
        qty_edit.setText("1")

    def on_item_click(index):
        row = index.row()
        col = index.column()
        if col == 4:
            if 0 <= row < len(order_items):
                order_items.pop(row)
                items_tree.removeRow(row)

    items_tree.clicked.connect(on_item_click)

    # Add button
    add_btn = make_button(select_frame, "Add", command=add_item, kind="primary")
    select_layout.addWidget(add_btn)

    # Payment info
    payment_frame = QtWidgets.QGroupBox("Payment Information")
    payment_layout = QtWidgets.QFormLayout(payment_frame)
    main_layout.addWidget(payment_frame)

    payment_combo = QtWidgets.QComboBox()
    payment_combo.addItems(["pending", "partial", "paid"])
    payment_layout.addRow(styled_label(payment_frame, "Payment Status:"), payment_combo)

    paid_edit = QtWidgets.QLineEdit("0")
    payment_layout.addRow(styled_label(payment_frame, "Paid Amount:"), paid_edit)

    # Notes
    styled_label(dlg, "Notes:", font=FONT_BOLD)
    notes_edit = QtWidgets.QTextEdit()
    notes_edit.setMaximumHeight(80)
    main_layout.addWidget(notes_edit)

    # Total label
    total_label = styled_label(dlg, "Total: Rs. 0.00", font=("Segoe UI", 14, "bold"), foreground=COLOR_PRIMARY)
    total_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
    main_layout.addWidget(total_label)

    # Buttons
    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 10, 0, 0)
    main_layout.addWidget(btn_frame)

    def save_order():
        customer_name = customer_name_edit.text().strip()
        customer_phone = customer_phone_edit.text().strip()
        customer_email = customer_email_edit.text().strip()
        delivery_date = delivery_edit.text().strip()
        payment_status = payment_combo.currentText()
        paid_amount = paid_edit.text()
        notes = notes_edit.toPlainText().strip()

        if not order_items:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please add at least one product")
            return

        # Generate order number
        order_number = f"SO-{datetime.now().strftime('%Y%m%d%H%M')}"

        # Build order data dict
        order_data = {
            'order_number': order_number,
            'customer_name': customer_name or 'Walk-in',
            'customer_phone': customer_phone,
            'customer_email': customer_email,
            'delivery_date': delivery_date or None,
            'status': 'confirmed',
            'payment_status': payment_status,
            'paid_amount': float(paid_amount) if paid_amount else 0,
            'notes': notes,
            'created_by': current_user,
        }

        # Build items list for service
        items_for_svc = []
        for item in order_items:
            items_for_svc.append({
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],
                'total_price': item['total'],
            })

        try:
            svc.sales.create_order(order_data, items_for_svc, username=current_user)

            QtWidgets.QMessageBox.information(dlg, "Success", f"Sales Order created: {order_number}")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()
            elif hasattr(parent, 'refresh_orders'):
                parent.refresh_orders()

        except Exception as e:
            logging.exception("Failed to create sales order")
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Failed to create order: {e}")

    create_btn = make_button(btn_frame, "Create Order", command=save_order, kind="success")
    btn_layout.addWidget(create_btn)
    cancel_btn = make_button(btn_frame, "Cancel", command=dlg.reject, kind="secondary")
    btn_layout.addWidget(cancel_btn)
    btn_layout.addStretch()
    
    dlg.setLayout(main_layout)
    dlg.exec()


def open_order_details(parent, order_number, current_user=None):
    """View sales order details."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Sales Order Details")
    dlg.resize(900, 750)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Get all orders and find the matching one via service
    all_orders = svc.sales.get_all_orders()
    order = None
    for o in all_orders:
        if o['order_number'] == order_number:
            order = o
            break

    if not order:
        QtWidgets.QMessageBox.critical(dlg, "Error", "Order not found")
        dlg.reject()
        return

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QVBoxLayout(header_frame)
    main_layout.addWidget(header_frame)

    styled_label(header_frame, f"Sales Order: {order['order_number']}", font=FONT_BOLD)
    status_color = COLOR_SUCCESS if order['status'] == 'delivered' else COLOR_PRIMARY
    styled_label(header_frame, f"Status: {order['status'].title()}", foreground=status_color)

    # Order Info
    info_frame = make_card(dlg, padding=15)
    info_layout = QtWidgets.QFormLayout(info_frame)
    main_layout.addWidget(info_frame)

    info = [
        ("Customer:", order['customer_name'] or 'Walk-in'),
        ("Phone:", order['customer_phone'] or 'N/A'),
        ("Email:", order['customer_email'] or 'N/A'),
        ("Order Date:", order['order_date'][:10] if order['order_date'] else 'N/A'),
        ("Delivery Date:", order['delivery_date'][:10] if order['delivery_date'] else 'N/A'),
        ("Payment:", f"{order['payment_status'].title()} (Rs. {order['paid_amount'] or 0:,.2f})"),
    ]

    for lbl, val in info:
        info_layout.addRow(label(info_frame, lbl, kind="bold"), label(info_frame, val))

    # Items
    styled_label(dlg, "Order Items:", font=FONT_BOLD)

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

    # Get order items via service
    order_items = svc.sales.get_order_items(order['id'])

    total = 0
    for row_idx, row in enumerate(order_items):
        # Resolve product model from product_id
        product = svc.inventory.get_product_by_id(row.get('product_id'))
        model = product['model'] if product else 'Unknown'

        items_tree.insertRow(row_idx)
        items_tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(model))
        items_tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row['quantity'])))
        items_tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(f"Rs. {row['unit_price']:,.2f}"))
        items_tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"Rs. {row['total_price']:,.2f}"))
        total += row['total_price']

    # Total
    styled_label(dlg, f"Total Amount: Rs. {total:,.2f}", font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARY)

    # Notes
    if order['notes']:
        styled_label(dlg, "Notes:", font=FONT_BOLD)
        styled_label(dlg, order['notes'])

    # Close button
    close_btn = QtWidgets.QPushButton("Close", dlg)
    close_btn.clicked.connect(dlg.reject)
    main_layout.addWidget(close_btn)


def open_update_status_dialog(parent, order_number):
    """Update order status."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Update Order Status")
    dlg.resize(600, 500)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    styled_label(dlg, "Update Order Status", font=FONT_BOLD)

    form_frame = make_card(dlg, padding=20)
    form_layout = QtWidgets.QFormLayout(form_frame)
    main_layout.addWidget(form_frame)

    # Status
    status_combo = QtWidgets.QComboBox()
    status_combo.addItems(["confirmed", "processing", "shipped", "delivered", "cancelled"])
    form_layout.addRow(styled_label(form_frame, "Status:", font=FONT_BOLD), status_combo)

    # Payment
    payment_combo = QtWidgets.QComboBox()
    payment_combo.addItems(["pending", "partial", "paid"])
    form_layout.addRow(styled_label(form_frame, "Payment Status:", font=FONT_BOLD), payment_combo)

    def save_status():
        status = status_combo.currentText()
        payment = payment_combo.currentText()

        if not status:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please select a status")
            return

        # Find order
        all_orders = svc.sales.get_all_orders()
        order = next((o for o in all_orders if o['order_number'] == order_number), None)
        if not order:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Order not found")
            return

        try:
            svc.sales.update_order_status(
                order['id'], status=status, payment_status=payment, username=current_user
            )

            QtWidgets.QMessageBox.information(dlg, "Success", "Order status updated")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()
            elif hasattr(parent, 'refresh_orders'):
                parent.refresh_orders()

        except Exception as e:
            logging.exception("Failed to update order status")
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Failed to update status: {e}")

    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 15, 0, 0)
    main_layout.addWidget(btn_frame)

    update_btn = make_button(btn_frame, "Update", command=save_status, kind="success")
    btn_layout.addWidget(update_btn)
    cancel_btn = make_button(btn_frame, "Cancel", command=dlg.reject, kind="secondary")
    btn_layout.addWidget(cancel_btn)
    btn_layout.addStretch()
    
    dlg.setLayout(main_layout)
    dlg.exec()
