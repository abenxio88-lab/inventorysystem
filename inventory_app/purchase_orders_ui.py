"""
Purchase Orders Module
=======================
Complete purchase order management system.
Create POs, track status, receive goods, and manage supplier orders.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta

from services import svc
from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, BTN_WIDTH


def _get_suppliers_list():
    """Helper: get suppliers list for dropdowns."""
    return [(s.get('id'), s.get('name'), s.get('code')) for s in svc.supplier.get_all_suppliers()]


def create_purchase_orders_tab(parent, current_user=None):
    """
    Creates the purchase orders management tab.
    """
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "📦 Purchase Orders", font=FONT_BOLD).pack(side=tk.LEFT)

    # New PO button
    def open_new_po():
        open_create_po_dialog(window, current_user=current_user)

    make_button(header_frame, "➕ New Purchase Order", command=open_new_po, kind="success").pack(side=tk.RIGHT)

    # Summary cards
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))
    summary_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    def create_summary_card(parent, title, value, col):
        card = make_card(parent, padding=12)
        card.grid(row=0, column=col, padx=8, sticky="nsew")

        styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d").pack(anchor="w")
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        value_label.pack(anchor="w", pady=(3, 0))

        return value_label

    draft_lbl = create_summary_card(summary_frame, "Draft", 0, 0)
    sent_lbl = create_summary_card(summary_frame, "Sent", 0, 1)
    confirmed_lbl = create_summary_card(summary_frame, "Confirmed", 0, 2)
    received_lbl = create_summary_card(summary_frame, "Received", 0, 3)
    total_lbl = create_summary_card(summary_frame, "Total POs", 0, 4)

    window.summary_labels = {
        'draft': draft_lbl,
        'sent': sent_lbl,
        'confirmed': confirmed_lbl,
        'received': received_lbl,
        'total': total_lbl
    }

    # Filter toolbar
    toolbar_frame = ttk.Frame(window)
    toolbar_frame.pack(fill="x", pady=(0, 10))

    styled_label(toolbar_frame, "Status:").pack(side=tk.LEFT, padx=(0, 10))

    status_var = tk.StringVar(value="all")
    status_combo = ttk.Combobox(
        toolbar_frame,
        textvariable=status_var,
        values=["all", "draft", "sent", "confirmed", "partial", "received", "cancelled"],
        state="readonly",
        width=15
    )
    status_combo.pack(side=tk.LEFT, padx=5)

    styled_label(toolbar_frame, "Supplier:").pack(side=tk.LEFT, padx=(15, 5))

    supplier_var = tk.StringVar(value="all")
    supplier_combo = ttk.Combobox(toolbar_frame, textvariable=supplier_var, state="readonly", width=20)
    supplier_combo.pack(side=tk.LEFT, padx=5)

    # Load suppliers
    suppliers = svc.supplier.get_all_suppliers()
    supplier_data = [("all", "All Suppliers")] + [(s['id'], f"{s['code']} - {s['name']}") for s in suppliers]
    supplier_combo['values'] = [s[1] for s in supplier_data]

    def apply_filter():
        refresh_from_db()

    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), supplier_var.set("all"), refresh_from_db()), kind="secondary").pack(side=tk.LEFT)

    # PO table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("po_number", "supplier", "order_date", "expected_date", "status", "total_amount", "items")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "po_number": ("PO Number", 120),
        "supplier": ("Supplier", 200),
        "order_date": ("Order Date", 100),
        "expected_date": ("Expected", 100),
        "status": ("Status", 100),
        "total_amount": ("Total Amount", 120),
        "items": ("Items", 60)
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

    def on_view_details():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a purchase order")
            return

        po_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if po_id:
            open_po_details(window, po_id=int(po_id), current_user=current_user)

    def on_receive_goods():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a purchase order")
            return

        po_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if po_id:
            open_grn_dialog(window, po_id=int(po_id), current_user=current_user)

    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "📥 Receive Goods", command=on_receive_goods, kind="success").pack(side=tk.LEFT, padx=5)

    # Store state
    window.status_var = status_var
    window.supplier_var = supplier_var
    window.tree = tree
    window.supplier_data = supplier_data

    def refresh_from_db():
        """Refresh purchase orders list from database using services."""
        tree.delete(*tree.get_children())

        status_filter = status_var.get()
        supplier_sel = supplier_var.get()

        # Get all POs through service
        status_arg = None if status_filter == 'all' else status_filter
        pos = svc.purchase_order.get_all_orders(status=status_arg)

        # Get supplier ID if selected
        supplier_id = None
        if supplier_sel != "all":
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

        window.summary_labels['draft'].config(text=str(status_counts['draft']))
        window.summary_labels['sent'].config(text=str(status_counts['sent']))
        window.summary_labels['confirmed'].config(text=str(status_counts['confirmed']))
        window.summary_labels['received'].config(text=str(status_counts['received']))
        window.summary_labels['total'].config(text=str(status_counts['total']))

        # Populate table
        status_colors = {
            'draft': '#6c757d',
            'sent': COLOR_PRIMARY,
            'confirmed': COLOR_WARNING,
            'partial': COLOR_PRIMARY,
            'received': COLOR_SUCCESS,
            'cancelled': COLOR_DANGER
        }

        for po in pos:
            status_text = po['status'].replace('_', ' ').title()
            tags = (str(po['id']),)

            tree.insert("", "end", values=(
                po['po_number'],
                po['supplier_name'],
                po['order_date'][:10] if po['order_date'] else 'N/A',
                po['expected_date'][:10] if po['expected_date'] else 'N/A',
                status_text,
                f"Rs. {po['total_amount']:,.2f}" if po['total_amount'] else 'Rs. 0.00',
                po['item_count']
            ), tags=tags)

    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_create_po_dialog(parent, current_user=None):
    """Premium dialog to create a new purchase order with proper sizing and scrolling."""
    from app_core import PremiumPopup, app_state, data_linker

    dlg = PremiumPopup(parent, "Create Purchase Order", width=850, height=700, resizable=True)
    content = dlg.get_content_frame()

    # Header with industry context
    header_card = make_card(content, padx=30, pady=20)
    header_card.pack(fill="x", pady=(20, 15))

    industry_config = app_state.get_industry_config()
    header_title = styled_label(header_card, f"📦 {industry_config['icon']} New Purchase Order",
                                font=FONT_BOLD, foreground=COLOR_PRIMARY)
    header_title.pack()

    if industry_config['features']:
        features_text = " • ".join(industry_config['features'])
        features_label = styled_label(header_card, features_text,
                                     font=("Segoe UI", 9), foreground="#6c757d")
        features_label.pack(pady=(5, 0))

    # Main form card
    form_card = make_card(content, padding=20)
    form_card.pack(fill="both", expand=True, pady=(0, 15))

    # Supplier selection row
    supplier_row = ttk.Frame(form_card)
    supplier_row.pack(fill="x", pady=(0, 15))

    styled_label(supplier_row, "Supplier *:", font=FONT_BOLD).grid(row=0, column=0, sticky="w", padx=5, pady=5)
    styled_label(supplier_row, "Expected Date:", font=FONT_BOLD).grid(row=0, column=1, sticky="w", padx=(20, 5), pady=5)

    supplier_var = tk.StringVar()
    supplier_combo = ttk.Combobox(supplier_row, textvariable=supplier_var, state="readonly", width=40)
    supplier_combo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    expected_var = tk.StringVar()
    expected_entry = ttk.Entry(supplier_row, textvariable=expected_var, width=15)
    expected_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    # Load suppliers via service
    suppliers = svc.supplier.get_all_suppliers()
    supplier_data = [(s['id'], f"{s['code']} - {s['name']}") for s in suppliers]
    supplier_combo['values'] = [s[1] for s in supplier_data]

    # Set default expected date (7 days from now)
    default_expected = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    expected_var.set(default_expected)

    # Product addition section
    styled_label(form_card, "Add Products:", font=FONT_BOLD).pack(anchor="w", pady=(15, 8))

    products_card = make_card(form_card, padding=15)
    products_card.pack(fill="x", pady=(0, 15))

    # Product selection row with better spacing
    select_frame = ttk.Frame(products_card)
    select_frame.pack(fill="x", pady=(0, 10))

    styled_label(select_frame, "Product:", font=FONT_BOLD).pack(side="left", padx=(0, 5))

    product_var = tk.StringVar()
    product_combo = ttk.Combobox(select_frame, textvariable=product_var, state="readonly", width=35)
    product_combo.pack(side="left", padx=5, fill="x", expand=True)

    # Load products from service
    try:
        products = svc.inventory.get_all_products()
        product_data = [(p.id, f"{p.model} (Stock: {p.stock}, Cost: Rs. {p.purchase_price})") for p in products]
        product_combo['values'] = [p[1] for p in product_data]
    except Exception as e:
        logging.error(f"Failed to load products: {e}")
        product_data = []
        product_combo['values'] = ["No products available"]

    styled_label(select_frame, "Qty:", font=FONT_BOLD).pack(side="left", padx=(15, 5))

    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(select_frame, textvariable=qty_var, width=8)
    qty_entry.pack(side="left", padx=5)

    styled_label(select_frame, "Unit Price:", font=FONT_BOLD).pack(side="left", padx=(10, 5))

    price_var = tk.StringVar(value="0")
    price_entry = ttk.Entry(select_frame, textvariable=price_var, width=12)
    price_entry.pack(side="left", padx=5)

    # Add button
    add_btn = make_button(select_frame, "➕ Add", command=lambda: None, kind="primary")
    add_btn.pack(side="left", padx=15)

    # Items list section
    styled_label(form_card, "Order Items:", font=FONT_BOLD).pack(anchor="w", pady=(10, 5))

    items_frame = ttk.Frame(form_card)
    items_frame.pack(fill="both", expand=True)

    columns = ("product", "quantity", "unit_price", "total", "actions")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=8)

    column_widths = {"product": 280, "quantity": 100, "unit_price": 130, "total": 130, "actions": 100}
    for col in columns:
        items_tree.heading(col, text=col.replace("_", " ").title())
        items_tree.column(col, width=column_widths.get(col, 120))

    scrollbar = ttk.Scrollbar(items_frame, orient="vertical", command=items_tree.yview)
    items_tree.configure(yscrollcommand=scrollbar.set)

    items_tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # PO items storage
    po_items = []

    def add_item():
        product_sel = product_var.get()
        qty = qty_var.get()
        price = price_var.get()

        if not product_sel or product_sel == "No products available":
            messagebox.showerror("Error", "Please select a product")
            return

        try:
            qty_int = int(qty)
            price_float = float(price)
            if qty_int <= 0 or price_float < 0:
                raise ValueError("quantity must be positive and price non-negative")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid quantity or price: {e}")
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
            messagebox.showerror("Error", "Product not found")
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
        items_tree.insert("", "end", values=(
            product_name,
            qty_int,
            f"Rs. {price_float:,.2f}",
            f"Rs. {total:,.2f}",
            "🗑️ Remove"
        ))

        # Clear selection
        product_var.set("")
        qty_var.set("1")
        price_var.set("0")
        update_total()

    # Connect add button
    add_btn.config(command=add_item)

    def on_item_click(event):
        sel = items_tree.selection()
        if not sel:
            return

        item = items_tree.item(sel[0])
        if item['values'][4] == "🗑️ Remove":
            index = items_tree.index(sel[0])
            if 0 <= index < len(po_items):
                po_items.pop(index)
                items_tree.delete(sel[0])
                update_total()

    items_tree.bind("<Button-1>", on_item_click)

    # Notes section
    styled_label(form_card, "Notes:", font=FONT_BOLD).pack(anchor="w", pady=(15, 5))
    notes_text = tk.Text(form_card, height=3, font=FONT_REGULAR)
    notes_text.pack(fill="x", pady=(0, 15))

    # Total label
    total_var = tk.StringVar(value="Total: Rs. 0.00")
    total_label = styled_label(form_card, textvariable=total_var, font=("Segoe UI", 14, "bold"), foreground=COLOR_SUCCESS)
    total_label.pack(anchor="e", pady=(5, 10))

    def update_total():
        total = sum(item['total'] for item in po_items)
        total_var.set(f"Total: Rs. {total:,.2f}")

    # Button bar at bottom
    button_frame = ttk.Frame(content)
    button_frame.pack(fill="x", pady=(10, 25))

    def save_po():
        supplier_sel = supplier_var.get()
        expected_date = expected_var.get().strip()
        notes = notes_text.get("1.0", "end").strip()

        if not supplier_sel:
            messagebox.showerror("Error", "Please select a supplier")
            return

        if not po_items:
            messagebox.showerror("Error", "Please add at least one product")
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

            # Link to inventory (will be processed when received)
            # data_linker.process_purchase_order(po_items, supplier_id)

            messagebox.showinfo("Success", f"Purchase Order created:\n{po_number}")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to create purchase order")
            messagebox.showerror("Error", f"Failed to create PO: {str(e)}")

    # Buttons - right aligned, never hidden
    cancel_btn = make_button(button_frame, "Cancel", command=dlg.destroy, kind="secondary", width=BTN_WIDTH['dialog'])
    cancel_btn.pack(side="right", padx=10)

    create_btn = make_button(button_frame, "💾 Create PO", command=save_po, kind="success", width=BTN_WIDTH['action'])
    create_btn.pack(side="right", padx=10)

    # Auto-update total when items change
    update_total()


def open_po_details(parent, po_id, current_user=None):
    """View purchase order details."""
    from app_core import PremiumPopup
    dlg = PremiumPopup(parent, "Purchase Order Details", width=900, height=750, resizable=True)
    content = dlg.get_content_frame()

    # Get PO through service
    pos = svc.purchase_order.get_all_orders()
    po = next((p for p in pos if p['id'] == po_id), None)

    if not po:
        styled_label(content, "Purchase Order not found", font=FONT_BOLD, foreground=COLOR_DANGER).pack(anchor=tk.W)
        make_button(content, "Close", command=dlg.destroy, kind="secondary").pack(anchor=tk.E, pady=(15, 0))
        return

    # Get supplier info
    suppliers = svc.supplier.get_all_suppliers()
    supplier = next((s for s in suppliers if s['id'] == po['supplier_id']), None)

    # Header
    header_frame = ttk.Frame(content)
    header_frame.pack(fill=tk.X)

    styled_label(header_frame, f"Purchase Order: {po['po_number']}", font=FONT_BOLD).pack(anchor=tk.W)
    status_color = COLOR_SUCCESS if po['status'] == 'received' else COLOR_PRIMARY
    styled_label(header_frame, f"Status: {po['status'].title()}", foreground=status_color).pack(anchor=tk.W, pady=(5, 15))

    # PO Info
    info_frame = make_card(content, padding=15)
    info_frame.pack(fill=tk.X)

    info = [
        ("Supplier:", supplier['name'] if supplier else 'N/A'),
        ("Contact:", supplier.get('contact_person', 'N/A') if supplier else 'N/A'),
        ("Phone:", supplier.get('phone', 'N/A') if supplier else 'N/A'),
        ("Order Date:", po['order_date'][:10] if po['order_date'] else 'N/A'),
        ("Expected Date:", po['expected_date'][:10] if po['expected_date'] else 'N/A'),
        ("Created By:", po.get('created_by_name', 'System') or 'System'),
    ]

    for i, (label, value) in enumerate(info):
        row = i // 3
        col = (i % 3) * 2
        styled_label(info_frame, f"{label}", font=("Segoe UI", 10, "bold")).grid(row=row, column=col, sticky=tk.W, padx=5, pady=3)
        styled_label(info_frame, f"{value}").grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=3)

    # Items
    styled_label(content, "Order Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(15, 5))

    items_frame = make_card(content, padding=10)
    items_frame.pack(fill=tk.BOTH, expand=True)

    columns = ("product", "ordered", "received", "unit_price", "total")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

    for col in columns:
        items_tree.heading(col, text=col.replace('_', ' ').title())
        items_tree.column(col, width=100)

    items_tree.pack(fill=tk.BOTH, expand=True)

    # Get PO items through service
    po_items = svc.purchase_order.get_order_items(po_id)

    total = 0
    for item in po_items:
        # Get product info
        product = svc.inventory.get_product_by_id(item['product_id'])
        product_name = product.model if product else 'Unknown'

        items_tree.insert("", "end", values=(
            product_name,
            item['quantity_ordered'],
            item['quantity_received'] or 0,
            f"Rs. {item['unit_price']:,.2f}",
            f"Rs. {item['total_price']:,.2f}"
        ))
        total += item['total_price']

    # Total
    styled_label(content, f"Total Amount: Rs. {total:,.2f}", font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARY).pack(anchor=tk.E, pady=(10, 0))

    # Notes
    if po.get('notes'):
        styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
        styled_label(content, po['notes'], justify=tk.LEFT).pack(anchor=tk.W)

    def close():
        dlg.destroy()

    dlg.add_button_bar([{"text": "Close", "command": close, "style": "TButton"}])


def open_grn_dialog(parent, po_id, current_user=None):
    """Goods Receipt Note - Receive products from PO."""
    from app_core import PremiumPopup
    dlg = PremiumPopup(parent, "Receive Goods (GRN)", width=850, height=750, resizable=True)
    content = dlg.get_content_frame()

    # Get PO info through service
    pos = svc.purchase_order.get_all_orders()
    po = next((p for p in pos if p['id'] == po_id), None)

    if not po:
        styled_label(content, "Purchase Order not found", font=FONT_BOLD, foreground=COLOR_DANGER).pack(anchor=tk.W)
        make_button(content, "Close", command=dlg.destroy, kind="secondary").pack(anchor=tk.E, pady=(15, 0))
        return

    styled_label(content, f"Receive Goods for {po['po_number']}", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    if po['status'] == 'received':
        styled_label(content, "⚠️ This PO has already been fully received", foreground=COLOR_WARNING).pack(anchor=tk.W, pady=(0, 10))

    # Items to receive
    styled_label(content, "Items to Receive:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))

    items_frame = make_card(content, padding=10)
    items_frame.pack(fill=tk.BOTH, expand=True)

    columns = ("product", "ordered", "received", "pending", "receive_qty")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

    for col in columns:
        items_tree.heading(col, text=col.replace('_', ' ').title())
        items_tree.column(col, width=100 if col != "product" else 200)

    items_tree.pack(fill=tk.BOTH, expand=True)

    # Get PO items through service
    po_items_data = svc.purchase_order.get_order_items(po_id)

    items_data = []
    for item in po_items_data:
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

        items_tree.insert("", "end", values=(
            product_name,
            item['quantity_ordered'],
            item['quantity_received'] or 0,
            pending,
            pending  # Default receive qty = pending
        ))

    # Receive button
    def receive_goods():
        try:
            # Receive all pending items through service
            svc.purchase_order.receive_order(po_id, current_user)

            messagebox.showinfo("Success", "Goods received successfully")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to receive goods")
            messagebox.showerror("Error", f"Failed to receive goods: {e}")

    dlg.add_button_bar([
        {"text": "Receive All Pending", "command": receive_goods, "style": "Accent.TButton"},
        {"text": "Cancel", "command": dlg.destroy, "style": "TButton"}
    ])
