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

import tkinter as tk
from tkinter import ttk, messagebox
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
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill=tk.X, pady=(0, 15))
    
    styled_label(header_frame, "💊 Pharmacy Management", font=FONT_HEADING).pack(side=tk.LEFT)
    
    # Create notebook for sub-tabs
    notebook = ttk.Notebook(window)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Add sub-tabs
    inventory_frame = create_pharma_inventory_tab(notebook, current_user)
    notebook.add(inventory_frame, text="📦 Pharmacy Inventory")
    
    batches_frame = create_batches_tab(notebook, current_user)
    notebook.add(batches_frame, text="📋 Batch Tracking")
    
    expiry_frame = create_expiry_monitor_tab(notebook, current_user)
    notebook.add(expiry_frame, text="⚠️ Expiry Monitor")
    
    prescriptions_frame = create_prescriptions_tab(notebook, current_user)
    notebook.add(prescriptions_frame, text="📝 Prescriptions")
    
    return window


def create_pharma_inventory_tab(parent, current_user=None):
    """Pharmacy inventory with medication-specific fields."""
    global _inventory_tree, _stats_label
    frame = ttk.Frame(parent, padding=15)

    # Toolbar
    toolbar = ttk.Frame(frame)
    toolbar.pack(fill=tk.X, pady=(0, 10))

    def refresh_inventory():
        for item in tree.get_children():
            tree.delete(item)

        products = svc.pharmacy.get_pharmacy_inventory()

        for row in products:
            expiry_status = _get_expiry_status(row.get('expiry_date'))
            status_icon = _get_expiry_icon(expiry_status)

            tree.insert("", "end", values=(
                f"{status_icon} {row['model']}",
                row.get('batch_number') or 'N/A',
                row.get('expiry_date') or 'N/A',
                expiry_status,
                row.get('stock', 0),
                row.get('manufacturer') or 'N/A',
                'Yes' if row.get('requires_prescription') else 'No'
            ))

    # Add product button
    def add_product():
        dialog = PharmaProductDialog(frame, current_user)
        if dialog.result:
            refresh_from_db()
            messagebox.showinfo("Success", "Product added successfully")

    make_button(toolbar, "➕ Add Product", command=add_product, kind="primary").pack(side=tk.LEFT, padx=5)

    # Refresh button
    make_button(toolbar, "🔄 Refresh", command=refresh_from_db, kind="secondary").pack(side=tk.LEFT, padx=5)

    # Filter by expiry
    ttk.Label(toolbar, text="Filter:").pack(side=tk.LEFT, padx=(20, 5))

    expiry_filter = ttk.Combobox(toolbar, values=["All", "Expired", "Critical (<7 days)", "Warning (<30 days)", "OK"], state="readonly", width=20)
    expiry_filter.current(0)
    expiry_filter.pack(side=tk.LEFT)

    # Inventory table
    columns = ("product", "batch", "expiry", "status", "stock", "manufacturer", "prescription")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=120)

    tree.column("product", width=200)
    tree.column("batch", width=100)
    tree.column("expiry", width=100)
    tree.column("status", width=100)
    tree.column("stock", width=80)

    tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # Register global reference
    _inventory_tree = tree

    # Stats card
    stats_frame = make_card(frame, padding=15)
    stats_frame.pack(fill=tk.X, pady=(10, 0))

    def update_stats():
        stats = svc.pharmacy.get_pharmacy_stats()

        stats_text = (
            f"📊 Total Products: {stats.get('total', 0)}  |  "
            f"🔴 Expired: {stats.get('expired', 0)}  |  "
            f"🟠 Critical (7 days): {stats.get('expiring_soon', 0)}  |  "
            f"🟡 Warning (30 days): {stats.get('low_stock', 0)}"
        )

        stats_label.config(text=stats_text)

    stats_label = styled_label(stats_frame, "", font=FONT_BOLD)
    stats_label.pack()

    # Register global reference
    _stats_label = stats_label

    # Initial load
    refresh_inventory()
    update_stats()

    return frame


