"""
Purchase Orders Module
=======================
Complete purchase order management system.
Create POs, track status, receive goods, and manage supplier orders.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
from datetime import datetime, timedelta

from services import svc
from ui_theme import make_card, styled_label, make_button, label, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, BTN_WIDTH


def _get_suppliers_list():
    """Helper: get suppliers list for dropdowns."""
    return [(s.get('id'), s.get('name'), s.get('code')) for s in svc.supplier.get_all_suppliers()]


def create_purchase_orders_tab(parent, current_user=None):
    """
    Creates the purchase orders management tab.
    """
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 15)
    styled_label(header_frame, "Purchase Orders", font=FONT_BOLD)
    header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
    main_layout.addWidget(header_frame)

    # New PO button
    def open_new_po():
        open_create_po_dialog(window, current_user=current_user)

    new_btn = make_button(header_frame, "New Purchase Order", command=open_new_po, kind="success")
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

    draft_lbl = create_summary_card(summary_frame, "Draft", 0)
    sent_lbl = create_summary_card(summary_frame, "Sent", 0)
    confirmed_lbl = create_summary_card(summary_frame, "Confirmed", 0)
    received_lbl = create_summary_card(summary_frame, "Received", 0)
    total_lbl = create_summary_card(summary_frame, "Total POs", 0)

    window.summary_labels = {
        'draft': draft_lbl,
        'sent': sent_lbl,
        'confirmed': confirmed_lbl,
        'received': received_lbl,
        'total': total_lbl
    }

    # Filter toolbar
    toolbar_frame = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar_frame)
    toolbar_layout.setContentsMargins(0, 0, 0, 10)
    main_layout.addWidget(toolbar_frame)

    styled_label(toolbar_frame, "Status:")
    status_combo = QtWidgets.QComboBox()
    status_combo.addItems(["all", "draft", "sent", "confirmed", "partial", "received", "cancelled"])
    toolbar_layout.addWidget(status_combo)

    styled_label(toolbar_frame, "Supplier:")
    supplier_combo = QtWidgets.QComboBox()
    toolbar_layout.addWidget(supplier_combo)

    # Load suppliers
    suppliers = svc.supplier.get_all_suppliers()
    supplier_data = [("all", "All Suppliers")] + [(s['id'], f"{s['code']} - {s['name']}") for s in suppliers]
    supplier_combo.addItems([s[1] for s in supplier_data])

    def apply_filter():
        refresh_from_db()

    apply_btn = make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary")
    toolbar_layout.addWidget(apply_btn)
    clear_btn = make_button(toolbar_frame, "Clear", command=lambda: (status_combo.setCurrentText("all"), supplier_combo.setCurrentText("All Suppliers"), refresh_from_db()), kind="secondary")
    toolbar_layout.addWidget(clear_btn)
    toolbar_layout.addStretch()

    # PO table
    table_frame = make_card(window, padding=10)
    table_layout = QtWidgets.QHBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(table_frame)

    columns = ("po_number", "supplier", "order_date", "expected_date", "status", "total_amount", "items")
    column_map = {
        "po_number": ("PO Number", 120),
        "supplier": ("Supplier", 200),
        "order_date": ("Order Date", 100),
        "expected_date": ("Expected", 100),
        "status": ("Status", 100),
        "total_amount": ("Total Amount", 120),
        "items": ("Items", 60)
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
            QtWidgets.QMessageBox.information(window, "Select", "Please select a purchase order")
            return

        row = selected_rows[0].row()
        po_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if po_id:
            open_po_details(window, po_number=po_id, current_user=current_user)

    def on_receive_goods():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select a purchase order")
            return

        row = selected_rows[0].row()
        po_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if po_id:
            open_grn_dialog(window, po_number=po_id, current_user=current_user)

    view_btn = make_button(action_frame, "View Details", command=on_view_details, kind="primary")
    action_layout.addWidget(view_btn)
    receive_btn = make_button(action_frame, "Receive Goods", command=on_receive_goods, kind="success")
    action_layout.addWidget(receive_btn)
    action_layout.addStretch()

    # Store state
    window.status_combo = status_combo
    window.supplier_combo = supplier_combo
    window.tree = tree
    window.supplier_data = supplier_data

    def refresh_from_db():
        """Refresh purchase orders list from database using services."""
        tree.setRowCount(0)

        status_filter = status_combo.currentText()
        supplier_sel = supplier_combo.currentText()

        # Get all POs through service
        status_arg = None if status_filter == 'all' else status_filter
        pos = svc.purchase_order.get_all_orders(status=status_arg)

        # Get supplier ID if selected
        supplier_id = None
        if supplier_sel != "All Suppliers":
            for sid, sname in supplier_data:
                if sname == supplier_sel:
                    supplier_id = sid
                    break

        # Filter by supplier if needed
        if supplier_id:
            pos = [po for po in pos if po.get('supplier_id') == supplier_id]

        # Update summary
        status_counts = {'draft': 0, 'sent': 0, 'confirmed': 0, 'received': 0, 'total': len(pos)}
        for po in pos:
            if po['status'] in status_counts:
                status_counts[po['status']] += 1

        window.summary_labels['draft'].setText(str(status_counts['draft']))
        window.summary_labels['sent'].setText(str(status_counts['sent']))
        window.summary_labels['confirmed'].setText(str(status_counts['confirmed']))
        window.summary_labels['received'].setText(str(status_counts['received']))
        window.summary_labels['total'].setText(str(status_counts['total']))

        # Populate table
        status_colors = {
            'draft': '#6c757d',
            'sent': COLOR_PRIMARY,
            'confirmed': COLOR_WARNING,
            'partial': COLOR_PRIMARY,
            'received': COLOR_SUCCESS,
            'cancelled': COLOR_DANGER
        }

        for row_idx, po in enumerate(pos):
            status_text = po['status'].replace('_', ' ').title()
            tree.insertRow(row_idx)
            tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(po['po_number']))
            tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(po['supplier_name']))
            tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(po['order_date'][:10] if po['order_date'] else 'N/A'))
            tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(po['expected_date'][:10] if po['expected_date'] else 'N/A'))
            tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(status_text))
            tree.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(f"Rs. {po['total_amount']:,.2f}" if po['total_amount'] else 'Rs. 0.00'))
            tree.setItem(row_idx, 6, QtWidgets.QTableWidgetItem(str(po['item_count'])))

    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_create_po_dialog(parent, current_user=None):
    """Premium dialog to create a new purchase order with proper sizing and scrolling."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Create Purchase Order")
    dlg.resize(850, 700)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Header card
    header_card = make_card(dlg, padx=30, pady=20)
    header_layout = QtWidgets.QVBoxLayout(header_card)
    header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    main_layout.addWidget(header_card)

    header_title = styled_label(header_card, "New Purchase Order", font=FONT_BOLD, foreground=COLOR_PRIMARY)
    header_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    header_layout.addWidget(header_title)

    # Main form card
    form_card = make_card(dlg, padding=20)
    form_layout = QtWidgets.QVBoxLayout(form_card)
    form_layout.setSpacing(15)
    main_layout.addWidget(form_card)

    # Supplier selection row
    supplier_row = QtWidgets.QWidget()
    supplier_layout = QtWidgets.QHBoxLayout(supplier_row)
    supplier_layout.setContentsMargins(0, 0, 0, 0)
    form_layout.addWidget(supplier_row)

    supplier_left = QtWidgets.QWidget()
    sl_layout = QtWidgets.QFormLayout(supplier_left)
    supplier_layout.addWidget(supplier_left)

    supplier_right = QtWidgets.QWidget()
    sr_layout = QtWidgets.QFormLayout(supplier_right)
    supplier_layout.addWidget(supplier_right)

    supplier_combo = QtWidgets.QComboBox()
    supplier_combo.setMinimumWidth(300)
    sl_layout.addRow(styled_label(supplier_left, "Supplier *:", font=FONT_BOLD), supplier_combo)

    expected_edit = QtWidgets.QLineEdit()
    sr_layout.addRow(styled_label(supplier_right, "Expected Date:", font=FONT_BOLD), expected_edit)

    # Load suppliers via service
    suppliers = svc.supplier.get_all_suppliers()
    supplier_data = [(s['id'], f"{s['code']} - {s['name']}") for s in suppliers]
    supplier_combo.addItems([s[1] for s in supplier_data])

    # Set default expected date (7 days from now)
    default_expected = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    expected_edit.setText(default_expected)

    # Product addition section
    styled_label(form_card, "Add Products:", font=FONT_BOLD)

    products_card = make_card(form_card, padding=15)
    products_layout = QtWidgets.QVBoxLayout(products_card)
    products_layout.setSpacing(10)
    form_layout.addWidget(products_card)

    # Product selection row
    select_frame = QtWidgets.QWidget()
    select_layout = QtWidgets.QHBoxLayout(select_frame)
    select_layout.setContentsMargins(0, 0, 0, 0)
    products_layout.addWidget(select_frame)

    product_combo = QtWidgets.QComboBox()
    product_combo.setMinimumWidth(250)
    select_layout.addWidget(styled_label(select_frame, "Product:", font=FONT_BOLD))
    select_layout.addWidget(product_combo, stretch=1)

    # Load products from service
    try:
        products = svc.inventory.get_all_products()
        product_data = [(p.id, f"{p.model} (Stock: {p.stock}, Cost: Rs. {p.purchase_price})") for p in products]
        product_combo.addItems([p[1] for p in product_data])
    except Exception as e:
        logging.error(f"Failed to load products: {e}")
        product_data = []

    qty_edit = QtWidgets.QLineEdit("1")
    qty_edit.setFixedWidth(60)
    select_layout.addWidget(styled_label(select_frame, "Qty:", font=FONT_BOLD))
    select_layout.addWidget(qty_edit)

    price_edit = QtWidgets.QLineEdit("0")
    price_edit.setFixedWidth(100)
    select_layout.addWidget(styled_label(select_frame, "Unit Price:", font=FONT_BOLD))
    select_layout.addWidget(price_edit)

    # Items list section
    styled_label(form_card, "Order Items:", font=FONT_BOLD)

    items_frame = QtWidgets.QWidget()
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    items_layout.setContentsMargins(0, 0, 0, 0)
    form_layout.addWidget(items_frame)

    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(5)
    items_tree.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price", "Total", "Actions"])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    items_tree.setColumnWidth(0, 280)
    items_tree.setColumnWidth(1, 100)
    items_tree.setColumnWidth(2, 130)
    items_tree.setColumnWidth(3, 130)
    items_tree.setColumnWidth(4, 100)
    items_layout.addWidget(items_tree)

    # PO items storage
    po_items = []

    def add_item():
        product_sel = product_combo.currentText()
        qty = qty_edit.text()
        price = price_edit.text()

        if not product_sel:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please select a product")
            return

        try:
            qty_int = int(qty)
            price_float = float(price)
            if qty_int <= 0 or price_float < 0:
                raise ValueError("quantity must be positive and price non-negative")
        except ValueError as e:
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Invalid quantity or price: {e}")
            return

        # Find product ID
        product_id = None
        product_name = None
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                break

        if not product_id:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Product not found")
            return

        total = qty_int * price_float

        # Add to list
        po_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': qty_int,
            'unit_price': price_float,
            'total': total
        })

        # Update tree
        row = items_tree.rowCount()
        items_tree.insertRow(row)
        items_tree.setItem(row, 0, QtWidgets.QTableWidgetItem(product_name))
        items_tree.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty_int)))
        items_tree.setItem(row, 2, QtWidgets.QTableWidgetItem(f"Rs. {price_float:,.2f}"))
        items_tree.setItem(row, 3, QtWidgets.QTableWidgetItem(f"Rs. {total:,.2f}"))
        items_tree.setItem(row, 4, QtWidgets.QTableWidgetItem("Remove"))

        # Clear selection
        product_combo.setCurrentIndex(-1)
        qty_edit.setText("1")
        price_edit.setText("0")
        update_total()

    def on_item_click(index):
        row = index.row()
        col = index.column()
        if col == 4:
            if 0 <= row < len(po_items):
                po_items.pop(row)
                items_tree.removeRow(row)
                update_total()

    items_tree.clicked.connect(on_item_click)

    add_btn = make_button(select_frame, "Add", command=add_item, kind="primary")
    select_layout.addWidget(add_btn)

    # Notes section
    styled_label(form_card, "Notes:", font=FONT_BOLD)
    notes_edit = QtWidgets.QTextEdit()
    notes_edit.setMaximumHeight(80)
    form_layout.addWidget(notes_edit)

    # Total label
    total_label = styled_label(form_card, "Total: Rs. 0.00", font=("Segoe UI", 14, "bold"), foreground=COLOR_SUCCESS)
    total_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
    form_layout.addWidget(total_label)

    def update_total():
        total = sum(item['total'] for item in po_items)
        total_label.setText(f"Total: Rs. {total:,.2f}")

    # Button bar at bottom
    button_frame = QtWidgets.QWidget()
    button_layout = QtWidgets.QHBoxLayout(button_frame)
    button_layout.setContentsMargins(0, 10, 0, 0)
    button_layout.addStretch()
    main_layout.addWidget(button_frame)

    def save_po():
        supplier_sel = supplier_combo.currentText()
        expected_date = expected_edit.text().strip()
        notes = notes_edit.toPlainText().strip()

        if not supplier_sel:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please select a supplier")
            return

        if not po_items:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please add at least one product")
            return

        # Get supplier ID
        supplier_id = None
        for sid, sname in supplier_data:
            if sname == supplier_sel:
                supplier_id = sid
                break

        # Generate PO number
        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        try:
            # Prepare order data
            order_data = {
                'po_number': po_number,
                'supplier_id': supplier_id,
                'expected_date': expected_date or None,
                'notes': notes,
            }

            # Prepare items
            items = []
            for item in po_items:
                items.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'total': item['total'],
                })

            # Create PO through service
            svc.purchase_order.create_order(order_data, items, current_user)

            QtWidgets.QMessageBox.information(dlg, "Success", f"Purchase Order created:\n{po_number}")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to create purchase order")
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Failed to create PO: {str(e)}")

    create_btn = make_button(button_frame, "Create PO", command=save_po, kind="success")
    button_layout.addWidget(create_btn)
    cancel_btn = make_button(button_frame, "Cancel", command=dlg.reject, kind="secondary")
    button_layout.addWidget(cancel_btn)

    # Auto-update total when items change
    update_total()
    
    dlg.setLayout(main_layout)
    dlg.exec()


