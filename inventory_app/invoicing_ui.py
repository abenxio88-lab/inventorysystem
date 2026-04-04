"""
Invoicing UI Tab
=================
UI-ONLY layer. All data goes through the service layer.
After every write, refresh_from_db() reloads fresh data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import os
from datetime import datetime, timedelta

from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED,
    COLOR_TEXT_MAIN, COLOR_APP_BG, COLOR_CARD_BG,
    label, frame, entry, combobox
)
from services import svc
from app_core import app_state

logger = logging.getLogger(__name__)


def create_invoicing_tab(parent, current_user=None):
    """Creates the comprehensive invoicing tab."""
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    styled_label(header_frame, "📄 Invoice Management", font=FONT_HEADING).pack(side=tk.LEFT)

    def open_new_invoice():
        _open_create_invoice_dialog(window, current_user=current_user)

    make_button(header_frame, "➕ New Invoice", command=open_new_invoice, kind="success").pack(side=tk.RIGHT)

    # Summary cards
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))

    def _update_summary():
        invoices = svc.invoice.get_all_invoices()
        total = sum(inv.get("total_amount", 0) for inv in invoices)
        paid = sum(inv.get("amount_paid", 0) for inv in invoices if inv.get("status") == "paid")
        pending = total - paid
        counts = {"pending": 0, "paid": 0, "overdue": 0}
        for inv in invoices:
            status = inv.get("status", "pending")
            if status in counts:
                counts[status] += 1

        widgets = _summary_widgets
        widgets["total"].config(text=f"Rs. {total:,.2f}")
        widgets["paid"].config(text=f"Rs. {paid:,.2f}")
        widgets["pending"].config(text=f"Rs. {pending:,.2f}")
        widgets["count_pending"].config(text=str(counts["pending"]))
        widgets["count_paid"].config(text=str(counts["paid"]))

    _summary_widgets = {}
    for i, (title, key) in enumerate([
        ("Total Invoiced", "total"), ("Total Paid", "paid"),
        ("Outstanding", "pending"), ("Pending Count", "count_pending"), ("Paid Count", "count_paid")
    ]):
        card = make_card(summary_frame, padding=12)
        card.grid(row=0, column=i, padx=8, sticky="nsew")
        styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d").pack(anchor="w")
        val = styled_label(card, text="...", font=("Segoe UI", 18, "bold"), foreground=COLOR_PRIMARY)
        val.pack(anchor="w", pady=(3, 0))
        _summary_widgets[key] = val
    summary_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

    # Filter toolbar
    toolbar = ttk.Frame(window)
    toolbar.pack(fill="x", pady=(0, 10))
    styled_label(toolbar, "Status:").pack(side=tk.LEFT, padx=(0, 5))
    status_var = tk.StringVar(value="All")
    status_cb = combobox(toolbar, values=["All", "pending", "paid", "overdue"],
                         textvariable=status_var, state="readonly")
    status_cb.pack(side=tk.LEFT, padx=(0, 10))

    refresh_btn = make_button(toolbar, "Refresh", kind="primary")
    refresh_btn.pack(side=tk.LEFT)

    # Table
    table_frame = make_card(window, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("number", "customer", "date", "due_date", "total", "paid", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "number": ("Invoice #", 120),
        "customer": ("Customer", 150),
        "date": ("Date", 100),
        "due_date": ("Due Date", 100),
        "total": ("Total", 100),
        "paid": ("Paid", 100),
        "status": ("Status", 80),
    }

    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text.upper(), anchor="w")
        tree.column(col, width=width, anchor="w")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    try:
        style = ttk.Style()
        style.configure("Treeview", font=FONT_REGULAR, rowheight=28)
        style.configure("Treeview.Heading", font=FONT_BOLD)
    except Exception:
        pass

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    # ========================================================

    def refresh_from_db():
        """Reload invoices and update summary."""
        _update_summary()
        tree.delete(*tree.get_children())

        status_filter = status_var.get()
        invoices = svc.invoice.get_all_invoices(
            status=None if status_filter == "All" else status_filter
        )

        for inv in invoices:
            tree.insert("", "end", values=(
                inv.get("invoice_number", ""),
                inv.get("customer_name", ""),
                inv.get("invoice_date", "")[:10],
                inv.get("due_date", "")[:10],
                f"{inv.get('total_amount', 0):,.2f}",
                f"{inv.get('amount_paid', 0):,.2f}",
                inv.get("status", ""),
            ))

    # Now wire the combobox and button (after refresh_from_db is defined)
    status_cb.bind("<<ComboboxSelected>>", lambda e: refresh_from_db())
    refresh_btn.config(command=refresh_from_db)

    # Double-click to view/pay
    def on_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        inv_number = tree.item(sel[0], "values")[0]
        invoices = svc.invoice.get_all_invoices()
        inv = next((i for i in invoices if i.get("invoice_number") == inv_number), None)
        if inv:
            _open_invoice_detail(window, inv, current_user=current_user, on_refresh=refresh_from_db)

    tree.bind("<Double-1>", on_double_click)

    # Initial load
    refresh_from_db()
    return window


def _open_create_invoice_dialog(master, current_user=None):
    """Dialog to create a new invoice."""
    dlg = tk.Toplevel(master)
    dlg.title("New Invoice")
    dlg.geometry("600x550")
    dlg.transient(master)
    dlg.grab_set()

    form_card = make_card(dlg, padx=20, pady=20)
    form_card.pack(fill="both", expand=True, padx=10, pady=10)

    # Customer selection
    label(form_card, "Customer Name", kind="bold").grid(row=0, column=0, sticky="w", pady=5, padx=5)
    customer_var = tk.StringVar()
    customers = svc.customer.get_all_customers()
    customer_names = [c.get("name", "") for c in customers if c.get("name")]
    customer_cb = combobox(form_card, values=customer_names, textvariable=customer_var, state="readonly")
    customer_cb.grid(row=0, column=1, sticky="ew", pady=5, padx=5)

    # Product selection
    label(form_card, "Product", kind="bold").grid(row=1, column=0, sticky="w", pady=5, padx=5)
    product_var = tk.StringVar()
    products = svc.inventory.get_all_products(active_only=True)
    product_names = [p.get("model", "") for p in products if p.get("model")]
    product_cb = combobox(form_card, values=product_names, textvariable=product_var, state="readonly")
    product_cb.grid(row=1, column=1, sticky="ew", pady=5, padx=5)

    # Quantity
    label(form_card, "Quantity", kind="bold").grid(row=2, column=0, sticky="w", pady=5, padx=5)
    qty_var = tk.StringVar(value="1")
    qty_entry = entry(form_card, textvariable=qty_var)
    qty_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=5)

    # Due date
    label(form_card, "Due Date (YYYY-MM-DD)", kind="bold").grid(row=3, column=0, sticky="w", pady=5, padx=5)
    due_var = tk.StringVar(value=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
    due_entry = entry(form_card, textvariable=due_var)
    due_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=5)

    # Notes
    label(form_card, "Notes", kind="bold").grid(row=4, column=0, sticky="w", pady=5, padx=5)
    notes_var = tk.StringVar()
    notes_entry = entry(form_card, textvariable=notes_var)
    notes_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=5)

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(fill="x", pady=10, padx=10)

    def create():
        customer_name = customer_var.get()
        product_name = product_var.get()
        if not customer_name or not product_name:
            messagebox.showerror("Error", "Customer and Product are required")
            return

        try:
            qty = int(qty_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return

        product = next((p for p in products if p.get("model") == product_name), None)
        if not product:
            messagebox.showerror("Error", "Product not found")
            return

        unit_price = product.get("selling_price", 0)
        subtotal = qty * unit_price
        tax_rate = 0  # Can be configurable
        tax_amount = subtotal * tax_rate / 100
        total = subtotal + tax_amount

        username = current_user or getattr(app_state, "username", "system")
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        invoice_data = {
            "invoice_number": invoice_number,
            "customer_name": customer_name,
            "invoice_date": datetime.now().isoformat(),
            "due_date": due_var.get(),
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total_amount": total,
            "amount_paid": 0,
            "status": "pending",
            "notes": notes_var.get(),
            "created_by": username,
        }

        items = [{
            "product_id": product.get("id"),
            "product_name": product_name,
            "quantity": qty,
            "unit_price": unit_price,
            "line_total": subtotal,
        }]

        try:
            svc.invoice.create_invoice(invoice_data, items, username=username)
            messagebox.showinfo("Success", f"Invoice {invoice_number} created")
            dlg.destroy()
        except Exception as e:
            logger.error(f"Failed to create invoice: {e}", exc_info=True)
            messagebox.showerror("Error", str(e))

    make_button(btn_frame, "Create Invoice", command=create, kind="primary").pack(side="right", padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side="right", padx=5)


def _open_invoice_detail(master, invoice, current_user=None, on_refresh=None):
    """Dialog to view invoice details and record payments."""
    dlg = tk.Toplevel(master)
    dlg.title(f"Invoice {invoice.get('invoice_number', '')}")
    dlg.geometry("500x400")
    dlg.transient(master)
    dlg.grab_set()

    form_card = make_card(dlg, padx=20, pady=20)
    form_card.pack(fill="both", expand=True, padx=10, pady=10)

    details = [
        ("Invoice #", invoice.get("invoice_number", "")),
        ("Customer", invoice.get("customer_name", "")),
        ("Date", invoice.get("invoice_date", "")[:10]),
        ("Due Date", invoice.get("due_date", "")[:10]),
        ("Total", f"{invoice.get('total_amount', 0):,.2f}"),
        ("Paid", f"{invoice.get('amount_paid', 0):,.2f}"),
        ("Status", invoice.get("status", "")),
    ]

    for i, (lbl, val) in enumerate(details):
        label(form_card, lbl, kind="bold").grid(row=i, column=0, sticky="w", pady=3, padx=5)
        label(form_card, val).grid(row=i, column=1, sticky="w", pady=3, padx=5)

    # Payment section
    pay_frame = ttk.Frame(dlg)
    pay_frame.pack(fill="x", pady=10, padx=10)

    label(pay_frame, "Payment Amount", kind="bold").pack(anchor="w")
    pay_var = tk.StringVar()
    pay_entry = entry(pay_frame, textvariable=pay_var)
    pay_entry.pack(fill="x", pady=3)

    def record_payment():
        try:
            amount = float(pay_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid payment amount")
            return

        username = current_user or getattr(app_state, "username", "system")
        try:
            from database import db
            db.audit_event(username, "invoice_payment", "invoices", invoice.get("invoice_id"),
                           f"Payment of {amount} for {invoice.get('invoice_number')}")
            messagebox.showinfo("Success", f"Payment of {amount} recorded")
            dlg.destroy()
            if on_refresh:
                on_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    make_button(pay_frame, "Record Payment", command=record_payment, kind="success").pack(pady=5)
    make_button(pay_frame, "Close", command=dlg.destroy, kind="secondary").pack(pady=5)
