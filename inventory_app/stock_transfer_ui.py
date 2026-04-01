"""
Stock Transfer Module
======================
Transfer inventory between locations/warehouses.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

try:
    from .database import get_db_cursor, get_connection
    from .ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from .locations_ui import get_locations_list
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor, get_connection
    from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from locations_ui import get_locations_list


def create_stock_transfers_tab(parent, current_user=None):
    """
    Creates the stock transfers management tab.
    """
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "🔄 Stock Transfers", font=FONT_BOLD).pack(side=tk.LEFT)
    
    # New Transfer button
    def open_new_transfer():
        open_transfer_dialog(window, current_user=current_user)
    
    make_button(header_frame, "➕ New Transfer", command=open_new_transfer, kind="success").pack(side=tk.RIGHT)
    
    # Filter toolbar
    toolbar_frame = ttk.Frame(window)
    toolbar_frame.pack(fill="x", pady=(0, 10))
    
    styled_label(toolbar_frame, "Status:").pack(side=tk.LEFT, padx=(0, 10))
    
    status_var = tk.StringVar(value="all")
    status_combo = ttk.Combobox(
        toolbar_frame,
        textvariable=status_var,
        values=["all", "pending", "in_transit", "completed", "cancelled"],
        state="readonly",
        width=15
    )
    status_combo.pack(side=tk.LEFT)
    
    def apply_filter():
        refresh_transfers()
    
    make_button(toolbar_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    
    # Transfers table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("transfer_number", "from_location", "to_location", "date", "status", "items", "created_by")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    column_map = {
        "transfer_number": ("Transfer #", 120),
        "from_location": ("From", 150),
        "to_location": ("To", 150),
        "date": ("Date", 120),
        "status": ("Status", 100),
        "items": ("Items", 80),
        "created_by": ("Created By", 120)
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
            messagebox.showinfo("Select", "Please select a transfer")
            return
        
        transfer_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if transfer_id:
            open_transfer_details(window, transfer_id=int(transfer_id))
    
    def on_complete_transfer():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select a transfer")
            return
        
        transfer_id = tree.item(sel[0], 'tags')[0] if tree.item(sel[0], 'tags') else None
        
        if transfer_id and messagebox.askyesno("Confirm", "Mark this transfer as completed?"):
            complete_transfer(int(transfer_id))
            refresh_transfers()
    
    make_button(action_frame, "👁️ View Details", command=on_view_details, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_frame, "✅ Complete", command=on_complete_transfer, kind="success").pack(side=tk.LEFT, padx=5)
    
    # Store state
    window.status_var = status_var
    window.tree = tree
    
    def refresh_transfers():
        """Refresh transfers list."""
        tree.delete(*tree.get_children())
        
        status_filter = status_var.get()
        
        with get_db_cursor() as cur:
            if status_filter == 'all':
                cur.execute("""
                    SELECT st.id, st.transfer_number, st.from_location_id, st.to_location_id,
                           st.transfer_date, st.status, st.created_by,
                           l1.name as from_name, l2.name as to_name,
                           u.username as created_by_name,
                           (SELECT COUNT(*) FROM stock_transfer_items WHERE transfer_id = st.id) as item_count
                    FROM stock_transfers st
                    JOIN locations l1 ON st.from_location_id = l1.id
                    JOIN locations l2 ON st.to_location_id = l2.id
                    LEFT JOIN users u ON st.created_by = u.id
                    ORDER BY st.transfer_date DESC
                """)
            else:
                cur.execute("""
                    SELECT st.id, st.transfer_number, st.from_location_id, st.to_location_id,
                           st.transfer_date, st.status, st.created_by,
                           l1.name as from_name, l2.name as to_name,
                           u.username as created_by_name,
                           (SELECT COUNT(*) FROM stock_transfer_items WHERE transfer_id = st.id) as item_count
                    FROM stock_transfers st
                    JOIN locations l1 ON st.from_location_id = l1.id
                    JOIN locations l2 ON st.to_location_id = l2.id
                    LEFT JOIN users u ON st.created_by = u.id
                    WHERE st.status = ?
                    ORDER BY st.transfer_date DESC
                """, (status_filter,))
            
            transfers = cur.fetchall()
        
        status_colors = {
            'pending': COLOR_WARNING,
            'in_transit': COLOR_PRIMARY,
            'completed': COLOR_SUCCESS,
            'cancelled': COLOR_DANGER
        }
        
        for transfer in transfers:
            status_text = transfer['status'].replace('_', ' ').title()
            tags = (str(transfer['id']),)
            
            tree.insert("", "end", values=(
                transfer['transfer_number'],
                transfer['from_name'],
                transfer['to_name'],
                transfer['transfer_date'][:16] if transfer['transfer_date'] else '',
                status_text,
                transfer['item_count'],
                transfer['created_by_name'] or 'System'
            ), tags=tags)
    
    window.refresh_transfers = refresh_transfers
    refresh_transfers()
    
    return window


def open_transfer_dialog(parent, current_user=None):
    """Open dialog to create a new stock transfer."""
    dlg = tk.Toplevel(parent)
    dlg.title("New Stock Transfer")
    dlg.geometry("700x600")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()
    
    # Content
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Heading
    styled_label(content, "Create Stock Transfer", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))
    
    # From/To locations
    loc_frame = ttk.Frame(content)
    loc_frame.pack(fill=tk.X, pady=(0, 15))
    loc_frame.grid_columnconfigure(1, weight=1)
    
    styled_label(loc_frame, "From Location *:", font=FONT_BOLD).grid(row=0, column=0, sticky=tk.W, padx=5)
    from_var = tk.StringVar()
    from_combo = ttk.Combobox(loc_frame, textvariable=from_var, state="readonly", width=30)
    from_combo.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)
    
    styled_label(loc_frame, "To Location *:", font=FONT_BOLD).grid(row=0, column=1, sticky=tk.W, padx=5)
    to_var = tk.StringVar()
    to_combo = ttk.Combobox(loc_frame, textvariable=to_var, state="readonly", width=30)
    to_combo.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
    
    # Load locations
    locations = get_locations_list()
    loc_data = [(loc['id'], f"{loc['code']} - {loc['name']}") for loc in locations]
    from_combo['values'] = [loc[1] for loc in loc_data]
    to_combo['values'] = [loc[1] for loc in loc_data]
    
    # Products list
    styled_label(content, "Products to Transfer:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    
    products_frame = make_card(content, padding=10)
    products_frame.pack(fill=tk.BOTH, expand=True)
    
    # Product selection
    select_frame = ttk.Frame(products_frame)
    select_frame.pack(fill=tk.X, pady=(0, 10))
    
    styled_label(select_frame, "Product:").pack(side=tk.LEFT, padx=5)
    
    product_var = tk.StringVar()
    product_combo = ttk.Combobox(select_frame, textvariable=product_var, state="readonly", width=40)
    product_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # Load products with stock
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT p.id, p.sku, p.model, p.stock
            FROM products p
            WHERE p.stock > 0 AND p.status = 'active'
            ORDER BY p.model
        """)
        products = cur.fetchall()
    
    product_data = [(p['id'], f"{p['model']} (Stock: {p['stock']})") for p in products]
    product_combo['values'] = [p[1] for p in product_data]
    
    styled_label(select_frame, "Qty:").pack(side=tk.LEFT, padx=(15, 5))
    
    qty_var = tk.StringVar(value="1")
    qty_entry = ttk.Entry(select_frame, textvariable=qty_var, width=8)
    qty_entry.pack(side=tk.LEFT, padx=5)
    
    # Items list
    styled_label(content, "Transfer Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    
    items_frame = ttk.Frame(products_frame)
    items_frame.pack(fill=tk.BOTH, expand=True)
    
    columns = ("product", "quantity", "actions")
    items_tree = ttk.Treeview(items_frame, columns=columns, show="headings", height=8)
    items_tree.heading("product", text="Product")
    items_tree.heading("quantity", text="Quantity")
    items_tree.heading("actions", text="Actions")
    items_tree.column("product", width=300)
    items_tree.column("quantity", width=100, anchor="center")
    items_tree.column("actions", width=100, anchor="center")
    
    items_tree.pack(fill=tk.BOTH, expand=True)
    
    # Transfer items storage
    transfer_items = []
    
    def add_item():
        product_sel = product_var.get()
        qty = qty_var.get()
        
        if not product_sel:
            messagebox.showerror("Error", "Please select a product")
            return
        
        try:
            qty_int = int(qty)
            if qty_int <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Error", "Invalid quantity")
            return
        
        # Find product ID
        product_id = None
        product_name = None
        for pid, pname in product_data:
            if pname.startswith(product_sel.split(' (')[0]):
                product_id = pid
                product_name = pname
                break
        
        if not product_id:
            return
        
        # Add to list
        transfer_items.append({
            'product_id': product_id,
            'product_name': product_name,
            'quantity': qty_int
        })
        
        # Update tree
        items_tree.insert("", "end", values=(
            product_name,
            qty_int,
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
        if item['values'][2] == "🗑️ Remove":
            index = items_tree.index(sel[0])
            if 0 <= index < len(transfer_items):
                transfer_items.pop(index)
                items_tree.delete(sel[0])
    
    items_tree.bind("<Button-1>", on_item_click)
    
    # Add button
    make_button(select_frame, "➕ Add", command=add_item, kind="primary").pack(side=tk.LEFT, padx=10)
    
    # Notes
    styled_label(content, "Notes:", font=FONT_BOLD).pack(anchor=tk.W, pady=(10, 5))
    notes_text = tk.Text(content, height=3)
    notes_text.pack(fill=tk.X, pady=(0, 10))
    
    # Buttons
    btn_frame = ttk.Frame(content)
    btn_frame.pack(fill=tk.X, pady=(10, 0))
    
    def save_transfer():
        from_loc = from_var.get()
        to_loc = to_var.get()
        
        if not from_loc or not to_loc:
            messagebox.showerror("Error", "Please select both locations")
            return
        
        if from_loc == to_loc:
            messagebox.showerror("Error", "From and To locations must be different")
            return
        
        if not transfer_items:
            messagebox.showerror("Error", "Please add at least one product")
            return
        
        # Get location IDs
        from_id = None
        to_id = None
        for loc in locations:
            if f"{loc['code']} - {loc['name']}" == from_loc:
                from_id = loc['id']
            if f"{loc['code']} - {loc['name']}" == to_loc:
                to_id = loc['id']
        
        # Generate transfer number
        transfer_number = f"TRF-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        try:
            with get_db_cursor() as cur:
                # Create transfer
                cur.execute("""
                    INSERT INTO stock_transfers (transfer_number, from_location_id, to_location_id, status, notes, created_by)
                    VALUES (?, ?, ?, 'pending', ?, ?)
                """, (transfer_number, from_id, to_id, notes_text.get("1.0", tk.END).strip(), current_user))
                
                transfer_id = cur.lastrowid
                
                # Add items
                for item in transfer_items:
                    cur.execute("""
                        INSERT INTO stock_transfer_items (transfer_id, product_id, quantity)
                        VALUES (?, ?, ?)
                    """, (transfer_id, item['product_id'], item['quantity']))
            
            messagebox.showinfo("Success", f"Transfer created: {transfer_number}")
            dlg.destroy()
            
            # Refresh parent
            if hasattr(parent, 'refresh_transfers'):
                parent.refresh_transfers()
                
        except Exception as e:
            logging.exception("Failed to create transfer")
            messagebox.showerror("Error", f"Failed to create transfer: {e}")
    
    make_button(btn_frame, "💾 Create Transfer", command=save_transfer, kind="success").pack(side=tk.LEFT, padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side=tk.LEFT, padx=5)


def open_transfer_details(parent, transfer_id):
    """View transfer details."""
    dlg = tk.Toplevel(parent)
    dlg.title("Transfer Details")
    dlg.geometry("600x500")
    dlg.transient(parent)
    dlg.grab_set()
    
    content = ttk.Frame(dlg, padding=20)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Get transfer info
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT st.*, l1.name as from_name, l2.name as to_name,
                   u.username as created_by
            FROM stock_transfers st
            JOIN locations l1 ON st.from_location_id = l1.id
            JOIN locations l2 ON st.to_location_id = l2.id
            LEFT JOIN users u ON st.created_by = u.id
            WHERE st.id = ?
        """, (transfer_id,))
        transfer = cur.fetchone()
        
        # Header
        styled_label(content, f"Transfer: {transfer['transfer_number']}", font=FONT_BOLD).pack(anchor=tk.W)
        styled_label(content, f"Status: {transfer['status'].title()}", foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(5, 15))
        
        # Info
        info_frame = make_card(content, padding=15)
        info_frame.pack(fill=tk.X)
        
        info = [
            ("From:", transfer['from_name']),
            ("To:", transfer['to_name']),
            ("Date:", transfer['transfer_date'][:16] if transfer['transfer_date'] else 'N/A'),
            ("Created By:", transfer['created_by'] or 'System'),
            ("Notes:", transfer['notes'] or 'None')
        ]
        
        for label, value in info:
            frame = ttk.Frame(info_frame)
            frame.pack(fill=tk.X, pady=3)
            styled_label(frame, f"{label}", font=("Segoe UI", 10, "bold"), width=12).pack(side=tk.LEFT)
            styled_label(frame, f"{value}").pack(side=tk.LEFT)
        
        # Items
        styled_label(content, "Transfer Items:", font=FONT_BOLD).pack(anchor=tk.W, pady=(15, 5))
        
        items_frame = make_card(content, padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("product", "quantity", "received")
        items_tree = ttk.Treeview(items_frame, columns=columns, show="headings")
        
        for col in columns:
            items_tree.heading(col, text=col.title())
            items_tree.column(col, width=150)
        
        items_tree.pack(fill=tk.BOTH, expand=True)
        
        cur.execute("""
            SELECT p.model, sti.quantity, sti.received_quantity
            FROM stock_transfer_items sti
            JOIN products p ON sti.product_id = p.id
            WHERE sti.transfer_id = ?
        """, (transfer_id,))
        
        for row in cur.fetchall():
            items_tree.insert("", "end", values=(
                row['model'],
                row['quantity'],
                row['received_quantity'] or 0
            ))
    
    # Close button with uniform styling
    make_button(dlg, text="Close", command=dlg.destroy, kind="secondary").pack(pady=10)


def complete_transfer(transfer_id):
    """Complete a transfer and update stock levels."""
    try:
        with get_db_cursor() as cur:
            # Get transfer info
            cur.execute("""
                SELECT from_location_id, to_location_id FROM stock_transfers WHERE id = ?
            """, (transfer_id,))
            transfer = cur.fetchone()
            
            if not transfer:
                raise ValueError("Transfer not found")
            
            # Get items
            cur.execute("""
                SELECT product_id, quantity FROM stock_transfer_items WHERE transfer_id = ?
            """, (transfer_id,))
            items = cur.fetchall()
            
            # Update stock levels
            for item in items:
                # Remove from source location
                cur.execute("""
                    UPDATE product_stock
                    SET quantity = quantity - ?
                    WHERE product_id = ? AND location_id = ?
                """, (item['quantity'], item['product_id'], transfer['from_location_id']))
                
                # Add to destination location
                cur.execute("""
                    INSERT OR REPLACE INTO product_stock (product_id, location_id, quantity, reserved)
                    VALUES (?, ?, 
                        COALESCE((SELECT quantity FROM product_stock WHERE product_id = ? AND location_id = ?), 0) + ?,
                        COALESCE((SELECT reserved FROM product_stock WHERE product_id = ? AND location_id = ?), 0)
                    )
                """, (item['product_id'], transfer['to_location_id'],
                      item['product_id'], transfer['to_location_id'], item['quantity'],
                      item['product_id'], transfer['to_location_id']))
                
                # Update transfer items
                cur.execute("""
                    UPDATE stock_transfer_items
                    SET received_quantity = quantity
                    WHERE transfer_id = ? AND product_id = ?
                """, (transfer_id, item['product_id']))
            
            # Update transfer status
            cur.execute("""
                UPDATE stock_transfers
                SET status = 'completed', received_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (transfer_id,))
        
        messagebox.showinfo("Success", "Transfer completed successfully")
        
    except Exception as e:
        logging.exception("Failed to complete transfer")
        messagebox.showerror("Error", f"Failed to complete transfer: {e}")
