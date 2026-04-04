"""
Sales UI Tab
=============
UI-ONLY layer. All data goes through the service layer.
After every write, refresh_from_db() reloads fresh data.

RULES:
  - No SQL queries here.
  - No direct database access.
  - All reads/writes go through svc.sales and svc.inventory.
"""

import os
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

# Project imports
from app_core import app_state, PremiumPopup
from ui_theme import (
    toggle_theme, get_color, make_button, make_card, styled_label, styled_entry,
    frame, label, entry, combobox, treeview,
    COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT_MUTED, COLOR_APP_BG, COLOR_INFO,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, BTN_WIDTH, FONT_BOLD, FONT_HEADING, FONT_REGULAR
)
from services import svc

logger = logging.getLogger(__name__)


def create_sales_tab(parent):
    """Creates the sales management tab."""
    window = ttk.Frame(parent, padding=15)
    main_frame = frame(window, padding=15)
    main_frame.pack(fill="both", expand=True)

    # ── Toolbar ───────────────────────────────────────────
    toolbar = frame(main_frame)
    toolbar.pack(fill="x", pady=(0, 10))

    label(toolbar, "Search:").pack(side="left", padx=(0, 10))
    search_var = tk.StringVar()
    search_entry = entry(toolbar, textvariable=search_var)
    try:
        search_entry.configure(width=40)
    except Exception:
        pass
    search_entry.pack(side="left")

    def apply_search_bar():
        q = search_var.get().strip().lower()
        if not q:
            refresh_from_db()
            return
        all_orders = svc.sales.get_all_orders()
        filtered = []
        for s in all_orders:
            items = svc.sales.get_order_items(s["id"])
            model = _get_sale_model(s, items)
            if q in model.lower():
                filtered.append(s)
        refresh_from_db(filtered_sales=filtered)

    make_button(toolbar, "Search", command=apply_search_bar, kind="primary").pack(side="left", padx=10)
    make_button(toolbar, "Clear", command=lambda: (search_var.set(""), refresh_from_db()),
                kind="secondary").pack(side="left")

    def toggle_fullscreen():
        top_level = window.winfo_toplevel()
        top_level.attributes("-fullscreen", not top_level.attributes("-fullscreen"))

    make_button(toolbar, "⛶ Fullscreen", command=toggle_fullscreen, kind="secondary").pack(side="right")

    # ── Filter Section ────────────────────────────────────
    label(main_frame, "FILTER SALES", kind="heading").pack(anchor="w", pady=(10, 5))

    filter_card = make_card(main_frame, padx=25, pady=20)
    filter_card.pack(fill="x", pady=(0, 20))

    label(filter_card, "Model Name:", kind="bold", foreground=COLOR_TEXT_MUTED).grid(
        row=0, column=0, sticky="w", padx=5)
    model_var = tk.StringVar(value="All")

    # Load models from service
    products = svc.inventory.get_all_products(active_only=True)
    models = ["All"] + sorted({p["model"] for p in products if p.get("model")})
    model_cb = combobox(filter_card, values=models, textvariable=model_var, state="readonly")
    model_cb.grid(row=0, column=1, padx=5)
    model_cb.bind("<<ComboboxSelected>>", lambda e: _apply_filter(model_var, month_var, refresh_from_db))

    label(filter_card, "Month (YYYY-MM):", kind="bold", foreground="#6c757d").grid(
        row=0, column=2, sticky="w", padx=(20, 5))
    month_var = tk.StringVar()
    month_entry = entry(filter_card, textvariable=month_var)
    month_entry.grid(row=0, column=3, padx=5)
    month_entry.bind("<Return>", lambda e: _apply_filter(model_var, month_var, refresh_from_db))

    make_button(filter_card, "Reset Filter",
                command=lambda: (model_var.set("All"), month_var.set(""), refresh_from_db()),
                kind="secondary").grid(row=0, column=4, padx=20)

    # ── Table Section ─────────────────────────────────────
    label(main_frame, "SALES HISTORY", kind="heading").pack(anchor="w", pady=(10, 5))
    table_frame = make_card(main_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("date", "model", "qty", "price", "total")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "date": ("Date", 150),
        "model": ("Model Name", 300),
        "qty": ("Quantity", 100),
        "price": ("Unit Price", 150),
        "total": ("Total Amount", 150),
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
        style = ttk.Style()
        style.configure("Treeview", font=FONT_REGULAR, rowheight=28)
        style.configure("Treeview.Heading", font=FONT_BOLD)
        tree.tag_configure("Phone", background="#DBEAFE", foreground="#1E40AF")
        tree.tag_configure("Tablet", background="#FEF3C7", foreground="#B45309")
        tree.tag_configure("Accessory", background="#D1FAE5", foreground="#065F46")
    except Exception:
        pass

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    # ========================================================

    def refresh_from_db(filtered_sales=None):
        """Reload the sales tree from the database."""
        tree.delete(*tree.get_children())
        orders = filtered_sales if filtered_sales is not None else svc.sales.get_all_orders()
        products_map = {p["model"]: p.get("category", "") for p in svc.inventory.get_all_products()}

        for sale in orders:
            items = svc.sales.get_order_items(sale["id"])
            model = _get_sale_model(sale, items)
            qty = sum(it.get("quantity", 0) for it in items) if items else sale.get("quantity", 0)
            price = items[0].get("unit_price", 0) if items else sale.get("selling_price", 0)
            total = sale.get("total_amount", 0)
            cat = products_map.get(model, "")
            tags = (cat,) if cat else ()

            tree.insert("", "end", values=(
                sale.get("order_date", ""),
                model,
                qty,
                f"Rs. {price:.2f}",
                f"Rs. {total:.2f}",
            ), tags=tags)

        _refresh_filter_models(model_var, model_cb)

    def refresh_filter_models():
        """Refresh the model dropdown with current inventory."""
        _refresh_filter_models(model_var, model_cb)

    def auto_refresh():
        """Auto-refresh table and filter after any change."""
        refresh_from_db()
        refresh_filter_models()

    # ── Action Bar ────────────────────────────────────────
    actions = frame(main_frame)
    actions.pack(pady=10)
    make_button(actions, "Record New Sale", command=lambda: _record_sale(window, auto_refresh),
                kind="success", width=20).pack()

    # ── Initial load ──────────────────────────────────────
    refresh_from_db()
    return window


# ============================================================
#  Helper functions
# ============================================================

def _get_sale_model(sale: dict, items: list) -> str:
    """Extract model name from a sale record."""
    if items:
        # Try to get model from product lookup
        product_id = items[0].get("product_id")
        if product_id:
            product = svc.inventory.get_product_by_id(product_id)
            if product:
                return product.get("model", "Unknown")
    return sale.get("customer_name", "Unknown")


def _refresh_filter_models(model_var, model_cb):
    """Refresh the model dropdown with current inventory."""
    products = svc.inventory.get_all_products(active_only=True)
    models = ["All"] + sorted({p["model"] for p in products if p.get("model")})
    model_cb.configure(values=models)
    current = model_var.get()
    if current not in models:
        model_var.set("All")


def _apply_filter(model_var, month_var, refresh_cb):
    """Apply model + month filter to sales."""
    m = model_var.get()
    month = month_var.get().strip()
    all_orders = svc.sales.get_all_orders()
    filtered = []
    for s in all_orders:
        items = svc.sales.get_order_items(s["id"])
        sale_model = _get_sale_model(s, items)
        if m == "All" or sale_model == m:
            if not month:
                filtered.append(s)
            else:
                sale_date = s.get("order_date", "")
                sale_month = sale_date[:7] if sale_date else ""
                if sale_month == month:
                    filtered.append(s)
    refresh_cb(filtered_sales=filtered)


def _record_sale(master, on_refresh):
    """Open dialog to record a new sale through the service layer."""
    dlg = PremiumPopup(master, "Record New Sale", width=700, height=550, resizable=True)
    content = dlg.get_content_frame()

    # Header
    header_card = make_card(content, padx=30, pady=20)
    header_card.pack(fill="x", pady=(20, 15))

    industry_config = app_state.get_industry_config()
    label(header_card, f"{industry_config.get('icon', '💰')} Record Sale",
          kind="heading", foreground=COLOR_PRIMARY).pack()

    # Form
    form_card = make_card(content, padx=30, pady=25)
    form_card.pack(fill="both", expand=True, pady=(0, 15))

    # Product selection
    label(form_card, "Select Product Model", kind="bold",
          foreground=COLOR_TEXT_MAIN).grid(row=0, column=0, sticky="w", pady=(0, 8))

    model_var = tk.StringVar()

    # Load products with stock > 0 from service
    products = svc.inventory.get_all_products(active_only=True)
    available = [(p["model"], p["stock"], p["selling_price"]) for p in products if p.get("stock", 0) > 0]
    model_names = [p[0] for p in available] if available else ["No products available"]

    model_sel = combobox(form_card, values=model_names, textvariable=model_var, state="readonly")
    model_sel.grid(row=1, column=0, sticky="ew", pady=(0, 15), columnspan=2)
    try:
        model_sel.configure(width=40)
    except Exception:
        pass

    # Stock info display
    stock_frame = make_card(form_card, padx=15, pady=10)
    stock_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))

    stock_info = label(stock_frame, "Available: — | Unit Price: 0.00",
                       foreground=COLOR_TEXT_MUTED, size=12)
    stock_info.pack(side="left")

    stock_alert = label(stock_frame, "", foreground=COLOR_DANGER, size=11, bold=True)
    stock_alert.pack(side="right")

    # Quantity
    label(form_card, "Quantity", kind="bold", foreground=COLOR_TEXT_MAIN).grid(
        row=3, column=0, sticky="w", pady=(10, 8))

    qty_var = tk.IntVar(value=1)
    qty_spin = ttk.Spinbox(form_card, from_=1, to=10000, textvariable=qty_var, font=FONT_REGULAR)
    qty_spin.grid(row=4, column=0, sticky="ew", pady=(0, 15))
    try:
        qty_spin.configure(width=20)
    except Exception:
        pass

    # Total display
    total_frame = make_card(form_card, padx=20, pady=15)
    total_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 20))

    total_lbl = label(total_frame, "Total Amount: Rs. 0.00", kind="heading", foreground=COLOR_SUCCESS)
    total_lbl.pack()

    # Product info lookup
    product_map = {p["model"]: p for p in available}

    def update_info(event=None):
        sel = model_var.get()
        if not sel or sel == "No products available":
            return
        product = product_map.get(sel)
        if not product:
            return
        s = product.get("stock", 0)
        p = product.get("selling_price", 0)
        stock_info.config(text=f"Available: {s} | Unit Price: Rs. {p:.2f}")
        try:
            qty = int(qty_var.get())
            if qty > s:
                stock_alert.config(text=f"⚠️ Only {s} in stock!")
                total_lbl.config(text=f"Total Amount: Rs. {s * p:.2f}")
                qty_var.set(s)
            else:
                stock_alert.config(text="")
                total_lbl.config(text=f"Total Amount: Rs. {qty * p:.2f}")
        except Exception:
            total_lbl.config(text=f"Total Amount: Rs. {p:.2f}")

    model_var.trace_add("write", update_info)

    if model_names and model_names[0] != "No products available":
        model_var.set(model_names[0])
        update_info()

    # Buttons
    button_frame = frame(content)
    button_frame.pack(fill="x", pady=(15, 20))

    def save_sale_action():
        model = model_var.get()
        qty = qty_var.get()

        if not model or model == "No products available":
            messagebox.showerror("Error", "Please select a valid product")
            return

        if qty <= 0:
            messagebox.showerror("Error", "Quantity must be positive")
            return

        product = product_map.get(model)
        if not product:
            messagebox.showerror("Error", "Product not found")
            return

        s = product.get("stock", 0)
        if qty > s:
            messagebox.showerror("Error", f"Only {s} units available")
            return

        try:
            username = getattr(app_state, "username", "system")
            price = product.get("selling_price", 0)
            total = qty * price

            order_data = {
                "order_number": f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "customer_name": "Walk-in Customer",
                "order_date": datetime.now().isoformat(),
                "status": "confirmed",
                "total_amount": total,
                "paid_amount": total,
                "payment_status": "paid",
            }

            items = [{
                "product_id": product.get("id"),
                "quantity": qty,
                "unit_price": price,
                "total_price": total,
            }]

            svc.sales.create_order(order_data, items, username=username)
            messagebox.showinfo("Success", "Sale recorded successfully!")
            dlg.destroy()
            on_refresh()
        except Exception as e:
            logger.error(f"Failed to record sale: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to record sale: {e}")

    make_button(button_frame, "Cancel", command=dlg.destroy, kind="secondary",
                width=BTN_WIDTH.get("dialog", 15)).pack(side="right", padx=10)
    make_button(button_frame, "✓ Confirm Sale", command=save_sale_action, kind="success",
                width=BTN_WIDTH.get("action", 15)).pack(side="right", padx=10)

    dlg.update_idletasks()
    dlg.geometry(f"700x550+{(dlg.winfo_screenwidth() // 2) - 350}+{(dlg.winfo_screenheight() // 2) - 275}")
