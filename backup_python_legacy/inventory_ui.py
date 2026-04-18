"""
Inventory UI Tab
================
UI-ONLY layer. Reads data through the service layer.
After every write (add/update/delete) it calls refresh_from_db()
so the table view always reflects the true database state.

RULES:
  - No SQL queries here.
  - No direct database access.
  - All data reads go through svc.inventory
  - All data writes go through svc.inventory
"""

from PySide6 import QtWidgets, QtCore, QtGui
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


def _show_info(parent, title, text):
    QtWidgets.QMessageBox.information(parent, title, text)


def _show_warning(parent, title, text):
    QtWidgets.QMessageBox.warning(parent, title, text)


def _show_error(parent, title, text):
    QtWidgets.QMessageBox.critical(parent, title, text)


def _ask_yes_no(parent, title, text):
    return QtWidgets.QMessageBox.question(parent, title, text,
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes


def _ask_yes_no_cancel(parent, title, text):
    return QtWidgets.QMessageBox.question(parent, title, text,
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)


def create_inventory_tab(parent, current_user="Unknown"):
    """Creates the premium inventory management tab."""
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)
    main_layout.setSpacing(10)

    # ── Header ────────────────────────────────────────────
    header = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header)
    header_layout.setContentsMargins(20, 20, 20, 20)

    heading_label = QtWidgets.QLabel("📦 STOCK MANAGEMENT")
    heading_label.setStyleSheet(f"font-size: {FONT_HEADING}; font-weight: bold;")
    header_layout.addWidget(heading_label)

    header_layout.addStretch()

    total_lbl = QtWidgets.QLabel("Total Stock Items: 0")
    total_lbl.setStyleSheet(f"font-weight: bold; color: {COLOR_PRIMARY};")
    header_layout.addWidget(total_lbl)

    main_layout.addWidget(header)

    # ── Layout ────────────────────────────────────────────
    paned_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
    main_layout.addWidget(paned_splitter)

    left_frame = QtWidgets.QWidget()
    left_layout = QtWidgets.QVBoxLayout(left_frame)
    left_layout.setContentsMargins(20, 20, 20, 20)
    left_layout.setSpacing(10)
    paned_splitter.addWidget(left_frame)

    right_frame = QtWidgets.QWidget()
    right_layout = QtWidgets.QVBoxLayout(right_frame)
    right_layout.setContentsMargins(20, 20, 20, 20)
    right_layout.setSpacing(10)
    paned_splitter.addWidget(right_frame)

    paned_splitter.setSizes([1, 3])

    # ── undo stack (local to this tab) ────────────────────
    undo_stack = []

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    #  Every UI refresh reads fresh data through the service.
    # ========================================================
    # We store tree reference in a closure container
    tree_container = {"tree": None}

    def refresh_from_db(filtered_data=None):
        """Reload the table view and stats from the database."""
        _update_total()
        _populate_table(filtered_data)
        _refresh_model_dropdown()

    def _update_total():
        stats = get_db_stats()
        total = stats.get("total_products", 0)
        total_lbl.setText(f"Total Stock Items: {total:,}")

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

    def _populate_table(items=None):
        """Fill the table — dynamically matches table columns from DB data."""
        tree = tree_container["tree"]
        if tree is None:
            return

        tree.setRowCount(0)

        if items is None:
            items = svc.inventory.get_all_products(active_only=True)

        actual_columns = tree_container.get("columns", [])

        for i, item in enumerate(items):
            stock_val = int(item.get("stock", 0))

            values = []
            for col in actual_columns:
                raw = item.get(col, "")

                if col == "category_id":
                    values.append(_resolve_category_display(item))
                elif col == "supplier_id":
                    values.append(_resolve_supplier_display(item))
                elif col in ("purchase_price", "selling_price"):
                    val = float(raw) if raw else 0
                    values.append(f'{val:,}')
                elif col == "stock":
                    values.append(str(stock_val))
                elif col == "expiry_date":
                    values.append(str(raw)[:10] if raw else "-")
                else:
                    values.append(str(raw) if raw else "-")

            tree.insertRow(i)
            for j, val in enumerate(values):
                tree.setItem(i, j, QtWidgets.QTableWidgetItem(val))

            # Color low stock rows
            if stock_val <= 5:
                for j in range(len(values)):
                    cell_item = tree.item(i, j)
                    if cell_item:
                        cell_item.setBackground(QtGui.QColor("#FEF2F2"))
                        cell_item.setForeground(QtGui.QColor("#DC2626"))

    def _refresh_model_dropdown():
        """Update the model dropdown with current product models."""
        items = svc.inventory.get_all_products(active_only=True)
        models = sorted({i.get("model") for i in items if i.get("model")})
        if "form" in globals() and "model" in form.widgets:
            widget = form.widgets["model"]
            try:
                if isinstance(widget, QtWidgets.QComboBox):
                    widget.clear()
                    widget.addItems(models)
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

    form_heading = QtWidgets.QLabel("PRODUCT INFORMATION")
    form_heading.setStyleSheet(f"font-size: {FONT_HEADING}; font-weight: bold;")
    left_layout.addWidget(form_heading)

    form_card = QtWidgets.QWidget()
    form_card_layout = QtWidgets.QVBoxLayout(form_card)
    form_card_layout.setContentsMargins(20, 20, 20, 20)
    left_layout.addWidget(form_card)

    form = DynamicFormBuilder(form_card, get_industry_type(), "products")
    form.build_form()

    def clear_form():
        for widget in form.widgets.values():
            try:
                if isinstance(widget, QtWidgets.QLineEdit):
                    widget.clear()
                elif isinstance(widget, QtWidgets.QComboBox):
                    widget.setCurrentIndex(-1)
                elif isinstance(widget, QtWidgets.QTextEdit):
                    widget.clear()
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
                _show_error(window, "Invalid Selection", str(e))
                return

        model = values.get("model", "").strip()
        if not model:
            _show_error(window, "Error", "Model name required")
            return

        try:
            # Check duplicate
            existing = svc.inventory.get_product_by_model(model)
            if existing:
                _show_error(window, "Error", "Model already exists — use Update")
                return

            svc.inventory.add_product(values, username=current_user)
            report_info(f"Inventory Added: {model}", module="Inventory")
            refresh_from_db()
            clear_form()
        except Exception as e:
            report_error("Failed to add inventory item", exception=e, module="Inventory")
            _show_error(window, "Operation Failed", str(e))

    def update_item():
        """Update an existing product through the service layer."""
        values = form.get_values()

        # Normalize category_id/supplier_id to integer IDs
        for field in ('category_id', 'supplier_id'):
            try:
                values[field] = _parse_related_id(field, values.get(field, ""))
            except ValueError as e:
                _show_error(window, "Invalid Selection", str(e))
                return

        model = values.get("model", "").strip()
        if not model:
            _show_error(window, "Error", "Model name required")
            return

        try:
            existing = svc.inventory.get_product_by_model(model)
            if not existing:
                _show_error(window, "Error", "Model not found — use Add to create new model")
                return

            svc.inventory.update_product(model, values, username=current_user)
            report_info(f"Inventory Updated: {model}", module="Inventory")
            refresh_from_db()
            clear_form()
        except Exception as e:
            report_error("Failed to update inventory item", exception=e, module="Inventory")
            _show_error(window, "Operation Failed", str(e))

    def delete_item():
        """Delete a product through the service layer."""
        tree = tree_container["tree"]
        if tree is None:
            return
        sel = tree.currentRow()
        if sel < 0:
            _show_error(window, "Error", "Select item to delete")
            return

        if not _is_admin():
            _show_error(window, "Permission Denied", "Only admins can delete items")
            return

        model_item = tree.item(sel, 0)
        if model_item is None:
            return
        model = model_item.text()
        if not _ask_yes_no(window, "Confirm", f"Delete {model}?"):
            return

        try:
            svc.inventory.delete_product(model, username=current_user)
            report_info(f"Inventory Deleted: {model}", module="Inventory")
            refresh_from_db()
            clear_form()
        except Exception as e:
            report_error("Failed to delete inventory item", exception=e, module="Inventory")
            _show_error(window, "Operation Failed", str(e))

    def undo_action():
        if not undo_stack:
            _show_info(window, "Undo", "Nothing to undo")
            return
        prev = undo_stack.pop()
        try:
            svc.inventory.upsert_product(prev, username=current_user)
            refresh_from_db()
            clear_form()
            logging.info("Undo applied")
        except Exception:
            logging.error("Failed to undo", exc_info=True)
            _show_error(window, "Error", "Failed to undo")

    # ── Action buttons ────────────────────────────────────
    btn_frame = QtWidgets.QWidget()
    btn_frame_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_frame_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(btn_frame)

    btn_add = QtWidgets.QPushButton("Add Item")
    btn_add.clicked.connect(add_item)
    btn_frame_layout.addWidget(btn_add)

    btn_update = QtWidgets.QPushButton("Update Item")
    btn_update.clicked.connect(update_item)
    btn_frame_layout.addWidget(btn_update)

    btn_delete = QtWidgets.QPushButton("Delete Item")
    btn_delete.clicked.connect(delete_item)
    btn_frame_layout.addWidget(btn_delete)

    btn_frame_2 = QtWidgets.QWidget()
    btn_frame_2_layout = QtWidgets.QHBoxLayout(btn_frame_2)
    btn_frame_2_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.addWidget(btn_frame_2)

    btn_undo = QtWidgets.QPushButton("Undo")
    btn_undo.clicked.connect(undo_action)
    btn_frame_2_layout.addWidget(btn_undo)

    btn_clear = QtWidgets.QPushButton("Clear Form")
    btn_clear.clicked.connect(clear_form)
    btn_frame_2_layout.addWidget(btn_clear)

    # ========================================================
    #  TOOLBAR / SEARCH
    # ========================================================
    toolbar = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 6, 0, 6)
    right_layout.addWidget(toolbar)

    search_label = QtWidgets.QLabel("Search:")
    toolbar_layout.addWidget(search_label)

    search_entry = QtWidgets.QLineEdit()
    toolbar_layout.addWidget(search_entry, stretch=1)

    def apply_search():
        q = search_entry.text().strip().lower()
        if not q:
            refresh_from_db()
            return
        all_items = svc.inventory.get_all_products(active_only=True)
        results = [it for it in all_items if q in " ".join(str(v) for v in it.values()).lower()]
        refresh_from_db(filtered_data=results)

    search_entry.textChanged.connect(apply_search)

    btn_search = QtWidgets.QPushButton("Search")
    btn_search.clicked.connect(apply_search)
    toolbar_layout.addWidget(btn_search)

    btn_clear_search = QtWidgets.QPushButton("Clear")
    btn_clear_search.clicked.connect(lambda: (search_entry.clear(), refresh_from_db()))
    toolbar_layout.addWidget(btn_clear_search)

    # ── Extra toolbar buttons ─────────────────────────────
    def on_export_csv():
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            window,
            "Export CSV",
            f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV files (*.csv)"
        )
        if not fname:
            return
        try:
            _export_to_csv(fname)
            _show_info(window, "Export", f"Exported inventory to: {fname}")
        except Exception:
            logging.exception("Export failed")
            _show_error(window, "Export Failed", "Failed to export inventory to CSV")

    def on_import_csv():
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(
            window,
            "Import CSV",
            "",
            "CSV files (*.csv)"
        )
        if not fname:
            return
        if not _is_admin():
            _show_error(window, "Permission Denied", "Only admins can import inventory")
            return
        _preview_and_import_csv(fname)

    def on_backup():
        if not _is_admin():
            _show_error(window, "Permission Denied", "Only admins can run backups")
            return
        try:
            from utils import backup_data
            dest = backup_data()
            _show_info(window, "Backup", f"Data backed up to: {dest}")
        except Exception:
            logging.exception("Backup failed")
            _show_error(window, "Backup Failed", "Failed to backup data")

    def on_generate_qr():
        tree = tree_container["tree"]
        if tree is None:
            return
        sel = tree.currentRow()
        if sel < 0:
            _show_error(window, "Error", "Select item to generate QR")
            return
        model_item = tree.item(sel, 0)
        if model_item is None:
            return
        model = model_item.text()
        item = svc.inventory.get_product_by_model(model)
        if item:
            try:
                if "id" not in item:
                    item["id"] = abs(hash(model)) % 1000000
                from barcode_system import generate_product_barcode
                path = generate_product_barcode(item)
                if path:
                    _show_info(window, "Success", f"QR/Barcode generated at:\n{path}")
                    os.startfile(os.path.dirname(path))
            except Exception as e:
                logging.exception("QR generation failed")
                _show_error(window, "Error", f"Failed to generate QR: {e}")

    btn_export = QtWidgets.QPushButton("Export CSV")
    btn_export.clicked.connect(on_export_csv)
    toolbar_layout.addWidget(btn_export)

    btn_import = QtWidgets.QPushButton("Import CSV")
    btn_import.clicked.connect(on_import_csv)
    toolbar_layout.addWidget(btn_import)

    btn_backup = QtWidgets.QPushButton("Backup")
    btn_backup.clicked.connect(on_backup)
    toolbar_layout.addWidget(btn_backup)

    btn_qr = QtWidgets.QPushButton("Generate QR")
    btn_qr.clicked.connect(on_generate_qr)
    toolbar_layout.addWidget(btn_qr)

    toolbar_layout.addStretch()

    state = {"full": False}
    def toggle_fullscreen():
        state["full"] = not state["full"]
        top_level = window.window()
        if isinstance(top_level, QtWidgets.QMainWindow):
            if state["full"]:
                top_level.showFullScreen()
            else:
                top_level.showNormal()

    btn_fullscreen = QtWidgets.QPushButton("⛶")
    btn_fullscreen.clicked.connect(toggle_fullscreen)
    toolbar_layout.addWidget(btn_fullscreen)

    # ========================================================
    #  TABLE VIEW — columns built 100% from form field configs
    # ========================================================
    table_frame = QtWidgets.QWidget()
    table_frame_layout = QtWidgets.QVBoxLayout(table_frame)
    table_frame_layout.setContentsMargins(10, 10, 10, 10)
    right_layout.addWidget(table_frame, stretch=1)

    from migration_add_industry_type import get_industry_type
    from unified_data_entry import IndustryConfig

    industry_mode = get_industry_type()
    field_configs = IndustryConfig.get_fields(industry_mode, "products")

    # Build label lookup
    _labels = {}
    for fc in field_configs:
        _labels[fc["name"]] = fc["label"]

    # Build column map directly from field configs — EXACT same fields as form
    # Show ALL form fields in the table
    column_map = {}
    for fc in field_configs:
        name = fc["name"]
        label_text = fc["label"]
        column_map[name] = (label_text, 100)

    columns = list(column_map.keys())
    tree_container["columns"] = columns

    tree = QtWidgets.QTableWidget()
    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([label_text.upper() for label_text, _ in column_map.values()])
    tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    tree.setAlternatingRowColors(True)
    tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    for i, (col, (label_text, width)) in enumerate(column_map.items()):
        tree.setColumnWidth(i, width)

    tree_container["tree"] = tree
    table_frame_layout.addWidget(tree)

    def on_table_cell_double_clicked(row, column):
        pass  # Selection handles loading

    tree.cellDoubleClicked.connect(on_table_cell_double_clicked)

    def on_table_selection_changed(current, previous):
        if current.row() < 0:
            clear_form()
            return
        model_item = tree.item(current.row(), 0)
        if model_item is None:
            return
        model_name = model_item.text()
        item = svc.inventory.get_product_by_model(model_name)
        if not item:
            return

        for field_name, widget in form.widgets.items():
            val = item.get(field_name, "")

            try:
                # For combobox widgets (category_id, supplier_id), show human text or fall back
                if field_name == 'category_id':
                    display_text = _resolve_category_display(item)
                    if isinstance(widget, QtWidgets.QComboBox):
                        idx = widget.findText(display_text)
                        if idx >= 0:
                            widget.setCurrentIndex(idx)
                        else:
                            widget.setEditText(display_text)
                elif field_name == 'supplier_id':
                    display_text = _resolve_supplier_display(item)
                    if isinstance(widget, QtWidgets.QComboBox):
                        idx = widget.findText(display_text)
                        if idx >= 0:
                            widget.setCurrentIndex(idx)
                        else:
                            widget.setEditText(display_text)
                elif isinstance(widget, QtWidgets.QLineEdit):
                    widget.setText(str(val))
                elif isinstance(widget, QtWidgets.QComboBox):
                    idx = widget.findText(str(val))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                elif isinstance(widget, QtWidgets.QTextEdit):
                    widget.setPlainText(str(val))
            except Exception:
                pass

    tree.currentCellChanged.connect(on_table_selection_changed)

    # ── Initial load ──────────────────────────────────────
    refresh_from_db()

    # ── Key bindings ──────────────────────────────────────
    def focus_next_on_return():
        window.focusNextChild()

    search_entry.returnPressed.connect(focus_next_on_return)

    if "form" in globals():
        for name, w in form.widgets.items():
            try:
                if isinstance(w, QtWidgets.QLineEdit):
                    w.returnPressed.connect(focus_next_on_return)
            except Exception:
                pass

    window.setFocus()
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

    # Create a preview dialog
    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Import Preview")
    dialog.resize(900, 500)
    dialog_layout = QtWidgets.QVBoxLayout(dialog)

    preview_label = QtWidgets.QLabel(
        f"Previewing {os.path.basename(filepath)} — {len(parsed)} valid, {len(invalid)} invalid"
    )
    preview_label.setStyleSheet(f"font-size: {FONT_HEADING}; font-weight: bold;")
    dialog_layout.addWidget(preview_label)

    table_widget = QtWidgets.QTableWidget()
    cols = ("model", "category", "supplier", "purchase_price", "selling_price", "stock")
    table_widget.setColumnCount(len(cols))
    table_widget.setHorizontalHeaderLabels([c.upper() for c in cols])
    table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    for i, it in enumerate(parsed[:200]):
        table_widget.insertRow(i)
        for j, col_name in enumerate(cols):
            val = it.get(col_name, "")
            table_widget.setItem(i, j, QtWidgets.QTableWidgetItem(str(val)))

    dialog_layout.addWidget(table_widget)

    btn_layout = QtWidgets.QHBoxLayout()

    def proceed():
        merge = _ask_yes_no_cancel(dialog, "Import", "Merge with existing inventory?\nYes = merge, No = replace") == QtWidgets.QMessageBox.Yes
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
            _show_info(dialog, "Import", "Inventory imported successfully")
        except Exception:
            logging.exception("Import failed")
            _show_error(dialog, "Import Failed", "Failed to import inventory from CSV")
        dialog.accept()

    btn_import = QtWidgets.QPushButton("Proceed with Import")
    btn_import.clicked.connect(proceed)
    btn_layout.addWidget(btn_import)

    btn_cancel = QtWidgets.QPushButton("Cancel")
    btn_cancel.clicked.connect(dialog.reject)
    btn_layout.addWidget(btn_cancel)

    dialog_layout.addLayout(btn_layout)

    dialog.exec()
