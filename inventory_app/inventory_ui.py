"""
Inventory UI Tab
================
UI-ONLY layer. Reads data through the service layer.
After every write (add/update/delete) it calls refresh_from_db()
so the tree view always reflects the true database state.

RULES:
  - No SQL queries here.
  - No direct database access.
  - All data reads go through svc.inventory
  - All data writes go through svc.inventory
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import csv
import logging
from datetime import datetime

# Project imports
from app_core import app_state, PremiumPopup
from ui_theme import (
    toggle_theme, get_color, make_button, make_card, styled_label, styled_entry,
    frame, label, entry, combobox, treeview,
    COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_APP_BG, COLOR_INFO,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_CARD_BG,
    BTN_WIDTH, FONT_BOLD, FONT_HEADING, FONT_REGULAR,
    get_palette
)
from services import svc
from database import get_db_stats

# Industrial Imports
from unified_data_entry import DynamicFormBuilder
from error_manager import report_info, report_error


def create_inventory_tab(parent, current_user="Unknown"):
    """Creates the premium inventory management tab."""
    window = ttk.Frame(parent, padding=15)

    # ── Header ────────────────────────────────────────────
    header = frame(window, padding=20)
    header.pack(fill="x", pady=(0, 20))

    label(header, "📦 STOCK MANAGEMENT", kind="heading").pack(side="left")

    total_var = tk.StringVar(value="Total Stock Items: 0")
    total_lbl = label(header, total_var.get(), kind="bold", foreground=COLOR_PRIMARY)
    total_lbl.pack(side="right")

    # ── Layout ────────────────────────────────────────────
    paned = ttk.PanedWindow(window, orient="horizontal")
    paned.pack(fill="both", expand=True)

    left_frame = frame(paned, padding=20)
    paned.add(left_frame, weight=1)

    right_frame = frame(paned, padding=20)
    paned.add(right_frame, weight=3)

    # ── undo stack (local to this tab) ────────────────────
    undo_stack = []

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    #  Every UI refresh reads fresh data through the service.
    # ========================================================

    def refresh_from_db(filtered_data=None):
        """Reload the tree view and stats from the database."""
        _update_total()
        _populate_tree(filtered_data)
        _refresh_model_dropdown()

    def _update_total():
        stats = get_db_stats()
        total = stats.get("total_products", 0)
        total_var.set(f"Total Stock Items: {total:,}")
        total_lbl.configure(text=total_var.get())

    def _resolve_category_display(item):
        """Return human-friendly category text for tree/form."""
        cid = item.get("category_id") or item.get("category")
        if not cid:
            return ""
        return svc.inventory.resolve_category_display(cid)

    def _resolve_supplier_display(item):
        """Return human-friendly supplier text for tree/form."""
        sid = item.get("supplier_id") or item.get("supplier")
        if not sid:
            return ""
        return svc.inventory.resolve_supplier_display(sid)

    def _parse_related_id(field_name: str, raw_value):
        """
        Normalize category/supplier input to an integer ID.
        Delegates to the service layer — no direct SQL in UI.
        """
        return svc.inventory.parse_related_id(field_name, raw_value)

    def _populate_tree(items=None):
        """Fill the treeview with current inventory data."""
        from migration_add_industry_type import get_industry_type
        industry_mode = get_industry_type()

        tree.delete(*tree.get_children())

        if items is None:
            items = svc.inventory.get_all_products(active_only=True)

        for i, item in enumerate(items):
            stock_val = int(item.get("stock", 0))
            tags = ("even",) if i % 2 else ("odd",)
            if stock_val <= 5:
                tags = ("low",)

            industry_info = ""
            if industry_mode == "electronics":
                industry_info = f"{item.get('ram', '-')}/{item.get('storage', '-')}"
            elif industry_mode == "pharma":
                expiry = item.get("expiry_date", "")
                industry_info = f"Exp: {expiry[:10]}" if expiry else "No Expiry"

            tree.insert("", "end", values=(
                item.get("model", ""),
                _resolve_category_display(item),
                industry_info,
                _resolve_supplier_display(item),
                f'{item.get("purchase_price", 0):,}',
                f'{item.get("selling_price", 0):,}',
                stock_val,
            ), tags=tags)

    def _refresh_model_dropdown():
        """Update the model dropdown with current product models."""
        items = svc.inventory.get_all_products(active_only=True)
        models = sorted({i.get("model") for i in items if i.get("model")})
        if "form" in globals() and "model" in form.widgets:
            widget = form.widgets["model"]
            try:
                if hasattr(widget, "configure"):
                    widget.configure(values=models)
                elif hasattr(widget, "config"):
                    widget.config(values=models)
            except Exception:
                pass

    # ── Industry change callback ──────────────────────────
    def on_industry_changed(event_type, data):
        if event_type == "industry_change":
            try:
                refresh_from_db()
            except Exception:
                pass

    app_state.register_ui_callback(on_industry_changed)

    # ========================================================
    #  FORM
    # ========================================================
    from migration_add_industry_type import get_industry_type

    label(left_frame, "PRODUCT INFORMATION", kind="heading").pack(anchor="w", pady=(0, 10))
    form_card = make_card(left_frame, padx=20, pady=20)
    form_card.pack(fill="x", pady=(0, 15))

    form = DynamicFormBuilder(form_card, get_industry_type(), "products")
    form.build_form()

    def clear_form():
        for widget in form.widgets.values():
            try:
                if hasattr(widget, "delete"):
                    widget.delete(0, tk.END)
                if hasattr(widget, "set"):
                    widget.set("")
            except Exception:
                pass

    # ========================================================
    #  CRUD ACTIONS
    # ========================================================

    def add_item():
        """Add a new product through the service layer."""
        values = form.get_values()
        
        # Normalize category_id/supplier_id to integer IDs
        for field in ('category_id', 'supplier_id'):
            try:
                values[field] = _parse_related_id(field, values.get(field, ""))
            except ValueError as e:
                messagebox.showerror("Invalid Selection", str(e))
                return
        
        model = values.get("model", "").strip()
        if not model:
            messagebox.showerror("Error", "Model name required")
            return

        try:
            # Check duplicate
            existing = svc.inventory.get_product_by_model(model)
            if existing:
                messagebox.showerror("Error", "Model already exists — use Update")
                return

            svc.inventory.add_product(values, username=current_user)
            report_info(f"Inventory Added: {model}", module="Inventory")
            refresh_from_db()
            clear_form()
        except Exception as e:
            report_error("Failed to add inventory item", exception=e, module="Inventory")
            messagebox.showerror("Operation Failed", str(e))

    def update_item():
        """Update an existing product through the service layer."""
        values = form.get_values()
        
        # Normalize category_id/supplier_id to integer IDs
        for field in ('category_id', 'supplier_id'):
            try:
                values[field] = _parse_related_id(field, values.get(field, ""))
            except ValueError as e:
                messagebox.showerror("Invalid Selection", str(e))
                return
        
        model = values.get("model", "").strip()
        if not model:
            messagebox.showerror("Error", "Model name required")
            return

        try:
            existing = svc.inventory.get_product_by_model(model)
            if not existing:
                messagebox.showerror("Error", "Model not found — use Add to create new model")
                return

            svc.inventory.update_product(model, values, username=current_user)
            report_info(f"Inventory Updated: {model}", module="Inventory")
            refresh_from_db()
            clear_form()
        except Exception as e:
            report_error("Failed to update inventory item", exception=e, module="Inventory")
            messagebox.showerror("Operation Failed", str(e))

    def delete_item():
        """Delete a product through the service layer."""
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select item to delete")
            return

        if not _is_admin():
            messagebox.showerror("Permission Denied", "Only admins can delete items")
            return

        model = tree.item(sel[0], "values")[0]
        if not messagebox.askyesno("Confirm", f"Delete {model}?"):
            return

        try:
            svc.inventory.delete_product(model, username=current_user)
            report_info(f"Inventory Deleted: {model}", module="Inventory")
            refresh_from_db()
            clear_form()
        except Exception as e:
            report_error("Failed to delete inventory item", exception=e, module="Inventory")
            messagebox.showerror("Operation Failed", str(e))

    def undo_action():
        if not undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo")
            return
        prev = undo_stack.pop()
        try:
            svc.inventory.upsert_product(prev, username=current_user)
            refresh_from_db()
            clear_form()
            logging.info("Undo applied")
        except Exception:
            logging.error("Failed to undo", exc_info=True)
            messagebox.showerror("Error", "Failed to undo")

    # ── Action buttons ────────────────────────────────────
    btn_frame = ttk.Frame(left_frame)
    btn_frame.pack(fill="x", pady=10)

    make_button(btn_frame, "Add Item", command=add_item, kind="success").pack(
        side="left", expand=True, fill="x", padx=(0, 5))
    make_button(btn_frame, "Update Item", command=update_item, kind="primary").pack(
        side="left", expand=True, fill="x", padx=(0, 5))
    make_button(btn_frame, "Delete Item", command=delete_item, kind="danger").pack(
        side="left", expand=True, fill="x")

    btn_frame_2 = ttk.Frame(left_frame)
    btn_frame_2.pack(fill="x", pady=(5, 10))
    make_button(btn_frame_2, "Undo", command=undo_action, kind="warning").pack(
        side="left", expand=True, fill="x", padx=(0, 5))
    make_button(btn_frame_2, "Clear Form", command=clear_form, kind="secondary").pack(
        side="left", expand=True, fill="x")

    # ========================================================
    #  TOOLBAR / SEARCH
    # ========================================================
    toolbar = ttk.Frame(right_frame, padding=(0, 6))
    toolbar.pack(fill="x", pady=(0, 12))

    styled_label(toolbar, "Search:").pack(side="left", padx=(0, 10))
    search_var = tk.StringVar()
    search_entry = styled_entry(toolbar, textvariable=search_var)
    search_entry.pack(side="left", expand=True, fill="x")

    def apply_search(event=None):
        q = search_var.get().strip().lower()
        if not q:
            refresh_from_db()
            return
        all_items = svc.inventory.get_all_products(active_only=True)
        results = [it for it in all_items if q in " ".join(str(v) for v in it.values()).lower()]
        refresh_from_db(filtered_data=results)

    make_button(toolbar, "Search", command=apply_search, kind="primary").pack(side="left", padx=10)
    make_button(toolbar, "Clear", command=lambda: (search_var.set(""), refresh_from_db()),
                kind="secondary").pack(side="left")

    # ── Extra toolbar buttons ─────────────────────────────
    def on_export_csv():
        fname = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not fname:
            return
        try:
            _export_to_csv(fname)
            messagebox.showinfo("Export", f"Exported inventory to: {fname}")
        except Exception:
            logging.exception("Export failed")
            messagebox.showerror("Export Failed", "Failed to export inventory to CSV")

    def on_import_csv():
        fname = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not fname:
            return
        if not _is_admin():
            messagebox.showerror("Permission Denied", "Only admins can import inventory")
            return
        _preview_and_import_csv(fname)

    def on_backup():
        if not _is_admin():
            messagebox.showerror("Permission Denied", "Only admins can run backups")
            return
        try:
            from backup_manager import backup_data
            dest = backup_data()
            messagebox.showinfo("Backup", f"Data backed up to: {dest}")
        except Exception:
            logging.exception("Backup failed")
            messagebox.showerror("Backup Failed", "Failed to backup data")

    def on_generate_qr():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select item to generate QR")
            return
        model = tree.item(sel[0], "values")[0]
        item = svc.inventory.get_product_by_model(model)
        if item:
            try:
                if "id" not in item:
                    item["id"] = abs(hash(model)) % 1000000
                from barcode_system import generate_product_barcode
                path = generate_product_barcode(item)
                if path:
                    messagebox.showinfo("Success", f"QR/Barcode generated at:\n{path}")
                    os.startfile(os.path.dirname(path))
            except Exception as e:
                logging.exception("QR generation failed")
                messagebox.showerror("Error", f"Failed to generate QR: {e}")

    make_button(toolbar, "Export CSV", command=on_export_csv, kind="secondary").pack(side="left", padx=(10, 0))
    make_button(toolbar, "Import CSV", command=on_import_csv, kind="secondary").pack(side="left", padx=(5, 0))
    make_button(toolbar, "Backup", command=on_backup, kind="secondary").pack(side="left", padx=(5, 0))
    make_button(toolbar, "Generate QR", command=on_generate_qr, kind="success").pack(side="left", padx=(5, 0))

    state = {"full": False}
    def toggle_fullscreen():
        state["full"] = not state["full"]
        top_level = window.winfo_toplevel()
        top_level.attributes("-fullscreen", state["full"])

    make_button(toolbar, "⛶", command=toggle_fullscreen, kind="secondary").pack(side="right")

    # ========================================================
    #  TREE VIEW
    # ========================================================
    table_frame = make_card(right_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("model", "category", "screen", "supplier", "purchase", "selling", "stock")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "model": ("Model Name", 150),
        "category": ("Category", 80),
        "screen": ("Screen Type", 80),
        "supplier": ("Supplier", 100),
        "purchase": ("Purchase Price", 100),
        "selling": ("Selling Price", 100),
        "stock": ("Stock Level", 60),
    }

    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text.upper(), anchor="center")
        tree.column(col, width=width, anchor="center")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    palette = get_palette()
    tree.tag_configure("low", background="#FEF2F2", foreground="#DC2626")
    tree.tag_configure("odd", background=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN)
    tree.tag_configure("even", background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN)

    def on_tree_click(event):
        row = tree.identify_row(event.y)
        if row == "":
            try:
                sel = tree.selection()
                if sel:
                    tree.selection_remove(sel)
            except Exception:
                pass
            clear_form()
            return "break"

    def on_select(event=None):
        sel = tree.selection()
        if not sel:
            clear_form()
            return
        model_name = tree.item(sel[0], "values")[0]
        item = svc.inventory.get_product_by_model(model_name)
        if not item:
            return
        
        for field_name, widget in form.widgets.items():
            val = item.get(field_name, "")
            
            try:
                # For combobox widgets (category_id, supplier_id), show human text or fall back
                if field_name == 'category_id':
                    display_text = _resolve_category_display(item)
                    widget.set(display_text)
                elif field_name == 'supplier_id':
                    display_text = _resolve_supplier_display(item)
                    widget.set(display_text)
                elif hasattr(widget, "delete"):
                    widget.delete(0, tk.END)
                    widget.insert(0, str(val))
                elif hasattr(widget, "set"):
                    widget.set(val)
            except Exception:
                pass

    tree.bind("<Button-1>", on_tree_click)
    tree.bind("<<TreeviewSelect>>", on_select)

    try:
        style = ttk.Style()
        style.configure("Treeview", font=FONT_REGULAR, rowheight=28)
        style.configure("Treeview.Heading", font=FONT_BOLD)
    except Exception:
        pass

    # ── Initial load ──────────────────────────────────────
    refresh_from_db()

    # ── Key bindings ──────────────────────────────────────
    def focus_next(event):
        event.widget.tk_focusNext().focus()
        return "break"

    search_entry.bind("<Return>", lambda e: apply_search())

    if "form" in globals():
        for name, w in form.widgets.items():
            try:
                w.bind("<Return>", focus_next)
            except Exception:
                pass

    window.focus_set()
    return window


# ============================================================
#  Helper stubs (imported or local)
# ============================================================

def _is_admin():
    """Check if current user has admin role."""
    return getattr(app_state, "role", None) == "admin"


def _export_to_csv(filepath: str):
    """Export current inventory to CSV."""
    items = svc.inventory.get_all_products(active_only=True)
    if not items:
        return
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=items[0].keys())
        writer.writeheader()
        writer.writerows(items)


def _preview_and_import_csv(filepath: str):
    """Show a preview dialog for CSV import, then merge or replace."""
    import csv as csv_mod

    parsed = []
    invalid = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        for i, r in enumerate(reader, start=1):
            try:
                item = {
                    "model": str(r.get("model", "")).strip(),
                    "category": str(r.get("category", "")).strip(),
                    "supplier": str(r.get("supplier", "")).strip(),
                    "purchase_price": float(r.get("purchase_price", 0) or 0),
                    "selling_price": float(r.get("selling_price", 0) or 0),
                    "stock": int(float(r.get("stock", 0) or 0)),
                    "notes": str(r.get("notes", "")).strip(),
                }
            except Exception:
                invalid.append((i, r))
                continue
            if not item.get("model"):
                invalid.append((i, r))
            else:
                parsed.append(item)

    pv = PremiumPopup(app_state.main_notebook.winfo_toplevel() if app_state.main_notebook else None, "Import Preview", width=900, height=500)
    
    content = pv.get_content_frame()

    label(content, f"Previewing {os.path.basename(filepath)} — {len(parsed)} valid, {len(invalid)} invalid",
          kind="heading").pack(anchor="w", pady=6, padx=6)

    treef = make_card(content, padx=6, pady=6)
    treef.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    cols = ("model", "category", "supplier", "purchase_price", "selling_price", "stock")
    t = ttk.Treeview(treef, columns=cols, show="headings")
    for c in cols:
        t.heading(c, text=c)
        t.column(c, width=120)
    for it in parsed[:200]:
        t.insert("", "end", values=(
            it.get("model"), it.get("category"), it.get("supplier"),
            it.get("purchase_price"), it.get("selling_price"), it.get("stock"),
        ))
    t.pack(fill="both", expand=True)

    def proceed():
        merge = messagebox.askyesno(
            "Import", "Merge with existing inventory?\nYes = merge, No = replace", parent=pv
        )
        try:
            if merge:
                # Merge: Only update products that don't exist, preserve existing
                existing_models = {p.get("model") for p in svc.inventory.get_all_products()}
                for item in parsed:
                    if item.get("model") not in existing_models:
                        svc.inventory.upsert_product(item, username=getattr(app_state, "username", "system"))
            else:
                # Replace: Upsert all products (overwrite existing)
                for item in parsed:
                    svc.inventory.upsert_product(item, username=getattr(app_state, "username", "system"))
            messagebox.showinfo("Import", "Inventory imported successfully", parent=pv)
        except Exception:
            logging.exception("Import failed")
            messagebox.showerror("Import Failed", "Failed to import inventory from CSV", parent=pv)
        pv.destroy()

    pv.add_button_bar([
        {"text": "Proceed with Import", "command": proceed, "style": "Accent.TButton"},
        {"text": "Cancel", "command": pv.destroy, "style": "TButton"}
    ])
