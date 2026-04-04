"""
Suppliers UI Tab
=================
UI-ONLY layer. All data goes through the service layer.
After every write, refresh_from_db() reloads fresh data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

from ui_theme import (
    make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN,
    COLOR_APP_BG, COLOR_CARD_BG, label, frame, entry, combobox
)
from services import svc
from app_core import app_state


def create_suppliers_tab(parent, current_user=None):
    """Creates the suppliers management tab."""
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    styled_label(header_frame, "🏭 Supplier Management", font=FONT_BOLD).pack(side=tk.LEFT)

    def open_add_supplier():
        _open_supplier_dialog(window, current_user=current_user, mode="add")

    make_button(header_frame, "➕ Add Supplier", command=open_add_supplier, kind="success").pack(side=tk.RIGHT)

    # Search
    toolbar = ttk.Frame(window)
    toolbar.pack(fill="x", pady=(0, 10))
    styled_label(toolbar, "Search:").pack(side=tk.LEFT, padx=(0, 10))
    search_var = tk.StringVar()
    search_entry = entry(toolbar, textvariable=search_var)
    search_entry.pack(side=tk.LEFT, expand=True, fill="x")

    def apply_search():
        q = search_var.get().strip()
        refresh_from_db(q if q else None)

    make_button(toolbar, "Search", command=apply_search, kind="primary").pack(side=tk.LEFT, padx=10)
    make_button(toolbar, "Clear", command=lambda: (search_var.set(""), refresh_from_db()),
                kind="secondary").pack(side=tk.LEFT)

    # Table
    table_frame = make_card(window, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("code", "name", "contact_person", "phone", "city", "rating", "lead_time", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "code": ("Code", 80),
        "name": ("Name", 180),
        "contact_person": ("Contact", 120),
        "phone": ("Phone", 100),
        "city": ("City", 100),
        "rating": ("Rating", 60),
        "lead_time": ("Lead Days", 70),
        "status": ("Status", 70),
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

    def refresh_from_db(search_query=None):
        """Reload suppliers from the database."""
        tree.delete(*tree.get_children())
        suppliers = svc.supplier.get_all_suppliers(active_only=True)

        if search_query:
            q = search_query.lower()
            suppliers = [s for s in suppliers if
                         q in s.get("name", "").lower() or
                         q in s.get("code", "").lower() or
                         q in s.get("contact_person", "").lower()]

        for s in suppliers:
            tree.insert("", "end", values=(
                s.get("code", ""),
                s.get("name", ""),
                s.get("contact_person", ""),
                s.get("phone", ""),
                s.get("city", ""),
                s.get("rating", 5),
                s.get("lead_time_days", 7),
                "Active" if s.get("is_active", 1) else "Inactive",
            ))

    # Double-click to edit
    def on_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        code = tree.item(sel[0], "values")[0]
        suppliers = svc.supplier.get_all_suppliers()
        supplier = next((s for s in suppliers if s.get("code") == code), None)
        if supplier:
            _open_supplier_dialog(window, current_user=current_user, mode="edit", existing_data=supplier)

    tree.bind("<Double-1>", on_double_click)

    # Initial load
    refresh_from_db()
    return window


def _open_supplier_dialog(master, current_user=None, mode="add", existing_data=None):
    """Open dialog to add/edit a supplier."""
    from app_core import PremiumPopup
    title = "Edit Supplier" if mode == "edit" else "Add Supplier"
    dlg = PremiumPopup(master, title, width=650, height=550, resizable=True)
    content = dlg.get_content_frame()

    form_card = make_card(content, padx=20, pady=20)
    form_card.pack(fill="both", expand=True, padx=10, pady=10)

    fields = [
        ("code", "Code", existing_data.get("code", "") if existing_data else ""),
        ("name", "Name", existing_data.get("name", "") if existing_data else ""),
        ("contact_person", "Contact Person", existing_data.get("contact_person", "") if existing_data else ""),
        ("email", "Email", existing_data.get("email", "") if existing_data else ""),
        ("phone", "Phone", existing_data.get("phone", "") if existing_data else ""),
        ("mobile", "Mobile", existing_data.get("mobile", "") if existing_data else ""),
        ("address", "Address", existing_data.get("address", "") if existing_data else ""),
        ("city", "City", existing_data.get("city", "") if existing_data else ""),
        ("country", "Country", existing_data.get("country", "") if existing_data else ""),
        ("gst_number", "GST Number", existing_data.get("gst_number", "") if existing_data else ""),
        ("payment_terms", "Payment Terms", existing_data.get("payment_terms", "") if existing_data else ""),
        ("lead_time_days", "Lead Time (days)", str(existing_data.get("lead_time_days", 7)) if existing_data else "7"),
        ("rating", "Rating (1-5)", str(existing_data.get("rating", 5)) if existing_data else "5"),
        ("notes", "Notes", existing_data.get("notes", "") if existing_data else ""),
    ]

    widgets = {}
    for i, (key, lbl_text, default) in enumerate(fields):
        row = i // 2
        col = (i % 2) * 2
        label(form_card, lbl_text, kind="bold").grid(row=row, column=col, sticky="w", pady=3, padx=5)
        var = tk.StringVar(value=default)
        w = entry(form_card, textvariable=var)
        w.grid(row=row, column=col + 1, sticky="ew", pady=3, padx=5)
        widgets[key] = var

    def save():
        data = {k: v.get() for k, v in widgets.items()}
        try:
            data["lead_time_days"] = int(data.get("lead_time_days", 7))
            data["rating"] = int(data.get("rating", 5))
        except ValueError:
            pass

        username = current_user or getattr(app_state, "username", "system")

        try:
            if mode == "add":
                existing = svc.supplier.get_all_suppliers()
                if any(s.get("code") == data["code"] for s in existing):
                    messagebox.showerror("Error", "Supplier code already exists")
                    return
                svc.supplier.add_supplier(data, username=username)
                messagebox.showinfo("Success", "Supplier added successfully")
            else:
                code = existing_data.get("code")
                update_data = {k: v for k, v in data.items() if k != "code"}
                svc.supplier.update_supplier(code, update_data, username=username)
                messagebox.showinfo("Success", "Supplier updated successfully")
            dlg.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    dlg.add_button_bar([
        {"text": "Save", "command": save, "style": "Accent.TButton"},
        {"text": "Cancel", "command": dlg.destroy, "style": "TButton"}
    ])