def open_po_details(parent, po_number, current_user=None):
    """View purchase order details."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Purchase Order Details")
    dlg.resize(900, 750)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Get PO through service
    pos = svc.purchase_order.get_all_orders()
    po = next((p for p in pos if p['po_number'] == po_number), None)

    if not po:
        styled_label(dlg, "Purchase Order not found", font=FONT_BOLD, foreground=COLOR_DANGER)
        close_btn = QtWidgets.QPushButton("Close", dlg)
        close_btn.clicked.connect(dlg.reject)
        main_layout.addWidget(close_btn)
        return

    # Get supplier info
    suppliers = svc.supplier.get_all_suppliers()
    supplier = next((s for s in suppliers if s['id'] == po['supplier_id']), None)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QVBoxLayout(header_frame)
    main_layout.addWidget(header_frame)

    styled_label(header_frame, f"Purchase Order: {po['po_number']}", font=FONT_BOLD)
    status_color = COLOR_SUCCESS if po['status'] == 'received' else COLOR_PRIMARY
    styled_label(header_frame, f"Status: {po['status'].title()}", foreground=status_color)

    # PO Info
    info_frame = make_card(dlg, padding=15)
    info_layout = QtWidgets.QFormLayout(info_frame)
    main_layout.addWidget(info_frame)

    info = [
        ("Supplier:", supplier['name'] if supplier else 'N/A'),
        ("Contact:", supplier.get('contact_person', 'N/A') if supplier else 'N/A'),
        ("Phone:", supplier.get('phone', 'N/A') if supplier else 'N/A'),
        ("Order Date:", po['order_date'][:10] if po['order_date'] else 'N/A'),
        ("Expected Date:", po['expected_date'][:10] if po['expected_date'] else 'N/A'),
        ("Created By:", po.get('created_by_name', 'System') or 'System'),
    ]

    for lbl, val in info:
        info_layout.addRow(label(info_frame, lbl, kind="bold"), label(info_frame, val))

    # Items
    styled_label(dlg, "Order Items:", font=FONT_BOLD)

    items_frame = make_card(dlg, padding=10)
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    main_layout.addWidget(items_frame)

    columns = ("product", "ordered", "received", "unit_price", "total")
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(len(columns))
    items_tree.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in columns])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    for i in range(5):
        items_tree.setColumnWidth(i, 100)
    items_layout.addWidget(items_tree)

    # Get PO items through service
    po_items = svc.purchase_order.get_order_items(po['id'])

    total = 0
    for row_idx, item in enumerate(po_items):
        # Get product info
        product = svc.inventory.get_product_by_id(item['product_id'])
        product_name = product.model if product else 'Unknown'

        items_tree.insertRow(row_idx)
        items_tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(product_name))
        items_tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(item['quantity_ordered'])))
        items_tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(item['quantity_received'] or 0)))
        items_tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(f"Rs. {item['unit_price']:,.2f}"))
        items_tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(f"Rs. {item['total_price']:,.2f}"))
        total += item['total_price']

    # Total
    styled_label(dlg, f"Total Amount: Rs. {total:,.2f}", font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARY)

    # Notes
    if po.get('notes'):
        styled_label(dlg, "Notes:", font=FONT_BOLD)
        styled_label(dlg, po['notes'])

    # Close button
    close_btn = QtWidgets.QPushButton("Close", dlg)
    close_btn.clicked.connect(dlg.reject)
    main_layout.addWidget(close_btn)


def open_grn_dialog(parent, po_number, current_user=None):
    """Goods Receipt Note - Receive products from PO."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Receive Goods (GRN)")
    dlg.resize(850, 750)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Get PO info through service
    pos = svc.purchase_order.get_all_orders()
    po = next((p for p in pos if p['po_number'] == po_number), None)

    if not po:
        styled_label(dlg, "Purchase Order not found", font=FONT_BOLD, foreground=COLOR_DANGER)
        close_btn = QtWidgets.QPushButton("Close", dlg)
        close_btn.clicked.connect(dlg.reject)
        main_layout.addWidget(close_btn)
        return

    styled_label(dlg, f"Receive Goods for {po['po_number']}", font=FONT_BOLD)

    if po['status'] == 'received':
        styled_label(dlg, "This PO has already been fully received", foreground=COLOR_WARNING)

    # Items to receive
    styled_label(dlg, "Items to Receive:", font=FONT_BOLD)

    items_frame = make_card(dlg, padding=10)
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    main_layout.addWidget(items_frame)

    columns = ("product", "ordered", "received", "pending", "receive_qty")
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(len(columns))
    items_tree.setHorizontalHeaderLabels([col.replace('_', ' ').title() for col in columns])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    items_tree.setColumnWidth(0, 200)
    for i in range(1, 5):
        items_tree.setColumnWidth(i, 100)
    items_layout.addWidget(items_tree)

    # Get PO items through service
    po_items_data = svc.purchase_order.get_order_items(po['id'])

    items_data = []
    for row_idx, item in enumerate(po_items_data):
        product = svc.inventory.get_product_by_id(item['product_id'])
        product_name = product.model if product else 'Unknown'

        pending = item['quantity_ordered'] - (item['quantity_received'] or 0)
        items_data.append({
            'po_item_id': item['id'],
            'product_id': item['product_id'],
            'model': product_name,
            'ordered': item['quantity_ordered'],
            'received': item['quantity_received'] or 0,
            'pending': pending
        })

        items_tree.insertRow(row_idx)
        items_tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(product_name))
        items_tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(item['quantity_ordered'])))
        items_tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(item['quantity_received'] or 0)))
        items_tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(str(pending)))
        items_tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(str(pending)))

    # Receive button
    def receive_goods():
        try:
            # Receive all pending items through service
            svc.purchase_order.receive_order(po['id'], current_user)

            QtWidgets.QMessageBox.information(dlg, "Success", "Goods received successfully")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to receive goods")
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Failed to receive goods: {e}")

    # Button bar
    button_frame = QtWidgets.QWidget()
    button_layout = QtWidgets.QHBoxLayout(button_frame)
    button_layout.addStretch()
    main_layout.addWidget(button_frame)

    receive_btn = make_button(button_frame, "Receive All Pending", command=receive_goods, kind="success")
    button_layout.addWidget(receive_btn)
    cancel_btn = make_button(button_frame, "Cancel", command=dlg.reject, kind="secondary")
    button_layout.addWidget(cancel_btn)
