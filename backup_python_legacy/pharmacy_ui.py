"""
Pharmacy Management Module
===========================
Pharmacy-specific inventory management with:
- Batch tracking
- Expiry date monitoring
- Prescription management
- FEFO (First Expired, First Out) picking
- Medication-specific fields

All data access goes through the service layer (services.svc).
No direct SQL or get_db_cursor() calls in UI code.
"""

from PySide6.QtWidgets import (QFrame, QLabel, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QComboBox, QLineEdit, QTextEdit, QHeaderView,
                               QAbstractItemView, QTableWidget, QTableWidgetItem, QMessageBox,
                               QTabWidget, QFileDialog)
from PySide6.QtCore import Qt
from datetime import datetime, timedelta
import logging

from services import svc
from ui_theme import (
    make_button, make_card, styled_label, FONT_REGULAR, FONT_BOLD, FONT_HEADING,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)

logger = logging.getLogger(__name__)


def create_pharma_tab(parent, current_user=None):
    """
    Creates the Pharmacy management tab.
    """
    window = QFrame()
    window.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QFrame()
    header_layout = QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_layout, "💊 Pharmacy Management", font=FONT_HEADING)

    layout.addWidget(header_frame)

    # Create notebook for sub-tabs
    notebook = QTabWidget()

    # Add sub-tabs
    inventory_frame = create_pharma_inventory_tab(notebook, current_user)
    notebook.addTab(inventory_frame, "📦 Pharmacy Inventory")

    batches_frame = create_batches_tab(notebook, current_user)
    notebook.addTab(batches_frame, "📋 Batch Tracking")

    expiry_frame = create_expiry_monitor_tab(notebook, current_user)
    notebook.addTab(expiry_frame, "⚠️ Expiry Monitor")

    prescriptions_frame = create_prescriptions_tab(notebook, current_user)
    notebook.addTab(prescriptions_frame, "📝 Prescriptions")

    layout.addWidget(notebook)

    return window


def create_pharma_inventory_tab(parent, current_user=None):
    """Pharmacy inventory with medication-specific fields."""
    global _inventory_tree, _stats_label
    frame = QFrame()
    frame.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(15, 15, 15, 15)

    # Toolbar
    toolbar = QFrame()
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    def refresh_inventory():
        tree.setRowCount(0)

        products = svc.pharmacy.get_pharmacy_inventory()

        for row_data in products:
            expiry_status = _get_expiry_status(row_data.get('expiry_date'))
            status_icon = _get_expiry_icon(expiry_status)

            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QTableWidgetItem(f"{status_icon} {row_data['model']}"))
            tree.setItem(row, 1, QTableWidgetItem(row_data.get('batch_number') or 'N/A'))
            tree.setItem(row, 2, QTableWidgetItem(row_data.get('expiry_date') or 'N/A'))
            tree.setItem(row, 3, QTableWidgetItem(expiry_status))
            tree.setItem(row, 4, QTableWidgetItem(str(row_data.get('stock', 0))))
            tree.setItem(row, 5, QTableWidgetItem(row_data.get('manufacturer') or 'N/A'))
            tree.setItem(row, 6, QTableWidgetItem('Yes' if row_data.get('requires_prescription') else 'No'))

    # Add product button
    def add_product():
        dialog = PharmaProductDialog(frame, current_user)
        dialog.exec()
        if dialog.result:
            refresh_from_db()
            QMessageBox.information(frame, "Success", "Product added successfully")

    make_button(toolbar_layout, "➕ Add Product", command=add_product, kind="primary")

    # Refresh button
    make_button(toolbar_layout, "🔄 Refresh", command=refresh_from_db, kind="secondary")

    # Filter by expiry
    styled_label(toolbar_layout, "Filter:")

    expiry_filter = QComboBox()
    expiry_filter.addItems(["All", "Expired", "Critical (<7 days)", "Warning (<30 days)", "OK"])
    expiry_filter.setCurrentIndex(0)
    toolbar_layout.addWidget(expiry_filter)

    layout.addWidget(toolbar)

    # Inventory table
    columns = ("product", "batch", "expiry", "status", "stock", "manufacturer", "prescription")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([col.title() for col in columns])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    layout.addWidget(tree)

    # Register global reference
    _inventory_tree = tree

    # Stats card
    stats_frame = make_card(frame, padding=15)
    stats_layout = QVBoxLayout(stats_frame)

    stats_label = styled_label(stats_layout, "", font=FONT_BOLD)

    layout.addWidget(stats_frame)

    # Register global reference
    _stats_label = stats_label

    # Initial load
    refresh_inventory()
    update_stats()

    return frame


