"""
Locations/Warehouse Management Module
======================================
Manage multiple warehouse/store locations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

try:
    from .database import get_db_cursor, get_connection
    from .ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER


def create_locations_tab(parent, current_user=None):
    """
    Creates the locations/warehouse management tab.
    """
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "🏢 Locations & Warehouses", font=FONT_BOLD).pack(side=tk.LEFT)
    
    # Add Location button
    def open_add_location():
        open_location_dialog(window, current_user=current_user)
    
    make_button(header_frame, "➕ Add Location", command=open_add_location, kind="success").pack(side=tk.RIGHT)
    
    # Summary cards
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))
    summary_frame.grid_columnconfigure((0, 1, 2), weight=1)
    
    def create_summary_card(parent, title, value, col):
        card = make_card(parent, padding=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        
        styled_label(card, text=title, font=("Segoe UI", 10), foreground="#6c757d").pack(anchor="w")
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 24, "bold"), foreground=COLOR_PRIMARY)
        value_label.pack(anchor="w", pady=(5, 0))
        
        return value_label
    
    total_lbl = create_summary_card(summary_frame, "Total Locations", 0, 0)
    active_lbl = create_summary_card(summary_frame, "Active", 0, 1)
    inactive_lbl = create_summary_card(summary_frame, "Inactive", 0, 2)
    
    window.summary_labels = {
        'total': total_lbl,
        'active': active_lbl,
        'inactive': inactive_lbl
    }
    
    # Search/Filter toolbar
    toolbar_frame = ttk.Frame(window)
    toolbar_frame.pack(fill="x", pady=(0, 10))
    
    styled_label(toolbar_frame, "Search:").pack(side=tk.LEFT, padx=(0, 10))
    
    search_var = tk.StringVar()
    search_entry = ttk.Entry(toolbar_frame, textvariable=search_var, width=30)
    search_entry.pack(side=tk.LEFT, padx=5)
    
    def apply_search():
        refresh_locations()
    
    make_button(toolbar_frame, "🔍 Search", command=apply_search, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (search_var.set(""), refresh_locations()), kind="secondary").pack(side=tk.LEFT)
    
    # Locations table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("code", "name", "type", "city", "manager", "status", "capacity")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    column_map = {
        "code": ("Code", 100),
        "name": ("Name", 200),
        "type": ("Type", 100),
        "city": ("City", 120),
        "manager": ("Manager", 150),
        "status": ("Status", 80),
        "capacity": ("Capacity", 100)
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
            messagebox.showinfo("Select", "Please select a location to edit")
            return
        
        item = tree.item(sel[0])
        location_id = item['tags'][0] if item['tags'] else None
        
        if location_id:
            open_location_dialog(window, location_id=int(location_id), current_user=current_user)
    
    def on_toggle_status():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a location")
            return
        
        location_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if location_id and messagebox.askyesno("Confirm", "Toggle location status?"):
            with get_db_cursor() as cur:
                cur.execute("SELECT is_active FROM locations WHERE id = ?", (location_id,))
                row = cur.fetchone()
                if row:
                    new_status = 0 if row['is_active'] else 1
                    cur.execute("UPDATE locations SET is_active = ? WHERE id = ?", (new_status, location_id))
                    refresh_locations()
                    messagebox.showinfo("Success", "Location status updated")
    
    def on_view_stock():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a location")
            return
        
        location_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if location_id:
            open_location_stock_viewer(window, location_id=int(location_id))
    
    make_button(action_frame, "✏️ Edit", command=on_edit, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "📊 View Stock", command=on_view_stock, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "🔄 Toggle Status", command=on_toggle_status, kind="warning").pack(side=tk.LEFT, padx=5)
    
    # Store state
    window.search_var = search_var
    window.tree = tree
    
    def refresh_locations():
        """Refresh locations list."""
        tree.delete(*tree.get_children())
        
        search_text = search_var.get().strip().lower()
        
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT l.id, l.code, l.name, l.type, l.city, l.country,
                       l.is_active, l.capacity,
                       u.full_name as manager_name
                FROM locations l
                LEFT JOIN users u ON l.manager_id = u.id
                WHERE ? = '' OR l.name LIKE ? OR l.code LIKE ? OR l.city LIKE ?
            """, (search_text == '', f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
            
            locations = cur.fetchall()
        
        # Update summary
        total = len(locations)
        active = sum(1 for loc in locations if loc['is_active'])
        inactive = total - active
        
        window.summary_labels['total'].config(text=str(total))
        window.summary_labels['active'].config(text=str(active))
        window.summary_labels['inactive'].config(text=str(inactive))
        
        # Populate table
        for loc in locations:
            status_text = "✅ Active" if loc['is_active'] else "❌ Inactive"
            tags = (str(loc['id']),)
            
            tree.insert("", "end", values=(
                loc['code'],
                loc['name'],
                loc['type'].title(),
                loc['city'] or 'N/A',
                loc['manager_name'] or 'Unassigned',
                status_text,
                loc['capacity'] if loc['capacity'] else 'Unlimited'
            ), tags=tags)
    
    window.refresh_locations = refresh_locations
    refresh_locations()
    
    return window


def open_location_dialog(parent, location_id=None, current_user=None):
    """Open dialog to add/edit location."""
    is_edit = location_id is not None
    
    dlg = tk.Toplevel(parent)
    dlg.title("Edit Location" if is_edit else "Add Location")
    dlg.geometry("500x550")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    # Content frame
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Heading
    styled_label(content, "Location Details", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))
    
    # Form
    form_frame = make_card(content, padding=20)
    form_frame.pack(fill=tk.BOTH, expand=True)
    
    # Form fields
    fields = {}
    
    def add_field(label_text, row, field_type="entry", **kwargs):
        styled_label(form_frame, label_text, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky=tk.W, pady=5)
        
        if field_type == "entry":
            var = tk.StringVar()
            entry = ttk.Entry(form_frame, textvariable=var)
            entry.grid(row=row+1, column=0, columnspan=2, sticky=tk.EW, pady=3)
            fields[label_text] = var
            return var
        elif field_type == "combobox":
            var = tk.StringVar()
            combo = ttk.Combobox(form_frame, textvariable=var, **kwargs)
            combo.grid(row=row+1, column=0, columnspan=2, sticky=tk.EW, pady=3)
            fields[label_text] = var
            return var
        elif field_type == "text":
            text = tk.Text(form_frame, height=4, **kwargs)
            text.grid(row=row+1, column=0, columnspan=2, sticky=tk.EW, pady=3)
            fields[label_text] = text
            return text
    
    form_frame.grid_columnconfigure(0, weight=1)
    
    # Location Code
    code_var = add_field("Location Code *", 0)
    
    # Location Name
    name_var = add_field("Location Name *", 2)
    
    # Location Type
    type_var = add_field("Type", 4, "combobox", values=["Warehouse", "Store", "Shop", "Office", "Other"])
    type_var.set("Warehouse")
    
    # Address
    address_text = add_field("Address", 6, "text")
    
    # City
    city_var = add_field("City", 8)
    
    # Country
    country_var = add_field("Country", 10)
    country_var.set("Pakistan")
    
    # Phone
    phone_var = add_field("Phone", 12)
    
    # Email
    email_var = add_field("Email", 14)
    
    # Capacity
    capacity_var = add_field("Capacity (optional)", 16)
    
    # Manager
    manager_var = add_field("Manager (User ID)", 18)
    
    # Load existing data if editing
    if is_edit:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT code, name, type, address, city, country, phone, email, capacity, manager_id
                FROM locations WHERE id = ?
            """, (location_id,))
            loc = cur.fetchone()
            
            if loc:
                code_var.set(loc['code'])
                name_var.set(loc['name'])
                type_var.set(loc['type'])
                address_text.insert("1.0", loc['address'] or '')
                city_var.set(loc['city'] or '')
                country_var.set(loc['country'] or '')
                phone_var.set(loc['phone'] or '')
                email_var.set(loc['email'] or '')
                capacity_var.set(str(loc['capacity']) if loc['capacity'] else '')
                manager_var.set(str(loc['manager_id']) if loc['manager_id'] else '')
    
    # Save button
    def save_location():
        code = code_var.get().strip()
        name = name_var.get().strip()
        loc_type = type_var.get().strip()
        address = address_text.get("1.0", tk.END).strip()
        city = city_var.get().strip()
        country = country_var.get().strip()
        phone = phone_var.get().strip()
        email = email_var.get().strip()
        capacity = capacity_var.get().strip()
        manager_id = manager_var.get().strip()
        
        # Validation
        if not code:
            messagebox.showerror("Error", "Location code is required")
            return
        
        if not name:
            messagebox.showerror("Error", "Location name is required")
            return
        
        # Check for duplicate code (when adding)
        if not is_edit:
            with get_db_cursor() as cur:
                cur.execute("SELECT id FROM locations WHERE code = ?", (code,))
                if cur.fetchone():
                    messagebox.showerror("Error", "Location code already exists")
                    return
        
        # Save
        try:
            with get_db_cursor() as cur:
                if is_edit:
                    cur.execute("""
                        UPDATE locations SET
                        code = ?, name = ?, type = ?, address = ?, city = ?,
                        country = ?, phone = ?, email = ?, capacity = ?, manager_id = ?
                        WHERE id = ?
                    """, (code, name, loc_type, address, city, country, phone, email,
                          int(capacity) if capacity else None,
                          int(manager_id) if manager_id else None,
                          location_id))
                else:
                    cur.execute("""
                        INSERT INTO locations (code, name, type, address, city, country, phone, email, capacity, manager_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, loc_type, address, city, country, phone, email,
                          int(capacity) if capacity else None,
                          int(manager_id) if manager_id else None))
            
            messagebox.showinfo("Success", "Location saved successfully")
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_locations'):
                parent.refresh_locations()
                
        except Exception as e:
            logging.exception("Failed to save location")
            messagebox.showerror("Error", f"Failed to save location: {e}")
    
    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    make_button(btn_frame, "💾 Save", command=save_location, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_location_stock_viewer(parent, location_id):
    """View stock levels at a specific location."""
    dlg = tk.Toplevel(parent)
    dlg.title("Location Stock Levels")
    dlg.geometry("800x500")
    dlg.transient(parent)
    dlg.grab_set()
    
    # Header
    header = ttk.Frame(dlg, padding=15)
    header.pack(fill=tk.X)
    
    with get_db_cursor() as cur:
        cur.execute("SELECT name, code FROM locations WHERE id = ?", (location_id,))
        loc = cur.fetchone()
        styled_label(header, f"📦 Stock at {loc['name']} ({loc['code']})", font=FONT_BOLD).pack(anchor=tk.W)
    
    # Stock table
    table_frame = make_card(dlg, padding=10)
    table_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("sku", "model", "quantity", "reserved", "available", "rack")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    column_map = {
        "sku": ("SKU", 120),
        "model": ("Model", 250),
        "quantity": ("Quantity", 100),
        "reserved": ("Reserved", 100),
        "available": ("Available", 100),
        "rack": ("Rack", 100)
    }
    
    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text)
        tree.column(col, width=width, anchor="w")
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Load stock data
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.sku, p.model, ps.quantity, ps.reserved, ps.available,
                   p.rack_location, p.shelf_location
            FROM product_stock ps
            JOIN products p ON ps.product_id = p.id
            WHERE ps.location_id = ?
            ORDER BY p.model
        """, (location_id,))
        
        for row in cur.fetchall():
            tree.insert("", "end", values=(
                row['sku'] or 'N/A',
                row['model'],
                row['quantity'],
                row['reserved'] or 0,
                row['available'],
                row['rack_location'] or 'N/A'
            ))
    
    # Close button
    ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=10)


def get_locations_list():
    """Get list of all active locations."""
    with get_db_cursor() as cur:
        cur.execute("SELECT id, code, name FROM locations WHERE is_active = 1 ORDER BY name")
        return cur.fetchall()
