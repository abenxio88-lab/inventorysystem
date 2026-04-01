import tkinter as tk
from tkinter import messagebox, ttk
import logging
import json
import os
from datetime import datetime
import logging
try:
    from .ui_theme import (
        make_button, make_card, frame, label, entry, combobox, treeview,
        COLOR_APP_BG, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_BORDER,
        COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
        COLOR_CARD_BG, COLOR_INFO
    )
except Exception:
    from ui_theme import (
        make_button, make_card, frame, label, entry, combobox, treeview,
        COLOR_APP_BG, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_BORDER,
        COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
        COLOR_CARD_BG, COLOR_INFO
    )

try:
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir

DATA_DIR = get_data_dir()
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
SALES_FILE = os.path.join(DATA_DIR, "sales.json")

try:
    # safe JSON helpers
    from .utils import write_json_atomic, load_json_file
except (ImportError, ModuleNotFoundError):
    from utils import write_json_atomic, load_json_file

def load_inventory():
    return load_json_file(INVENTORY_FILE, default=[])

def save_inventory(data):
    try:
        write_json_atomic(INVENTORY_FILE, data)
    except Exception:
        logging.exception("Failed to save inventory from sales_ui")

def load_sales():
    return load_json_file(SALES_FILE, default=[])

def save_sales(data):
    try:
        write_json_atomic(SALES_FILE, data)
    except Exception:
        logging.exception("Failed to save sales file")

def create_sales_tab(parent):
    """
    Creates the sales management tab.
    """
    window = ttk.Frame(parent, padding=15)

    main_frame = frame(window, padding=15)
    main_frame.pack(fill="both", expand=True)

    # toolbar Section
    toolbar = frame(main_frame)
    toolbar.pack(fill="x", pady=(0, 10))
    label(toolbar, "Search:").pack(side="left", padx=(0, 10))
    search_var = tk.StringVar()
    search_entry = entry(toolbar, textvariable=search_var)
    try: search_entry.configure(width=40)
    except: pass
    search_entry.pack(side="left")

    def apply_search_bar():
        q = search_var.get().strip().lower()
        if not q:
            refresh_table()
            return
        filtered = []
        for s in load_sales():
            combined = " ".join([str(s.get(k, "")) for k in ("model", "date", "month")]).lower()
            if q in combined:
                filtered.append(s)
        refresh_table(filtered)

    make_button(toolbar, "Search", command=apply_search_bar, kind="primary").pack(side="left", padx=10)
    make_button(toolbar, "Clear", command=lambda: (search_var.set(""), refresh_table()), kind="secondary").pack(side="left")

    def toggle_fullscreen():
        top_level = window.winfo_toplevel()
        top_level.attributes("-fullscreen", not top_level.attributes("-fullscreen"))

    make_button(toolbar, "⛶ Fullscreen", command=toggle_fullscreen, kind="secondary").pack(side="right")

    # ===== FILTER SECTION =====
    label(main_frame, "FILTER SALES", kind="heading").pack(anchor="w", pady=(10, 5))

    filter_card = make_card(main_frame, padx=25, pady=20)
    filter_card.pack(fill="x", pady=(0, 20))

    def get_bg(w):
        try: return w.cget("background")
        except:
            try: return w.cget("bg")
            except: return None

    f_bg = get_bg(filter_card)

    label(filter_card, "Model Name:", kind="bold", foreground=COLOR_TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=5)
    model_var = tk.StringVar()
    inventory = load_inventory()
    models = ["All"] + sorted(list({item["model"] for item in inventory}))
    model_cb = combobox(filter_card, values=models, textvariable=model_var, state="readonly")
    try: model_cb.set("All")
    except: pass
    model_cb.grid(row=0, column=1, padx=5)

    label(filter_card, "Month (YYYY-MM):", kind="bold", foreground="#6c757d").grid(row=0, column=2, sticky="w", padx=(20, 5))
    month_var = tk.StringVar()
    month_entry = entry(filter_card, textvariable=month_var)
    try: month_entry.configure(width=20)
    except: pass
    month_entry.grid(row=0, column=3, padx=5)

    def apply_filter():
        sales = load_sales()
        m = model_var.get()
        month = month_var.get().strip()
        filtered = [s for s in sales if (m == "All" or s["model"] == m) and (not month or s["month"] == month)]
        refresh_table(filtered)

    make_button(filter_card, "Apply Filter", kind="primary").grid(row=0, column=4, padx=20)

    # ===== TABLE SECTION =====
    label(main_frame, "SALES HISTORY", kind="heading").pack(anchor="w", pady=(10, 5))
    table_frame = make_card(main_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("date", "model", "qty", "price", "total")
    tree = treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "date": ("Date", 150),
        "model": ("Model Name", 300),
        "qty": ("Quantity", 100),
        "price": ("Unit Price", 150),
        "total": ("Total Amount", 150)
    }

    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text.upper(), anchor="w")
        tree.column(col, width=width, anchor="w")

    try:
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    except Exception:
        pass
    tree.pack(side="left", fill="both", expand=True)

    try:
        # Light-theme friendly tag colors
        style = ttk.Style()
        style.configure("Treeview", font=FONT_REGULAR, rowheight=28) # Apply font and row height
        style.configure("Treeview.Heading", font=FONT_BOLD)

        tree.tag_configure("Phone", background="#DBEAFE", foreground="#1E40AF") # Light Blue, dark blue text
        tree.tag_configure("Tablet", background="#FEF3C7", foreground="#B45309") # Light Yellow, dark orange text
        tree.tag_configure("Accessory", background="#D1FAE5", foreground="#065F46") # Light Green, dark green text
    except Exception:
        pass

    def refresh_table(filtered_sales=None):
        tree.delete(*tree.get_children())
        sales = filtered_sales if filtered_sales is not None else load_sales()
        inv = {i.get("model"): i.get("category", "") for i in load_inventory()}
        for sale in sales:
            cat = inv.get(sale.get("model"), "")
            tags = (cat,) if cat else ()
            tree.insert("", "end", values=(
                sale.get("date"),
                sale.get("model"),
                sale.get("quantity"),
                sale.get("selling_price"),
                sale.get("total")
            ), tags=tags)

    def record_sale():
        open_record_sale_dialog(window, refresh_table)

    # Action Bar
    actions = frame(main_frame)
    actions.pack(pady=10)
    make_button(actions, "Record New Sale", command=record_sale, kind="success", width=20).pack()

    refresh_table()
    return window

