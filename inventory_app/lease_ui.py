"""
Lease & Rental Management Module
=================================
Complete lease/rental system with tracking, payments, and returns.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta

from services import svc
from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING


def create_lease_management_tab(parent, current_user=None):
    """
    Creates the lease management tab.
    """
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "🎯 Lease & Rental Management", font=FONT_BOLD).pack(side=tk.LEFT)

    # New Lease button
    def open_new_lease():
        open_create_lease_dialog(window, current_user=current_user)

    make_button(header_frame, "➕ New Lease", command=open_new_lease, kind="success").pack(side=tk.RIGHT)

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

    active_lbl = create_summary_card(summary_frame, "Active Leases", 0, 0)
    expiring_lbl = create_summary_card(summary_frame, "Expiring Soon", 0, 1)
    overdue_lbl = create_summary_card(summary_frame, "Overdue Payments", 0, 2)
    pending_lbl = create_summary_card(summary_frame, "Pending Return", 0, 3)
    revenue_lbl = create_summary_card(summary_frame, "Monthly Revenue", "Rs. 0", 4)

    window.summary_labels = {
        'active': active_lbl,
        'expiring': expiring_lbl,
        'overdue': overdue_lbl,
        'pending': pending_lbl,
        'revenue': revenue_lbl
    }

    # Filter toolbar
    toolbar_frame = ttk.Frame(window)
    toolbar_frame.pack(fill="x", pady=(0, 10))

    styled_label(toolbar_frame, "Status:").pack(side=tk.LEFT, padx=(0, 10))

    status_var = tk.StringVar(value="all")
    status_combo = ttk.Combobox(
        toolbar_frame,
        textvariable=status_var,
        values=["all", "active", "completed", "defaulted", "expired"],
        state="readonly",
        width=15
    )
    status_combo.pack(side=tk.LEFT, padx=5)

    def apply_filter():
        refresh_from_db()

    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), refresh_from_db()), kind="secondary").pack(side=tk.LEFT)

    # Leases table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("lease_id", "customer", "product", "start_date", "end_date", "monthly_amount", "status", "last_payment")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "lease_id": ("Lease #", 80),
        "customer": ("Customer", 150),
        "product": ("Product", 200),
        "start_date": ("Start Date", 100),
        "end_date": ("End Date", 100),
        "monthly_amount": ("Monthly", 100),
        "status": ("Status", 100),
        "last_payment": ("Last Payment", 100)
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
            messagebox.showinfo("Select", "Please select a lease")
            return

        lease_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if lease_id:
            open_lease_details(window, lease_id=int(lease_id), current_user=current_user)

    def on_record_payment():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a lease")
            return

        lease_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if lease_id:
            open_record_payment_dialog(window, lease_id=int(lease_id), current_user=current_user)

    def on_return_item():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a lease")
            return

        lease_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None

        if lease_id:
            open_return_item_dialog(window, lease_id=int(lease_id))

    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "💰 Record Payment", command=on_record_payment, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "📦 Return Item", command=on_return_item, kind="warning").pack(side=tk.LEFT, padx=5)

    # Store state
    window.status_var = status_var
    window.tree = tree

    def refresh_from_db():
        """Refresh leases list from database through services."""
        tree.delete(*tree.get_children())

        status_filter = status_var.get() if status_var.get() != "all" else None
        today = datetime.now().strftime('%Y-%m-%d')

        # Fetch leases through service
        leases = svc.lease.get_all_leases(status=status_filter)

        # Fetch lease payments for summary calculations
        all_payments = svc.stock_transfer.get_lease_payments()

        # Build payment aggregates per lease
        payment_totals = {}
        for p in all_payments:
            lid = p['lease_id']
            if lid not in payment_totals:
                payment_totals[lid] = {'total_paid': 0, 'last_payment_date': None}
            payment_totals[lid]['total_paid'] += p['amount_paid'] or 0
            if p['payment_date']:
                if payment_totals[lid]['last_payment_date'] is None or p['payment_date'] > payment_totals[lid]['last_payment_date']:
                    payment_totals[lid]['last_payment_date'] = p['payment_date']

        # Update summary
        active_count = sum(1 for l in leases if l['status'] == 'active')
        expiring_count = sum(1 for l in leases if l['status'] == 'active' and l.get('end_date') and
                            datetime.strptime(l['end_date'], '%Y-%m-%d').date() <= (datetime.now() + timedelta(days=7)).date())
        overdue_count = sum(1 for l in leases if l['status'] == 'active' and l.get('last_payment_date') and
                           datetime.strptime(l['last_payment_date'], '%Y-%m-%d').date() < (datetime.now() - timedelta(days=7)).date())
        pending_count = sum(1 for l in leases if l['status'] == 'active' and l.get('end_date') and
                           datetime.strptime(l['end_date'], '%Y-%m-%d').date() <= datetime.now().date())

        # Calculate monthly revenue from payments
        monthly_revenue = sum(p['amount_paid'] or 0 for p in all_payments
                             if p['payment_date'] and p['payment_date'] >= (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))

        window.summary_labels['active'].config(text=str(active_count))
        window.summary_labels['expiring'].config(text=str(expiring_count))
        window.summary_labels['overdue'].config(text=str(overdue_count))
        window.summary_labels['pending'].config(text=str(pending_count))
        window.summary_labels['revenue'].config(text=f"Rs. {monthly_revenue:,.2f}")

        # Populate table
        for lease in leases:
            lease_id = lease.get('lease_id')
            payment_info = payment_totals.get(lease_id, {'total_paid': 0, 'last_payment_date': None})

            tree.insert("", "end", values=(
                lease_id,
                lease.get('customer_name', ''),
                lease.get('product_name', ''),
                lease.get('start_date', 'N/A')[:10] if lease.get('start_date') else 'N/A',
                lease.get('end_date', 'N/A')[:10] if lease.get('end_date') else 'N/A',
                f"Rs. {lease.get('monthly_amount', 0):,.2f}",
                lease.get('status', 'unknown').replace('_', ' ').title(),
                payment_info['last_payment_date'][:10] if payment_info['last_payment_date'] else 'Never'
            ), tags=(str(lease_id),))

    window.refresh_from_db = refresh_from_db
    refresh_from_db()

    return window


def open_create_lease_dialog(parent, current_user=None):
    """Dialog to create a new lease."""
    dlg = tk.Toplevel(parent)
    dlg.title("Create New Lease")
    dlg.geometry("950x900")
    dlg.resizable(True, True)
    dlg.minsize(750, 700)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Heading
    styled_label(content, "New Lease Agreement", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    # Form
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    form_frame.grid_columnconfigure(0, weight=0, minsize=150)
    form_frame.grid_columnconfigure(1, weight=1)

    # Customer
    styled_label(form_frame, "Customer Name *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    customer_var = tk.StringVar()
    customer_entry = ttk.Entry(form_frame, textvariable=customer_var, width=30)
    customer_entry.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)

    # Product
    styled_label(form_frame, "Product *:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    product_var = tk.StringVar()
    product_combo = ttk.Combobox(form_frame, textvariable=product_var, state="readonly", width=30)
    product_combo.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)

    # Load products through service
    products = svc.inventory.get_all_products(active_only=True)
    products = [p for p in products if p.get('stock', 0) > 0]

    product_data = [(p['id'], f"{p['model']} (Price: Rs. {p['selling_price']}, Stock: {p['stock']})") for p in products]
    product_combo['values'] = [p[1] for p in product_data]

    # Lease terms
    styled_label(form_frame, "Lease Duration (months) *:", font=FONT_BOLD).grid(row=4, column=0, sticky=tk.W, pady=5)
    duration_var = tk.StringVar(value="12")
    duration_entry = ttk.Entry(form_frame, textvariable=duration_var, width=15)
    duration_entry.grid(row=5, column=0, sticky=tk.W, pady=5)

    styled_label(form_frame, "Monthly Amount (Rs.) *:", font=FONT_BOLD).grid(row=4, column=1, sticky=tk.W, pady=5)
    monthly_var = tk.StringVar(value="0")
    monthly_entry = ttk.Entry(form_frame, textvariable=monthly_var, width=15)
    monthly_entry.grid(row=5, column=1, sticky=tk.W, pady=5)

    # Dates
    styled_label(form_frame, "Start Date *:", font=FONT_BOLD).grid(row=6, column=0, sticky=tk.W, pady=5)
    start_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    start_entry = ttk.Entry(form_frame, textvariable=start_var, width=15)
    start_entry.grid(row=7, column=0, sticky=tk.W, pady=5)

    styled_label(form_frame, "End Date:", font=FONT_BOLD).grid(row=6, column=1, sticky=tk.W, pady=5)
    end_var = tk.StringVar()
    end_entry = ttk.Entry(form_frame, textvariable=end_var, width=15)
    end_entry.grid(row=7, column=1, sticky=tk.W, pady=5)

    # Security deposit
    styled_label(form_frame, "Security Deposit (Rs.):", font=FONT_BOLD).grid(row=8, column=0, sticky=tk.W, pady=5)
    deposit_var = tk.StringVar(value="0")
    deposit_entry = ttk.Entry(form_frame, textvariable=deposit_var, width=15)
    deposit_entry.grid(row=9, column=0, sticky=tk.W, pady=5)

    # Notes
    styled_label(form_frame, "Notes:", font=FONT_BOLD).grid(row=10, column=0, sticky=tk.W, pady=5)
    notes_text = tk.Text(form_frame, height=3, width=40)
    notes_text.grid(row=11, column=0, columnspan=2, sticky=tk.EW, pady=5)

    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    def save_lease():
        customer = customer_var.get().strip()
        product_sel = product_var.get()
        duration = duration_var.get().strip()
        monthly = monthly_var.get().strip()
        start_date = start_var.get().strip()
        end_date = end_var.get().strip()
        deposit = deposit_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()

        if not customer:
            messagebox.showerror("Error", "Customer name required")
            return

        if not product_sel:
            messagebox.showerror("Error", "Please select a product")
            return

        try:
            duration_months = int(duration)
            monthly_amount = float(monthly)
            security_deposit = float(deposit) if deposit else 0

            if duration_months <= 0 or monthly_amount <= 0:
                raise ValueError("Duration and amount must be positive")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid duration or amount: {e}")
            return

        # Get product ID
        product_id = None
        product_name = None
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                break

        # Calculate end date if not provided
        if not end_date:
            end_dt = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=duration_months * 30)
            end_date = end_dt.strftime('%Y-%m-%d')

        # Generate lease ID
        lease_id = f"LEASE-{datetime.now().strftime('%Y%m%d%H%M')}"

        try:
            # Create lease through service
            lease_data = {
                'lease_id': lease_id,
                'customer_name': customer,
                'product_id': product_id,
                'product_name': product_name,
                'start_date': start_date,
                'end_date': end_date,
                'monthly_amount': monthly_amount,
                'duration_months': duration_months,
                'security_deposit': security_deposit,
                'status': 'active',
                'notes': notes,
                'created_by': current_user,
            }
            svc.lease.create_lease(lease_data, username=current_user)

            # Deduct from stock through service
            product = svc.inventory.get_product_by_id(product_id)
            if product:
                svc.inventory.adjust_stock(product['model'], -1, username=current_user, reason=f"Lease {lease_id}")

            messagebox.showinfo("Success", f"Lease created: {lease_id}")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to create lease")
            messagebox.showerror("Error", f"Failed to create lease: {e}")

    make_button(btn_frame, "💾 Create Lease", command=save_lease, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_lease_details(parent, lease_id, current_user=None):
    """View lease details."""
    dlg = tk.Toplevel(parent)
    dlg.title("Lease Details")
    dlg.geometry("950x850")
    dlg.resizable(True, True)
    dlg.minsize(750, 700)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    # Get lease through service
    leases = svc.lease.get_all_leases()
    lease = None
    for l in leases:
        if str(l.get('lease_id')) == str(lease_id):
            lease = l
            break

    if not lease:
        messagebox.showerror("Error", "Lease not found")
        dlg.destroy()
        return

    # Header
    styled_label(content, f"Lease: {lease['lease_id']}", font=FONT_BOLD).pack(anchor=tk.W)
    styled_label(content, f"Status: {lease['status'].title()}", foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(5, 15))

    # Info
    info_frame = make_card(content, padding=15)
    info_frame.pack(fill=tk.X)

    info = [
        ("Customer:", lease.get('customer_name', 'N/A')),
        ("Product:", lease.get('product_name', 'N/A')),
        ("Start Date:", lease.get('start_date', 'N/A')[:10] if lease.get('start_date') else 'N/A'),
        ("End Date:", lease.get('end_date', 'N/A')[:10] if lease.get('end_date') else 'N/A'),
        ("Monthly Amount:", f"Rs. {lease.get('monthly_amount', 0):,.2f}"),
        ("Duration:", f"{lease.get('duration_months', 0)} months"),
        ("Security Deposit:", f"Rs. {lease.get('security_deposit', 0):,.2f}"),
    ]

    for label, value in info:
        frame = ttk.Frame(info_frame)
        frame.pack(fill=tk.X, pady=3)
        styled_label(frame, f"{label}", font=("Segoe UI", 10, "bold"), width=15).pack(side=tk.LEFT)
        styled_label(frame, f"{value}").pack(side=tk.LEFT)

    # Payment history
    styled_label(content, "Payment History:", font=FONT_BOLD).pack(anchor=tk.W, pady=(15, 5))

    payments_frame = make_card(content, padding=10)
    payments_frame.pack(fill=tk.BOTH, expand=True)

    columns = ("date", "amount", "method", "notes")
    payments_tree = ttk.Treeview(payments_frame, columns=columns, show="headings", height=6)

    for col in columns:
        payments_tree.heading(col, text=col.title())
        payments_tree.column(col, width=120)

    payments_tree.pack(fill=tk.BOTH, expand=True)

    # Fetch payments through service
    payments = svc.stock_transfer.get_lease_payments(lease_id=lease_id)

    for row in payments:
        payments_tree.insert("", "end", values=(
            row['payment_date'][:10] if row['payment_date'] else 'N/A',
            f"Rs. {row['amount_paid']:,.2f}",
            row['payment_method'] or 'Cash',
            row['notes'] or ''
        ))

    if not payments:
        styled_label(payments_frame, "No payments recorded yet", foreground=COLOR_WARNING).pack(pady=20)

    # Close button
    ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=10)


def open_record_payment_dialog(parent, lease_id, current_user=None):
    """Dialog to record a lease payment."""
    dlg = tk.Toplevel(parent)
    dlg.title("Record Lease Payment")
    dlg.geometry("800x700")
    dlg.resizable(True, True)
    dlg.minsize(650, 550)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    styled_label(content, "Record Payment", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    form_frame.grid_columnconfigure(0, weight=0, minsize=150)
    form_frame.grid_columnconfigure(1, weight=1)

    # Amount
    styled_label(form_frame, "Amount (Rs.) *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    amount_var = tk.StringVar()
    amount_entry = ttk.Entry(form_frame, textvariable=amount_var, width=20)
    amount_entry.grid(row=1, column=0, sticky=tk.W, pady=5)

    # Payment method
    styled_label(form_frame, "Payment Method:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    method_var = tk.StringVar(value="cash")
    method_combo = ttk.Combobox(form_frame, textvariable=method_var, values=[
        "cash", "check", "bank_transfer", "card", "other"
    ], state="readonly", width=20)
    method_combo.grid(row=3, column=0, sticky=tk.W, pady=5)

    # Payment date
    styled_label(form_frame, "Payment Date:", font=FONT_BOLD).grid(row=4, column=0, sticky=tk.W, pady=5)
    date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    date_entry = ttk.Entry(form_frame, textvariable=date_var, width=15)
    date_entry.grid(row=5, column=0, sticky=tk.W, pady=5)

    # Notes
    styled_label(form_frame, "Notes:", font=FONT_BOLD).grid(row=6, column=0, sticky=tk.W, pady=5)
    notes_text = tk.Text(form_frame, height=3, width=30)
    notes_text.grid(row=7, column=0, sticky=tk.EW, pady=5)

    def save_payment():
        amount = amount_var.get().strip()
        method = method_var.get()
        payment_date = date_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()

        if not amount:
            messagebox.showerror("Error", "Amount required")
            return

        try:
            amount_paid = float(amount)
            if amount_paid <= 0:
                raise ValueError("Amount must be positive")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid amount: {e}")
            return

        try:
            # Record payment through service
            payment_data = {
                "lease_id": lease_id,
                "payment_date": payment_date,
                "amount_paid": amount_paid,
                "payment_method": method,
                "notes": notes,
                "recorded_by": current_user
            }
            svc.stock_transfer.record_lease_payment(payment_data, username=current_user)

            # Update lease last payment date through service
            svc.lease.update_lease(str(lease_id), {'last_payment_date': payment_date}, username=current_user)

            messagebox.showinfo("Success", "Payment recorded")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to record payment")
            messagebox.showerror("Error", f"Failed to record payment: {e}")

    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    make_button(btn_frame, "💾 Record Payment", command=save_payment, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_return_item_dialog(parent, lease_id):
    """Dialog to process lease item return."""
    dlg = tk.Toplevel(parent)
    dlg.title("Return Lease Item")
    dlg.geometry("850x750")
    dlg.resizable(True, True)
    dlg.minsize(700, 600)
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)

    styled_label(content, "Return Lease Item", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))

    # Get lease info through service
    leases = svc.lease.get_all_leases()
    lease = None
    for l in leases:
        if str(l.get('lease_id')) == str(lease_id):
            lease = l
            break

    if not lease:
        messagebox.showerror("Error", "Lease not found")
        dlg.destroy()
        return

    styled_label(content, f"Product: {lease.get('product_name', 'N/A')}", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    styled_label(content, f"Customer: {lease.get('customer_name', 'N/A')}", foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(0, 15))

    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    form_frame.grid_columnconfigure(0, weight=0, minsize=150)
    form_frame.grid_columnconfigure(1, weight=1)

    # Condition
    styled_label(form_frame, "Item Condition:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    condition_var = tk.StringVar(value="good")
    condition_combo = ttk.Combobox(form_frame, textvariable=condition_var, values=[
        "good", "fair", "damaged", "needs_repair"
    ], state="readonly", width=20)
    condition_combo.grid(row=1, column=0, sticky=tk.W, pady=5)

    # Return date
    styled_label(form_frame, "Return Date:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    date_entry = ttk.Entry(form_frame, textvariable=date_var, width=15)
    date_entry.grid(row=3, column=0, sticky=tk.W, pady=5)

    # Notes
    styled_label(form_frame, "Return Notes:", font=FONT_BOLD).grid(row=4, column=0, sticky=tk.W, pady=5)
    notes_text = tk.Text(form_frame, height=3, width=30)
    notes_text.grid(row=5, column=0, sticky=tk.EW, pady=5)

    # Deduct from security
    deduct_var = tk.StringVar(value="0")
    styled_label(form_frame, "Deduction from Security (Rs.):", font=FONT_BOLD).grid(row=6, column=0, sticky=tk.W, pady=5)
    deduct_entry = ttk.Entry(form_frame, textvariable=deduct_var, width=15)
    deduct_entry.grid(row=7, column=0, sticky=tk.W, pady=5)

    def process_return():
        condition = condition_var.get()
        return_date = date_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()
        deduction = deduct_var.get().strip()

        try:
            # Update lease status through service
            svc.lease.update_lease(str(lease_id), {
                'status': 'completed',
                'return_date': return_date,
                'return_condition': condition,
                'return_notes': notes,
                'security_deduction': float(deduction) if deduction else 0,
            }, username="system")

            # Add product back to stock through service
            product_name = lease.get('product_name')
            if product_name:
                product = svc.inventory.get_product_by_model(product_name)
                if product:
                    svc.inventory.adjust_stock(product['model'], 1, username="system", reason=f"Lease {lease_id} returned")

            messagebox.showinfo("Success", "Item returned successfully")
            dlg.destroy()

            # Refresh parent
            if hasattr(parent, 'refresh_from_db'):
                parent.refresh_from_db()

        except Exception as e:
            logging.exception("Failed to process return")
            messagebox.showerror("Error", f"Failed to process return: {e}")

    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))

    make_button(btn_frame, "📦 Process Return", command=process_return, kind="warning").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)
