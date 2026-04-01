"""
Trade-in & Service/Repair Module
=================================
Trade-in valuation and service ticket management.
Phase 5 - Complete Implementation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

try:
    from .database import get_db_cursor, get_connection
    from .ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER


def create_trade_ins_tab(parent, current_user=None):
    """Creates the trade-in management tab."""
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "💱 Trade-In Management", font=FONT_HEADING).pack(side=tk.LEFT)
    
    def open_new_trade_in():
        open_trade_in_dialog(window, current_user=current_user)
    
    make_button(header_frame, "➕ New Trade-In", command=open_new_trade_in, kind="success").pack(side=tk.RIGHT)
    
    # Summary
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))
    summary_frame.grid_columnconfigure((0, 1, 2), weight=1)
    
    def create_summary_card(parent, title, value, col):
        card = make_card(parent, padding=12)
        card.grid(row=0, column=col, padx=8, sticky="nsew")
        styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d").pack(anchor="w")
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 20, "bold"), foreground=COLOR_PRIMARY)
        value_label.pack(anchor="w", pady=(3, 0))
        return value_label
    
    pending_lbl = create_summary_card(summary_frame, "Pending", 0, 0)
    completed_lbl = create_summary_card(summary_frame, "Completed", 0, 1)
    total_value_lbl = create_summary_card(summary_frame, "Total Value", "Rs. 0", 2)
    
    window.summary_labels = {'pending': pending_lbl, 'completed': completed_lbl, 'total_value': total_value_lbl}
    
    # Table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("trade_in_number", "customer", "product", "value", "credit", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').title())
        tree.column(col, width=120)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.pack(side=tk.LEFT, fill="both", expand=True)
    
    def refresh():
        tree.delete(*tree.get_children())
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT trade_in_id, trade_in_number, customer_name, product_name,
                       trade_in_value, credit_amount, status
                FROM trade_ins ORDER BY trade_in_date DESC
            """)
            trades = cur.fetchall()
        
        counts = {'pending': 0, 'completed': 0, 'total_value': 0}
        for t in trades:
            if t['status'] in counts: counts[t['status']] += 1
            counts['total_value'] += t['trade_in_value'] or 0
            
            tree.insert("", "end", values=(
                t['trade_in_number'], t['customer_name'], t['product_name'],
                f"Rs. {t['trade_in_value']:,.2f}", f"Rs. {t['credit_amount']:,.2f}",
                t['status'].title()
            ), tags=(str(t['trade_in_id']),))
        
        window.summary_labels['pending'].config(text=str(counts['pending']))
        window.summary_labels['completed'].config(text=str(counts['completed']))
        window.summary_labels['total_value'].config(text=f"Rs. {counts['total_value']:,.2f}")
    
    window.refresh = refresh
    refresh()
    
    return window