def open_record_sale_dialog(master, on_refresh):
    """
    Opens a premium dialog to record a new sale.
    - Proper sizing (no hidden buttons)
    - Scrollable content
    - Glassmorphism design
    """
    from app_core import PremiumPopup, app_state
    
    dlg = PremiumPopup(master, "Record New Sale", width=700, height=550, resizable=True)
    content = dlg.get_content_frame()
    
    # Header
    header_card = make_card(content, padx=30, pady=20)
    header_card.pack(fill="x", pady=(20, 15))
    
    industry_config = app_state.get_industry_config()
    header_title = label(header_card, f"{industry_config['icon']} Record Sale", 
                        kind="heading", foreground=COLOR_PRIMARY)
    header_title.pack()
    
    # Industry-specific info badge
    if industry_config['features']:
        features_text = " • ".join(industry_config['features'])
        features_label = label(header_card, features_text, 
                              foreground=COLOR_TEXT_MUTED, size=11)
        features_label.pack(pady=(5, 0))
    
    # Form Card
    form_card = make_card(content, padx=30, pady=25)
    form_card.pack(fill="both", expand=True, pady=(0, 15))
    
    # Model Selection
    label(form_card, "Select Product Model", kind="bold", 
          foreground=COLOR_TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0, 8))
    
    model_var = tk.StringVar()
    models = sorted(list({i.get("model") for i in load_inventory() if i.get("stock", 0) > 0}))
    
    if not models:
        models = ["No products available"]
        model_sel = combobox(form_card, values=models, textvariable=model_var, state="readonly")
    else:
        model_sel = combobox(form_card, values=models, textvariable=model_var, state="readonly")
    
    model_sel.grid(row=1, column=0, sticky="ew", pady=(0, 15), columnspan=2)
    try: model_sel.configure(width=40)
    except: pass
    
    # Stock Info Display
    stock_frame = make_card(form_card, padx=15, pady=10)
    stock_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
    
    stock_info = label(stock_frame, "Available: — | Unit Price: 0.00", 
                      foreground=COLOR_TEXT_MUTED, size=12)
    stock_info.pack(side="left")
    
    stock_alert = label(stock_frame, "", foreground=COLOR_DANGER, size=11, bold=True)
    stock_alert.pack(side="right")
    
    # Quantity
    qty_label = label(form_card, "Quantity", kind="bold", foreground=COLOR_TEXT_MAIN)
    qty_label.grid(row=3, column=0, sticky="w", pady=(10, 8))
    
    qty_var = tk.IntVar(value=1)
    qty_spin = ttk.Spinbox(form_card, from_=1, to=10000, textvariable=qty_var, font=FONT_REGULAR)
    qty_spin.grid(row=4, column=0, sticky="ew", pady=(0, 15))
    try: qty_spin.configure(width=20)
    except: pass
    
    # Total Display
    total_frame = make_card(form_card, padx=20, pady=15)
    total_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 20))
    
    total_lbl = label(total_frame, "Total Amount: $0.00", 
                     kind="heading", foreground=COLOR_SUCCESS)
    total_lbl.pack()
    
    def update_info(event=None):
        sel = model_var.get()
        if not sel or sel == "No products available": 
            return
        
        for it in load_inventory():
            if it.get("model") == sel:
                s = int(it.get("stock", 0))
                p = float(it.get("selling_price", 0))
                
                stock_info.config(text=f"Available: {s} | Unit Price: ${p:.2f}")
                
                try: 
                    qty = int(qty_var.get())
                    if qty > s:
                        stock_alert.config(text=f"⚠️ Only {s} in stock!")
                        total_lbl.config(text=f"Total Amount: ${s * p:.2f}")
                        qty_var.set(s)
                    else:
                        stock_alert.config(text="")
                        total_lbl.config(text=f"Total Amount: ${qty * p:.2f}")
                except: 
                    total_lbl.config(text=f"Total Amount: ${p:.2f}")
                return
    
    model_sel.bind("<<ComboboxSelected>>", update_info)
    qty_spin.bind("<KeyRelease>", update_info)
    qty_spin.config(command=update_info)
    
    # Initialize display
    if models and models[0] != "No products available":
        model_sel.set(models[0])
        update_info()
    
    # Button Bar - Using responsive layout
    button_frame = ttk.Frame(content)
    button_frame.pack(fill="x", pady=(10, 25))
    
    def save_sale_action():
        m = model_var.get()
        if m == "No products available":
            messagebox.showwarning("No Products", "No products available in inventory.")
            return
            
        try: q = int(qty_var.get())
        except: 
            messagebox.showerror("Invalid Input", "Please enter a valid quantity.")
            return
            
        if not m or q <= 0: 
            messagebox.showwarning("Invalid Input", "Please select a product and enter quantity.")
            return

        inv_data = load_inventory()
        item_found = None
        for it in inv_data:
            if it.get("model") == m:
                current_stock = int(it.get("stock", 0))
                if current_stock < q:
                    response = messagebox.askyesno(
                        "Low Stock Warning", 
                        f"Only {current_stock} items in stock!\n\nDo you want to record this sale and set stock to 0?"
                    )
                    if not response:
                        return
                # Reduce stock but never go below 0
                it["stock"] = max(0, current_stock - q)
                item_found = it
                break
        
        if not item_found: 
            messagebox.showerror("Error", "Product not found.")
            return
            
        save_inventory(inv_data)

        d = datetime.now()
        s = load_sales()
        s.append({
            "date": d.strftime("%Y-%m-%d"),
            "month": d.strftime("%Y-%m"),
            "model": m,
            "quantity": q,
            "selling_price": item_found.get("selling_price", 0),
            "purchase_price": item_found.get("purchase_price", 0),
            "total": float(item_found.get("selling_price", 0)) * q,
            "user": getattr(app_state, 'current_user', 'Unknown')
        })
        save_sales(s)
        
        # Trigger data link update
        try:
            from app_core import data_linker
            # In real implementation, this would notify other modules
        except:
            pass
        
        messagebox.showsuccess("Success", "Sale recorded successfully!") if hasattr(messagebox, 'showsuccess') else messagebox.showinfo("Success", "Sale recorded successfully!")
        on_refresh()
        dlg.destroy()

    # Cancel button
    cancel_btn = make_button(button_frame, "Cancel", command=dlg.destroy, kind="secondary", width=15)
    cancel_btn.pack(side="right", padx=10)
    
    # Confirm button
    confirm_btn = make_button(button_frame, "✓ Confirm Sale", command=save_sale_action, kind="success", width=20)
    confirm_btn.pack(side="right", padx=10)
    
    # Center the dialog properly
    dlg.update_idletasks()
    dlg_width = 700
    dlg_height = 550
    x = master.winfo_x() + (master.winfo_width() - dlg_width) // 2
    y = master.winfo_y() + (master.winfo_height() - dlg_height) // 2
    dlg.geometry(f"+{x}+{y}")