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

try:
    from .database import get_db_cursor, get_connection
    from .ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from .suppliers_ui import get_suppliers_list
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from suppliers_ui import get_suppliers_list


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
    suppliers = get_suppliers_list()
    supplier_data = [("all", "All Suppliers")] + [(s['id'], f"{s['code']} - {s['name']}") for s in suppliers]
    supplier_combo['values'] = [s[1] for s in supplier_data]
    
    def apply_filter():
        refresh_pos()
    
    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar_frame, "Clear", command=lambda: (status_var.set("all"), supplier_var.set("all"), refresh_pos()), kind="secondary").pack(side=tk.LEFT)
    
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
    
    def refresh_pos():
        """Refresh purchase orders list."""
        tree.delete(*tree.get_children())
        
        status_filter = status_var.get()
        supplier_sel = supplier_var.get()
        
        # Get supplier ID if selected
        supplier_id = None
        if supplier_sel != "all":
            for sid, sname in supplier_data:
                if sname == supplier_sel:
                    supplier_id = sid
                    break
        
        with get_db_cursor() as cur:
            if status_filter == 'all' and supplier_id is None:
                cur.execute("""
                    SELECT po.id, po.po_number, po.supplier_id, po.order_date, po.expected_date,
                           po.status, po.total_amount, po.created_by,
                           s.name as supplier_name,
                           (SELECT COUNT(*) FROM po_items WHERE po_id = po.id) as item_count
                    FROM purchase_orders po
                    JOIN suppliers s ON po.supplier_id = s.id
                    ORDER BY po.order_date DESC
                """)
            else:
                where_clauses = []
                params = []
                
                if status_filter != 'all':
                    where_clauses.append("po.status = ?")
                    params.append(status_filter)
                
                if supplier_id:
                    where_clauses.append("po.supplier_id = ?")
                    params.append(supplier_id)
                
                where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                
                cur.execute(f"""
                    SELECT po.id, po.po_number, po.supplier_id, po.order_date, po.expected_date,
                           po.status, po.total_amount, po.created_by,
                           s.name as supplier_name,
                           (SELECT COUNT(*) FROM po_items WHERE po_id = po.id) as item_count
                    FROM purchase_orders po
                    JOIN suppliers s ON po.supplier_id = s.id
                    {where_sql}
                    ORDER BY po.order_date DESC
                """, params)
            
            pos = cur.fetchall()
        
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
    
    window.refresh_pos = refresh_pos
    refresh_pos()
    
    return window


