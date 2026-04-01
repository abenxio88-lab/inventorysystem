"""
Supplier Management Module
===========================
Manage suppliers, contact info, and performance tracking.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

try:
    from .database import get_db_cursor, get_connection
    from .ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING


def create_suppliers_tab(parent, current_user=None):
    """
    Creates the suppliers management tab.
    """
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "🏭 Supplier Management", font=FONT_BOLD).pack(side=tk.LEFT)
    
    # Add Supplier button
    def open_add_supplier():
        open_supplier_dialog(window, current_user=current_user)
    
    make_button(header_frame, "➕ Add Supplier", command=open_add_supplier, kind="success").pack(side=tk.RIGHT)
    
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
    
    total_lbl = create_summary_card(summary_frame, "Total Suppliers", 0, 0)
    active_lbl = create_summary_card(summary_frame, "Active", 0, 1)
    rated_lbl = create_summary_card(summary_frame, "Rated 4+ ⭐", 0, 2)
    avg_lead_lbl = create_summary_card(summary_frame, "Avg Lead Time", "0 days", 3)
    
    window.summary_labels = {
        'total': total_lbl,
        'active': active_lbl,
        'rated': rated_lbl,
        'avg_lead': avg_lead_lbl
    }
    
    # Search/Filter toolbar
    toolbar_frame = ttk.Frame(window)
    toolbar_frame.pack(fill="x", pady=(0, 10))
    
    styled_label(toolbar_frame, "Search:").pack(side=tk.LEFT, padx=(0, 10))
    
    search_var = tk.StringVar()
    search_entry = ttk.Entry(toolbar_frame, textvariable=search_var, width=30)
    search_entry.pack(side=tk.LEFT, padx=5)
    
    def apply_search():
        refresh_suppliers()
    
    make_button(toolbar_frame, "🔍 Search", command=apply_search, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (search_var.set(""), refresh_suppliers()), kind="secondary").pack(side=tk.LEFT)
    
    # Suppliers table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("code", "name", "contact", "phone", "city", "rating", "lead_time", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    column_map = {
        "code": ("Code", 80),
        "name": ("Name", 200),
        "contact": ("Contact Person", 150),
        "phone": ("Phone", 120),
        "city": ("City", 100),
        "rating": ("Rating", 80),
        "lead_time": ("Lead Time", 90),
        "status": ("Status", 80)
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
    
    def on_edit():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a supplier to edit")
            return
        
        supplier_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if supplier_id:
            open_supplier_dialog(window, supplier_id=int(supplier_id), current_user=current_user)
    
    def on_view_products():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a supplier")
            return
        
        supplier_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if supplier_id:
            open_supplier_products(window, supplier_id=int(supplier_id))
    
    def on_toggle_status():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a supplier")
            return
        
        supplier_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if supplier_id and messagebox.askyesno("Confirm", "Toggle supplier status?"):
            with get_db_cursor() as cur:
                cur.execute("SELECT is_active FROM suppliers WHERE id = ?", (supplier_id,))
                row = cur.fetchone()
                if row:
                    new_status = 0 if row['is_active'] else 1
                    cur.execute("UPDATE suppliers SET is_active = ? WHERE id = ?", (new_status, supplier_id))
                    refresh_suppliers()
                    messagebox.showinfo("Success", "Supplier status updated")
    
    make_button(action_frame, "✏️ Edit", command=on_edit, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "📦 Products", command=on_view_products, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "🔄 Toggle Status", command=on_toggle_status, kind="warning").pack(side=tk.LEFT, padx=5)
    
    # Store state
    window.search_var = search_var
    window.tree = tree
    
    def refresh_suppliers():
        """Refresh suppliers list."""
        tree.delete(*tree.get_children())
        
        search_text = search_var.get().strip().lower()
        
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT id, code, name, contact_person, phone, city,
                       rating, lead_time_days, is_active
                FROM suppliers
                WHERE ? = '' OR name LIKE ? OR code LIKE ? OR contact_person LIKE ?
                ORDER BY name
            """, (search_text == '', f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
            
            suppliers = cur.fetchall()
        
        # Update summary
        total = len(suppliers)
        active = sum(1 for s in suppliers if s['is_active'])
        rated_4plus = sum(1 for s in suppliers if s['rating'] >= 4)
        
        # Calculate average lead time
        lead_times = [s['lead_time_days'] for s in suppliers if s['lead_time_days']]
        avg_lead = f"{sum(lead_times) // len(lead_times)} days" if lead_times else "N/A"
        
        window.summary_labels['total'].config(text=str(total))
        window.summary_labels['active'].config(text=str(active))
        window.summary_labels['rated'].config(text=str(rated_4plus))
        window.summary_labels['avg_lead'].config(text=avg_lead)
        
        # Populate table
        for supplier in suppliers:
            status_text = "✅ Active" if supplier['is_active'] else "❌ Inactive"
            rating_stars = "⭐" * int(supplier['rating']) if supplier['rating'] else "Not rated"
            tags = (str(supplier['id']),)
            
            tree.insert("", "end", values=(
                supplier['code'],
                supplier['name'],
                supplier['contact_person'] or 'N/A',
                supplier['phone'] or 'N/A',
                supplier['city'] or 'N/A',
                rating_stars,
                f"{supplier['lead_time_days']} days" if supplier['lead_time_days'] else 'N/A',
                status_text
            ), tags=tags)
    
    window.refresh_suppliers = refresh_suppliers
    refresh_suppliers()
    
    return window


def open_supplier_dialog(parent, supplier_id=None, current_user=None):
    """Open dialog to add/edit supplier."""
    is_edit = supplier_id is not None
    
    dlg = tk.Toplevel(parent)
    dlg.title("Edit Supplier" if is_edit else "Add Supplier")
    dlg.geometry("600x650")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    # Content
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Heading
    styled_label(content, "Supplier Details", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))
    
    # Form
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    
    form_frame.grid_columnconfigure(0, weight=1)
    form_frame.grid_columnconfigure(1, weight=1)
    
    # Form fields
    fields = {}
    
    def add_field(label_text, row, col, field_type="entry", **kwargs):
        styled_label(form_frame, label_text, font=("Segoe UI", 10, "bold")).grid(row=row, column=col, sticky=tk.W, pady=5)
        
        if field_type == "entry":
            var = tk.StringVar()
            entry = ttk.Entry(form_frame, textvariable=var)
            entry.grid(row=row+1, column=col, sticky=tk.EW, pady=3)
            fields[label_text] = var
            return var
        elif field_type == "combobox":
            var = tk.StringVar()
            combo = ttk.Combobox(form_frame, textvariable=var, **kwargs)
            combo.grid(row=row+1, column=col, sticky=tk.EW, pady=3)
            fields[label_text] = var
            return var
        elif field_type == "text":
            text = tk.Text(form_frame, height=3, **kwargs)
            text.grid(row=row+1, column=col, columnspan=2, sticky=tk.EW, pady=3)
            fields[label_text] = text
            return text
    
    # Supplier Code
    code_var = add_field("Supplier Code *", 0, 0)
    
    # Supplier Name
    name_var = add_field("Supplier Name *", 2, 0)
    
    # Contact Person
    contact_var = add_field("Contact Person", 4, 0)
    
    # Email
    email_var = add_field("Email", 6, 0)
    
    # Phone
    phone_var = add_field("Phone *", 8, 0)
    
    # Mobile
    mobile_var = add_field("Mobile", 10, 0)
    
    # Address
    address_text = add_field("Address", 0, 1, "text")
    
    # City
    city_var = add_field("City", 4, 1)
    
    # Country
    country_var = add_field("Country", 6, 1)
    country_var.set("Pakistan")
    
    # GST Number
    gst_var = add_field("GST/Tax ID", 8, 1)
    
    # Payment Terms
    payment_var = add_field("Payment Terms", 10, 1, "combobox", values=[
        "Net 15", "Net 30", "Net 45", "Net 60", "Net 90",
        "COD", "Advance", "50% Advance"
    ])
    payment_var.set("Net 30")
    
    # Lead Time
    lead_time_var = add_field("Lead Time (days)", 0, 2)
    
    # Rating
    rating_var = add_field("Rating (1-5)", 2, 2, "combobox", values=[
        "1 ⭐", "2 ⭐⭐", "3 ⭐⭐⭐", "4 ⭐⭐⭐⭐", "5 ⭐⭐⭐⭐⭐"
    ])
    
    # Notes
    notes_text = add_field("Notes", 4, 2, "text")
    
    # Load existing data if editing
    if is_edit:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT code, name, contact_person, email, phone, mobile,
                       address, city, country, gst_number, payment_terms,
                       lead_time_days, rating, notes
                FROM suppliers WHERE id = ?
            """, (supplier_id,))
            supplier = cur.fetchone()
            
            if supplier:
                code_var.set(supplier['code'])
                name_var.set(supplier['name'])
                contact_var.set(supplier['contact_person'] or '')
                email_var.set(supplier['email'] or '')
                phone_var.set(supplier['phone'] or '')
                mobile_var.set(supplier['mobile'] or '')
                address_text.insert("1.0", supplier['address'] or '')
                city_var.set(supplier['city'] or '')
                country_var.set(supplier['country'] or '')
                gst_var.set(supplier['gst_number'] or '')
                payment_var.set(supplier['payment_terms'] or 'Net 30')
                lead_time_var.set(str(supplier['lead_time_days']) if supplier['lead_time_days'] else '')
                rating_var.set(f"{supplier['rating']} {'⭐' * supplier['rating']}" if supplier['rating'] else '')
                notes_text.insert("1.0", supplier['notes'] or '')
    
    # Save button
    def save_supplier():
        code = code_var.get().strip()
        name = name_var.get().strip()
        contact = contact_var.get().strip()
        email = email_var.get().strip()
        phone = phone_var.get().strip()
        mobile = mobile_var.get().strip()
        address = address_text.get("1.0", tk.END).strip()
        city = city_var.get().strip()
        country = country_var.get().strip()
        gst = gst_var.get().strip()
        payment = payment_var.get().strip()
        lead_time = lead_time_var.get().strip()
        rating = rating_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()
        
        # Validation
        if not code:
            messagebox.showerror("Error", "Supplier code is required")
            return
        
        if not name:
            messagebox.showerror("Error", "Supplier name is required")
            return
        
        if not phone:
            messagebox.showerror("Error", "Phone number is required")
            return
        
        # Check for duplicate code
        if not is_edit:
            with get_db_cursor() as cur:
                cur.execute("SELECT id FROM suppliers WHERE code = ?", (code,))
                if cur.fetchone():
                    messagebox.showerror("Error", "Supplier code already exists")
                    return
        
        # Parse rating
        rating_val = None
        if rating:
            try:
                rating_val = int(rating[0])
            except:
                pass
        
        # Save
        try:
            with get_db_cursor() as cur:
                if is_edit:
                    cur.execute("""
                        UPDATE suppliers SET
                        code = ?, name = ?, contact_person = ?, email = ?,
                        phone = ?, mobile = ?, address = ?, city = ?,
                        country = ?, gst_number = ?, payment_terms = ?,
                        lead_time_days = ?, rating = ?, notes = ?
                        WHERE id = ?
                    """, (code, name, contact, email, phone, mobile, address, city,
                          country, gst, payment,
                          int(lead_time) if lead_time else None,
                          rating_val, notes, supplier_id))
                else:
                    cur.execute("""
                        INSERT INTO suppliers (code, name, contact_person, email, phone, mobile,
                                              address, city, country, gst_number, payment_terms,
                                              lead_time_days, rating, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, contact, email, phone, mobile, address, city,
                          country, gst, payment,
                          int(lead_time) if lead_time else None,
                          rating_val, notes))
            
            messagebox.showinfo("Success", "Supplier saved successfully")
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_suppliers'):
                parent.refresh_suppliers()
                
        except Exception as e:
            logging.exception("Failed to save supplier")
            messagebox.showerror("Error", f"Failed to save supplier: {e}")
    
    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    make_button(btn_frame, "💾 Save", command=save_supplier, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_supplier_products(parent, supplier_id):
    """View products from a supplier."""
    dlg = tk.Toplevel(parent)
    dlg.title("Supplier Products")
    dlg.geometry("700x500")
    dlg.transient(parent)
    dlg.grab_set()
    
    # Header
    header = ttk.Frame(dlg, padding=15)
    header.pack(fill=tk.X)
    
    with get_db_cursor() as cur:
        cur.execute("SELECT name, code FROM suppliers WHERE id = ?", (supplier_id,))
        supplier = cur.fetchone()
        styled_label(header, f"📦 Products from {supplier['name']}", font=FONT_BOLD).pack(anchor=tk.W)
    
    # Products table
    table_frame = make_card(dlg, padding=10)
    table_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("model", "category", "stock", "purchase_price", "selling_price")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').title())
        tree.column(col, width=120)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Load products
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT model, category, stock, purchase_price, selling_price
            FROM products
            WHERE supplier_id = ?
            ORDER BY model
        """, (supplier_id,))
        
        for row in cur.fetchall():
            tree.insert("", "end", values=(
                row['model'],
                row['category'],
                row['stock'],
                f"Rs. {row['purchase_price']:,.2f}",
                f"Rs. {row['selling_price']:,.2f}"
            ))
    
    # Close button with uniform styling
    make_button(dlg, text="Close", command=dlg.destroy, kind="secondary").pack(pady=10)


def get_suppliers_list():
    """Get list of all active suppliers."""
    with get_db_cursor() as cur:
        cur.execute("SELECT id, code, name FROM suppliers WHERE is_active = 1 ORDER BY name")
        return cur.fetchall()
