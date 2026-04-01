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
    Opens a dialog to record a new sale.
    """
    dlg = tk.Toplevel(master)
    dlg.title("Record Sale")
    dlg.geometry("450x400") # Slightly smaller dialog
    dlg.resizable(False, False)
    dlg.focus_set()
    dlg.grab_set()

    cnt = frame(dlg, padding=20)
    cnt.pack(fill="both", expand=True)

    label(cnt, "NEW SALE", kind="heading", foreground=COLOR_PRIMARY).pack(pady=(0, 20))

    form = make_card(cnt, padx=20, pady=20)
    form.pack(fill="both", expand=True)

    # Model Selection
    label(form, "Model", kind="bold").grid(row=0, column=0, sticky="w")
    model_var = tk.StringVar()
    models = sorted(list({i.get("model") for i in load_inventory()}))
    model_sel = combobox(form, values=models, textvariable=model_var, state="readonly")
    try: model_sel.configure(width=25)
    except: pass
    model_sel.grid(row=1, column=0, sticky="ew", pady=(5, 15), columnspan=2)

    stock_info = label(form, "Available: — | Price: 0.00", foreground=COLOR_TEXT_MUTED)
    stock_info.grid(row=2, column=0, columnspan=2, sticky="w")

    # Quantity
    label(form, "Quantity", kind="bold").grid(row=3, column=0, sticky="w", pady=(10, 0))
    qty_var = tk.IntVar(value=1)
    qty_spin = ttk.Spinbox(form, from_=1, to=1000, textvariable=qty_var)
    qty_spin.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5, 15))

    total_lbl = label(form, "Total: 0.00", kind="bold", foreground=COLOR_SUCCESS)
    total_lbl.grid(row=5, column=0, columnspan=2, pady=10)

    def update_info(event=None):
        sel = model_var.get()
        if not sel: return
        for it in load_inventory():
            if it.get("model") == sel:
                s = it.get("stock", 0)
                p = it.get("selling_price", 0)
                stock_info.config(text=f"Available: {s} | Price: {p:.2f}")
                try: total_lbl.config(text=f"Total: {int(qty_var.get()) * float(p):.2f}")
                except: pass
                return

    model_sel.bind("<<ComboboxSelected>>", update_info)
    qty_spin.bind("<KeyRelease>", update_info)
    qty_spin.config(command=update_info)

    def save_sale_action():
        m = model_var.get()
        try: q = int(qty_var.get())
        except: return
        if not m or q <= 0: return

        inv_data = load_inventory()
        item_found = None
        for it in inv_data:
            if it.get("model") == m:
                current_stock = int(it.get("stock", 0))
                if current_stock < q:
                    # Notify user but allow the sale to be recorded; mark stock as low (no error)
                    try:
                        messagebox.showinfo("Low Stock", f"Only {current_stock} in stock. Recording sale and setting stock to 0.")
                    except Exception:
                        pass
                # Reduce stock but never go below 0
                it["stock"] = max(0, current_stock - q)
                item_found = it
                break
        
        if not item_found: return
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
            "total": float(item_found.get("selling_price", 0)) * q
        })
        save_sales(s)
        on_refresh()
        dlg.destroy()

    make_button(form, "Confirm Sale", command=save_sale_action, kind="success", width=20).grid(row=6, column=0, columnspan=2, pady=10)