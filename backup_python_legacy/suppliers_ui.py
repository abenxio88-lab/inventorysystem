"""
Suppliers UI Tab
=================
UI-ONLY layer. All data goes through the service layer.
After every write, refresh_from_db() reloads fresh data.
"""

from PySide6 import QtWidgets, QtCore, QtGui
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
    window = QtWidgets.QWidget()
    window.setContentsMargins(15, 15, 15, 15)

    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    header_label = QtWidgets.QLabel("Supplier Management")
    header_label.setFont(FONT_BOLD)
    header_layout.addWidget(header_label)
    header_layout.addStretch()

    def open_add_supplier():
        _open_supplier_dialog(window, current_user=current_user, mode="add")

    add_btn = QtWidgets.QPushButton("Add Supplier")
    add_btn.clicked.connect(open_add_supplier)
    add_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px; border-radius: 3px;")
    header_layout.addWidget(add_btn)

    main_layout.addWidget(header_frame)

    # Search
    toolbar = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    search_label = QtWidgets.QLabel("Search:")
    toolbar_layout.addWidget(search_label)

    search_entry = QtWidgets.QLineEdit()
    toolbar_layout.addWidget(search_entry, stretch=1)

    def apply_search():
        q = search_entry.text().strip()
        refresh_from_db(q if q else None)

    search_btn = QtWidgets.QPushButton("Search")
    search_btn.clicked.connect(apply_search)
    search_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    toolbar_layout.addWidget(search_btn)

    clear_btn = QtWidgets.QPushButton("Clear")
    clear_btn.clicked.connect(lambda: (search_entry.clear(), refresh_from_db()))
    clear_btn.setStyleSheet("padding: 5px 15px; border-radius: 3px;")
    toolbar_layout.addWidget(clear_btn)

    main_layout.addWidget(toolbar)

    # Table
    table_frame = QtWidgets.QWidget()
    table_layout = QtWidgets.QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    tree = QtWidgets.QTableWidget()
    columns = ("code", "name", "contact_person", "phone", "city", "rating", "lead_time", "status")
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

    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([column_map[c][0].upper() for c in columns])
    for i, col in enumerate(columns):
        tree.horizontalHeader().resizeSection(i, column_map[col][1])
    tree.horizontalHeader().setStretchLastSection(True)

    table_layout.addWidget(tree)
    main_layout.addWidget(table_frame, stretch=1)

    # ========================================================
    #  SINGLE SOURCE OF TRUTH: refresh_from_db()
    # ========================================================

    def refresh_from_db(search_query=None):
        """Reload suppliers from the database."""
        tree.setRowCount(0)
        suppliers = svc.supplier.get_all_suppliers(active_only=True)

        if search_query:
            q = search_query.lower()
            suppliers = [s for s in suppliers if
                         q in s.get("name", "").lower() or
                         q in s.get("code", "").lower() or
                         q in s.get("contact_person", "").lower()]

        for s in suppliers:
            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QtWidgets.QTableWidgetItem(str(s.get("code", ""))))
            tree.setItem(row, 1, QtWidgets.QTableWidgetItem(str(s.get("name", ""))))
            tree.setItem(row, 2, QtWidgets.QTableWidgetItem(str(s.get("contact_person", ""))))
            tree.setItem(row, 3, QtWidgets.QTableWidgetItem(str(s.get("phone", ""))))
            tree.setItem(row, 4, QtWidgets.QTableWidgetItem(str(s.get("city", ""))))
            tree.setItem(row, 5, QtWidgets.QTableWidgetItem(str(s.get("rating", 5))))
            tree.setItem(row, 6, QtWidgets.QTableWidgetItem(str(s.get("lead_time_days", 7))))
            tree.setItem(row, 7, QtWidgets.QTableWidgetItem("Active" if s.get("is_active", 1) else "Inactive"))

    # Double-click to edit
    def on_double_click(row, col):
        code = tree.item(row, 0).text() if tree.item(row, 0) else ""
        if not code:
            return
        suppliers = svc.supplier.get_all_suppliers()
        supplier = next((s for s in suppliers if s.get("code") == code), None)
        if supplier:
            _open_supplier_dialog(window, current_user=current_user, mode="edit", existing_data=supplier)

    tree.cellDoubleClicked.connect(on_double_click)

    # Initial load
    refresh_from_db()
    return window


def _open_supplier_dialog(master, current_user=None, mode="add", existing_data=None):
    """Open dialog to add/edit a supplier."""
    dlg = QtWidgets.QDialog(master)
    title = "Edit Supplier" if mode == "edit" else "Add Supplier"
    dlg.setWindowTitle(title)
    dlg.resize(650, 550)
    dlg.setModal(True)

    main_layout = QtWidgets.QVBoxLayout(dlg)
    main_layout.setContentsMargins(10, 10, 10, 10)

    form_card = QtWidgets.QWidget()
    form_layout = QtWidgets.QFormLayout(form_card)
    form_layout.setContentsMargins(20, 20, 20, 20)
    main_layout.addWidget(form_card)

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
    for key, lbl_text, default in fields:
        w = QtWidgets.QLineEdit()
        w.setText(default)
        form_layout.addRow(lbl_text, w)
        widgets[key] = w

    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    btn_layout.addStretch()

    def save():
        data = {k: v.text() for k, v in widgets.items()}
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
                    QtWidgets.QMessageBox.critical(dlg, "Error", "Supplier code already exists")
                    return
                svc.supplier.add_supplier(data, username=username)
                QtWidgets.QMessageBox.information(dlg, "Success", "Supplier added successfully")
            else:
                code = existing_data.get("code")
                update_data = {k: v for k, v in data.items() if k != "code"}
                svc.supplier.update_supplier(code, update_data, username=username)
                QtWidgets.QMessageBox.information(dlg, "Success", "Supplier updated successfully")
            dlg.accept()
        except Exception as e:
            QtWidgets.QMessageBox.critical(dlg, "Error", str(e))

    save_btn = QtWidgets.QPushButton("Save")
    save_btn.clicked.connect(save)
    save_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    btn_layout.addWidget(save_btn)

    cancel_btn = QtWidgets.QPushButton("Cancel")
    cancel_btn.clicked.connect(dlg.reject)
    cancel_btn.setStyleSheet("padding: 5px 15px; border-radius: 3px;")
    btn_layout.addWidget(cancel_btn)

    main_layout.addWidget(btn_frame)

    if dlg.exec() == QtWidgets.QDialog.Accepted:
        pass
