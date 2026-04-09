"""
Electronics-Specific Features Module
=====================================
Serial number tracking, device specifications, and warranty management.

REFACTORED: All database access goes through the service layer (svc).
"""

from PySide6.QtWidgets import (QFrame, QLabel, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QComboBox, QLineEdit, QTextEdit, QHeaderView,
                               QAbstractItemView, QTableWidget, QTableWidgetItem, QMessageBox)
from PySide6.QtCore import Qt
import logging
from datetime import datetime, date

from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED
)
from services import svc


def create_electronics_tab(parent, current_user=None):
    """
    Creates the electronics management tab with serial numbers and warranty tracking.
    """
    window = QFrame()
    window.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header with stats
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_layout, "📱 Electronics Management", font=FONT_BOLD)

    layout.addWidget(header_frame)

    # Summary cards
    summary_frame = QFrame()
    summary_layout = QGridLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 0)
    for i in range(4):
        summary_layout.setColumnStretch(i, 1)

    def create_summary_card(parent_layout, title, value, col):
        card = make_card(parent_layout, padding=15)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        styled_label(card_layout, text=title, font=("Segoe UI", 10), foreground="#6c757d")
        value_label = styled_label(card_layout, text=str(value), font=("Segoe UI", 24, "bold"), foreground=COLOR_PRIMARY)
        parent_layout.addWidget(card, 0, col)
        return value_label

    total_lbl = create_summary_card(summary_layout, "Devices Tracked", 0, 0)
    warranty_lbl = create_summary_card(summary_layout, "Under Warranty", 0, 1)
    expiring_lbl = create_summary_card(summary_layout, "Warranty Expiring", 0, 2)
    expired_lbl = create_summary_card(summary_layout, "Warranty Expired", 0, 3)

    summary_labels = {
        'total': total_lbl,
        'warranty': warranty_lbl,
        'expiring': expiring_lbl,
        'expired': expired_lbl
    }
    layout.addWidget(summary_frame)

    # Filter toolbar
    toolbar_frame = QFrame()
    toolbar_layout = QHBoxLayout(toolbar_frame)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(toolbar_layout, "Filter:")

    status_combo = QComboBox()
    status_combo.addItems(["all", "in_stock", "sold", "warranty_active", "warranty_expiring", "warranty_expired"])
    toolbar_layout.addWidget(status_combo)

    def apply_filter():
        refresh_from_db()

    make_button(toolbar_layout, "Apply", command=apply_filter, kind="primary")
    make_button(toolbar_layout, "Clear", command=lambda: (status_combo.setCurrentText("all"), refresh_from_db()), kind="secondary")

    layout.addWidget(toolbar_frame)

    # Devices table
    table_frame = make_card(window, padding=10)
    table_layout = QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    columns = ("serial", "product", "status", "warranty_end", "purchase_date", "sold_date", "actions")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([
        "Serial Number", "Product", "Status", "Warranty End", "Purchase Date", "Sold Date", "Actions"
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

    def on_add_serial():
        open_add_serial_dialog(window, current_user=current_user)

    def on_view_details():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(window, "Select", "Please select a device")
            return

        row = sel[0].row()
        serial_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if serial_id:
            open_device_details(window, serial_id=int(serial_id))

    def on_mark_sold():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(window, "Select", "Please select a device")
            return

        row = sel[0].row()
        serial_id = tree.item(row, 0).text() if tree.item(row, 0) else None

        if serial_id:
            open_mark_sold_dialog(window, serial_id=int(serial_id))

    make_button(action_layout, "➕ Add Serial", command=on_add_serial, kind="success")
    make_button(action_layout, "👁️ View Details", command=on_view_details, kind="primary")
    make_button(action_layout, "💰 Mark Sold", command=on_mark_sold, kind="success")

    layout.addWidget(action_frame)

    # Store state
    window.status_combo = status_combo
    window.tree = tree
    window.summary_labels = summary_labels

    # Cache for products lookup
    window._products_cache = {}

    def refresh_from_db():
        """Reload all data from the database through services."""
        tree.setRowCount(0)

        # Reload all serial numbers through service
        all_serials = svc.serial.get_serial_numbers()

        # Build product lookup cache
        all_products = svc.inventory.get_all_products()
        product_cache = {}
        for p in all_products:
            product_cache[p['id']] = p
        window._products_cache = product_cache

        status_filter = status_combo.currentText()

        # Apply filter in-memory
        if status_filter == 'all':
            devices = all_serials
        elif status_filter == 'in_stock':
            devices = [d for d in all_serials if d.get('status') == 'in_stock']
        elif status_filter == 'sold':
            devices = [d for d in all_serials if d.get('status') == 'sold']
        elif status_filter == 'warranty_active':
            today_str = date.today().isoformat()
            devices = [d for d in all_serials
                       if d.get('warranty_end') and d.get('warranty_end') >= today_str
                       and d.get('status') != 'sold']
        elif status_filter == 'warranty_expiring':
            today = date.today()
            from datetime import timedelta
            threshold = (today + timedelta(days=30)).isoformat()
            today_str = today.isoformat()
            devices = [d for d in all_serials
                       if d.get('warranty_end') and today_str <= d['warranty_end'] <= threshold]
        elif status_filter == 'warranty_expired':
            today_str = date.today().isoformat()
            devices = [d for d in all_serials
                       if d.get('warranty_end') and d.get('warranty_end') < today_str]
        else:
            devices = all_serials

        # Update summary
        total = len(devices)
        today_str = date.today().isoformat()
        under_warranty = sum(1 for d in devices if d.get('warranty_end') and d['warranty_end'] >= today_str)

        # Update labels
        summary_labels['total'].setText(str(total))
        summary_labels['warranty'].setText(str(under_warranty))

        # Populate table
        for device in devices:
            status_text = device.get('status', '').replace('_', ' ').title()

            # Resolve product info from cache
            product_id = device.get('product_id')
            product_info = "Unknown"
            if product_id and product_id in product_cache:
                p = product_cache[product_id]
                category = p.get('category', '') or p.get('category_id', '')
                model = p.get('model', 'Unknown')
                product_info = f"{model} ({category})" if category else model

            # Determine warranty status
            warranty_display = 'N/A'
            if device.get('warranty_end'):
                try:
                    warranty_date = datetime.strptime(device['warranty_end'], '%Y-%m-%d').date()
                    today = date.today()
                    days_left = (warranty_date - today).days

                    if days_left < 0:
                        warranty_display = "❌ Expired"
                    elif days_left <= 30:
                        warranty_display = "⚠️ Expiring"
                    else:
                        warranty_display = f"✅ {days_left}d left"
                except Exception:
                    warranty_display = device['warranty_end']

            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QTableWidgetItem(device.get('serial_number', '')))
            tree.setItem(row, 1, QTableWidgetItem(product_info))
            tree.setItem(row, 2, QTableWidgetItem(status_text))
            tree.setItem(row, 3, QTableWidgetItem(device.get('warranty_end', 'N/A')[:10] if device.get('warranty_end') else 'N/A'))
            tree.setItem(row, 4, QTableWidgetItem(device.get('purchase_date', 'N/A')[:10] if device.get('purchase_date') else 'N/A'))
            tree.setItem(row, 5, QTableWidgetItem(device.get('sold_date', 'N/A')[:10] if device.get('sold_date') else 'N/A'))
            tree.setItem(row, 6, QTableWidgetItem("👁️ View"))

    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_add_serial_dialog(parent, current_user=None):
    """Dialog to add a new serial number for a product."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Add Device Serial Number")
    dlg.resize(850, 800)
    dlg.setMinimumSize(700, 650)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    # Heading
    styled_label(content_layout, "Device Information", font=FONT_BOLD)

    # Form
    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(0, 1)

    # Product selection
    form_layout.addWidget(styled_label(None, "Product *:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)

    product_combo = QComboBox()
    form_layout.addWidget(product_combo, 1, 0)

    # Load products through service
    all_products = svc.inventory.get_all_products()
    product_data = [(p['id'], f"{p['model']} ({p.get('category', '')})") for p in all_products]
    product_combo.addItems([p[1] for p in product_data])

    # Serial Number
    form_layout.addWidget(styled_label(None, "Serial Number *:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    serial_var = QLineEdit()
    form_layout.addWidget(serial_var, 3, 0)

    # Purchase Date
    form_layout.addWidget(styled_label(None, "Purchase Date:", font=FONT_BOLD), 4, 0, alignment=Qt.AlignLeft)
    purchase_var = QLineEdit(str(date.today()))
    form_layout.addWidget(purchase_var, 5, 0)

    # Warranty End Date
    form_layout.addWidget(styled_label(None, "Warranty End Date:", font=FONT_BOLD), 6, 0, alignment=Qt.AlignLeft)
    warranty_var = QLineEdit()
    form_layout.addWidget(warranty_var, 7, 0)

    # Status
    form_layout.addWidget(styled_label(None, "Status:", font=FONT_BOLD), 8, 0, alignment=Qt.AlignLeft)
    status_combo = QComboBox()
    status_combo.addItems(["in_stock", "sold", "damaged", "refurbished"])
    status_combo.setCurrentText("in_stock")
    form_layout.addWidget(status_combo, 9, 0)

    # Notes
    form_layout.addWidget(styled_label(None, "Notes:", font=FONT_BOLD), 10, 0, alignment=Qt.AlignLeft)
    notes_text = QTextEdit()
    notes_text.setMaximumHeight(60)
    form_layout.addWidget(notes_text, 11, 0)

    content_layout.addWidget(form_frame)

    # Save button
    def save_serial():
        product_sel = product_combo.currentText()
        serial = serial_var.text().strip()
        purchase_date = purchase_var.text().strip()
        warranty_end = warranty_var.text().strip()
        status = status_combo.currentText()
        notes = notes_text.toPlainText().strip()

        if not product_sel:
            QMessageBox.critical(dlg, "Error", "Please select a product")
            return

        if not serial:
            QMessageBox.critical(dlg, "Error", "Serial number is required")
            return

        # Find product ID
        product_id = None
        for pid, pname in product_data:
            if pname == product_sel:
                product_id = pid
                break

        if not product_id:
            QMessageBox.critical(dlg, "Error", "Invalid product selection")
            return

        # Check for duplicate serial through service
        existing_serials = svc.serial.get_serial_numbers(product_id=product_id)
        for existing in existing_serials:
            if existing.get('serial_number') == serial:
                QMessageBox.critical(dlg, "Error", "This serial number already exists for this product")
                return

        # Save through service
        try:
            username = current_user if current_user else "system"
            data = {
                'product_id': product_id,
                'serial_number': serial,
                'status': status,
                'purchase_date': purchase_date or None,
                'warranty_end': warranty_end or None,
                'notes': notes or None,
            }
            svc.serial.add_serial_number(data, username=username)

            QMessageBox.information(dlg, "Success", "Device serial number added")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to add serial number")
            QMessageBox.critical(dlg, "Error", f"Failed to add serial number: {e}")

    # Buttons
    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)

    make_button(btn_layout, "💾 Save", command=save_serial, kind="success")
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary")
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()


def open_device_details(parent, serial_id):
    """View detailed device information."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Device Details")
    dlg.resize(950, 850)
    dlg.setMinimumSize(750, 700)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    # Get device info through service
    all_serials = svc.serial.get_serial_numbers()
    device = None
    for sn in all_serials:
        if sn.get('id') == serial_id:
            device = sn
            break

    if not device:
        styled_label(content_layout, "Device not found", font=FONT_BOLD, foreground=COLOR_DANGER)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dlg.reject)
        content_layout.addWidget(close_btn)
        dlg.setLayout(content_layout)
        dlg.exec()
        return

    # Get product info through service
    product_id = device.get('product_id')
    product = svc.inventory.get_product_by_id(product_id) if product_id else None

    # Heading
    model_name = product.get('model', 'Unknown') if product else 'Unknown'
    styled_label(content_layout, f"📱 {model_name}", font=FONT_BOLD)
    styled_label(content_layout, f"Serial: {device.get('serial_number', '')}", foreground=COLOR_PRIMARY)

    # Device specs
    specs_frame = make_card(content, padding=15)
    specs_layout = QVBoxLayout(specs_frame)

    styled_label(specs_layout, "Device Specifications", font=FONT_BOLD)

    specs = [
        ("Category:", product.get('category', 'N/A') if product else 'N/A'),
        ("Brand:", product.get('brand') or 'N/A' if product else 'N/A'),
        ("Color:", product.get('color') or 'N/A' if product else 'N/A'),
        ("RAM:", product.get('ram') or 'N/A' if product else 'N/A'),
        ("Storage:", product.get('storage') or 'N/A' if product else 'N/A'),
        ("Screen:", product.get('screen_size') or 'N/A' if product else 'N/A'),
        ("Camera:", product.get('camera') or 'N/A' if product else 'N/A'),
        ("Battery:", product.get('battery') or 'N/A' if product else 'N/A'),
    ]

    for label_text, value in specs:
        frame = QFrame()
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        styled_label(frame_layout, f"{label_text}", font=("Segoe UI", 10, "bold"))
        styled_label(frame_layout, f"{value}")
        specs_layout.addWidget(frame)

    content_layout.addWidget(specs_frame)

    # Status info
    status_frame = make_card(content, padding=15)
    status_layout = QVBoxLayout(status_frame)

    styled_label(status_layout, "Status Information", font=FONT_BOLD)

    status_info = [
        ("Status:", device.get('status', '').replace('_', ' ').title()),
        ("Purchase Date:", device.get('purchase_date', 'N/A')[:10] if device.get('purchase_date') else 'N/A'),
        ("Warranty End:", device.get('warranty_end', 'N/A')[:10] if device.get('warranty_end') else 'N/A'),
        ("Sold Date:", device.get('sold_date', 'N/A')[:10] if device.get('sold_date') else 'N/A'),
        ("Notes:", device.get('notes') or 'None'),
    ]

    for label_text, value in status_info:
        frame = QFrame()
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        styled_label(frame_layout, f"{label_text}", font=("Segoe UI", 10, "bold"))
        styled_label(frame_layout, f"{value}")
        status_layout.addWidget(frame)

    content_layout.addWidget(status_frame)

    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dlg.reject)
    content_layout.addWidget(close_btn)

    dlg.setLayout(content_layout)
    dlg.exec()


