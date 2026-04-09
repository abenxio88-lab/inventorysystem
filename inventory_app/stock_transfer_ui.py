"""
Stock Transfer Module
======================
Transfer inventory between locations/warehouses.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
from datetime import datetime

from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
from services import svc


def _get_locations_list():
    """Helper: get locations for dropdowns."""
    return [(loc.get('id'), loc.get('name'), loc.get('code')) for loc in svc.location.get_all_locations()]


def create_stock_transfers_tab(parent, current_user=None):
    """
    Creates the stock transfers management tab.
    """
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 15)
    styled_label(header_frame, "Stock Transfers", font=FONT_BOLD)
    header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
    main_layout.addWidget(header_frame)

    # New Transfer button
    def open_new_transfer():
        open_transfer_dialog(window, current_user=current_user)

    new_btn = make_button(header_frame, "New Transfer", command=open_new_transfer, kind="success")
    header_layout.addStretch()
    header_layout.addWidget(new_btn)

    # Filter toolbar
    toolbar_frame = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar_frame)
    toolbar_layout.setContentsMargins(0, 0, 0, 10)
    main_layout.addWidget(toolbar_frame)

    styled_label(toolbar_frame, "Status:")
    status_combo = QtWidgets.QComboBox()
    status_combo.addItems(["all", "pending", "in_transit", "completed", "cancelled"])
    toolbar_layout.addWidget(status_combo)

    def apply_filter():
        refresh_from_db()

    apply_btn = make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary")
    toolbar_layout.addWidget(apply_btn)
    toolbar_layout.addStretch()

    # Transfers table
    table_frame = make_card(window, padding=10)
    table_layout = QtWidgets.QHBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(table_frame)

    columns = ("transfer_number", "from_location", "to_location", "date", "status", "items", "created_by")
    column_map = {
        "transfer_number": ("Transfer #", 120),
        "from_location": ("From", 150),
        "to_location": ("To", 150),
        "date": ("Date", 120),
        "status": ("Status", 100),
        "items": ("Items", 80),
        "created_by": ("Created By", 120)
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
            QtWidgets.QMessageBox.information(window, "Select", "Please select a transfer")
            return

        row = selected_rows[0].row()
        transfer_id_text = tree.item(row, 0).text() if tree.item(row, 0) else None

        if transfer_id_text:
            open_transfer_details(window, transfer_number=transfer_id_text)

    def on_complete_transfer():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select a transfer")
            return

        row = selected_rows[0].row()
        transfer_id_text = tree.item(row, 0).text() if tree.item(row, 0) else None

        if transfer_id_text:
            reply = QtWidgets.QMessageBox.question(window, "Confirm", "Mark this transfer as completed?",
                                                    QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                # Find transfer to get ID
                transfers = svc.stock_transfer.get_transfers()
                tr = next((t for t in transfers if t['transfer_number'] == transfer_id_text), None)
                if tr:
                    svc.stock_transfer.complete_transfer(tr['id'], username=current_user)
                    refresh_from_db()

    view_btn = make_button(action_frame, "View Details", command=on_view_details, kind="primary")
    action_layout.addWidget(view_btn)
    complete_btn = make_button(action_frame, "Complete", command=on_complete_transfer, kind="success")
    action_layout.addWidget(complete_btn)
    action_layout.addStretch()

    # Store state
    window.status_combo = status_combo
    window.tree = tree

    def refresh_from_db():
        """Refresh all data from the database through services."""
        tree.setRowCount(0)

        status_filter = status_combo.currentText()
        status_arg = None if status_filter == 'all' else status_filter

        transfers = svc.stock_transfer.get_transfers(status=status_arg)

        status_colors = {
            'pending': COLOR_WARNING,
            'in_transit': COLOR_PRIMARY,
            'completed': COLOR_SUCCESS,
            'cancelled': COLOR_DANGER
        }

        for row_idx, transfer in enumerate(transfers):
            status_text = transfer['status'].replace('_', ' ').title()
            tree.insertRow(row_idx)
            tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(transfer['transfer_number']))
            tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(transfer.get('from_location_name', '')))
            tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(transfer.get('to_location_name', '')))
            tree.setItem(row_idx, 3, QtWidgets.QTableWidgetItem(transfer['transfer_date'][:16] if transfer['transfer_date'] else ''))
            tree.setItem(row_idx, 4, QtWidgets.QTableWidgetItem(status_text))
            tree.setItem(row_idx, 5, QtWidgets.QTableWidgetItem(str(transfer.get('item_count', 0))))
            tree.setItem(row_idx, 6, QtWidgets.QTableWidgetItem(transfer.get('created_by_name', '') or 'System'))

    window.refresh_from_db = refresh_from_db
    window.refresh_transfers = refresh_from_db  # backward compatibility
    refresh_from_db()

    return window


def open_transfer_dialog(parent, current_user=None):
    """Open dialog to create a new stock transfer."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("New Stock Transfer")
    dlg.resize(900, 750)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Heading
    styled_label(dlg, "Create Stock Transfer", font=FONT_BOLD)

    # From/To locations
    loc_frame = QtWidgets.QWidget()
    loc_layout = QtWidgets.QHBoxLayout(loc_frame)
    loc_layout.setContentsMargins(0, 0, 0, 15)
    main_layout.addWidget(loc_frame)

    from_combo = QtWidgets.QComboBox()
    from_combo.setMinimumWidth(250)
    loc_layout.addWidget(styled_label(loc_frame, "From Location *:", font=FONT_BOLD))
    loc_layout.addWidget(from_combo)

    to_combo = QtWidgets.QComboBox()
    to_combo.setMinimumWidth(250)
    loc_layout.addWidget(styled_label(loc_frame, "To Location *:", font=FONT_BOLD))
    loc_layout.addWidget(to_combo)

    # Load locations via service
    locations = svc.location.get_all_locations()
    loc_data = [(loc['id'], f"{loc['code']} - {loc['name']}") for loc in locations]
    from_combo.addItems([loc[1] for loc in loc_data])
    to_combo.addItems([loc[1] for loc in loc_data])

    # Products list
    styled_label(dlg, "Products to Transfer:", font=FONT_BOLD)

    products_frame = make_card(dlg, padding=10)
    products_main_layout = QtWidgets.QVBoxLayout(products_frame)
    main_layout.addWidget(products_frame)

    # Product selection
    select_frame = QtWidgets.QWidget()
    select_layout = QtWidgets.QHBoxLayout(select_frame)
    select_layout.setContentsMargins(0, 0, 0, 10)
    products_main_layout.addWidget(select_frame)

    product_combo = QtWidgets.QComboBox()
    product_combo.setMinimumWidth(250)
    select_layout.addWidget(styled_label(select_frame, "Product:"), stretch=0)
    select_layout.addWidget(product_combo, stretch=1)

    # Load products with stock via service
    products = svc.stock_transfer.get_products_with_stock()

    product_data = [(p['id'], f"{p['model']} (Stock: {p['stock']})") for p in products]
    product_combo.addItems([p[1] for p in product_data])

    qty_edit = QtWidgets.QLineEdit("1")
    qty_edit.setFixedWidth(60)
    select_layout.addWidget(styled_label(select_frame, "Qty:"))
    select_layout.addWidget(qty_edit)

    # Items list
    styled_label(dlg, "Transfer Items:", font=FONT_BOLD)

    items_frame = QtWidgets.QWidget()
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    items_layout.setContentsMargins(0, 0, 0, 0)
    products_main_layout.addWidget(items_frame)

    columns = ("product", "quantity", "actions")
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(len(columns))
    items_tree.setHorizontalHeaderLabels(["Product", "Quantity", "Actions"])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    items_tree.setColumnWidth(0, 300)
    items_tree.setColumnWidth(1, 100)
    items_tree.setColumnWidth(2, 100)
    items_layout.addWidget(items_tree)

    # Transfer items storage
    transfer_items = []

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

        # Find product ID
        product_id = None
        product_name = None
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname
                break

        if not product_id:
            return

        # Add to list
        transfer_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': qty_int
        })

        # Update tree
        row = items_tree.rowCount()
        items_tree.insertRow(row)
        items_tree.setItem(row, 0, QtWidgets.QTableWidgetItem(product_name))
        items_tree.setItem(row, 1, QtWidgets.QTableWidgetItem(str(qty_int)))
        items_tree.setItem(row, 2, QtWidgets.QTableWidgetItem("Remove"))

        # Clear selection
        product_combo.setCurrentIndex(-1)
        qty_edit.setText("1")

    def on_item_click(index):
        row = index.row()
        col = index.column()
        if col == 2:
            if 0 <= row < len(transfer_items):
                transfer_items.pop(row)
                items_tree.removeRow(row)

    items_tree.clicked.connect(on_item_click)

    # Add button
    add_btn = make_button(select_frame, "Add", command=add_item, kind="primary")
    select_layout.addWidget(add_btn)

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

    def save_transfer():
        from_loc = from_combo.currentText()
        to_loc = to_combo.currentText()

        if not from_loc or not to_loc:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please select both locations")
            return

        if from_loc == to_loc:
            QtWidgets.QMessageBox.critical(dlg, "Error", "From and To locations must be different")
            return

        if not transfer_items:
            QtWidgets.QMessageBox.critical(dlg, "Error", "Please add at least one product")
            return

        # Get location IDs
        from_id = None
        to_id = None
        for loc in locations:
            if f"{loc['code']} - {loc['name']}" == from_loc:
                from_id = loc['id']
            if f"{loc['code']} - {loc['name']}" == to_loc:
                to_id = loc['id']

        # Generate transfer number
        transfer_number = f"TRF-{datetime.now().strftime('%Y%m%d%H%M')}"

        try:
            transfer_data = {
                'transfer_number': transfer_number,
                'from_location_id': from_id,
                'to_location_id': to_id,
                'status': 'pending',
                'notes': notes_edit.toPlainText().strip(),
                'created_by': current_user
            }

            items = [
                {
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'notes': ''
                }
                for item in transfer_items
            ]

            svc.stock_transfer.create_transfer(transfer_data, items, username=current_user)

            QtWidgets.QMessageBox.information(dlg, "Success", f"Transfer created: {transfer_number}")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to create transfer")
            QtWidgets.QMessageBox.critical(dlg, "Error", f"Failed to create transfer: {e}")

    create_btn = make_button(btn_frame, "Create Transfer", command=save_transfer, kind="success")
    btn_layout.addWidget(create_btn)
    cancel_btn = make_button(btn_frame, "Cancel", command=dlg.reject, kind="secondary")
    btn_layout.addWidget(cancel_btn)
    btn_layout.addStretch()


