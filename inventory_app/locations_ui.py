"""
Locations UI Tab
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


def create_locations_tab(parent, current_user=None):
    """Creates the locations/warehouse management tab."""
    window = QtWidgets.QWidget()
    window.setContentsMargins(15, 15, 15, 15)

    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(0)

    header_label = QtWidgets.QLabel("Locations & Warehouses")
    header_label.setFont(FONT_BOLD)
    header_layout.addWidget(header_label)
    header_layout.addStretch()

    def open_add_location():
        _open_location_dialog(window, current_user=current_user, mode="add")

    add_btn = QtWidgets.QPushButton("Add Location")
    add_btn.clicked.connect(open_add_location)
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
    columns = ("code", "name", "type", "city", "country", "capacity", "status")
    column_map = {
        "code": ("Code", 80),
        "name": ("Name", 200),
        "type": ("Type", 100),
        "city": ("City", 120),
        "country": ("Country", 100),
        "capacity": ("Capacity", 80),
        "status": ("Status", 80),
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
        """Reload locations from the database."""
        tree.setRowCount(0)
        locations = svc.location.get_all_locations(active_only=True)

        if search_query:
            q = search_query.lower()
            locations = [loc for loc in locations if
                         q in loc.get("name", "").lower() or
                         q in loc.get("code", "").lower() or
                         q in loc.get("city", "").lower()]

        for loc in locations:
            row = tree.rowCount()
            tree.insertRow(row)
            tree.setItem(row, 0, QtWidgets.QTableWidgetItem(str(loc.get("code", ""))))
            tree.setItem(row, 1, QtWidgets.QTableWidgetItem(str(loc.get("name", ""))))
            tree.setItem(row, 2, QtWidgets.QTableWidgetItem(str(loc.get("type", ""))))
            tree.setItem(row, 3, QtWidgets.QTableWidgetItem(str(loc.get("city", ""))))
            tree.setItem(row, 4, QtWidgets.QTableWidgetItem(str(loc.get("country", ""))))
            tree.setItem(row, 5, QtWidgets.QTableWidgetItem(str(loc.get("capacity", ""))))
            status_item = QtWidgets.QTableWidgetItem("Active" if loc.get("is_active", 1) else "Inactive")
            tree.setItem(row, 6, status_item)

    # Double-click to edit
    def on_double_click(row, col):
        code = tree.item(row, 0).text() if tree.item(row, 0) else ""
        if not code:
            return
        locations = svc.location.get_all_locations()
        loc = next((l for l in locations if l.get("code") == code), None)
        if loc:
            _open_location_dialog(window, current_user=current_user, mode="edit", existing_data=loc)

    tree.cellDoubleClicked.connect(on_double_click)

    # Initial load
    refresh_from_db()
    return window


def _open_location_dialog(master, current_user=None, mode="add", existing_data=None):
    """Open dialog to add/edit a location."""
    dlg = QtWidgets.QDialog(master)
    title = "Edit Location" if mode == "edit" else "Add Location"
    dlg.setWindowTitle(title)
    dlg.resize(500, 450)
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
        ("type", "Type", existing_data.get("type", "warehouse") if existing_data else "warehouse"),
        ("address", "Address", existing_data.get("address", "") if existing_data else ""),
        ("city", "City", existing_data.get("city", "") if existing_data else ""),
        ("country", "Country", existing_data.get("country", "") if existing_data else ""),
        ("phone", "Phone", existing_data.get("phone", "") if existing_data else ""),
        ("email", "Email", existing_data.get("email", "") if existing_data else ""),
        ("capacity", "Capacity", str(existing_data.get("capacity", 0)) if existing_data else "0"),
    ]

    widgets = {}
    for key, lbl_text, default in fields:
        if key == "type":
            w = QtWidgets.QComboBox()
            w.addItems(["warehouse", "store", "office"])
            w.setCurrentText(default)
            form_layout.addRow(lbl_text, w)
            widgets[key] = w
        else:
            w = QtWidgets.QLineEdit()
            w.setText(default)
            form_layout.addRow(lbl_text, w)
            widgets[key] = w

    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)
    btn_layout.addStretch()

    def save():
        data = {}
        for k, w in widgets.items():
            if isinstance(w, QtWidgets.QComboBox):
                data[k] = w.currentText()
            else:
                data[k] = w.text()

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
                    QtWidgets.QMessageBox.critical(dlg, "Error", "Location code already exists")
                    return
                svc.location.add_location(data, username=username)
                QtWidgets.QMessageBox.information(dlg, "Success", "Location added successfully")
            else:
                code = existing_data.get("code")
                update_data = {k: v for k, v in data.items() if k != "code"}
                svc.location.update_location(code, update_data, username=username)
                QtWidgets.QMessageBox.information(dlg, "Success", "Location updated successfully")
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
        # Refresh the parent - caller should handle this
        pass
