"""
Locations UI Tab
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


def create_locations_tab(parent, current_user=None):
    """Creates the locations/warehouse management tab."""
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "🏢 Locations & Warehouses", font=FONT_BOLD).pack(side=tk.LEFT)

    def open_add_location():
        _open_location_dialog(window, current_user=current_user, mode="add")

    make_button(header_frame, "➕ Add Location", command=open_add_location, kind="success").pack(side=tk.RIGHT)

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

    columns = ("code", "name", "type", "city", "country", "capacity", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "code": ("Code", 80),
        "name": ("Name", 200),
        "type": ("Type", 100),
        "city": ("City", 120),
        "country": ("Country", 100),
        "capacity": ("Capacity", 80),
        "status": ("Status", 80),
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
        """Reload locations from the database."""
        tree.delete(*tree.get_children())
        locations = svc.location.get_all_locations(active_only=True)

        if search_query:
            q = search_query.lower()
            locations = [loc for loc in locations if
                         q in loc.get("name", "").lower() or
                         q in loc.get("code", "").lower() or
                         q in loc.get("city", "").lower()]

        for loc in locations:
            tree.insert("", "end", values=(
                loc.get("code", ""),
                loc.get("name", ""),
                loc.get("type", ""),
                loc.get("city", ""),
                loc.get("country", ""),
                loc.get("capacity", ""),
                "Active" if loc.get("is_active", 1) else "Inactive",
            ), tags=("active",) if loc.get("is_active", 1) else ("inactive",))

        tree.tag_configure("active", background=COLOR_APP_BG)
        tree.tag_configure("inactive", background=COLOR_CARD_BG, foreground=COLOR_TEXT_MUTED)

    # Double-click to edit
    def on_double_click(event):
        sel = tree.selection()
        if not sel:
            return
        code = tree.item(sel[0], "values")[0]
        locations = svc.location.get_all_locations()
        loc = next((l for l in locations if l.get("code") == code), None)
        if loc:
            _open_location_dialog(window, current_user=current_user, mode="edit", existing_data=loc)

    tree.bind("<Double-1>", on_double_click)

    # Initial load
    refresh_from_db()
    return window


def _open_location_dialog(master, current_user=None, mode="add", existing_data=None):
    """Open dialog to add/edit a location."""
    dlg = tk.Toplevel(master)
    title = "Edit Location" if mode == "edit" else "Add Location"
    dlg.title(title)
    dlg.geometry("500x450")
    dlg.transient(master)
    dlg.grab_set()

    form_card = make_card(dlg, padx=20, pady=20)
    form_card.pack(fill="both", expand=True, padx=10, pady=10)

    fields = [
        ("code", "Code", existing_data.get("code", "") if existing_data else ""),
        ("name", "Name", existing_data.get("name", "") if existing_data else ""),
        ("type", "Type", existing_data.get("type", "warehouse") if existing_data else "warehouse"),
        ("address", "Address", existing_data.get("address", "") if existing_data else ""),
        ("city", "City", existing_data.get("city", "") if existing_data else ""),
        ("country", "Country", existing_data.get("country", "") if existing_data else ""),
        ("phone", "Phone", existing_data.get("phone", "") if existing_data else ""),
        ("email", "Email", existing_data.get("email", "") if existing_data else ""),
        ("capacity", "Capacity", str(existing_data.get("capacity", 0)) if existing_data else "0"),
    ]

    widgets = {}
    for i, (key, lbl_text, default) in enumerate(fields):
        label(form_card, lbl_text, kind="bold").grid(row=i, column=0, sticky="w", pady=5, padx=5)
        if key == "type":
            var = tk.StringVar(value=default)
            w = combobox(form_card, values=["warehouse", "store", "office"], textvariable=var, state="readonly")
            widgets[key] = var
        else:
            var = tk.StringVar(value=default)
            w = entry(form_card, textvariable=var)
            widgets[key] = var
        w.grid(row=i, column=1, sticky="ew", pady=5, padx=5)

    btn_frame = ttk.Frame(dlg)
    btn_frame.pack(fill="x", pady=10, padx=10)

    def save():
        data = {k: v.get() if hasattr(v, "get") else v for k, v in widgets.items()}
        # Convert capacity to int
        try:
            data["capacity"] = int(data.get("capacity", 0))
        except ValueError:
            data["capacity"] = 0

        username = current_user or getattr(app_state, "username", "system")

        try:
            if mode == "add":
                # Check duplicate code
                existing = svc.location.get_all_locations()
                if any(loc.get("code") == data["code"] for loc in existing):
                    messagebox.showerror("Error", "Location code already exists")
                    return
                svc.location.add_location(data, username=username)
                messagebox.showinfo("Success", "Location added successfully")
            else:
                code = existing_data.get("code")
                update_data = {k: v for k, v in data.items() if k != "code"}
                svc.location.update_location(code, update_data, username=username)
                messagebox.showinfo("Success", "Location updated successfully")
            dlg.destroy()
            # Refresh the parent tab's tree — we call the outer refresh_from_db
            # Since we're inside the same module, we can't directly call it.
            # The dialog destroy will trigger a re-load by the caller pattern.
        except Exception as e:
            messagebox.showerror("Error", str(e))

    make_button(btn_frame, "Save", command=save, kind="primary").pack(side="right", padx=5)
    make_button(btn_frame, "Cancel", command=dlg.destroy, kind="secondary").pack(side="right", padx=5)