def open_transfer_details(parent, transfer_number):
    """View transfer details."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Transfer Details")
    dlg.resize(800, 700)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(20, 20, 20, 20)

    # Get transfer info via service
    transfers = svc.stock_transfer.get_transfers()
    transfer = next((t for t in transfers if t['transfer_number'] == transfer_number), None)

    if not transfer:
        styled_label(dlg, "Transfer not found", foreground=COLOR_DANGER, font=FONT_BOLD)
        close_btn = QtWidgets.QPushButton("Close", dlg)
        close_btn.clicked.connect(dlg.reject)
        main_layout.addWidget(close_btn)
        return

    # Header
    styled_label(dlg, f"Transfer: {transfer['transfer_number']}", font=FONT_BOLD)
    styled_label(dlg, f"Status: {transfer['status'].title()}", foreground=COLOR_PRIMARY)

    # Info
    info_frame = make_card(dlg, padding=15)
    info_layout = QtWidgets.QFormLayout(info_frame)
    main_layout.addWidget(info_frame)

    info = [
        ("From:", transfer.get('from_location_name', 'N/A')),
        ("To:", transfer.get('to_location_name', 'N/A')),
        ("Date:", transfer['transfer_date'][:16] if transfer['transfer_date'] else 'N/A'),
        ("Created By:", transfer.get('created_by_name', '') or 'System'),
        ("Notes:", transfer.get('notes', '') or 'None')
    ]

    for lbl, val in info:
        info_layout.addRow(label(info_frame, lbl, kind="bold"), label(info_frame, val))

    # Items
    styled_label(dlg, "Transfer Items:", font=FONT_BOLD)

    items_frame = make_card(dlg, padding=10)
    items_layout = QtWidgets.QVBoxLayout(items_frame)
    main_layout.addWidget(items_frame)

    columns = ("product", "quantity", "received")
    items_tree = QtWidgets.QTableWidget()
    items_tree.setColumnCount(len(columns))
    items_tree.setHorizontalHeaderLabels([col.title() for col in columns])
    items_tree.horizontalHeader().setStretchLastSection(True)
    items_tree.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
    items_tree.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
    items_tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
    for i in range(3):
        items_tree.setColumnWidth(i, 150)
    items_layout.addWidget(items_tree)

    items = svc.stock_transfer.get_transfer_items(transfer['id'])
    for row_idx, row in enumerate(items):
        items_tree.insertRow(row_idx)
        items_tree.setItem(row_idx, 0, QtWidgets.QTableWidgetItem(row.get('product_name', '')))
        items_tree.setItem(row_idx, 1, QtWidgets.QTableWidgetItem(str(row['quantity'])))
        items_tree.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(str(row.get('received_quantity', 0) or 0)))

    # Close button
    close_btn = QtWidgets.QPushButton("Close", dlg)
    close_btn.clicked.connect(dlg.reject)
    main_layout.addWidget(close_btn)