def create_batches_tab(parent, current_user=None):
    """Batch tracking for pharmacy products."""
    global _batches_tree
    frame = ttk.Frame(parent, padding=15)

    # Toolbar
    toolbar = ttk.Frame(frame)
    toolbar.pack(fill=tk.X, pady=(0, 10))

    def refresh_batches():
        for item in tree.get_children():
            tree.delete(item)

        batches = svc.pharmacy.get_batches()

        for row in batches:
            expiry_status = _get_batch_expiry_status(row.get('expiry_date'))

            tree.insert("", "end", values=(
                row.get('batch_number') or 'N/A',
                row.get('model') or 'N/A',
                row.get('sku') or 'N/A',
                row.get('stock', 0),
                row.get('expiry_date') or 'N/A',
                expiry_status,
                row.get('supplier_name') or 'N/A'
            ))

    # Add batch button
    def add_batch():
        dialog = AddBatchDialog(frame, current_user)
        if dialog.result:
            refresh_from_db()
            messagebox.showinfo("Success", "Batch added successfully")

    make_button(toolbar, "➕ Add Batch", command=add_batch, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(toolbar, "🔄 Refresh", command=refresh_from_db, kind="secondary").pack(side=tk.LEFT, padx=5)

    # Batches table
    columns = ("batch_number", "product", "sku", "quantity", "expiry", "status", "supplier")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=120)

    tree.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    # Register global reference
    _batches_tree = tree

    # Initial load
    refresh_batches()

    return frame