def open_mark_sold_dialog(parent, serial_id):
    """Mark a device as sold."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("Mark Device as Sold")
    dlg.resize(750, 650)
    dlg.setMinimumSize(600, 550)
    dlg.setModal(True)

    content = QFrame()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(20, 20, 20, 20)

    styled_label(content_layout, "Mark Device as Sold", font=FONT_BOLD)

    form_frame = make_card(content, padding=20)
    form_layout = QGridLayout(form_frame)
    form_layout.setColumnStretch(0, 1)

    # Sold Date
    form_layout.addWidget(styled_label(None, "Sold Date:", font=FONT_BOLD), 0, 0, alignment=Qt.AlignLeft)
    sold_var = QLineEdit(str(date.today()))
    form_layout.addWidget(sold_var, 1, 0)

    # Notes
    form_layout.addWidget(styled_label(None, "Notes:", font=FONT_BOLD), 2, 0, alignment=Qt.AlignLeft)
    notes_text = QTextEdit()
    notes_text.setMaximumHeight(80)
    form_layout.addWidget(notes_text, 3, 0)

    content_layout.addWidget(form_frame)

    def save_sold():
        sold_date = sold_var.text().strip()
        notes = notes_text.toPlainText().strip()

        try:
            # Get the serial number first to use for update
            all_serials = svc.serial.get_serial_numbers()
            serial_record = None
            for sn in all_serials:
                if sn.get('id') == serial_id:
                    serial_record = sn
                    break

            if not serial_record:
                QMessageBox.critical(dlg, "Error", "Serial number record not found")
                return

            serial_number = serial_record.get('serial_number', '')

            # Update status through service
            username = getattr(parent, '_current_user', None) or "system"
            svc.serial.update_serial_status(serial_number, 'sold', username=username)

            QMessageBox.information(dlg, "Success", "Device marked as sold")
            dlg.accept()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to mark device as sold")
            QMessageBox.critical(dlg, "Error", f"Failed to mark as sold: {e}")

    btn_frame = QFrame()
    btn_layout = QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)

    make_button(btn_layout, "💾 Mark as Sold", command=save_sold, kind="success")
    make_button(btn_layout, "Cancel", command=dlg.reject, kind="secondary")
    content_layout.addWidget(btn_frame)

    dlg.setLayout(content_layout)
    dlg.exec()