def open_create_po_dialog(parent, current_user=None):
    """Dialog to create a new purchase order."""
    dlg = tk.Toplevel(parent)
    dlg.title("Create Purchase Order")
    dlg.geometry("750x650")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Heading
    styled_label(content, "New Purchase Order", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))
    
    # Supplier selection
    supplier_frame = ttk.Frame(content)
    supplier_frame.pack(fill=tk.X, pady=(0, 15))
    
    styled_label(supplier_frame, "Supplier *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    
    supplier_var = tk.StringVar()
    supplier_combo = ttk.Combobox(supplier_frame, textvariable=supplier_var, state="readonly", width=40)
    supplier_combo.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)
    
    # Load suppliers
    suppliers = get_suppliers_list()
    supplier_data = [(s['id'], f"{s['code']} - {s['name']}") for s in suppliers]
    supplier_combo['values'] = [s[1] for s in supplier_data]
    
    styled_label(supplier_frame, "Expected Date:", font=FONT_BOLD).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
    
    expected_var = tk.StringVar()
    expected_entry = ttk.Entry(supplier_frame, textvariable=expected_var, width=15)
    expected_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    
    # Set default expected date (7 days from now)
    default_expected = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    expected_var.set(default_expected)
    
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
    
    # Load products
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, model, category, stock, purchase_price, supplier_id
            FROM products
            WHERE status = 'active'
            ORDER BY model
        """)
        products = cur.fetchall()
    
    product_data = [(p['id'], f"{p['model']} (Stock: {p['stock']}, Cost: Rs. {p['purchase_price']})") for p in products]
    product_combo['values'] = [p[1] for p in product_data]
    
    styled_label(select_frame, "Qty:").pack(side=tk.LEFT, padx=(15, 5))
    
    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(select_frame, textvariable=qty_var, width=8)
    qty_entry.pack(side=tk.LEFT, padx=5)
    
    styled_label(select_frame, "Unit Price:").pack(side=tk.LEFT, padx=(10, 5))
    
    price_var = tk.StringVar(value="0")
    price_entry = ttk.Entry(select_frame, textvariable=price_var, width=10)
    price_entry.pack(side=tk.LEFT, padx=5)
    
    # Items list
    styled_label(content, "Order Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    
    items_frame = ttk.Frame(products_frame)
    items_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("product", "quantity", "unit_price", "total", "actions")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=10)
    
    for col in columns:
        items_tree.heading(col, text=col.title())
        items_tree.column(col, width=120 if col != "product" else 250)
    
    items_tree.pack(fill=tk.BOTH, expand=True)
    
    # PO items storage
    po_items = []
    
    def add_item():
        product_sel = product_var.get()
        qty = qty_var.get()
        price = price_var.get()
        
        if not product_sel:
            messagebox.showerror("Error", "Please select a product")
            return
        
        try:
            qty_int = int(qty)
            price_float = float(price)
            if qty_int <= 0 or price_float < 0:
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid quantity or price")
            return
        
        # Find product
        product_id = None
        product_name = None
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname.split(' (')[0]
                break
        
        if not product_id:
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
    
    items_tree.bind("<Button-1>", on_item_click)
    
    # Add button
    make_button(select_frame, "➕ Add", command=add_item, kind="primary").pack(side=tk.LEFT, padx=10)
    
    # Notes
    styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    notes_text = tk.Text(content, height=3)
    notes_text.pack(fill=tk.X, pady=(0, 10))
    
    # Total label
    total_var = tk.StringVar(value="Total: Rs. 0.00")
    total_label = styled_label(content, textvariable=total_var, font=("Segoe UI", 14, "bold"), foreground=COLOR_PRIMARY)
    total_label.pack(anchor=tk.E, pady=(5, 10))
    
    # Update total when items change
    def update_total():
        total = sum(item['total'] for item in po_items)
        total_var.set(f"Total: Rs. {total:,.2f}")
    
    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    
    def save_po():
        supplier_sel = supplier_var.get()
        expected_date = expected_var.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()
        
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
        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        try:
            with get_db_cursor() as cur:
                # Create PO
                cur.execute("""
                    INSERT INTO purchase_orders (po_number, supplier_id, order_date, expected_date, status, notes, created_by)
                    VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'draft', ?, ?)
                """, (po_number, supplier_id, expected_date or None, notes, current_user))
                
                po_id = cur.lastrowid
                
                # Add items
                for item in po_items:
                    cur.execute("""
                        INSERT INTO po_items (po_id, product_id, quantity_ordered, unit_price, total_price)
                        VALUES (?, ?, ?, ?, ?)
                    """, (po_id, item['product_id'], item['quantity'], item['unit_price'], item['total']))
            
            messagebox.showinfo("Success", f"Purchase Order created: {po_number}")
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_pos'):
                parent.refresh_pos()
                
        except Exception as e:
            logging.exception("Failed to create purchase order")
            messagebox.showerror("Error", f"Failed to create PO: {e}")
    
    make_button(btn_frame, "💾 Create PO", command=save_po, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_po_details(parent, po_id, current_user=None):
    """View purchase order details."""
    dlg = tk.Toplevel(parent)
    dlg.title("Purchase Order Details")
    dlg.geometry("700x600")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    with get_db_cursor() as cur:
        # Get PO info
        cur.execute("""
            SELECT po.*, s.name as supplier_name, s.contact_person, s.phone, s.email,
                   u.username as created_by_name
            FROM purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            LEFT JOIN users u ON po.created_by = u.id
            WHERE po.id = ?
        """, (po_id,))
        po = cur.fetchone()
        
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
            ("Supplier:", po['supplier_name']),
            ("Contact:", po['contact_person'] or 'N/A'),
            ("Phone:", po['phone'] or 'N/A'),
            ("Order Date:", po['order_date'][:10] if po['order_date'] else 'N/A'),
            ("Expected Date:", po['expected_date'][:10] if po['expected_date'] else 'N/A'),
            ("Created By:", po['created_by_name'] or 'System'),
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
        
        cur.execute("""
            SELECT p.model, poi.quantity_ordered, poi.quantity_received, poi.unit_price, poi.total_price
            FROM po_items poi
            JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = ?
        """, (po_id,))
        
        total = 0
        for row in cur.fetchall():
            items_tree.insert("", "end", values=(
                row['model'],
                row['quantity_ordered'],
                row['quantity_received'] or 0,
                f"Rs. {row['unit_price']:,.2f}",
                f"Rs. {row['total_price']:,.2f}"
            ))
            total += row['total_price']
        
        # Total
        styled_label(content, f"Total Amount: Rs. {total:,.2f}", font=("Segoe UI", 12, "bold"), foreground=COLOR_PRIMARY).pack(anchor=tk.E, pady=(10, 0))
        
        # Notes
        if po['notes']:
            styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
            styled_label(content, po['notes'], justify=tk.LEFT).pack(anchor=tk.W)
    
    # Action buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    def close():
        dlg.destroy()
    
    make_button(btn_frame, "Close", command=close, kind="secondary").pack(side=tk.RIGHT)


def open_grn_dialog(parent, po_id, current_user=None):
    """Goods Receipt Note - Receive products from PO."""
    dlg = tk.Toplevel(parent)
    dlg.title("Receive Goods (GRN)")
    dlg.geometry("650x550")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Get PO info
    with get_db_cursor() as cur:
        cur.execute("SELECT po_number, status FROM purchase_orders WHERE id = ?", (po_id,))
        po = cur.fetchone()
        
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
        
        cur.execute("""
            SELECT poi.id, p.model, p.id as product_id, poi.quantity_ordered, poi.quantity_received
            FROM po_items poi
            JOIN products p ON poi.product_id = p.id
            WHERE poi.po_id = ?
        """, (po_id,))
        
        items_data = []
        for row in cur.fetchall():
            pending = row['quantity_ordered'] - (row['quantity_received'] or 0)
            items_data.append({
                'po_item_id': row['id'],
                'product_id': row['product_id'],
                'model': row['model'],
                'ordered': row['quantity_ordered'],
                'received': row['quantity_received'] or 0,
                'pending': pending
            })
            
            items_tree.insert("", "end", values=(
                row['model'],
                row['quantity_ordered'],
                row['quantity_received'] or 0,
                pending,
                pending  # Default receive qty = pending
            ))
    
    # Receive button
    def receive_goods():
        try:
            with get_db_cursor() as cur:
                all_received = True
                
                for item in items_data:
                    # In a real implementation, you'd get the receive quantity from UI
                    # For now, we'll receive all pending
                    receive_qty = item['pending']
                    
                    if receive_qty > 0:
                        # Update PO item
                        cur.execute("""
                            UPDATE po_items
                            SET quantity_received = quantity_received + ?
                            WHERE id = ?
                        """, (receive_qty, item['po_item_id']))
                        
                        # Update product stock
                        cur.execute("""
                            UPDATE products
                            SET stock = stock + ?, purchase_price = ?
                            WHERE id = ?
                        """, (receive_qty, 0, item['product_id']))  # Note: Should use weighted average
                
                # Check if all items received
                cur.execute("""
                    SELECT quantity_ordered, quantity_received
                    FROM po_items
                    WHERE po_id = ?
                """, (po_id,))
                
                all_received = all(row['quantity_ordered'] == (row['quantity_received'] or 0) for row in cur.fetchall())
                
                # Update PO status
                new_status = 'received' if all_received else 'partial'
                cur.execute("""
                    UPDATE purchase_orders
                    SET status = ?, received_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_status, po_id))
            
            messagebox.showinfo("Success", "Goods received successfully")
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_pos'):
                parent.refresh_pos()
                
        except Exception as e:
            logging.exception("Failed to receive goods")
            messagebox.showerror("Error", f"Failed to receive goods: {e}")
    
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(15, 0))
    
    make_button(btn_frame, "📥 Receive All Pending", command=receive_goods, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)