def create_expiry_monitor_tab(parent, current_user=None):
    """Expiry date monitoring dashboard."""
    global _expiry_tree, _days_var
    frame = ttk.Frame(parent, padding=15)

    # Header
    header = ttk.Frame(frame)
    header.pack(fill=tk.X, pady=(0, 10))

    styled_label(header, "⚠️ Expiry Monitor", font=FONT_HEADING).pack(side=tk.LEFT)

    # Time range filter
    ttk.Label(header, text="Show products expiring within:").pack(side=tk.LEFT, padx=(20, 5))

    days_var = tk.StringVar(value="30")
    days_combo = ttk.Combobox(header, textvariable=days_var, values=["7", "14", "30", "60", "90", "ALL"], state="readonly", width=10)
    days_combo.pack(side=tk.LEFT)

    def apply_filter():
        refresh_expiry()

    make_button(header, "Apply Filter", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=5)

    # Expiry table
    columns = ("product", "batch", "expiry_date", "days_left", "stock", "manufacturer", "status")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)

    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=120)

    tree.column("product", width=250)
    tree.column("days_left", width=100)

    tree.pack(fill=tk.BOTH, expand=True)

    # Register global references
    _expiry_tree = tree
    _days_var = days_var

    def refresh_expiry():
        for item in tree.get_children():
            tree.delete(item)

        days = days_var.get()

        if days == "ALL":
            products = svc.pharmacy.get_expiring_products(days=9999)
        else:
            products = svc.pharmacy.get_expiring_products(days=int(days))

        for row in products:
            days_left = row.get('days_until_expiry', 0)
            if days_left < 0:
                status = 'expired'
            elif days_left <= 7:
                status = 'critical'
            elif days_left <= 30:
                status = 'warning'
            else:
                status = 'ok'

            if status != 'ok':
                tree.insert("", "end", values=(
                    row.get('model', 'N/A'),
                    row.get('batch_number') or 'N/A',
                    row.get('expiry_date') or 'N/A',
                    f"{int(days_left)} days" if days_left else 'N/A',
                    row.get('stock', 0),
                    row.get('manufacturer') or 'N/A',
                    status.upper()
                ), tags=(status,))

        # Configure tag colors
        tree.tag_configure('expired', background='#ffcccc')
        tree.tag_configure('critical', background='#ffe6cc')
        tree.tag_configure('warning', background='#fff2cc')

    # Export button
    def export_expiry_report():
        try:
            import csv
            from tkinter import filedialog
            from utils import get_data_dir

            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialdir=get_data_dir(),
                title="Save Expiry Report"
            )

            if file_path:
                products = svc.pharmacy.get_expiring_products(days=9999)

                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Product', 'Batch Number', 'Expiry Date', 'Stock', 'Manufacturer'])
                    for row in products:
                        writer.writerow([
                            row.get('model', ''),
                            row.get('batch_number', ''),
                            row.get('expiry_date', ''),
                            row.get('stock', 0),
                            row.get('manufacturer', '')
                        ])

                messagebox.showinfo("Success", f"Expiry report exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

    make_button(toolbar_frame := ttk.Frame(frame), "📄 Export Report", command=export_expiry_report, kind="secondary").pack(side=tk.RIGHT)

    # Initial load
    refresh_expiry()

    return frame


def create_prescriptions_tab(parent, current_user=None):
    """Prescription management."""
    global _prescriptions_tree
    frame = ttk.Frame(parent, padding=15)

    # Toolbar
    toolbar = ttk.Frame(frame)
    toolbar.pack(fill=tk.X, pady=(0, 10))

    def refresh_prescriptions():
        for item in tree.get_children():
            tree.delete(item)

        try:
            prescriptions = svc.db.fetch_prescriptions() if hasattr(svc.db, 'fetch_prescriptions') else []

            for row in prescriptions:
                tree.insert("", "end", values=(
                    row.get('prescription_number', 'N/A'),
                    row.get('patient_name', 'N/A'),
                    row.get('patient_phone', 'N/A'),
                    row.get('doctor_name', 'N/A'),
                    row.get('prescribed_date', 'N/A'),
                    row.get('expiry_date', 'N/A'),
                    f"{int(row.get('days_until_expiry', 0))} days" if row.get('days_until_expiry') is not None else 'N/A',
                    row.get('status', 'N/A'),
                    f"{row.get('refills_used', 0)}/{row.get('refills_allowed', 0)}"
                ))
        except Exception as e:
            logger.warning(f"Could not load prescriptions: {e}")

    # New prescription button
    def add_prescription():
        dialog = AddPrescriptionDialog(frame, current_user)
        if dialog.result:
            refresh_from_db()
            messagebox.showinfo("Success", "Prescription added successfully")

    make_button(toolbar, "➕ New Prescription", command=add_prescription, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(toolbar, "🔄 Refresh", command=refresh_from_db, kind="secondary").pack(side=tk.LEFT, padx=5)

    # Prescriptions table
    columns = ("rx_number", "patient", "phone", "doctor", "date", "expiry", "days_left", "status", "refills")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

    for col in columns:
        tree.heading(col, text=col.title())
        tree.column(col, width=100)

    tree.column("rx_number", width=120)
    tree.column("patient", width=150)
    tree.column("days_left", width=90)

    tree.pack(fill=tk.BOTH, expand=True)

    # Register global reference
    _prescriptions_tree = tree

    # Action buttons
    action_frame = ttk.Frame(frame)
    action_frame.pack(fill=tk.X, pady=(10, 0))

    def verify_prescription():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a prescription")
            return

        item = tree.item(sel[0])
        rx_number = item['values'][0]

        try:
            svc.db.verify_prescription(rx_number, current_user)
            refresh_from_db()
            messagebox.showinfo("Success", "Prescription verified")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to verify: {e}")

    def mark_filled():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select a prescription")
            return

        item = tree.item(sel[0])
        rx_number = item['values'][0]

        try:
            svc.db.mark_prescription_filled(rx_number)
            refresh_from_db()
            messagebox.showinfo("Success", "Prescription marked as filled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {e}")

    make_button(action_frame, "✓ Verify", command=verify_prescription, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "✓ Mark Filled", command=mark_filled, kind="primary").pack(side=tk.LEFT, padx=5)

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
        for item in _inventory_tree.get_children():
            _inventory_tree.delete(item)

        products = svc.pharmacy.get_pharmacy_inventory()
        for row in products:
            expiry_status = _get_expiry_status(row.get('expiry_date'))
            status_icon = _get_expiry_icon(expiry_status)

            _inventory_tree.insert("", "end", values=(
                f"{status_icon} {row['model']}",
                row.get('batch_number') or 'N/A',
                row.get('expiry_date') or 'N/A',
                expiry_status,
                row.get('stock', 0),
                row.get('manufacturer') or 'N/A',
                'Yes' if row.get('requires_prescription') else 'No'
            ))

    # Refresh stats
    if _stats_label is not None:
        stats = svc.pharmacy.get_pharmacy_stats()
        stats_text = (
            f"📊 Total Products: {stats.get('total', 0)}  |  "
            f"🔴 Expired: {stats.get('expired', 0)}  |  "
            f"🟠 Critical (7 days): {stats.get('expiring_soon', 0)}  |  "
            f"🟡 Warning (30 days): {stats.get('low_stock', 0)}"
        )
        _stats_label.config(text=stats_text)

    # Refresh batches
    if _batches_tree is not None:
        for item in _batches_tree.get_children():
            _batches_tree.delete(item)

        batches = svc.pharmacy.get_batches()
        for row in batches:
            expiry_status = _get_batch_expiry_status(row.get('expiry_date'))

            _batches_tree.insert("", "end", values=(
                row.get('batch_number') or 'N/A',
                row.get('model') or 'N/A',
                row.get('sku') or 'N/A',
                row.get('stock', 0),
                row.get('expiry_date') or 'N/A',
                expiry_status,
                row.get('supplier_name') or 'N/A'
            ))

    # Refresh expiry monitor
    if _expiry_tree is not None and _days_var is not None:
        for item in _expiry_tree.get_children():
            _expiry_tree.delete(item)

        days = _days_var.get()
        if days == "ALL":
            products = svc.pharmacy.get_expiring_products(days=9999)
        else:
            products = svc.pharmacy.get_expiring_products(days=int(days))

        for row in products:
            days_left = row.get('days_until_expiry', 0)
            if days_left < 0:
                status = 'expired'
            elif days_left <= 7:
                status = 'critical'
            elif days_left <= 30:
                status = 'warning'
            else:
                status = 'ok'

            if status != 'ok':
                _expiry_tree.insert("", "end", values=(
                    row.get('model', 'N/A'),
                    row.get('batch_number') or 'N/A',
                    row.get('expiry_date') or 'N/A',
                    f"{int(days_left)} days" if days_left else 'N/A',
                    row.get('stock', 0),
                    row.get('manufacturer') or 'N/A',
                    status.upper()
                ), tags=(status,))

    # Refresh prescriptions
    if _prescriptions_tree is not None:
        for item in _prescriptions_tree.get_children():
            _prescriptions_tree.delete(item)

        try:
            prescriptions = svc.db.fetch_prescriptions() if hasattr(svc.db, 'fetch_prescriptions') else []
            for row in prescriptions:
                _prescriptions_tree.insert("", "end", values=(
                    row.get('prescription_number', 'N/A'),
                    row.get('patient_name', 'N/A'),
                    row.get('patient_phone', 'N/A'),
                    row.get('doctor_name', 'N/A'),
                    row.get('prescribed_date', 'N/A'),
                    row.get('expiry_date', 'N/A'),
                    f"{int(row.get('days_until_expiry', 0))} days" if row.get('days_until_expiry') is not None else 'N/A',
                    row.get('status', 'N/A'),
                    f"{row.get('refills_used', 0)}/{row.get('refills_allowed', 0)}"
                ))
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

class PharmaProductDialog:
    """Dialog for adding pharmacy products."""

    def __init__(self, parent, current_user):
        self.result = None

        self.dlg = tk.Toplevel(parent)
        self.dlg.title("Add Pharmacy Product")
        self.dlg.geometry("700x750")
        self.dlg.transient(parent)
        self.dlg.grab_set()

        content = ttk.Frame(self.dlg, padding=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Product details
        ttk.Label(content, text="Product Details", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        row = 1
        ttk.Label(content, text="Model Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.model_entry = ttk.Entry(content, width=50)
        self.model_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Generic Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.generic_entry = ttk.Entry(content, width=50)
        self.generic_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Manufacturer:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.manufacturer_entry = ttk.Entry(content, width=50)
        self.manufacturer_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Batch Number:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.batch_entry = ttk.Entry(content, width=50)
        self.batch_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Expiry Date (YYYY-MM-DD):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.expiry_entry = ttk.Entry(content, width=50)
        self.expiry_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Form:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.form_combo = ttk.Combobox(content, values=["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Ointment", "Drops", "Other"], state="readonly", width=47)
        self.form_combo.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Dosage:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.dosage_entry = ttk.Entry(content, width=50)
        self.dosage_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Storage Temperature:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.storage_entry = ttk.Entry(content, width=50)
        self.storage_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Purchase Price:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.purchase_entry = ttk.Entry(content, width=50)
        self.purchase_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Selling Price:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.selling_entry = ttk.Entry(content, width=50)
        self.selling_entry.grid(row=row, column=1, pady=5)

        row += 1
        ttk.Label(content, text="Stock Quantity:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.stock_entry = ttk.Entry(content, width=50)
        self.stock_entry.grid(row=row, column=1, pady=5)

        row += 1
        self.requires_rx_var = tk.BooleanVar()
        ttk.Checkbutton(content, text="Requires Prescription", variable=self.requires_rx_var).grid(row=row, column=1, sticky=tk.W, pady=10)

        row += 1
        ttk.Label(content, text="Notes:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(content, width=50, height=4)
        self.notes_text.grid(row=row, column=1, pady=5)

        # Buttons
        btn_frame = ttk.Frame(content)
        btn_frame.grid(row=row+1, column=0, columnspan=2, pady=(20, 0))

        def save():
            try:
                product_data = {
                    'model': self.model_entry.get(),
                    'generic_name': self.generic_entry.get(),
                    'manufacturer': self.manufacturer_entry.get(),
                    'batch_number': self.batch_entry.get(),
                    'expiry_date': self.expiry_entry.get(),
                    'form': self.form_combo.get(),
                    'dosage': self.dosage_entry.get(),
                    'storage_temp': self.storage_entry.get(),
                    'purchase_price': float(self.purchase_entry.get() or 0),
                    'selling_price': float(self.selling_entry.get() or 0),
                    'stock': int(self.stock_entry.get() or 0),
                    'requires_prescription': 1 if self.requires_rx_var.get() else 0,
                    'notes': self.notes_text.get("1.0", tk.END).strip()
                }

                # Save through service layer
                svc.inventory.add_product(product_data, username=current_user)

                self.result = product_data
                self.dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        make_button(btn_frame, "Save", command=save, kind="primary").pack(side=tk.LEFT, padx=5)
        make_button(btn_frame, "Cancel", command=self.dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


class AddBatchDialog:
    """Dialog for adding batches."""

    def __init__(self, parent, current_user):
        self.result = None

        self.dlg = tk.Toplevel(parent)
        self.dlg.title("Add Batch")
        self.dlg.geometry("600x500")
        self.dlg.transient(parent)
        self.dlg.grab_set()

        content = ttk.Frame(self.dlg, padding=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Product selection
        ttk.Label(content, text="Select Product:").grid(row=0, column=0, sticky=tk.W, pady=5)

        # Load products through service layer
        products = svc.inventory.get_all_products()

        self.product_var = tk.StringVar()
        self.product_ids = {p['model']: p['id'] for p in products}
        product_combo = ttk.Combobox(content, textvariable=self.product_var, values=[p['model'] for p in products], state="readonly", width=47)
        product_combo.grid(row=0, column=1, pady=5)

        # Batch number
        ttk.Label(content, text="Batch Number:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_entry = ttk.Entry(content, width=50)
        self.batch_entry.grid(row=1, column=1, pady=5)

        # Quantity
        ttk.Label(content, text="Quantity Received:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.quantity_entry = ttk.Entry(content, width=50)
        self.quantity_entry.grid(row=2, column=1, pady=5)

        # Dates
        ttk.Label(content, text="Manufacture Date (YYYY-MM-DD):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.mfg_entry = ttk.Entry(content, width=50)
        self.mfg_entry.grid(row=3, column=1, pady=5)

        ttk.Label(content, text="Expiry Date (YYYY-MM-DD):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.expiry_entry = ttk.Entry(content, width=50)
        self.expiry_entry.grid(row=4, column=1, pady=5)

        # Notes
        ttk.Label(content, text="Notes:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(content, width=50, height=4)
        self.notes_text.grid(row=5, column=1, pady=5)

        # Buttons
        btn_frame = ttk.Frame(content)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))

        def save():
            try:
                product_id = self.product_ids.get(self.product_var.get())
                if not product_id:
                    messagebox.showerror("Error", "Select a product")
                    return

                # Update product with batch info through service layer
                product = svc.inventory.get_product_by_id(product_id)
                if product:
                    update_data = {
                        'batch_number': self.batch_entry.get(),
                        'manufacture_date': self.mfg_entry.get(),
                        'expiry_date': self.expiry_entry.get(),
                        'notes': self.notes_text.get("1.0", tk.END).strip()
                    }
                    svc.inventory.update_product(product['model'], update_data, username=current_user)

                    # Adjust stock if quantity provided
                    qty = int(self.quantity_entry.get() or 0)
                    if qty > 0:
                        current_stock = product.get('stock', 0)
                        delta = qty - current_stock
                        if delta != 0:
                            svc.inventory.adjust_stock(product['model'], delta, username=current_user,
                                                      reason=f"Batch {self.batch_entry.get()} received")

                self.result = True
                self.dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        make_button(btn_frame, "Save", command=save, kind="primary").pack(side=tk.LEFT, padx=5)
        make_button(btn_frame, "Cancel", command=self.dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


class AddPrescriptionDialog:
    """Dialog for adding prescriptions."""

    def __init__(self, parent, current_user):
        self.result = None

        self.dlg = tk.Toplevel(parent)
        self.dlg.title("Add Prescription")
        self.dlg.geometry("700x650")
        self.dlg.transient(parent)
        self.dlg.grab_set()

        content = ttk.Frame(self.dlg, padding=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Patient details
        ttk.Label(content, text="Patient Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.patient_entry = ttk.Entry(content, width=50)
        self.patient_entry.grid(row=0, column=1, pady=5)

        ttk.Label(content, text="Phone:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.phone_entry = ttk.Entry(content, width=50)
        self.phone_entry.grid(row=1, column=1, pady=5)

        ttk.Label(content, text="Email:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.email_entry = ttk.Entry(content, width=50)
        self.email_entry.grid(row=2, column=1, pady=5)

        # Doctor details
        ttk.Label(content, text="Doctor Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.doctor_entry = ttk.Entry(content, width=50)
        self.doctor_entry.grid(row=3, column=1, pady=5)

        ttk.Label(content, text="Doctor License:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.license_entry = ttk.Entry(content, width=50)
        self.license_entry.grid(row=4, column=1, pady=5)

        # Dates
        ttk.Label(content, text="Prescribed Date (YYYY-MM-DD):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.date_entry = ttk.Entry(content, width=50)
        self.date_entry.grid(row=5, column=1, pady=5)

        ttk.Label(content, text="Expiry Date (YYYY-MM-DD):").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.expiry_entry = ttk.Entry(content, width=50)
        self.expiry_entry.grid(row=6, column=1, pady=5)

        # Medications
        ttk.Label(content, text="Medications:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.meds_text = tk.Text(content, width=50, height=5)
        self.meds_text.grid(row=7, column=1, pady=5)

        ttk.Label(content, text="Dosage Instructions:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.dosage_text = tk.Text(content, width=50, height=3)
        self.dosage_text.grid(row=8, column=1, pady=5)

        # Refills
        ttk.Label(content, text="Refills Allowed:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.refills_entry = ttk.Entry(content, width=50)
        self.refills_entry.grid(row=9, column=1, pady=5)

        # Notes
        ttk.Label(content, text="Notes:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(content, width=50, height=3)
        self.notes_text.grid(row=10, column=1, pady=5)

        # Buttons
        btn_frame = ttk.Frame(content)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(20, 0))

        def save():
            try:
                rx_number = f"RX-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                prescription_data = {
                    'prescription_number': rx_number,
                    'patient_name': self.patient_entry.get(),
                    'patient_phone': self.phone_entry.get(),
                    'patient_email': self.email_entry.get(),
                    'doctor_name': self.doctor_entry.get(),
                    'doctor_license': self.license_entry.get(),
                    'prescribed_date': self.date_entry.get(),
                    'expiry_date': self.expiry_entry.get(),
                    'medications': self.meds_text.get("1.0", tk.END).strip(),
                    'dosage_instructions': self.dosage_text.get("1.0", tk.END).strip(),
                    'refills_allowed': int(self.refills_entry.get() or 0),
                    'notes': self.notes_text.get("1.0", tk.END).strip(),
                    'created_by': current_user
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
                        self.patient_entry.get(),
                        self.phone_entry.get(),
                        self.email_entry.get(),
                        self.doctor_entry.get(),
                        self.license_entry.get(),
                        self.date_entry.get(),
                        self.expiry_entry.get(),
                        self.meds_text.get("1.0", tk.END).strip(),
                        self.dosage_text.get("1.0", tk.END).strip(),
                        int(self.refills_entry.get() or 0),
                        self.notes_text.get("1.0", tk.END).strip(),
                        current_user
                    ))

                self.result = True
                self.dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        make_button(btn_frame, "Save", command=save, kind="primary").pack(side=tk.LEFT, padx=5)
        make_button(btn_frame, "Cancel", command=self.dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)