def create_batches_tab(parent, current_user=None):
    """Batch tracking for pharmacy products."""
    global _batches_tree
    frame = QFrame()
    frame.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(15, 15, 15, 15)

    # Toolbar
    toolbar = QFrame()
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    def refresh_batches():
        tree.setRowCount(0)

        batches = svc.pharmacy.get_batches()

        for row_data in batches:
            expiry_status = _get_batch_expiry_status(row_data.get('expiry_date'))

            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QTableWidgetItem(row_data.get('batch_number') or 'N/A'))
            tree.setItem(row, 1, QTableWidgetItem(row_data.get('model') or 'N/A'))
            tree.setItem(row, 2, QTableWidgetItem(row_data.get('sku') or 'N/A'))
            tree.setItem(row, 3, QTableWidgetItem(str(row_data.get('stock', 0))))
            tree.setItem(row, 4, QTableWidgetItem(row_data.get('expiry_date') or 'N/A'))
            tree.setItem(row, 5, QTableWidgetItem(expiry_status))
            tree.setItem(row, 6, QTableWidgetItem(row_data.get('supplier_name') or 'N/A'))

    # Add batch button
    def add_batch():
        dialog = AddBatchDialog(frame, current_user)
        dialog.exec()
        if dialog.result:
            refresh_from_db()
            QMessageBox.information(frame, "Success", "Batch added successfully")

    make_button(toolbar_layout, "➕ Add Batch", command=add_batch, kind="primary")
    make_button(toolbar_layout, "🔄 Refresh", command=refresh_from_db, kind="secondary")

    layout.addWidget(toolbar)

    # Batches table
    columns = ("batch_number", "product", "sku", "quantity", "expiry", "status", "supplier")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([col.title() for col in columns])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    layout.addWidget(tree)

    # Register global reference
    _batches_tree = tree

    # Initial load
    refresh_batches()

    return frame