def open_trade_in_dialog(parent, current_user=None):
    """Dialog to create a new trade-in."""
    dlg = tk.Toplevel(parent)
    dlg.title("New Trade-In")
    dlg.geometry("500x550")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    styled_label(content, "💱 New Trade-In", font=FONT_HEADING).pack(anchor=tk.W, pady=(0, 15))
    
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    form_frame.grid_columnconfigure(1, weight=1)
    
    # Customer
    styled_label(form_frame, "Customer Name *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    customer_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=customer_var, width=30).grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Phone
    styled_label(form_frame, "Phone:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    phone_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=phone_var, width=30).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Product
    styled_label(form_frame, "Product Name *:", font=FONT_BOLD).grid(row=4, column=0, sticky=tk.W, pady=5)
    product_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=product_var, width=30).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Condition
    styled_label(form_frame, "Condition:", font=FONT_BOLD).grid(row=6, column=0, sticky=tk.W, pady=5)
    condition_var = tk.StringVar(value="good")
    condition_combo = ttk.Combobox(form_frame, textvariable=condition_var, values=[
        "excellent", "good", "fair", "poor", "damaged"
    ], state="readonly", width=28)
    condition_combo.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Value
    styled_label(form_frame, "Trade-In Value (Rs.):", font=FONT_BOLD).grid(row=8, column=0, sticky=tk.W, pady=5)
    value_var = tk.StringVar(value="0")
    ttk.Entry(form_frame, textvariable=value_var, width=15).grid(row=9, column=0, sticky=tk.W, pady=5)
    
    # Credit
    styled_label(form_frame, "Credit Amount (Rs.):", font=FONT_BOLD).grid(row=8, column=1, sticky=tk.W, pady=5)
    credit_var = tk.StringVar(value="0")
    ttk.Entry(form_frame, textvariable=credit_var, width=15).grid(row=9, column=1, sticky=tk.W, pady=5)
    
    # Notes
    styled_label(form_frame, "Notes:", font=FONT_BOLD).grid(row=10, column=0, sticky=tk.W, pady=5)
    notes_text = tk.Text(form_frame, height=3, width=40)
    notes_text.grid(row=11, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    def save():
        customer = customer_var.get().strip()
        product = product_var.get().strip()
        
        if not customer or not product:
            messagebox.showerror("Error", "Customer name and product required")
            return
        
        try:
            value = float(value_var.get())
            credit = float(credit_var.get())
        except:
            messagebox.showerror("Error", "Invalid value/credit amount")
            return
        
        trade_number = f"TI-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO trade_ins 
                    (trade_in_number, customer_name, customer_phone, product_name,
                     product_condition, trade_in_value, credit_amount, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                """, (trade_number, customer, phone_var.get(), product, condition_var.get(),
                      value, credit, current_user))
            
            messagebox.showinfo("Success", f"Trade-in created: {trade_number}")
            dlg.destroy()
            if hasattr(parent, 'refresh'): parent.refresh()
        except Exception as e:
            logging.exception("Failed to create trade-in")
            messagebox.showerror("Error", f"Failed: {e}")
    
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    make_button(btn_frame, "💾 Create", command=save, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def create_service_tab(parent, current_user=None):
    """Creates the service/repair management tab."""
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "🔧 Service & Repair", font=FONT_HEADING).pack(side=tk.LEFT)
    
    def open_new_ticket():
        open_service_ticket_dialog(window, current_user=current_user)
    
    make_button(header_frame, "➕ New Service Ticket", command=open_new_ticket, kind="warning").pack(side=tk.RIGHT)
    
    # Summary
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
    
    received_lbl = create_summary_card(summary_frame, "Received", 0, 0)
    in_progress_lbl = create_summary_card(summary_frame, "In Progress", 0, 1)
    completed_lbl = create_summary_card(summary_frame, "Completed", 0, 2)
    revenue_lbl = create_summary_card(summary_frame, "Revenue", "Rs. 0", 3)
    
    window.summary_labels = {'received': received_lbl, 'in_progress': in_progress_lbl, 
                            'completed': completed_lbl, 'revenue': revenue_lbl}
    
    # Table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("ticket_number", "customer", "device", "status", "estimated", "received_date")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').title())
        tree.column(col, width=120)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.pack(side=tk.LEFT, fill="both", expand=True)
    
    def refresh():
        tree.delete(*tree.get_children())
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT ticket_id, ticket_number, customer_name, device_type, device_brand,
                       device_model, status, estimated_cost, final_cost, received_date
                FROM service_tickets ORDER BY received_date DESC
            """)
            tickets = cur.fetchall()
        
        counts = {'received': 0, 'in_progress': 0, 'completed': 0, 'revenue': 0}
        for t in tickets:
            if t['status'] in counts: counts[t['status']] += 1
            if t['status'] == 'completed': counts['revenue'] += t['final_cost'] or 0
            
            device = f"{t['device_brand']} {t['device_model']}" if t['device_brand'] else t['device_type']
            
            tree.insert("", "end", values=(
                t['ticket_number'], t['customer_name'], device,
                t['status'].replace('_', ' ').title(),
                f"Rs. {t['estimated_cost']:,.2f}",
                t['received_date'][:10] if t['received_date'] else 'N/A'
            ), tags=(str(t['ticket_id']),))
        
        window.summary_labels['received'].config(text=str(counts['received']))
        window.summary_labels['in_progress'].config(text=str(counts['in_progress']))
        window.summary_labels['completed'].config(text=str(counts['completed']))
        window.summary_labels['revenue'].config(text=f"Rs. {counts['revenue']:,.2f}")
    
    window.refresh = refresh
    refresh()
    
    return window


def open_service_ticket_dialog(parent, current_user=None):
    """Dialog to create a new service ticket."""
    dlg = tk.Toplevel(parent)
    dlg.title("New Service Ticket")
    dlg.geometry("600x650")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    styled_label(content, "🔧 New Service Ticket", font=FONT_HEADING).pack(anchor=tk.W, pady=(0, 15))
    
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    form_frame.grid_columnconfigure(1, weight=1)
    
    # Customer
    styled_label(form_frame, "Customer Name *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, pady=5)
    customer_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=customer_var, width=30).grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Phone
    styled_label(form_frame, "Phone:", font=FONT_BOLD).grid(row=2, column=0, sticky=tk.W, pady=5)
    phone_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=phone_var, width=30).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Email
    styled_label(form_frame, "Email:", font=FONT_BOLD).grid(row=4, column=0, sticky=tk.W, pady=5)
    email_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=email_var, width=30).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Device
    styled_label(form_frame, "Device Type:", font=FONT_BOLD).grid(row=6, column=0, sticky=tk.W, pady=5)
    device_type_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=device_type_var, width=30).grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    styled_label(form_frame, "Brand:", font=FONT_BOLD).grid(row=8, column=0, sticky=tk.W, pady=5)
    brand_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=brand_var, width=15).grid(row=9, column=0, sticky=tk.W, pady=5)
    
    styled_label(form_frame, "Model:", font=FONT_BOLD).grid(row=8, column=1, sticky=tk.W, pady=5)
    model_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=model_var, width=15).grid(row=9, column=1, sticky=tk.W, pady=5)
    
    # Serial
    styled_label(form_frame, "Serial Number:", font=FONT_BOLD).grid(row=10, column=0, sticky=tk.W, pady=5)
    serial_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=serial_var, width=30).grid(row=11, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Issue
    styled_label(form_frame, "Issue Description *:", font=FONT_BOLD).grid(row=12, column=0, sticky=tk.W, pady=5)
    issue_text = tk.Text(form_frame, height=3, width=40)
    issue_text.grid(row=13, column=0, columnspan=2, sticky=tk.EW, pady=5)
    
    # Estimated cost
    styled_label(form_frame, "Estimated Cost (Rs.):", font=FONT_BOLD).grid(row=14, column=0, sticky=tk.W, pady=5)
    cost_var = tk.StringVar(value="0")
    ttk.Entry(form_frame, textvariable=cost_var, width=15).grid(row=15, column=0, sticky=tk.W, pady=5)
    
    def save():
        customer = customer_var.get().strip()
        issue = issue_text.get("1.0", tk.END).strip()
        
        if not customer or not issue:
            messagebox.showerror("Error", "Customer name and issue description required")
            return
        
        ticket_number = f"SVC-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        try:
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO service_tickets 
                    (ticket_number, customer_name, customer_phone, customer_email,
                     device_type, device_brand, device_model, serial_number,
                     issue_description, estimated_cost, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'received', ?)
                """, (ticket_number, customer, phone_var.get(), email_var.get(),
                      device_type_var.get(), brand_var.get(), model_var.get(),
                      serial_var.get(), issue, float(cost_var.get()), current_user))
            
            messagebox.showinfo("Success", f"Service ticket created: {ticket_number}")
            dlg.destroy()
            if hasattr(parent, 'refresh'): parent.refresh()
        except Exception as e:
            logging.exception("Failed to create service ticket")
            messagebox.showerror("Error", f"Failed: {e}")
    
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    make_button(btn_frame, "💾 Create Ticket", command=save, kind="warning").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)
