"""
Sales Orders Module
====================
Complete sales order management system.
Create orders, track delivery, manage customers, and process payments.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta

from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED
)
from services import svc


def create_sales_orders_tab(parent, current_user=None):
    """
    Creates the sales orders management tab.
    """
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "💼 Sales Orders", font=FONT_BOLD).pack(side=tk.LEFT)

    # New Order button
    def open_new_order():
        open_create_order_dialog(window, current_user=current_user)

    make_button(header_frame, "➕ New Sales Order", command=open_new_order, kind="success").pack(side=tk.RIGHT)

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

    confirmed_lbl = create_summary_card(summary_frame, "Confirmed", 0, 0)
    processing_lbl = create_summary_card(summary_frame, "Processing", 0, 1)
    shipped_lbl = create_summary_card(summary_frame, "Shipped", 0, 2)
    delivered_lbl = create_summary_card(summary_frame, "Delivered", 0, 3)
    total_lbl = create_summary_card(summary_frame, "Total Orders", 0, 4)

    window.summary_labels = {
        'confirmed': confirmed_lbl,
        'processing': processing_lbl,
        'shipped': shipped_lbl,
        'delivered': delivered_lbl,
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
        values=["all", "confirmed", "processing", "shipped", "delivered", "cancelled"],
        state="readonly",
        width=15
    )
    status_combo.pack(side=tk.LEFT, padx=5)

    def apply_filter():
        refresh_orders()

    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), refresh_orders()), kind="secondary").pack(side=tk.LEFT)

    # Orders table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("order_number", "customer", "order_date", "delivery_date", "status", "total_amount", "payment")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "order_number": ("Order #", 120),
        "customer": ("Customer", 200),
        "order_date": ("Order Date", 100),
        "delivery_date": ("Delivery", 100),
        "status": ("Status", 100),
        "total_amount": ("Total", 120),
        "payment": ("Payment", 100)
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
            messagebox.showinfo("Select", "Please select an order")
            return

        order_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if order_id:
            open_order_details(window, order_id=int(order_id), current_user=current_user)

    def on_update_status():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an order")
            return

        order_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if order_id:
            open_update_status_dialog(window, order_id=int(order_id))

    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "🔄 Update Status", command=on_update_status, kind="warning").pack(side=tk.LEFT, padx=5)

    # Store state
    window.status_var = status_var
    window.tree = tree

    def refresh_from_db():
        """Reload all data from the database through services and refresh the UI."""
        tree.delete(*tree.get_children())

        status_filter = status_var.get()
        status_arg = None if status_filter == 'all' else status_filter
        orders = svc.sales.get_all_orders(status=status_arg)

        # Update summary
        status_counts = {'confirmed': 0, 'processing': 0, 'shipped': 0, 'delivered': 0, 'total': len(orders)}
        for order in orders:
            if order['status'] in status_counts:
                status_counts[order['status']] += 1

        window.summary_labels['confirmed'].config(text=str(status_counts['confirmed']))
        window.summary_labels['processing'].config(text=str(status_counts['processing']))
        window.summary_labels['shipped'].config(text=str(status_counts['shipped']))
        window.summary_labels['delivered'].config(text=str(status_counts['delivered']))
        window.summary_labels['total'].config(text=str(status_counts['total']))

        # Populate table
        for order in orders:
            payment_status = order['payment_status'].replace('_', ' ').title()
            payment_color = COLOR_SUCCESS if order['payment_status'] == 'paid' else COLOR_WARNING

            tree.insert("", "end", values=(
                order['order_number'],
                order['customer_name'] or 'Walk-in Customer',
                order['order_date'][:10] if order['order_date'] else 'N/A',
                order['delivery_date'][:10] if order['delivery_date'] else 'N/A',
                order['status'].replace('_', ' ').title(),
                f"Rs. {order['total_amount']:,.2f}" if order['total_amount'] else 'Rs. 0.00',
                payment_status
            ), tags=(str(order['id']),))

    def refresh_orders():
        """Refresh sales orders list."""
        refresh_from_db()

    window.refresh_orders = refresh_orders
    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_create_order_dialog(parent, current_user=None):
    """Dialog to create a new sales order."""
    dlg = tk.Toplevel(parent)
    dlg.title("Create Sales Order")
    dlg.geometry("950x800")
    dlg.resizable(True, True)
    dlg.minsize(750, 650)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Heading
    styled_label(content, "New Sales Order", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    # Customer info frame
    customer_frame = ttk.LabelFrame(content, text="Customer Information", padding=15)
    customer_frame.pack(fill=tk.X, pady=(0, 15))
    customer_frame.grid_columnconfigure(0, weight=0, minsize=150)
    customer_frame.grid_columnconfigure(1, weight=1)
    customer_frame.grid_columnconfigure(2, weight=0, minsize=150)
    customer_frame.grid_columnconfigure(3, weight=1)

    # Customer fields
    styled_label(customer_frame, "Customer Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    customer_name_var = tk.StringVar()
    customer_name_entry = ttk.Entry(customer_frame, textvariable=customer_name_var, width=25)
    customer_name_entry.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)

    styled_label(customer_frame, "Phone:").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    customer_phone_var = tk.StringVar()
    customer_phone_entry = ttk.Entry(customer_frame, textvariable=customer_phone_var, width=20)
    customer_phone_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

    styled_label(customer_frame, "Email:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
    customer_email_var = tk.StringVar()
    customer_email_entry = ttk.Entry(customer_frame, textvariable=customer_email_var, width=25)
    customer_email_entry.grid(row=1, column=2, sticky=tk.EW, padx=5, pady=5)

    styled_label(customer_frame, "Delivery Date:").grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
    delivery_var = tk.StringVar()
    delivery_entry = ttk.Entry(customer_frame, textvariable=delivery_var, width=15)
    delivery_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

    # Set default delivery date (3 days from now)
    default_delivery = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    delivery_var.set(default_delivery)

    # Products list
    styled_label(content, "Add Products:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))

    products_frame = make_card(content, padding=10)
    products_frame.pack(fill=tk.BOTH, expand=True)

    # Product selection row
    select_frame = ttk.Frame(products_frame)
    select_frame.pack(fill=tk.X, pady=(0, 10))

    styled_label(select_frame, "Product:").pack(side=tk.LEFT, padx=5)

    product_var = tk.StringVar()
    product_combo = ttk.Combobox(select_frame, textvariable=product_var, state="readonly", width=35)
    product_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    # Load products with stock via service
    products = svc.inventory.get_all_products(active_only=True)
    products = [p for p in products if p.get('stock', 0) > 0]
    products.sort(key=lambda p: p.get('model', ''))

    product_data = [(p['id'], f"{p['model']} (Stock: {p['stock']}, Price: Rs. {p['selling_price']})") for p in products]
    product_combo['values'] = [p[1] for p in product_data]

    styled_label(select_frame, "Qty:").pack(side=tk.LEFT, padx=(15, 5))

    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(select_frame, textvariable=qty_var, width=8)
    qty_entry.pack(side=tk.LEFT, padx=5)

    # Items list
    styled_label(content, "Order Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))

    items_frame = ttk.Frame(products_frame)
    items_frame.pack(fill=tk.BOTH, expand=True)

    columns = ("product", "quantity", "unit_price", "total", "actions")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)

    for col in columns:
        items_tree.heading(col, text=col.title())
        items_tree.column(col, width=120 if col != "product" else 300)

    items_tree.pack(fill=tk.BOTH, expand=True)

    # Order items storage
    order_items = []

    def add_item():
        product_sel = product_var.get()
        qty = qty_var.get()

        if not product_sel:
            messagebox.showerror("Error", "Please select a product")
            return

        try:
            qty_int = int(qty)
            if qty_int <= 0:
                raise ValueError("must be positive")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid quantity: {e}")
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
            if not messagebox.askyesno("Low Stock", f"Only {available_stock} in stock. Continue anyway?"):
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
        items_tree.insert("", "end", values=(
            product_name,
            qty_int,
            f"Rs. {unit_price:,.2f}",
            f"Rs. {total:,.2f}",
            "🗑️ Remove"
        ))

        # Clear selection
        product_var.set("")
        qty_var.set("1")

    def on_item_click(event):
        sel = items_tree.selection()
        if not sel:
            return

        item = items_tree.item(sel[0])
        if item['values'][4] == "🗑️ Remove":
            index = items_tree.index(sel[0])
            if 0 <= index < len(order_items):
                order_items.pop(index)
                items_tree.delete(sel[0])

    items_tree.bind("<Button-1>", on_item_click)

    # Add button
    make_button(select_frame, "➕ Add", command=add_item, kind="primary").pack(side=tk.LEFT, padx=10)

    # Payment info
    payment_frame = ttk.LabelFrame(content, text="Payment Information", padding=15)
    payment_frame.pack(fill=tk.X, pady=(10, 0))

    styled_label(payment_frame, "Payment Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    payment_var = tk.StringVar(value="pending")
    payment_combo = ttk.Combobox(payment_frame, textvariable=payment_var, values=["pending", "partial", "paid"], state="readonly", width=20)
    payment_combo.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

    styled_label(payment_frame, "Paid Amount:").grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    paid_var = tk.StringVar(value="0")
    paid_entry = ttk.Entry(payment_frame, textvariable=paid_var, width=15)
    paid_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

    # Notes
    styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    notes_text = tk.Text(content, height=3)
    notes_text.pack(fill=tk.X, pady=(0, 10))

    # Total label
    total_var = tk.StringVar(value="Total: Rs. 0.00")
    total_label = styled_label(content, textvariable=total_var, font=("Segoe UI", 14, "bold"), foreground=COLOR_PRIMARY)
    total_label.pack(anchor=tk.E, pady=(5, 10))

    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(10, 0))

    def save_order():
        customer_name = customer_name_var.get().strip()
        customer_phone = customer_phone_var.get().strip()
        customer_email = customer_email_var.get().strip()
        delivery_date = delivery_var.get().strip()
        payment_status = payment_var.get()
        paid_amount = paid_var.get()
        notes = notes_text.get("1.0", tk.END).strip()

        if not order_items:
            messagebox.showerror("Error", "Please add at least one product")
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

            messagebox.showinfo("Success", f"Sales Order created: {order_number}")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()
            elif hasattr(parent, 'refresh_orders'):
                parent.refresh_orders()

        except Exception as e:
            logging.exception("Failed to create sales order")
            messagebox.showerror("Error", f"Failed to create order: {e}")

    make_button(btn_frame, "💾 Create Order", command=save_order, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_order_details(parent, order_id, current_user=None):
    """View sales order details."""
    dlg = tk.Toplevel(parent)
    dlg.title("Sales Order Details")
    dlg.geometry("900x750")
    dlg.resizable(True, True)
    dlg.minsize(700, 600)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Get all orders and find the matching one via service
    all_orders = svc.sales.get_all_orders()
    order = None
    for o in all_orders:
        if o['id'] == order_id:
            order = o
            break

    if not order:
        messagebox.showerror("Error", "Order not found")
        dlg.destroy()
        return

    # Header
    header_frame = ttk.Frame(content)
    header_frame.pack(fill=tk.X)

    styled_label(header_frame, f"Sales Order: {order['order_number']}", font=FONT_BOLD).pack(anchor=tk.W)
    status_color = COLOR_SUCCESS if order['status'] == 'delivered' else COLOR_PRIMARY
    styled_label(header_frame, f"Status: {order['status'].title()}", foreground=status_color).pack(anchor=tk.W, pady=(5, 15))

    # Order Info
    info_frame = make_card(content, padding=15)
    info_frame.pack(fill=tk.X)

    info = [
        ("Customer:", order['customer_name'] or 'Walk-in'),
        ("Phone:", order['customer_phone'] or 'N/A'),
        ("Email:", order['customer_email'] or 'N/A'),
        ("Order Date:", order['order_date'][:10] if order['order_date'] else 'N/A'),
        ("Delivery Date:", order['delivery_date'][:10] if order['delivery_date'] else 'N/A'),
        ("Payment:", f"{order['payment_status'].title()} (Rs. {order['paid_amount'] or 0:,.2f})"),
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

    columns = ("product", "quantity", "unit_price", "total")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

    for col in columns:
        items_tree.heading(col, text=col.replace('_', ' ').title())
        items_tree.column(col, width=120)

    items_tree.pack(fill=tk.BOTH, expand=True)

    # Get order items via service
    order_items = svc.sales.get_order_items(order_id)

    total = 0
    for row in order_items:
        # Resolve product model from product_id
        product = svc.inventory.get_product_by_id(row.get('product_id'))
        model = product['model'] if product else 'Unknown'

        items_tree.insert("", "end", values=(
            model,
            row['quantity'],
            f"Rs. {row['unit_price']:,.2f}",
            f"Rs. {row['total_price']:,.2f}"
        ))
        total += row['total_price']

    # Total
    styled_label(content, f"Total Amount: Rs. {total:,.2f}", font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARY).pack(anchor=tk.E, pady=(10, 0))

    # Notes
    if order['notes']:
        styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
        styled_label(content, order['notes'], justify=tk.LEFT).pack(anchor=tk.W)

    # Close button
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    make_button(btn_frame, "Close", command=dlg.destroy, kind="secondary").pack(side=tk.RIGHT)


def open_update_status_dialog(parent, order_id):
    """Update order status."""
    dlg = tk.Toplevel(parent)
    dlg.title("Update Order Status")
    dlg.geometry("600x500")
    dlg.resizable(True, True)
    dlg.minsize(450, 400)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    styled_label(content, "Update Order Status", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)

    # Status
    styled_label(form_frame, "Status:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    status_var = tk.StringVar()
    status_combo = ttk.Combobox(form_frame, textvariable=status_var, values=[
        "confirmed", "processing", "shipped", "delivered", "cancelled"
    ], state="readonly", width=25)
    status_combo.grid(row=1, column=0, sticky=tk.EW, pady=5)

    # Payment
    styled_label(form_frame, "Payment Status:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    payment_var = tk.StringVar()
    payment_combo = ttk.Combobox(form_frame, textvariable=payment_var, values=[
        "pending", "partial", "paid"
    ], state="readonly", width=25)
    payment_combo.grid(row=3, column=0, sticky=tk.EW, pady=5)

    def save_status():
        status = status_var.get()
        payment = payment_var.get()

        if not status:
            messagebox.showerror("Error", "Please select a status")
            return

        try:
            svc.sales.update_order_status(
                order_id, status=status, payment_status=payment, username=current_user
            )

            messagebox.showinfo("Success", "Order status updated")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()
            elif hasattr(parent, 'refresh_orders'):
                parent.refresh_orders()

        except Exception as e:
            logging.exception("Failed to update order status")
            messagebox.showerror("Error", f"Failed to update status: {e}")

    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    make_button(btn_frame, "💾 Update", command=save_status, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)
