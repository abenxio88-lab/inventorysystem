"""
RMA/Returns Management Module
==============================
Return Merchandise Authorization and returns processing.
Phase 5 - Complete Implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime

from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED
)
from utils import get_data_dir

from services import svc


def create_returns_tab(parent, current_user=None):
    """
    Creates the returns/RMA management tab.
    """
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "🔄 Returns & RMA", font=FONT_HEADING).pack(side=tk.LEFT)

    # New Return button
    def open_new_return():
        open_create_return_dialog(window, current_user=current_user)

    make_button(header_frame, "➕ New Return", command=open_new_return, kind="warning").pack(side=tk.RIGHT)

    # Summary cards
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))
    summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def create_summary_card(parent, title, value, col):
        card = make_card(parent, padding=12)
        card.grid(row=0, column=col, padx=8, sticky="nsew")

        styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d").pack(anchor="w")
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        value_label.pack(anchor="w", pady=(3, 0))

        return value_label

    pending_lbl = create_summary_card(summary_frame, "Pending", 0, 0)
    approved_lbl = create_summary_card(summary_frame, "Approved", 0, 1)
    refunded_lbl = create_summary_card(summary_frame, "Refunded", 0, 2)
    total_lbl = create_summary_card(summary_frame, "Total Returns", 0, 3)

    window.summary_labels = {
        'pending': pending_lbl,
        'approved': approved_lbl,
        'refunded': refunded_lbl,
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
        values=["all", "pending", "approved", "refunded", "rejected"],
        state="readonly",
        width=15
    )
    status_combo.pack(side=tk.LEFT, padx=5)

    def apply_filter():
        refresh_returns()

    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), refresh_returns()), kind="secondary").pack(side=tk.LEFT)

    # Returns table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("return_number", "customer", "date", "reason", "amount", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "return_number": ("Return #", 120),
        "customer": ("Customer", 200),
        "date": ("Date", 100),
        "reason": ("Reason", 250),
        "amount": ("Refund Amount", 120),
        "status": ("Status", 100)
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
            messagebox.showinfo("Select", "Please select a return")
            return

        return_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if return_id:
            open_return_details(window, return_id=int(return_id), current_user=current_user)

    def on_approve():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a return")
            return

        return_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if return_id:
            approve_return(return_id, refresh_callback=refresh_returns)

    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "✓ Approve Return", command=on_approve, kind="success").pack(side=tk.LEFT, padx=5)

    # Store state
    window.status_var = status_var
    window.tree = tree

    def refresh_returns():
        """Refresh returns list from database through services."""
        tree.delete(*tree.get_children())

        status_filter = status_var.get()
        status_arg = None if status_filter == 'all' else status_filter
        returns = svc.return_svc.get_all_returns(status=status_arg)

        # Update summary
        status_counts = {'pending': 0, 'approved': 0, 'refunded': 0, 'total': len(returns)}
        for ret in returns:
            if ret['status'] in status_counts:
                status_counts[ret['status']] += 1

        window.summary_labels['pending'].config(text=str(status_counts['pending']))
        window.summary_labels['approved'].config(text=str(status_counts['approved']))
        window.summary_labels['refunded'].config(text=str(status_counts['refunded']))
        window.summary_labels['total'].config(text=str(status_counts['total']))

        # Populate table
        for ret in returns:
            status_text = ret['status'].replace('_', ' ').title()
            tags = (str(ret['return_id']),)

            tree.insert("", "end", values=(
                ret['return_number'],
                ret['customer_name'],
                ret['return_date'][:10] if ret['return_date'] else 'N/A',
                ret['reason'][:50] + ('...' if len(ret['reason'] or '') > 50 else ''),
                f"Rs. {ret['total_refund']:,.2f}" if ret['total_refund'] else "Rs. 0.00",
                status_text
            ), tags=tags)

    window.refresh_returns = refresh_returns
    refresh_returns()

    return window


def open_create_return_dialog(parent, current_user=None):
    """Dialog to create a new return."""
    dlg = tk.Toplevel(parent)
    dlg.title("Create Return/RMA")
    dlg.geometry("900x800")
    dlg.resizable(True, True)
    dlg.minsize(750, 650)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Heading
    styled_label(content, "🔄 New Return/RMA", font=FONT_HEADING).pack(anchor=tk.W, pady=(0, 15))

    # Customer info
    customer_frame = ttk.LabelFrame(content, text="Customer Information", padding=15)
    customer_frame.pack(fill=tk.X, pady=(0, 15))
    customer_frame.grid_columnconfigure(0, weight=0, minsize=150)
    customer_frame.grid_columnconfigure(1, weight=1)

    styled_label(customer_frame, "Customer Name *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    customer_name_var = tk.StringVar()
    customer_name_entry = ttk.Entry(customer_frame, textvariable=customer_name_var, width=30)
    customer_name_entry.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)

    styled_label(customer_frame, "Email:", font=FONT_BOLD).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    customer_email_var = tk.StringVar()
    customer_email_entry = ttk.Entry(customer_frame, textvariable=customer_email_var, width=25)
    customer_email_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

    styled_label(customer_frame, "Phone:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    customer_phone_var = tk.StringVar()
    customer_phone_entry = ttk.Entry(customer_frame, textvariable=customer_phone_var, width=30)
    customer_phone_entry.grid(row=3, column=0, sticky=tk.EW, padx=5, pady=5)

    # Return details
    details_frame = ttk.LabelFrame(content, text="Return Details", padding=15)
    details_frame.pack(fill=tk.X, pady=(0, 15))
    details_frame.grid_columnconfigure(0, weight=0, minsize=150)
    details_frame.grid_columnconfigure(1, weight=1)

    # Return number (auto-generated)
    return_number = f"RMA-{datetime.now().strftime('%Y%m%d%H%M')}"
    styled_label(details_frame, "Return Number:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    return_number_var = tk.StringVar(value=return_number)
    return_number_entry = ttk.Entry(details_frame, textvariable=return_number_var, width=20, state='readonly')
    return_number_entry.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

    # Return date
    styled_label(details_frame, "Return Date *:", font=FONT_BOLD).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    return_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    return_date_entry = ttk.Entry(details_frame, textvariable=return_date_var, width=15)
    return_date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

    # Reason
    styled_label(details_frame, "Reason *:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    reason_var = tk.StringVar()
    reason_combo = ttk.Combobox(details_frame, textvariable=reason_var, values=[
        "Defective Product", "Wrong Item", "Damaged in Shipping",
        "Not as Described", "Changed Mind", "Other"
    ], state="readonly", width=40)
    reason_combo.grid(row=3, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)

    # Items section
    styled_label(content, "Return Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))

    items_frame = make_card(content, padding=10)
    items_frame.pack(fill=tk.BOTH, expand=True)

    # Add item row
    add_frame = ttk.Frame(items_frame)
    add_frame.pack(fill=tk.X, pady=(0, 10))

    styled_label(add_frame, "Product:").pack(side=tk.LEFT, padx=5)

    product_var = tk.StringVar()
    product_combo = ttk.Combobox(add_frame, textvariable=product_var, state="readonly", width=35)
    product_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    # Load products via service
    products = svc.inventory.get_all_products(active_only=True)

    product_data = [(p['id'], f"{p['model']} (Rs. {p['selling_price']})") for p in products]
    product_combo['values'] = [p[1] for p in product_data]

    styled_label(add_frame, "Qty:").pack(side=tk.LEFT, padx=(15, 5))

    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(add_frame, textvariable=qty_var, width=8)
    qty_entry.pack(side=tk.LEFT, padx=5)

    # Add button
    return_items = []

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
        items_tree.insert("", "end", values=(
            product_name,
            qty_int,
            f"Rs. {unit_price:,.2f}",
            f"Rs. {line_total:,.2f}",
            "🗑️ Remove"
        ))

        product_var.set("")
        qty_var.set("1")

    def on_item_click(event):
        sel = items_tree.selection()
        if not sel:
            return

        item = items_tree.item(sel[0])
        if item['values'][4] == "🗑️ Remove":
            index = items_tree.index(sel[0])
            if 0 <= index < len(return_items):
                return_items.pop(index)
                items_tree.delete(sel[0])
                update_total()

    make_button(add_frame, "➕ Add Item", command=add_item, kind="primary").pack(side=tk.LEFT, padx=10)

    # Items tree
    items_frame2 = ttk.Frame(items_frame)
    items_frame2.pack(fill=tk.BOTH, expand=True)

    columns = ("product", "quantity", "unit_price", "total", "actions")
    items_tree = ttk.Treeview(items_frame2, columns=columns, show="headings", height=8)

    for col in columns:
        items_tree.heading(col, text=col.replace('_', ' ').title())
        items_tree.column(col, width=100 if col != "product" else 200)

    items_tree.pack(fill=tk.BOTH, expand=True)
    items_tree.bind("<Button-1>", on_item_click)

    # Total
    total_var = tk.StringVar(value="Total Refund: Rs. 0.00")
    total_label = styled_label(items_frame, textvariable=total_var, font=("Segoe UI", 12, "bold"), foreground=COLOR_DANGER)
    total_label.pack(anchor=tk.E, pady=10)

    def update_total():
        total = sum(item['line_total'] for item in return_items)
        total_var.set(f"Total Refund: Rs. {total:,.2f}")

    # Notes
    styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    notes_text = tk.Text(content, height=3)
    notes_text.pack(fill=tk.X, pady=(0, 10))

    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(10, 0))

    def save_return():
        customer_name = customer_name_var.get().strip()
        customer_email = customer_email_var.get().strip()
        customer_phone = customer_phone_var.get().strip()
        return_date = return_date_var.get().strip()
        reason = reason_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()

        if not customer_name:
            messagebox.showerror("Error", "Customer name required")
            return

        if not reason:
            messagebox.showerror("Error", "Please select a reason")
            return

        if not return_items:
            messagebox.showerror("Error", "Please add at least one item")
            return

        total_refund = sum(item['line_total'] for item in return_items)

        try:
            return_data = {
                'return_number': return_number_var.get(),
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

            messagebox.showinfo("Success", f"Return created: {return_number_var.get()}")
            dlg.destroy()

            if hasattr(parent, 'refresh_returns'):
                parent.refresh_returns()

        except Exception as e:
            logging.exception("Failed to create return")
            messagebox.showerror("Error", f"Failed to create return: {e}")

    make_button(btn_frame, "💾 Create Return", command=save_return, kind="warning").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_return_details(parent, return_id, current_user=None):
    """View return details."""
    dlg = tk.Toplevel(parent)
    dlg.title("Return Details")
    dlg.geometry("850x750")
    dlg.resizable(True, True)
    dlg.minsize(700, 600)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    returns = svc.return_svc.get_all_returns()
    ret = next((r for r in returns if r['return_id'] == return_id), None)

    if not ret:
        styled_label(content, "Return not found", foreground=COLOR_DANGER).pack()
        ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=10)
        return

    # Header
    styled_label(content, f"Return: {ret['return_number']}", font=FONT_HEADING).pack(anchor=tk.W)
    styled_label(content, f"Status: {ret['status'].title()}", foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(5, 15))

    # Info
    info_frame = make_card(content, padding=15)
    info_frame.pack(fill=tk.X)

    info = [
        ("Customer:", ret['customer_name']),
        ("Email:", ret['customer_email'] or 'N/A'),
        ("Phone:", ret['customer_phone'] or 'N/A'),
        ("Return Date:", ret['return_date'][:10] if ret['return_date'] else 'N/A'),
        ("Reason:", ret['reason']),
        ("Refund Amount:", f"Rs. {ret['total_refund']:,.2f}"),
    ]

    for label, value in info:
        frame = ttk.Frame(info_frame)
        frame.pack(fill=tk.X, pady=3)
        styled_label(frame, f"{label}", font=("Segoe UI", 10, "bold"), width=15).pack(side=tk.LEFT)
        styled_label(frame, f"{value}").pack(side=tk.LEFT)

    # Items
    styled_label(content, "Return Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(15, 5))

    items_frame = make_card(content, padding=10)
    items_frame.pack(fill=tk.BOTH, expand=True)

    columns = ("product", "quantity", "unit_price", "total")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")

    for col in columns:
        items_tree.heading(col, text=col.replace('_', ' ').title())
        items_tree.column(col, width=120)

    items_tree.pack(fill=tk.BOTH, expand=True)

    # Load return items through service
    return_items = svc.return_svc.get_return_items(return_id)
    for row in return_items:
        items_tree.insert("", "end", values=(
            row['product_name'],
            row['quantity'],
            f"Rs. {row['unit_price']:,.2f}",
            f"Rs. {row['line_total']:,.2f}"
        ))

    # Close button
    ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=10)


def approve_return(return_id, refresh_callback=None):
    """Approve a return."""
    if messagebox.askyesno("Confirm", "Approve this return and process refund?"):
        try:
            svc.return_svc.approve_return(return_id, username="system")
            messagebox.showinfo("Success", "Return approved")

            if refresh_callback:
                refresh_callback()

        except Exception as e:
            logging.exception("Failed to approve return")
            messagebox.showerror("Error", f"Failed to approve return: {e}")
