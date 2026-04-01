"""
Comprehensive Invoicing System
===============================
Professional invoice generation with company branding, PDF export,
email integration, and payment tracking.
Phase 15 - Complete Implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List

try:
    from .database import get_db_cursor, get_connection
    from .ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, FONT_REGULAR, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, FONT_REGULAR, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from utils import get_data_dir

# Try to import PDF libraries
try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("reportlab not available - PDF generation disabled")


def create_invoicing_tab(parent, current_user=None):
    """
    Creates the comprehensive invoicing tab.
    """
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "📄 Invoice Management", font=FONT_HEADING).pack(side=tk.LEFT)
    
    # New Invoice button
    def open_new_invoice():
        open_create_invoice_dialog(window, current_user=current_user)
    
    make_button(header_frame, "➕ New Invoice", command=open_new_invoice, kind="success").pack(side=tk.RIGHT)
    
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
    pending_lbl = create_summary_card(summary_frame, "Pending", 0, 1)
    paid_lbl = create_summary_card(summary_frame, "Paid", 0, 2)
    overdue_lbl = create_summary_card(summary_frame, "Overdue", 0, 3)
    total_lbl = create_summary_card(summary_frame, "Total Invoices", 0, 4)
    
    window.summary_labels = {
        'draft': draft_lbl,
        'pending': pending_lbl,
        'paid': paid_lbl,
        'overdue': overdue_lbl,
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
        values=["all", "draft", "pending", "paid", "overdue", "cancelled"],
        state="readonly",
        width=15
    )
    status_combo.pack(side=tk.LEFT, padx=5)
    
    def apply_filter():
        refresh_invoices()
    
    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), refresh_invoices()), kind="secondary").pack(side=tk.LEFT)
    
    # Invoices table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("invoice_number", "customer", "date", "due_date", "amount", "paid", "balance", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    column_map = {
        "invoice_number": ("Invoice #", 100),
        "customer": ("Customer", 200),
        "date": ("Date", 100),
        "due_date": ("Due Date", 100),
        "amount": ("Amount", 100),
        "paid": ("Paid", 100),
        "balance": ("Balance", 100),
        "status": ("Status", 100)
    }
    
    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text)
        tree.column(col, width=width, anchor="w")
    
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
            messagebox.showinfo("Select", "Please select an invoice")
            return
        
        invoice_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if invoice_id:
            open_invoice_details(window, invoice_id=int(invoice_id), current_user=current_user)
    
    def on_record_payment():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an invoice")
            return
        
        invoice_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if invoice_id:
            open_invoice_payment_dialog(window, invoice_id=int(invoice_id), current_user=current_user)
    
    def on_print_invoice():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an invoice")
            return
        
        invoice_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if invoice_id:
            print_invoice(invoice_id)
    
    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "💰 Record Payment", command=on_record_payment, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "🖨️ Print/PDF", command=on_print_invoice, kind="warning").pack(side=tk.LEFT, padx=5)
    
    # Store state
    window.status_var = status_var
    window.tree = tree
    
    def refresh_invoices():
        """Refresh invoices list."""
        tree.delete(*tree.get_children())
        
        status_filter = status_var.get()
        
        with get_db_cursor() as cur:
            if status_filter == 'all':
                cur.execute("""
                    SELECT invoice_id, invoice_number, customer_name, customer_email,
                           invoice_date, due_date, subtotal, tax_amount, discount_amount,
                           total_amount, amount_paid, status, notes
                    FROM invoices
                    ORDER BY invoice_date DESC
                """)
            else:
                cur.execute("""
                    SELECT invoice_id, invoice_number, customer_name, customer_email,
                           invoice_date, due_date, subtotal, tax_amount, discount_amount,
                           total_amount, amount_paid, status, notes
                    FROM invoices
                    WHERE status = ?
                    ORDER BY invoice_date DESC
                """, (status_filter,))
            
            invoices = cur.fetchall()
        
        # Update summary
        status_counts = {'draft': 0, 'pending': 0, 'paid': 0, 'overdue': 0, 'total': len(invoices)}
        for inv in invoices:
            if inv['status'] in status_counts:
                status_counts[inv['status']] += 1
            elif inv['status'] == 'overdue':
                status_counts['overdue'] += 1
        
        window.summary_labels['draft'].config(text=str(status_counts['draft']))
        window.summary_labels['pending'].config(text=str(status_counts['pending']))
        window.summary_labels['paid'].config(text=str(status_counts['paid']))
        window.summary_labels['overdue'].config(text=str(status_counts['overdue']))
        window.summary_labels['total'].config(text=str(status_counts['total']))
        
        # Populate table
        today = datetime.now().strftime('%Y-%m-%d')
        
        for inv in invoices:
            balance = inv['total_amount'] - (inv['amount_paid'] or 0)
            
            # Determine status color
            status_text = inv['status'].replace('_', ' ').title()
            if inv['status'] == 'pending' and inv['due_date'] and inv['due_date'] < today:
                status_text = "⚠️ Overdue"
            
            tags = (str(inv['invoice_id']),)
            
            tree.insert("", "end", values=(
                inv['invoice_number'],
                inv['customer_name'] or 'Walk-in Customer',
                inv['invoice_date'][:10] if inv['invoice_date'] else 'N/A',
                inv['due_date'][:10] if inv['due_date'] else 'N/A',
                f"Rs. {inv['total_amount']:,.2f}",
                f"Rs. {inv['amount_paid']:,.2f}" if inv['amount_paid'] else "Rs. 0.00",
                f"Rs. {balance:,.2f}",
                status_text
            ), tags=tags)
    
    window.refresh_invoices = refresh_invoices
    refresh_invoices()
    
    return window


def open_create_invoice_dialog(parent, current_user=None, from_barcode=False, barcode_data=None):
    """Dialog to create a new invoice."""
    dlg = tk.Toplevel(parent)
    dlg.title("Create New Invoice")
    dlg.geometry("1200x900")
    dlg.resizable(True, True)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Heading
    styled_label(content, "📄 New Invoice", font=FONT_HEADING).pack(anchor=tk.W, pady=(0, 15))
    
    # Customer info frame
    customer_frame = ttk.LabelFrame(content, text="Customer Information", padding=15)
    customer_frame.pack(fill=tk.X, pady=(0, 15))
    customer_frame.grid_columnconfigure(1, weight=1)
    customer_frame.grid_columnconfigure(3, weight=1)
    
    # Customer fields
    styled_label(customer_frame, "Customer Name *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    customer_name_var = tk.StringVar()
    customer_name_entry = ttk.Entry(customer_frame, textvariable=customer_name_var, width=25)
    customer_name_entry.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)
    
    styled_label(customer_frame, "Phone:", font=FONT_BOLD).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    customer_phone_var = tk.StringVar()
    customer_phone_entry = ttk.Entry(customer_frame, textvariable=customer_phone_var, width=20)
    customer_phone_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    
    styled_label(customer_frame, "Email:", font=FONT_BOLD).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
    customer_email_var = tk.StringVar()
    customer_email_entry = ttk.Entry(customer_frame, textvariable=customer_email_var, width=25)
    customer_email_entry.grid(row=1, column=2, sticky=tk.EW, padx=5, pady=5)
    
    styled_label(customer_frame, "Address:", font=FONT_BOLD).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
    customer_address_var = tk.StringVar()
    customer_address_entry = ttk.Entry(customer_frame, textvariable=customer_address_var, width=25)
    customer_address_entry.grid(row=1, column=3, sticky=tk.EW, padx=5, pady=5)
    
    # Invoice settings
    settings_frame = ttk.LabelFrame(content, text="Invoice Settings", padding=15)
    settings_frame.pack(fill=tk.X, pady=(0, 15))
    settings_frame.grid_columnconfigure(1, weight=1)
    settings_frame.grid_columnconfigure(3, weight=1)
    
    # Invoice number (auto-generated)
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M')}"
    styled_label(settings_frame, "Invoice Number:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    invoice_number_var = tk.StringVar(value=invoice_number)
    invoice_number_entry = ttk.Entry(settings_frame, textvariable=invoice_number_var, width=20, state='readonly')
    invoice_number_entry.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    
    # Invoice date
    styled_label(settings_frame, "Invoice Date *:", font=FONT_BOLD).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    invoice_date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    invoice_date_entry = ttk.Entry(settings_frame, textvariable=invoice_date_var, width=15)
    invoice_date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
    # Due date
    styled_label(settings_frame, "Due Date:", font=FONT_BOLD).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
    due_date_var = tk.StringVar(value=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
    due_date_entry = ttk.Entry(settings_frame, textvariable=due_date_var, width=15)
    due_date_entry.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
    
    # Payment terms
    styled_label(settings_frame, "Payment Terms:", font=FONT_BOLD).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
    payment_terms_var = tk.StringVar(value="Net 30")
    payment_terms_combo = ttk.Combobox(settings_frame, textvariable=payment_terms_var, values=[
        "Due on Demand", "Net 15", "Net 30", "Net 45", "Net 60", "Net 90"
    ], state="readonly", width=18)
    payment_terms_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
    
    # Products section
    styled_label(content, "Invoice Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    
    products_frame = make_card(content, padding=10)
    products_frame.pack(fill=tk.BOTH, expand=True)
    
    # Add item row
    add_frame = ttk.Frame(products_frame)
    add_frame.pack(fill=tk.X, pady=(0, 10))
    
    styled_label(add_frame, "Product:").pack(side=tk.LEFT, padx=5)
    
    product_var = tk.StringVar()
    product_combo = ttk.Combobox(add_frame, textvariable=product_var, state="readonly", width=35)
    product_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # Load products
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, model, category, stock, selling_price
            FROM products
            WHERE status = 'active' AND stock > 0
            ORDER BY model
        """)
        products = cur.fetchall()
    
    product_data = [(p['id'], f"{p['model']} (Stock: {p['stock']}, Price: Rs. {p['selling_price']})") for p in products]
    product_combo['values'] = [p[1] for p in product_data]
    
    # If from barcode, pre-select the product
    if from_barcode and barcode_data:
        # Try to match barcode data to product
        for pid, pname in product_data:
            if barcode_data.get('id') == pid or barcode_data.get('sku') in pname:
                product_var.set(pname)
                break
    
    styled_label(add_frame, "Qty:").pack(side=tk.LEFT, padx=(15, 5))
    
    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(add_frame, textvariable=qty_var, width=8)
    qty_entry.pack(side=tk.LEFT, padx=5)
    
    styled_label(add_frame, "Discount:").pack(side=tk.LEFT, padx=(10, 5))
    
    discount_var = tk.StringVar(value="0")
    discount_entry = ttk.Entry(add_frame, textvariable=discount_var, width=8)
    discount_entry.pack(side=tk.LEFT, padx=5)
    
    # Add button
    def add_item():
        product_sel = product_var.get()
        qty = qty_var.get()
        discount = discount_var.get()
        
        if not product_sel:
            messagebox.showerror("Error", "Please select a product")
            return
        
        try:
            qty_int = int(qty)
            discount_float = float(discount)
            if qty_int <= 0 or discount_float < 0:
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid quantity or discount")
            return
        
        # Find product
        product_id = None
        product_name = None
        unit_price = 0
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                for p in products:
                    if p['id'] == pid:
                        unit_price = p['selling_price']
                        break
                break
        
        if not product_id:
            return
        
        total = qty_int * unit_price
        discount_amount = total * (discount_float / 100)
        line_total = total - discount_amount
        
        # Add to list
        invoice_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': qty_int,
            'unit_price': unit_price,
            'discount_percent': discount_float,
            'discount_amount': discount_amount,
            'line_total': line_total
        })
        
        # Update tree
        items_tree.insert("", "end", values=(
            product_name,
            qty_int,
            f"Rs. {unit_price:,.2f}",
            f"{discount_float}%",
            f"Rs. {discount_amount:,.2f}",
            f"Rs. {line_total:,.2f}",
            "🗑️ Remove"
        ))
        
        # Clear selection
        product_var.set("")
        qty_var.set("1")
        discount_var.set("0")
        
        update_totals()
    
    def on_item_click(event):
        sel = items_tree.selection()
        if not sel:
            return
        
        item = items_tree.item(sel[0])
        if item['values'][6] == "🗑️ Remove":
            index = items_tree.index(sel[0])
            if 0 <= index < len(invoice_items):
                invoice_items.pop(index)
                items_tree.delete(sel[0])
                update_totals()
    
    make_button(add_frame, "➕ Add Item", command=add_item, kind="primary").pack(side=tk.LEFT, padx=10)
    
    # Items tree
    items_frame = ttk.Frame(products_frame)
    items_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("product", "quantity", "unit_price", "discount", "discount_amt", "total", "actions")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
    
    for col in columns:
        items_tree.heading(col, text=col.replace('_', ' ').title())
        items_tree.column(col, width=100 if col not in ["product", "actions"] else 120)
    
    items_tree.pack(fill=tk.BOTH, expand=True)
    
    # Invoice items storage
    invoice_items = []
    
    # Tax and totals frame
    totals_frame = ttk.LabelFrame(content, text="Invoice Totals", padding=15)
    totals_frame.pack(fill=tk.X, pady=(10, 0))
    totals_frame.grid_columnconfigure(1, weight=1)
    
    # Subtotal
    styled_label(totals_frame, "Subtotal:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
    subtotal_var = tk.StringVar(value="Rs. 0.00")
    subtotal_label = styled_label(totals_frame, textvariable=subtotal_var, font=FONT_REGULAR)
    subtotal_label.grid(row=0, column=1, sticky=tk.E, padx=5, pady=5)
    
    # Tax rate
    styled_label(totals_frame, "Tax Rate (%):", font=FONT_BOLD).grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
    tax_rate_var = tk.StringVar(value="0")
    tax_rate_entry = ttk.Entry(totals_frame, textvariable=tax_rate_var, width=10)
    tax_rate_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
    # Tax amount
    styled_label(totals_frame, "Tax Amount:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.E, padx=5, pady=5)
    tax_amount_var = tk.StringVar(value="Rs. 0.00")
    tax_amount_label = styled_label(totals_frame, textvariable=tax_amount_var, font=FONT_REGULAR)
    tax_amount_label.grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)
    
    # Total
    styled_label(totals_frame, "Total Amount:", font=("Segoe UI", 12, "bold")).grid(row=3, column=0, sticky=tk.E, padx=5, pady=5)
    total_amount_var = tk.StringVar(value="Rs. 0.00")
    total_amount_label = styled_label(totals_frame, textvariable=total_amount_var, font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARY)
    total_amount_label.grid(row=3, column=1, sticky=tk.E, padx=5, pady=5)
    
    def update_totals():
        subtotal = sum(item['line_total'] for item in invoice_items)
        tax_rate = float(tax_rate_var.get()) if tax_rate_var.get() else 0
        tax_amount = subtotal * (tax_rate / 100)
        total = subtotal + tax_amount
        
        subtotal_var.set(f"Rs. {subtotal:,.2f}")
        tax_amount_var.set(f"Rs. {tax_amount:,.2f}")
        total_amount_var.set(f"Rs. {total:,.2f}")
    
    tax_rate_var.trace('w', lambda *args: update_totals())
    
    # Notes
    styled_label(content, "Notes/Terms:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    notes_text = tk.Text(content, height=3)
    notes_text.pack(fill=tk.X, pady=(0, 10))
    
    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    
    def save_invoice():
        customer_name = customer_name_var.get().strip()
        customer_phone = customer_phone_var.get().strip()
        customer_email = customer_email_var.get().strip()
        customer_address = customer_address_var.get().strip()
        invoice_date = invoice_date_var.get().strip()
        due_date = due_date_var.get().strip()
        payment_terms = payment_terms_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()
        
        if not customer_name:
            messagebox.showerror("Error", "Customer name required")
            return
        
        if not invoice_items:
            messagebox.showerror("Error", "Please add at least one item")
            return
        
        tax_rate = float(tax_rate_var.get()) if tax_rate_var.get() else 0
        
        try:
            with get_db_cursor() as cur:
                # Calculate totals
                subtotal = sum(item['line_total'] for item in invoice_items)
                tax_amount = subtotal * (tax_rate / 100)
                total_amount = subtotal + tax_amount
                
                # Create invoice
                cur.execute("""
                    INSERT INTO invoices 
                    (invoice_number, customer_name, customer_phone, customer_email, customer_address,
                     invoice_date, due_date, payment_terms, subtotal, tax_rate, tax_amount,
                     total_amount, notes, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (invoice_number_var.get(), customer_name, customer_phone, customer_email,
                      customer_address, invoice_date, due_date, payment_terms,
                      subtotal, tax_rate, tax_amount, total_amount, notes, current_user))
                
                invoice_id = cur.lastrowid
                
                # Add invoice items
                for item in invoice_items:
                    cur.execute("""
                        INSERT INTO invoice_items 
                        (invoice_id, product_id, product_name, quantity, unit_price,
                         discount_percent, discount_amount, line_total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (invoice_id, item['product_id'], item['product_name'], item['quantity'],
                          item['unit_price'], item['discount_percent'], item['discount_amount'],
                          item['line_total']))
                    
                    # Deduct stock
                    cur.execute("""
                        UPDATE products SET stock = stock - ? WHERE id = ?
                    """, (item['quantity'], item['product_id']))
            
            # Ask to print
            if messagebox.askyesno("Success", f"Invoice created: {invoice_number_var.get()}\n\nPrint invoice?"):
                print_invoice(invoice_id)
            
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_invoices'):
                parent.refresh_invoices()
                
        except Exception as e:
            logging.exception("Failed to create invoice")
            messagebox.showerror("Error", f"Failed to create invoice: {e}")
    
    make_button(btn_frame, "💾 Create Invoice", command=save_invoice, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_invoice_details(parent, invoice_id, current_user=None):
    """View invoice details."""
    dlg = tk.Toplevel(parent)
    dlg.title("Invoice Details")
    dlg.geometry("1000x850")
    dlg.resizable(True, True)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    with get_db_cursor() as cur:
        # Get invoice info
        cur.execute("""
            SELECT * FROM invoices WHERE invoice_id = ?
        """, (invoice_id,))
        inv = cur.fetchone()
        
        # Header
        header_frame = ttk.Frame(content)
        header_frame.pack(fill=tk.X)
        
        styled_label(header_frame, f"Invoice: {inv['invoice_number']}", font=FONT_HEADING).pack(anchor=tk.W)
        status_color = COLOR_SUCCESS if inv['status'] == 'paid' else COLOR_DANGER if inv['status'] == 'overdue' else COLOR_PRIMARY
        styled_label(header_frame, f"Status: {inv['status'].title()}", foreground=status_color).pack(anchor=tk.W, pady=(5, 15))
        
        # Invoice info
        info_frame = make_card(content, padding=15)
        info_frame.pack(fill=tk.X)
        
        info = [
            ("Customer:", inv['customer_name']),
            ("Email:", inv['customer_email'] or 'N/A'),
            ("Phone:", inv['customer_phone'] or 'N/A'),
            ("Invoice Date:", inv['invoice_date'][:10] if inv['invoice_date'] else 'N/A'),
            ("Due Date:", inv['due_date'][:10] if inv['due_date'] else 'N/A'),
            ("Payment Terms:", inv['payment_terms'] or 'N/A'),
        ]
        
        for i, (label, value) in enumerate(info):
            row = i // 3
            col = (i % 3) * 2
            styled_label(info_frame, f"{label}", font=("Segoe UI", 10, "bold")).grid(row=row, column=col, sticky=tk.W, padx=5, pady=3)
            styled_label(info_frame, f"{value}").grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=3)
        
        # Items
        styled_label(content, "Invoice Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(15, 5))
        
        items_frame = make_card(content, padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("product", "quantity", "unit_price", "discount", "total")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")
        
        for col in columns:
            items_tree.heading(col, text=col.replace('_', ' ').title())
            items_tree.column(col, width=120)
        
        items_tree.pack(fill=tk.BOTH, expand=True)
        
        cur.execute("""
            SELECT product_name, quantity, unit_price, discount_percent, line_total
            FROM invoice_items
            WHERE invoice_id = ?
        """, (invoice_id,))
        
        for row in cur.fetchall():
            items_tree.insert("", "end", values=(
                row['product_name'],
                row['quantity'],
                f"Rs. {row['unit_price']:,.2f}",
                f"{row['discount_percent']}%",
                f"Rs. {row['line_total']:,.2f}"
            ))
        
        # Totals
        totals_frame = ttk.Frame(content)
        totals_frame.pack(fill=tk.X, pady=(10, 0))
        totals_frame.pack_propagate(False)
        totals_frame.config(height=100)
        
        # Right-aligned totals
        totals_info = [
            ("Subtotal:", f"Rs. {inv['subtotal']:,.2f}"),
            (f"Tax ({inv['tax_rate']}%):", f"Rs. {inv['tax_amount']:,.2f}"),
            ("Total:", f"Rs. {inv['total_amount']:,.2f}"),
            ("Paid:", f"Rs. {inv['amount_paid']:,.2f}"),
            ("Balance Due:", f"Rs. {inv['total_amount'] - (inv['amount_paid'] or 0):,.2f}"),
        ]
        
        for label, value in totals_info:
            frame = ttk.Frame(totals_frame)
            frame.pack(fill=tk.X, pady=2)
            styled_label(frame, f"{label}", font=FONT_BOLD, width=15).pack(side=tk.RIGHT, padx=10)
            styled_label(frame, f"{value}", font=FONT_REGULAR).pack(side=tk.RIGHT)
    
    # Close button
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    def close():
        dlg.destroy()
    
    make_button(btn_frame, "Close", command=close, kind="secondary").pack(side=tk.RIGHT)


def open_invoice_payment_dialog(parent, invoice_id, current_user=None):
    """Dialog to record payment against invoice."""
    dlg = tk.Toplevel(parent)
    dlg.title("Record Payment")
    dlg.geometry("700x600")
    dlg.resizable(True, True)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Get invoice info
    with get_db_cursor() as cur:
        cur.execute("SELECT invoice_number, total_amount, amount_paid FROM invoices WHERE invoice_id = ?", (invoice_id,))
        inv = cur.fetchone()
        
        balance = inv['total_amount'] - (inv['amount_paid'] or 0)
        
        styled_label(content, f"Invoice: {inv['invoice_number']}", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 10))
        styled_label(content, f"Balance Due: Rs. {balance:,.2f}", font=("Segoe UI", 14, "bold"), foreground=COLOR_DANGER).pack(anchor=tk.W, pady=(0, 15))
    
    # Payment form
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    form_frame.grid_columnconfigure(1, weight=1)
    
    # Amount
    styled_label(form_frame, "Payment Amount (Rs.) *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    amount_var = tk.StringVar(value=str(balance))
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
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid amount")
            return
        
        try:
            with get_db_cursor() as cur:
                # Record payment
                cur.execute("""
                    INSERT INTO invoice_payments 
                    (invoice_id, payment_date, amount_paid, payment_method, notes, recorded_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, payment_date, amount_paid, method, notes, current_user))
                
                # Update invoice
                cur.execute("""
                    UPDATE invoices 
                    SET amount_paid = COALESCE(amount_paid, 0) + ?,
                        status = CASE 
                            WHEN (COALESCE(amount_paid, 0) + ?) >= total_amount THEN 'paid'
                            ELSE 'pending'
                        END
                    WHERE invoice_id = ?
                """, (amount_paid, amount_paid, invoice_id))
            
            messagebox.showinfo("Success", "Payment recorded")
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_invoices'):
                parent.refresh_invoices()
                
        except Exception as e:
            logging.exception("Failed to record payment")
            messagebox.showerror("Error", f"Failed to record payment: {e}")
    
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    make_button(btn_frame, "💾 Record Payment", command=save_payment, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def print_invoice(invoice_id):
    """Generate and print/save invoice PDF."""
    if not PDF_AVAILABLE:
        messagebox.showerror("Error", "reportlab library required for PDF generation")
        return
    
    try:
        with get_db_cursor() as cur:
            # Get invoice data
            cur.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
            inv = cur.fetchone()
            
            # Get invoice items
            cur.execute("""
                SELECT product_name, quantity, unit_price, discount_percent, line_total
                FROM invoice_items WHERE invoice_id = ?
            """, (invoice_id,))
            items = cur.fetchall()
            
            # Get company info
            cur.execute("SELECT value FROM settings WHERE key = 'company_name'")
            row = cur.fetchone()
            company_name = row['value'] if row else "Minataka Sphere"
        
        # File dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Invoice_{inv['invoice_number']}.pdf"
        )
        
        if not filename:
            return
        
        # Create PDF
        doc = SimpleDocTemplate(filename, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        # Header - Company Info
        elements.append(Paragraph(company_name, title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Invoice title
        elements.append(Paragraph(f"INVOICE", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Invoice details
        invoice_info = [
            ["Invoice Number:", inv['invoice_number']],
            ["Invoice Date:", inv['invoice_date'][:10] if inv['invoice_date'] else 'N/A'],
            ["Due Date:", inv['due_date'][:10] if inv['due_date'] else 'N/A'],
        ]
        
        info_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Customer info
        elements.append(Paragraph("Bill To:", styles['Heading3']))
        customer_info = [
            ["Name:", inv['customer_name']],
            ["Email:", inv['customer_email'] or 'N/A'],
            ["Phone:", inv['customer_phone'] or 'N/A'],
        ]
        
        cust_table = Table(customer_info, colWidths=[1.5*inch, 4*inch])
        cust_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(cust_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Items table
        items_data = [["Product", "Qty", "Unit Price", "Discount", "Total"]]
        for item in items:
            items_data.append([
                item['product_name'],
                str(item['quantity']),
                f"Rs. {item['unit_price']:,.2f}",
                f"{item['discount_percent']}%",
                f"Rs. {item['line_total']:,.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 1*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Totals
        totals_data = [
            ["Subtotal:", f"Rs. {inv['subtotal']:,.2f}"],
            [f"Tax ({inv['tax_rate']}%):", f"Rs. {inv['tax_amount']:,.2f}"],
            ["Total:", f"Rs. {inv['total_amount']:,.2f}"],
            ["Paid:", f"Rs. {inv['amount_paid']:,.2f}"],
            ["Balance Due:", f"Rs. {inv['total_amount'] - (inv['amount_paid'] or 0):,.2f}"],
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTNAME', (0, 4), (0, 4), 'Helvetica-Bold'),
            ('FONTNAME', (1, 4), (1, 4), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(totals_table)
        
        # Footer
        if inv['notes']:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("Notes/Terms:", styles['Heading3']))
            elements.append(Paragraph(inv['notes'], styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        messagebox.showinfo("Success", f"Invoice saved to:\n{filename}")
        
    except Exception as e:
        logging.exception("Failed to generate invoice PDF")
        messagebox.showerror("Error", f"Failed to generate PDF: {e}")


# Note: Invoice tables are created in database.py during initialization
