from PySide6 import QtWidgets, QtCore, QtGui
import json
import os
import logging

from utils import AUDIT_LOG, load_users
from ui_theme import make_card, styled_label, make_button, frame


def open_audit_viewer(master=None, current_user=None):
    # Only admins allowed
    users = load_users()
    user_role = users.get(current_user, {}).get("role", "")
    if not current_user or user_role not in ["admin", "OWNER_ADMIN"]:
        try:
            QtWidgets.QMessageBox.critical(
                master if isinstance(master, QtWidgets.QWidget) else None,
                "Permission Denied",
                f"Audit logs restricted to administrators. Your role: {user_role}"
            )
        except Exception:
            pass
        return None

    win = QtWidgets.QDialog(master) if master is not None else QtWidgets.QWidget()
    win.setWindowTitle("Audit Log Viewer")
    win.resize(900, 500)

    top = QtWidgets.QWidget()
    top_layout = QtWidgets.QVBoxLayout(top)
    top_layout.setContentsMargins(12, 12, 12, 12)

    heading_label = QtWidgets.QLabel("Audit Events")
    heading_label.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
    top_layout.addWidget(heading_label)

    toolbar = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    search_label = QtWidgets.QLabel("Search:")
    toolbar_layout.addWidget(search_label)

    search_entry = QtWidgets.QLineEdit()
    toolbar_layout.addWidget(search_entry, stretch=1)

    def load_entries():
        rows = []
        if not os.path.exists(AUDIT_LOG):
            return rows
        try:
            with open(AUDIT_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    rows.append(obj)
        except Exception:
            logging.exception("Failed to read audit log")
        return rows

    cols = ("timestamp", "user", "action", "target", "details")
    tree = QtWidgets.QTableWidget()
    tree.setColumnCount(len(cols))
    tree.setHorizontalHeaderLabels([c.capitalize() for c in cols])
    for i in range(len(cols)):
        tree.horizontalHeader().resizeSection(i, 150)
    tree.horizontalHeader().setStretchLastSection(True)
    top_layout.addWidget(tree)

    def refresh(filter_text=None):
        tree.setRowCount(0)
        entries = load_entries()
        q = (filter_text or "").lower()
        for e in entries:
            details = e.get("details")
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False)
            vals = (e.get("timestamp"), e.get("user"), e.get("action"), e.get("target"), details)
            if not q or q in " ".join([str(v).lower() for v in vals]):
                row = tree.rowCount()
                tree.insertRow(row)
                for col_idx, val in enumerate(vals):
                    tree.setItem(row, col_idx, QtWidgets.QTableWidgetItem(str(val) if val else ""))

    def on_search():
        refresh(search_entry.text())

    search_btn = QtWidgets.QPushButton("Search")
    search_btn.clicked.connect(on_search)
    search_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    toolbar_layout.addWidget(search_btn)

    refresh_btn = QtWidgets.QPushButton("Refresh")
    refresh_btn.clicked.connect(lambda: refresh(search_entry.text()))
    refresh_btn.setStyleSheet("padding: 5px 15px; border-radius: 3px;")
    toolbar_layout.addWidget(refresh_btn)

    top_layout.addWidget(toolbar)

    refresh()

    if isinstance(win, QtWidgets.QDialog):
        win.setLayout(top_layout)
        win.exec()
    return win


def create_audit_tab(parent, current_user=None):
    """Embeddable version for notebook tabs."""
    tab = QtWidgets.QWidget()
    tab.setContentsMargins(12, 12, 12, 12)

    main_layout = QtWidgets.QVBoxLayout(tab)
    main_layout.setContentsMargins(0, 0, 0, 0)

    heading_label = QtWidgets.QLabel("Audit Events")
    heading_label.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
    main_layout.addWidget(heading_label)

    toolbar = QtWidgets.QWidget()
    toolbar_layout = QtWidgets.QHBoxLayout(toolbar)
    toolbar_layout.setContentsMargins(0, 0, 0, 0)

    search_label = QtWidgets.QLabel("Search:")
    toolbar_layout.addWidget(search_label)

    search_entry = QtWidgets.QLineEdit()
    toolbar_layout.addWidget(search_entry, stretch=1)

    def load_entries():
        rows = []
        if not os.path.exists(AUDIT_LOG):
            return rows
        try:
            with open(AUDIT_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    rows.append(obj)
        except Exception:
            logging.exception("Failed to read audit log")
        return rows

    cols = ("timestamp", "user", "action", "target", "details")
    tree = QtWidgets.QTableWidget()
    tree.setColumnCount(len(cols))
    tree.setHorizontalHeaderLabels([c.capitalize() for c in cols])
    for i in range(len(cols)):
        tree.horizontalHeader().resizeSection(i, 150)
    tree.horizontalHeader().setStretchLastSection(True)

    def refresh(filter_text=None):
        tree.setRowCount(0)
        entries = load_entries()
        q = (filter_text or "").lower()
        for e in entries:
            details = e.get("details")
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False)
            vals = (e.get("timestamp"), e.get("user"), e.get("action"), e.get("target"), details)
            if not q or q in " ".join([str(v).lower() for v in vals]):
                row = tree.rowCount()
                tree.insertRow(row)
                for col_idx, val in enumerate(vals):
                    tree.setItem(row, col_idx, QtWidgets.QTableWidgetItem(str(val) if val else ""))

    def on_search():
        refresh(search_entry.text())

    search_btn = QtWidgets.QPushButton("Search")
    search_btn.clicked.connect(on_search)
    search_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    toolbar_layout.addWidget(search_btn)

    refresh_btn = QtWidgets.QPushButton("Refresh")
    refresh_btn.clicked.connect(lambda: refresh(search_entry.text()))
    refresh_btn.setStyleSheet("padding: 5px 15px; border-radius: 3px;")
    toolbar_layout.addWidget(refresh_btn)

    main_layout.addWidget(toolbar)
    main_layout.addWidget(tree, stretch=1)

    refresh()
    return tab