def create_expiry_monitor_tab(parent, current_user=None):
    """Expiry date monitoring dashboard."""
    global _expiry_tree, _days_var
    frame = QFrame()
    frame.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header = QFrame()
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_layout, "⚠️ Expiry Monitor", font=FONT_HEADING)

    # Time range filter
    styled_label(header_layout, "Show products expiring within:")

    days_combo = QComboBox()
    days_combo.addItems(["7", "14", "30", "60", "90", "ALL"])
    days_combo.setCurrentText("30")
    header_layout.addWidget(days_combo)

    def apply_filter():
        refresh_expiry()

    make_button(header_layout, "Apply Filter", command=apply_filter, kind="primary")

    layout.addWidget(header)

    # Expiry table
    columns = ("product", "batch", "expiry_date", "days_left", "stock", "manufacturer", "status")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([col.title() for col in columns])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    layout.addWidget(tree)

    # Register global references
    _expiry_tree = tree
    _days_var = days_combo

    def refresh_expiry():
        tree.setRowCount(0)

        days = days_combo.currentText()

        if days == "ALL":
            products = svc.pharmacy.get_expiring_products(days=9999)
        else:
            products = svc.pharmacy.get_expiring_products(days=int(days))

        for row_data in products:
            days_left = row_data.get('days_until_expiry', 0)
            if days_left < 0:
                status = 'expired'
            elif days_left <= 7:
                status = 'critical'
            elif days_left <= 30:
                status = 'warning'
            else:
                status = 'ok'

            if status != 'ok':
                row = tree.rowCount()
                tree.insertRow(row)
                tree.setItem(row, 0, QTableWidgetItem(row_data.get('model', 'N/A')))
                tree.setItem(row, 1, QTableWidgetItem(row_data.get('batch_number') or 'N/A'))
                tree.setItem(row, 2, QTableWidgetItem(row_data.get('expiry_date') or 'N/A'))
                tree.setItem(row, 3, QTableWidgetItem(f"{int(days_left)} days" if days_left else 'N/A'))
                tree.setItem(row, 4, QTableWidgetItem(str(row_data.get('stock', 0))))
                tree.setItem(row, 5, QTableWidgetItem(row_data.get('manufacturer') or 'N/A'))
                tree.setItem(row, 6, QTableWidgetItem(status.upper()))

    # Export button
    def export_expiry_report():
        try:
            import csv

            file_path, _ = QFileDialog.getSaveFileName(
                frame,
                "Save Expiry Report",
                "",
                "CSV files (*.csv)"
            )

            if file_path:
                products = svc.pharmacy.get_expiring_products(days=9999)

                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Product', 'Batch Number', 'Expiry Date', 'Stock', 'Manufacturer'])
                    for row_data in products:
                        writer.writerow([
                            row_data.get('model', ''),
                            row_data.get('batch_number', ''),
                            row_data.get('expiry_date', ''),
                            row_data.get('stock', 0),
                            row_data.get('manufacturer', '')
                        ])

                QMessageBox.information(frame, "Success", f"Expiry report exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(frame, "Error", f"Failed to export: {e}")

    export_frame = QFrame()
    export_layout = QHBoxLayout(export_frame)
    export_layout.setContentsMargins(0, 0, 0, 0)
    make_button(export_layout, "📄 Export Report", command=export_expiry_report, kind="secondary")
    layout.addWidget(export_frame)

    # Initial load
    refresh_expiry()

    return frame


def create_prescriptions_tab(parent, current_user=None):
    """Prescription management."""
    global _prescriptions_tree
    frame = QFrame()
    frame.setFrameShape(QFrame.NoFrame)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(15, 15, 15, 15)

    # Toolbar
    toolbar = QFrame()
    toolbar_layout = QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    def refresh_prescriptions():
        tree.setRowCount(0)

        try:
            prescriptions = svc.db.fetch_prescriptions() if hasattr(svc.db, 'fetch_prescriptions') else []

            for row_data in prescriptions:
                row = tree.rowCount()
                tree.insertRow(row)
                tree.setItem(row, 0, QTableWidgetItem(row_data.get('prescription_number', 'N/A')))
                tree.setItem(row, 1, QTableWidgetItem(row_data.get('patient_name', 'N/A')))
                tree.setItem(row, 2, QTableWidgetItem(row_data.get('patient_phone', 'N/A')))
                tree.setItem(row, 3, QTableWidgetItem(row_data.get('doctor_name', 'N/A')))
                tree.setItem(row, 4, QTableWidgetItem(row_data.get('prescribed_date', 'N/A')))
                tree.setItem(row, 5, QTableWidgetItem(row_data.get('expiry_date', 'N/A')))
                tree.setItem(row, 6, QTableWidgetItem(f"{int(row_data.get('days_until_expiry', 0))} days" if row_data.get('days_until_expiry') is not None else 'N/A'))
                tree.setItem(row, 7, QTableWidgetItem(row_data.get('status', 'N/A')))
                tree.setItem(row, 8, QTableWidgetItem(f"{row_data.get('refills_used', 0)}/{row_data.get('refills_allowed', 0)}"))
        except Exception as e:
            logger.warning(f"Could not load prescriptions: {e}")

    # New prescription button
    def add_prescription():
        dialog = AddPrescriptionDialog(frame, current_user)
        dialog.exec()
        if dialog.result:
            refresh_from_db()
            QMessageBox.information(frame, "Success", "Prescription added successfully")

    make_button(toolbar_layout, "➕ New Prescription", command=add_prescription, kind="primary")
    make_button(toolbar_layout, "🔄 Refresh", command=refresh_from_db, kind="secondary")

    layout.addWidget(toolbar)

    # Prescriptions table
    columns = ("rx_number", "patient", "phone", "doctor", "date", "expiry", "days_left", "status", "refills")
    tree = QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([col.title() for col in columns])
    tree.setSelectionBehavior(QAbstractItemView.SelectRows)
    tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tree.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tree.verticalHeader().setVisible(False)

    layout.addWidget(tree)

    # Register global reference
    _prescriptions_tree = tree

    # Action buttons
    action_frame = QFrame()
    action_layout = QHBoxLayout(action_frame)
    action_layout.setContentsMargins(0, 0, 0, 0)

    def verify_prescription():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.critical(frame, "Error", "Select a prescription")
            return

        row = sel[0].row()
        rx_number = tree.item(row, 0).text() if tree.item(row, 0) else ''

        try:
            svc.db.verify_prescription(rx_number, current_user)
            refresh_from_db()
            QMessageBox.information(frame, "Success", "Prescription verified")
        except Exception as e:
            QMessageBox.critical(frame, "Error", f"Failed to verify: {e}")

    def mark_filled():
        sel = tree.selectionModel().selectedRows()
        if not sel:
            QMessageBox.critical(frame, "Error", "Select a prescription")
            return

        row = sel[0].row()
        rx_number = tree.item(row, 0).text() if tree.item(row, 0) else ''

        try:
            svc.db.mark_prescription_filled(rx_number)
            refresh_from_db()
            QMessageBox.information(frame, "Success", "Prescription marked as filled")
        except Exception as e:
            QMessageBox.critical(frame, "Error", f"Failed to update: {e}")

    make_button(action_layout, "✓ Verify", command=verify_prescription, kind="success")
    make_button(action_layout, "✓ Mark Filled", command=mark_filled, kind="primary")

    layout.addWidget(action_frame)

    # Initial load
    refresh_prescriptions()

    return frame


# ============================================================================
# GLOBAL REFERENCES FOR refresh_from_db
# ============================================================================

# These will be set by create_pharma_tab() to allow refresh_from_db() to work
_inventory_tree = None
_batches_tree = None
_expiry_tree = None
_prescriptions_tree = None
_stats_label = None
_days_var = None

def refresh_from_db():
    """
    Reloads all data from the database through the service layer.
    Call this after every write operation.
    """
    global _inventory_tree, _batches_tree, _expiry_tree, _prescriptions_tree
    global _stats_label, _days_var

    # Refresh inventory
    if _inventory_tree is not None:
        _inventory_tree.setRowCount(0)

        products = svc.pharmacy.get_pharmacy_inventory()
        for row_data in products:
            expiry_status = _get_expiry_status(row_data.get('expiry_date'))
            status_icon = _get_expiry_icon(expiry_status)

            row = _inventory_tree.rowCount()
            _inventory_tree.insertRow(row)
            _inventory_tree.setItem(row, 0, QTableWidgetItem(f"{status_icon} {row_data['model']}"))
            _inventory_tree.setItem(row, 1, QTableWidgetItem(row_data.get('batch_number') or 'N/A'))
            _inventory_tree.setItem(row, 2, QTableWidgetItem(row_data.get('expiry_date') or 'N/A'))
            _inventory_tree.setItem(row, 3, QTableWidgetItem(expiry_status))
            _inventory_tree.setItem(row, 4, QTableWidgetItem(str(row_data.get('stock', 0))))
            _inventory_tree.setItem(row, 5, QTableWidgetItem(row_data.get('manufacturer') or 'N/A'))
            _inventory_tree.setItem(row, 6, QTableWidgetItem('Yes' if row_data.get('requires_prescription') else 'No'))

    # Refresh stats
    if _stats_label is not None:
        stats = svc.pharmacy.get_pharmacy_stats()
        stats_text = (
            f"📊 Total Products: {stats.get('total', 0)}  |  "
            f"🔴 Expired: {stats.get('expired', 0)}  |  "
            f"🟠 Critical (7 days): {stats.get('expiring_soon', 0)}  |  "
            f"🟡 Warning (30 days): {stats.get('low_stock', 0)}"
        )
        _stats_label.setText(stats_text)

    # Refresh batches
    if _batches_tree is not None:
        _batches_tree.setRowCount(0)

        batches = svc.pharmacy.get_batches()
        for row_data in batches:
            expiry_status = _get_batch_expiry_status(row_data.get('expiry_date'))

            row = _batches_tree.rowCount()
            _batches_tree.insertRow(row)
            _batches_tree.setItem(row, 0, QTableWidgetItem(row_data.get('batch_number') or 'N/A'))
            _batches_tree.setItem(row, 1, QTableWidgetItem(row_data.get('model') or 'N/A'))
            _batches_tree.setItem(row, 2, QTableWidgetItem(row_data.get('sku') or 'N/A'))
            _batches_tree.setItem(row, 3, QTableWidgetItem(str(row_data.get('stock', 0))))
            _batches_tree.setItem(row, 4, QTableWidgetItem(row_data.get('expiry_date') or 'N/A'))
            _batches_tree.setItem(row, 5, QTableWidgetItem(expiry_status))
            _batches_tree.setItem(row, 6, QTableWidgetItem(row_data.get('supplier_name') or 'N/A'))

    # Refresh expiry monitor
    if _expiry_tree is not None and _days_var is not None:
        _expiry_tree.setRowCount(0)

        days = _days_var.currentText()
        if days == "ALL":
            products = svc.pharmacy.get_expiring_products(days=9999)
        else:
            products = svc.pharmacy.get_expiring_products(days=int(days))

        for row_data in products:
            days_left = row_data.get('days_until_expiry', 0)
            if days_left < 0:
                status = 'expired'
            elif days_left <= 7:
                status = 'critical'
            elif days_left <= 30:
                status = 'warning'
            else:
                status = 'ok'

            if status != 'ok':
                row = _expiry_tree.rowCount()
                _expiry_tree.insertRow(row)
                _expiry_tree.setItem(row, 0, QTableWidgetItem(row_data.get('model', 'N/A')))
                _expiry_tree.setItem(row, 1, QTableWidgetItem(row_data.get('batch_number') or 'N/A'))
                _expiry_tree.setItem(row, 2, QTableWidgetItem(row_data.get('expiry_date') or 'N/A'))
                _expiry_tree.setItem(row, 3, QTableWidgetItem(f"{int(days_left)} days" if days_left else 'N/A'))
                _expiry_tree.setItem(row, 4, QTableWidgetItem(str(row_data.get('stock', 0))))
                _expiry_tree.setItem(row, 5, QTableWidgetItem(row_data.get('manufacturer') or 'N/A'))
                _expiry_tree.setItem(row, 6, QTableWidgetItem(status.upper()))

    # Refresh prescriptions
    if _prescriptions_tree is not None:
        _prescriptions_tree.setRowCount(0)

        try:
            prescriptions = svc.db.fetch_prescriptions() if hasattr(svc.db, 'fetch_prescriptions') else []
            for row_data in prescriptions:
                row = _prescriptions_tree.rowCount()
                _prescriptions_tree.insertRow(row)
                _prescriptions_tree.setItem(row, 0, QTableWidgetItem(row_data.get('prescription_number', 'N/A')))
                _prescriptions_tree.setItem(row, 1, QTableWidgetItem(row_data.get('patient_name', 'N/A')))
                _prescriptions_tree.setItem(row, 2, QTableWidgetItem(row_data.get('patient_phone', 'N/A')))
                _prescriptions_tree.setItem(row, 3, QTableWidgetItem(row_data.get('doctor_name', 'N/A')))
                _prescriptions_tree.setItem(row, 4, QTableWidgetItem(row_data.get('prescribed_date', 'N/A')))
                _prescriptions_tree.setItem(row, 5, QTableWidgetItem(row_data.get('expiry_date', 'N/A')))
                _prescriptions_tree.setItem(row, 6, QTableWidgetItem(f"{int(row_data.get('days_until_expiry', 0))} days" if row_data.get('days_until_expiry') is not None else 'N/A'))
                _prescriptions_tree.setItem(row, 7, QTableWidgetItem(row_data.get('status', 'N/A')))
                _prescriptions_tree.setItem(row, 8, QTableWidgetItem(f"{row_data.get('refills_used', 0)}/{row_data.get('refills_allowed', 0)}"))
        except Exception as e:
            logger.warning(f"Could not refresh prescriptions: {e}")


# Helper functions for refresh_from_db
def _get_expiry_status(expiry_date):
    if not expiry_date:
        return 'ok'
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        now = datetime.now()
        days_left = (expiry - now).days
        if days_left < 0:
            return 'expired'
        elif days_left <= 7:
            return 'critical'
        elif days_left <= 30:
            return 'warning'
        else:
            return 'ok'
    except Exception:
        logging.debug("Failed to check expiry status")
        return 'unknown'

def _get_expiry_icon(status):
    icons = {
        'expired': '🔴',
        'critical': '🟠',
        'warning': '🟡',
        'ok': '🟢',
        'unknown': '⚪'
    }
    return icons.get(status, '⚪')

def _get_batch_expiry_status(expiry_date):
    if not expiry_date:
        return 'unknown'
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        now = datetime.now()
        days_left = (expiry - now).days
        if days_left < 0:
            return 'expired'
        elif days_left <= 7:
            return 'critical'
        elif days_left <= 30:
            return 'warning'
        else:
            return 'good'
    except Exception:
        logging.debug("Failed to check batch expiry status")
        return 'unknown'


# ============================================================================
# DIALOGS
# ============================================================================

class PharmaProductDialog(QDialog):
    """Dialog for adding pharmacy products."""

    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.result = None
        self.current_user = current_user

        self.setWindowTitle("Add Pharmacy Product")
        self.resize(700, 750)
        self.setModal(True)

        content = QFrame()
        content_layout = QGridLayout(content)

        # Product details
        styled_label(content_layout, "Product Details", font=FONT_BOLD)

        row = 1
        content_layout.addWidget(QLabel("Model Name:"), row, 0)
        self.model_entry = QLineEdit()
        content_layout.addWidget(self.model_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Generic Name:"), row, 0)
        self.generic_entry = QLineEdit()
        content_layout.addWidget(self.generic_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Manufacturer:"), row, 0)
        self.manufacturer_entry = QLineEdit()
        content_layout.addWidget(self.manufacturer_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Batch Number:"), row, 0)
        self.batch_entry = QLineEdit()
        content_layout.addWidget(self.batch_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Expiry Date (YYYY-MM-DD):"), row, 0)
        self.expiry_entry = QLineEdit()
        content_layout.addWidget(self.expiry_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Form:"), row, 0)
        self.form_combo = QComboBox()
        self.form_combo.addItems(["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Drops", "Other"])
        content_layout.addWidget(self.form_combo, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Dosage:"), row, 0)
        self.dosage_entry = QLineEdit()
        content_layout.addWidget(self.dosage_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Storage Temperature:"), row, 0)
        self.storage_entry = QLineEdit()
        content_layout.addWidget(self.storage_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Purchase Price:"), row, 0)
        self.purchase_entry = QLineEdit()
        content_layout.addWidget(self.purchase_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Selling Price:"), row, 0)
        self.selling_entry = QLineEdit()
        content_layout.addWidget(self.selling_entry, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Stock Quantity:"), row, 0)
        self.stock_entry = QLineEdit()
        content_layout.addWidget(self.stock_entry, row, 1)

        row += 1
        self.requires_rx_var = QLineEdit()
        self.requires_rx_var.setPlaceholderText("1 for Yes, 0 for No")
        content_layout.addWidget(QLabel("Requires Prescription:"), row, 0)
        content_layout.addWidget(self.requires_rx_var, row, 1)

        row += 1
        content_layout.addWidget(QLabel("Notes:"), row, 0)
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        content_layout.addWidget(self.notes_text, row, 1)

        # Buttons
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        def save():
            try:
                product_data = {
                    'model': self.model_entry.text(),
                    'generic_name': self.generic_entry.text(),
                    'manufacturer': self.manufacturer_entry.text(),
                    'batch_number': self.batch_entry.text(),
                    'expiry_date': self.expiry_entry.text(),
                    'form': self.form_combo.currentText(),
                    'dosage': self.dosage_entry.text(),
                    'storage_temp': self.storage_entry.text(),
                    'purchase_price': float(self.purchase_entry.text() or 0),
                    'selling_price': float(self.selling_entry.text() or 0),
                    'stock': int(self.stock_entry.text() or 0),
                    'requires_prescription': 1 if self.requires_rx_var.text() == '1' else 0,
                    'notes': self.notes_text.toPlainText().strip()
                }

                # Save through service layer
                svc.inventory.add_product(product_data, username=self.current_user)

                self.result = product_data
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

        make_button(btn_layout, "Save", command=save, kind="primary")
        make_button(btn_layout, "Cancel", command=self.reject, kind="secondary")
        content_layout.addWidget(btn_frame, row + 1, 0, 1, 2)

        self.setLayout(content_layout)


class AddBatchDialog(QDialog):
    """Dialog for adding batches."""

    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.result = None
        self.current_user = current_user

        self.setWindowTitle("Add Batch")
        self.resize(600, 500)
        self.setModal(True)

        content = QFrame()
        content_layout = QGridLayout(content)

        # Product selection
        content_layout.addWidget(QLabel("Select Product:"), 0, 0)

        # Load products through service layer
        products = svc.inventory.get_all_products()

        self.product_var = QComboBox()
        self.product_ids = {p['model']: p['id'] for p in products}
        self.product_var.addItems([p['model'] for p in products])
        content_layout.addWidget(self.product_var, 0, 1)

        # Batch number
        content_layout.addWidget(QLabel("Batch Number:"), 1, 0)
        self.batch_entry = QLineEdit()
        content_layout.addWidget(self.batch_entry, 1, 1)

        # Quantity
        content_layout.addWidget(QLabel("Quantity Received:"), 2, 0)
        self.quantity_entry = QLineEdit()
        content_layout.addWidget(self.quantity_entry, 2, 1)

        # Dates
        content_layout.addWidget(QLabel("Manufacture Date (YYYY-MM-DD):"), 3, 0)
        self.mfg_entry = QLineEdit()
        content_layout.addWidget(self.mfg_entry, 3, 1)

        content_layout.addWidget(QLabel("Expiry Date (YYYY-MM-DD):"), 4, 0)
        self.expiry_entry = QLineEdit()
        content_layout.addWidget(self.expiry_entry, 4, 1)

        # Notes
        content_layout.addWidget(QLabel("Notes:"), 5, 0)
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(80)
        content_layout.addWidget(self.notes_text, 5, 1)

        # Buttons
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        def save():
            try:
                product_sel = self.product_var.currentText()
                product_id = self.product_ids.get(product_sel)
                if not product_id:
                    QMessageBox.critical(self, "Error", "Select a product")
                    return

                # Update product with batch info through service layer
                product = svc.inventory.get_product_by_id(product_id)
                if product:
                    update_data = {
                        'batch_number': self.batch_entry.text(),
                        'manufacture_date': self.mfg_entry.text(),
                        'expiry_date': self.expiry_entry.text(),
                        'notes': self.notes_text.toPlainText().strip()
                    }
                    svc.inventory.update_product(product['model'], update_data, username=self.current_user)

                    # Adjust stock if quantity provided
                    qty = int(self.quantity_entry.text() or 0)
                    if qty > 0:
                        current_stock = product.get('stock', 0)
                        delta = qty - current_stock
                        if delta != 0:
                            svc.inventory.adjust_stock(product['model'], delta, username=self.current_user,
                                                      reason=f"Batch {self.batch_entry.text()} received")

                self.result = True
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

        make_button(btn_layout, "Save", command=save, kind="primary")
        make_button(btn_layout, "Cancel", command=self.reject, kind="secondary")
        content_layout.addWidget(btn_frame, 6, 0, 1, 2)

        self.setLayout(content_layout)


class AddPrescriptionDialog(QDialog):
    """Dialog for adding prescriptions."""

    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.result = None
        self.current_user = current_user

        self.setWindowTitle("Add Prescription")
        self.resize(700, 650)
        self.setModal(True)

        content = QFrame()
        content_layout = QGridLayout(content)

        # Patient details
        content_layout.addWidget(QLabel("Patient Name:"), 0, 0)
        self.patient_entry = QLineEdit()
        content_layout.addWidget(self.patient_entry, 0, 1)

        content_layout.addWidget(QLabel("Phone:"), 1, 0)
        self.phone_entry = QLineEdit()
        content_layout.addWidget(self.phone_entry, 1, 1)

        content_layout.addWidget(QLabel("Email:"), 2, 0)
        self.email_entry = QLineEdit()
        content_layout.addWidget(self.email_entry, 2, 1)

        # Doctor details
        content_layout.addWidget(QLabel("Doctor Name:"), 3, 0)
        self.doctor_entry = QLineEdit()
        content_layout.addWidget(self.doctor_entry, 3, 1)

        content_layout.addWidget(QLabel("Doctor License:"), 4, 0)
        self.license_entry = QLineEdit()
        content_layout.addWidget(self.license_entry, 4, 1)

        # Dates
        content_layout.addWidget(QLabel("Prescribed Date (YYYY-MM-DD):"), 5, 0)
        self.date_entry = QLineEdit()
        content_layout.addWidget(self.date_entry, 5, 1)

        content_layout.addWidget(QLabel("Expiry Date (YYYY-MM-DD):"), 6, 0)
        self.expiry_entry = QLineEdit()
        content_layout.addWidget(self.expiry_entry, 6, 1)

        # Medications
        content_layout.addWidget(QLabel("Medications:"), 7, 0)
        self.meds_text = QTextEdit()
        self.meds_text.setMaximumHeight(100)
        content_layout.addWidget(self.meds_text, 7, 1)

        content_layout.addWidget(QLabel("Dosage Instructions:"), 8, 0)
        self.dosage_text = QTextEdit()
        self.dosage_text.setMaximumHeight(60)
        content_layout.addWidget(self.dosage_text, 8, 1)

        # Refills
        content_layout.addWidget(QLabel("Refills Allowed:"), 9, 0)
        self.refills_entry = QLineEdit()
        content_layout.addWidget(self.refills_entry, 9, 1)

        # Notes
        content_layout.addWidget(QLabel("Notes:"), 10, 0)
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(60)
        content_layout.addWidget(self.notes_text, 10, 1)

        # Buttons
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        def save():
            try:
                rx_number = f"RX-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                prescription_data = {
                    'prescription_number': rx_number,
                    'patient_name': self.patient_entry.text(),
                    'patient_phone': self.phone_entry.text(),
                    'patient_email': self.email_entry.text(),
                    'doctor_name': self.doctor_entry.text(),
                    'doctor_license': self.license_entry.text(),
                    'prescribed_date': self.date_entry.text(),
                    'expiry_date': self.expiry_entry.text(),
                    'medications': self.meds_text.toPlainText().strip(),
                    'dosage_instructions': self.dosage_text.toPlainText().strip(),
                    'refills_allowed': int(self.refills_entry.text() or 0),
                    'notes': self.notes_text.toPlainText().strip(),
                    'created_by': self.current_user
                }

                # Save through service layer if available
                if hasattr(svc.db, 'insert_prescription'):
                    svc.db.insert_prescription(prescription_data)
                else:
                    # Fallback: direct database access through svc.db
                    svc.db.execute_query("""
                        INSERT INTO prescriptions (
                            prescription_number, patient_name, patient_phone, patient_email,
                            doctor_name, doctor_license, prescribed_date, expiry_date,
                            medications, dosage_instructions, refills_allowed, notes, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rx_number,
                        self.patient_entry.text(),
                        self.phone_entry.text(),
                        self.email_entry.text(),
                        self.doctor_entry.text(),
                        self.license_entry.text(),
                        self.date_entry.text(),
                        self.expiry_entry.text(),
                        self.meds_text.toPlainText().strip(),
                        self.dosage_text.toPlainText().strip(),
                        int(self.refills_entry.text() or 0),
                        self.notes_text.toPlainText().strip(),
                        self.current_user
                    ))

                self.result = True
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

        make_button(btn_layout, "Save", command=save, kind="primary")
        make_button(btn_layout, "Cancel", command=self.reject, kind="secondary")
        content_layout.addWidget(btn_frame, 11, 0, 1, 2)

        self.setLayout(content_layout)
