"""
Electronics-Specific Features Module
=====================================
Serial number tracking, device specifications, and warranty management.

REFACTORED: All database access goes through the service layer (svc).
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
    window = ttk.Frame(parent, padding=15)

    # Header with stats
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "📱 Electronics Management", font=FONT_BOLD).pack(side=tk.LEFT)

    # Summary cards
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))
    summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def create_summary_card(parent, title, value, col):
        card = make_card(parent, padding=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")

        styled_label(card, text=title, font=("Segoe UI", 10), foreground="#6c757d").pack(anchor="w")
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 24, "bold"), foreground=COLOR_PRIMARY)
        value_label.pack(anchor="w", pady=(5, 0))

        return value_label

    total_lbl = create_summary_card(summary_frame, "Devices Tracked", 0, 0)
    warranty_lbl = create_summary_card(summary_frame, "Under Warranty", 0, 1)
    expiring_lbl = create_summary_card(summary_frame, "Warranty Expiring", 0, 2)
    expired_lbl = create_summary_card(summary_frame, "Warranty Expired", 0, 3)

    window.summary_labels = {
        'total': total_lbl,
        'warranty': warranty_lbl,
        'expiring': expiring_lbl,
        'expired': expired_lbl
    }

    # Filter toolbar
    toolbar_frame = ttk.Frame(window)
    toolbar_frame.pack(fill="x", pady=(0, 10))

    styled_label(toolbar_frame, "Filter:").pack(side=tk.LEFT, padx=(0, 10))

    status_var = tk.StringVar(value="all")
    status_combo = ttk.Combobox(
        toolbar_frame,
        textvariable=status_var,
        values=["all", "in_stock", "sold", "warranty_active", "warranty_expiring", "warranty_expired"],
        state="readonly",
        width=20
    )
    status_combo.pack(side=tk.LEFT, padx=5)

    def apply_filter():
        refresh_from_db()

    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), refresh_from_db()), kind="secondary").pack(side=tk.LEFT)

    # Devices table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("serial", "product", "status", "warranty_end", "purchase_date", "sold_date", "actions")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "serial": ("Serial Number", 150),
        "product": ("Product", 250),
        "status": ("Status", 100),
        "warranty_end": ("Warranty End", 120),
        "purchase_date": ("Purchase Date", 120),
        "sold_date": ("Sold Date", 120),
        "actions": ("Actions", 100)
    }

    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text, anchor="w")
        tree.column(col, width=width, anchor="w", minwidth=80)

    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.pack(side=tk.LEFT, fill="both", expand=True)

    # Action buttons
    action_frame = ttk.Frame(window)
    action_frame.pack(fill="x", pady=(10, 0))

    def on_add_serial():
        open_add_serial_dialog(window, current_user=current_user)

    def on_view_details():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a device")
            return

        serial_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if serial_id:
            open_device_details(window, serial_id=int(serial_id))

    def on_mark_sold():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a device")
            return

        serial_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if serial_id:
            open_mark_sold_dialog(window, serial_id=int(serial_id))

    make_button(action_frame, "➕ Add Serial", command=on_add_serial, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "💰 Mark Sold", command=on_mark_sold, kind="success").pack(side=tk.LEFT, padx=5)

    # Store state
    window.status_var = status_var
    window.tree = tree

    # Cache for products lookup
    window._products_cache = {}

    def refresh_from_db():
        """Reload all data from the database through services."""
        tree.delete(*tree.get_children())

        # Reload all serial numbers through service
        all_serials = svc.serial.get_serial_numbers()

        # Build product lookup cache
        all_products = svc.inventory.get_all_products()
        product_cache = {}
        for p in all_products:
            product_cache[p['id']] = p
        window._products_cache = product_cache

        status_filter = status_var.get()

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
        window.summary_labels['total'].config(text=str(total))
        window.summary_labels['warranty'].config(text=str(under_warranty))

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

            tags = (str(device['id']),)

            tree.insert("", "end", values=(
                device.get('serial_number', ''),
                product_info,
                status_text,
                device.get('warranty_end', 'N/A')[:10] if device.get('warranty_end') else 'N/A',
                device.get('purchase_date', 'N/A')[:10] if device.get('purchase_date') else 'N/A',
                device.get('sold_date', 'N/A')[:10] if device.get('sold_date') else 'N/A',
                "👁️ View"
            ), tags=tags)

    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_add_serial_dialog(parent, current_user=None):
    """Dialog to add a new serial number for a product."""
    dlg = tk.Toplevel(parent)
    dlg.title("Add Device Serial Number")
    dlg.geometry("850x800")
    dlg.resizable(True, True)
    dlg.minsize(700, 650)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Heading
    styled_label(content, "Device Information", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    # Form
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)

    form_frame.grid_columnconfigure(0, weight=1)

    # Product selection
    styled_label(form_frame, "Product *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)

    product_var = tk.StringVar()
    product_combo = ttk.Combobox(form_frame, textvariable=product_var, state="readonly")
    product_combo.grid(row=1, column=0, sticky=tk.EW, pady=5)

    # Load products through service
    all_products = svc.inventory.get_all_products()
    product_data = [(p['id'], f"{p['model']} ({p.get('category', '')})") for p in all_products]
    product_combo['values'] = [p[1] for p in product_data]

    # Serial Number
    styled_label(form_frame, "Serial Number *:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    serial_var = tk.StringVar()
    serial_entry = ttk.Entry(form_frame, textvariable=serial_var)
    serial_entry.grid(row=3, column=0, sticky=tk.EW, pady=5)

    # Purchase Date
    styled_label(form_frame, "Purchase Date:", font=FONT_BOLD).grid(row=4, column=0, sticky=tk.W, pady=5)
    purchase_var = tk.StringVar()
    purchase_entry = ttk.Entry(form_frame, textvariable=purchase_var)
    purchase_entry.grid(row=5, column=0, sticky=tk.EW, pady=5)
    purchase_var.set(str(date.today()))

    # Warranty End Date
    styled_label(form_frame, "Warranty End Date:", font=FONT_BOLD).grid(row=6, column=0, sticky=tk.W, pady=5)
    warranty_var = tk.StringVar()
    warranty_entry = ttk.Entry(form_frame, textvariable=warranty_var)
    warranty_entry.grid(row=7, column=0, sticky=tk.EW, pady=5)

    # Status
    styled_label(form_frame, "Status:", font=FONT_BOLD).grid(row=8, column=0, sticky=tk.W, pady=5)
    status_var = tk.StringVar(value="in_stock")
    status_combo = ttk.Combobox(form_frame, textvariable=status_var, values=["in_stock", "sold", "damaged", "refurbished"], state="readonly")
    status_combo.grid(row=9, column=0, sticky=tk.EW, pady=5)

    # Notes
    styled_label(form_frame, "Notes:", font=FONT_BOLD).grid(row=10, column=0, sticky=tk.W, pady=5)
    notes_text = tk.Text(form_frame, height=3)
    notes_text.grid(row=11, column=0, sticky=tk.EW, pady=5)

    # Save button
    def save_serial():
        product_sel = product_var.get()
        serial = serial_var.get().strip()
        purchase_date = purchase_var.get().strip()
        warranty_end = warranty_var.get().strip()
        status = status_var.get()
        notes = notes_text.get("1.0", tk.END).strip()

        if not product_sel:
            messagebox.showerror("Error", "Please select a product")
            return

        if not serial:
            messagebox.showerror("Error", "Serial number is required")
            return

        # Find product ID
        product_id = None
        for pid, pname in product_data:
            if pname == product_sel:
                product_id = pid
                break

        if not product_id:
            messagebox.showerror("Error", "Invalid product selection")
            return

        # Check for duplicate serial through service
        existing_serials = svc.serial.get_serial_numbers(product_id=product_id)
        for existing in existing_serials:
            if existing.get('serial_number') == serial:
                messagebox.showerror("Error", "This serial number already exists for this product")
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

            messagebox.showinfo("Success", "Device serial number added")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to add serial number")
            messagebox.showerror("Error", f"Failed to add serial number: {e}")

    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    make_button(btn_frame, "💾 Save", command=save_serial, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_device_details(parent, serial_id):
    """View detailed device information."""
    dlg = tk.Toplevel(parent)
    dlg.title("Device Details")
    dlg.geometry("950x850")
    dlg.resizable(True, True)
    dlg.minsize(750, 700)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Get device info through service
    all_serials = svc.serial.get_serial_numbers()
    device = None
    for sn in all_serials:
        if sn.get('id') == serial_id:
            device = sn
            break

    if not device:
        styled_label(content, "Device not found", font=FONT_BOLD, foreground=COLOR_DANGER).pack(anchor=tk.W)
        ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=15)
        return

    # Get product info through service
    product_id = device.get('product_id')
    product = svc.inventory.get_product_by_id(product_id) if product_id else None

    # Heading
    model_name = product.get('model', 'Unknown') if product else 'Unknown'
    styled_label(content, f"📱 {model_name}", font=FONT_BOLD).pack(anchor=tk.W)
    styled_label(content, f"Serial: {device.get('serial_number', '')}", foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(5, 15))

    # Device specs
    specs_frame = make_card(content, padding=15)
    specs_frame.pack(fill=tk.X)

    styled_label(specs_frame, "Device Specifications", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 10))

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
        frame = ttk.Frame(specs_frame)
        frame.pack(fill=tk.X, pady=3)
        styled_label(frame, f"{label_text}", font=("Segoe UI", 10, "bold"), width=12).pack(side=tk.LEFT)
        styled_label(frame, f"{value}").pack(side=tk.LEFT)

    # Status info
    status_frame = make_card(content, padding=15)
    status_frame.pack(fill=tk.X, pady=(10, 0))

    styled_label(status_frame, "Status Information", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 10))

    status_info = [
        ("Status:", device.get('status', '').replace('_', ' ').title()),
        ("Purchase Date:", device.get('purchase_date', 'N/A')[:10] if device.get('purchase_date') else 'N/A'),
        ("Warranty End:", device.get('warranty_end', 'N/A')[:10] if device.get('warranty_end') else 'N/A'),
        ("Sold Date:", device.get('sold_date', 'N/A')[:10] if device.get('sold_date') else 'N/A'),
        ("Notes:", device.get('notes') or 'None'),
    ]

    for label_text, value in status_info:
        frame = ttk.Frame(status_frame)
        frame.pack(fill=tk.X, pady=3)
        styled_label(frame, f"{label_text}", font=("Segoe UI", 10, "bold"), width=12).pack(side=tk.LEFT)
        styled_label(frame, f"{value}").pack(side=tk.LEFT)

    # Close button
    ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=15)


def open_mark_sold_dialog(parent, serial_id):
    """Mark a device as sold."""
    dlg = tk.Toplevel(parent)
    dlg.title("Mark Device as Sold")
    dlg.geometry("750x650")
    dlg.resizable(True, True)
    dlg.minsize(600, 550)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    styled_label(content, "Mark Device as Sold", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)

    # Sold Date
    styled_label(form_frame, "Sold Date:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    sold_var = tk.StringVar()
    sold_entry = ttk.Entry(form_frame, textvariable=sold_var)
    sold_entry.grid(row=1, column=0, sticky=tk.EW, pady=5)

    sold_var.set(str(date.today()))

    # Notes
    styled_label(form_frame, "Notes:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    notes_text = tk.Text(form_frame, height=4)
    notes_text.grid(row=3, column=0, sticky=tk.EW, pady=5)

    def save_sold():
        sold_date = sold_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()

        try:
            # Get the serial number first to use for update
            all_serials = svc.serial.get_serial_numbers()
            serial_record = None
            for sn in all_serials:
                if sn.get('id') == serial_id:
                    serial_record = sn
                    break

            if not serial_record:
                messagebox.showerror("Error", "Serial number record not found")
                return

            serial_number = serial_record.get('serial_number', '')

            # Update status through service
            username = getattr(parent, '_current_user', None) or "system"
            svc.serial.update_serial_status(serial_number, 'sold', username=username)

            # Note: The service only updates status. If we need to update sold_date and notes,
            # we would need an extended service method. For now, we update status only.

            messagebox.showinfo("Success", "Device marked as sold")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to mark device as sold")
            messagebox.showerror("Error", f"Failed to mark as sold: {e}")

    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    make_button(btn_frame, "💾 Mark as Sold", command=save_sold, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)
