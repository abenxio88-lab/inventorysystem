from PySide6 import QtWidgets, QtCore, QtGui
import logging

from utils import list_users, create_user, delete_user, set_password, load_users
from ui_theme import (
    make_card, styled_label, make_button,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_TEXT_MUTED
)
from security import (
    validate_username, validate_password_strength,
    sanitize_for_display, sanitize_html
)


def open_user_manager(master=None, current_user=None):
    # Require admin role to open user manager
    users = load_users()
    user_role = users.get(current_user, {}).get("role", "")
    if not current_user or user_role not in ["admin", "OWNER_ADMIN"]:
        try:
            QtWidgets.QMessageBox.critical(
                master if isinstance(master, QtWidgets.QWidget) else None,
                "Permission Denied",
                f"Management restricted to administrators. Your role: {user_role}"
            )
        except Exception:
            pass
        return None

    win = QtWidgets.QDialog(master) if master is not None else QtWidgets.QWidget()
    win.setWindowTitle("User Management")
    win.resize(700, 600)
    win.setMinimumSize(550, 450)

    main_widget = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(main_widget)
    main_layout.setContentsMargins(12, 12, 12, 12)

    heading_label = QtWidgets.QLabel("Users")
    heading_label.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
    main_layout.addWidget(heading_label)

    tree = QtWidgets.QTableWidget()
    tree.setColumnCount(2)
    tree.setHorizontalHeaderLabels(["Username", "Role"])
    tree.horizontalHeader().resizeSection(0, 200)
    tree.horizontalHeader().resizeSection(1, 200)
    tree.horizontalHeader().setStretchLastSection(True)
    main_layout.addWidget(tree, stretch=1)

    def refresh_from_db():
        """Reload user list from the data store."""
        tree.setRowCount(0)
        for u in list_users():
            row = tree.rowCount()
            tree.insertRow(row)
            safe_username = sanitize_for_display(u["username"])
            safe_role = sanitize_for_display(u["role"])
            tree.setItem(row, 0, QtWidgets.QTableWidgetItem(safe_username))
            tree.setItem(row, 1, QtWidgets.QTableWidgetItem(safe_role))

    def add_user():
        username, ok = QtWidgets.QInputDialog.getText(win, "New User", "Username:")
        if not ok or not username:
            return

        if not validate_username(username):
            QtWidgets.QMessageBox.critical(win, "Invalid Username",
                               "Username must be 3-50 characters, start with a letter, "
                               "and contain only letters, numbers, and underscores.")
            return

        password, ok = QtWidgets.QInputDialog.getText(win, "Password", f"Password for {username}:",
                                                       QtWidgets.QLineEdit.Password)
        if not ok or not password:
            return

        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            QtWidgets.QMessageBox.critical(win, "Weak Password", error_msg)
            return

        role, ok = QtWidgets.QInputDialog.getText(win, "Role", f"Role for {username} (admin/staff):")
        if not ok:
            role = "staff"
        else:
            role = role.lower().strip()
            if role not in ["admin", "staff", "manager", "viewer"]:
                role = "staff"

        try:
            create_user(username, password, role)
            QtWidgets.QMessageBox.information(win, "User Created", f"User '{sanitize_for_display(username)}' created successfully")
            refresh_from_db()
        except ValueError as e:
            QtWidgets.QMessageBox.critical(win, "Error", f"User creation failed: {str(e)}")
            logging.warning(f"Failed to create user {username}: {e}")
        except Exception as e:
            logging.exception("Failed to create user")
            QtWidgets.QMessageBox.critical(win, "Error", str(e))

    def remove_user():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.critical(win, "Select", "Select a user to delete")
            return
        row = selected_rows[0].row()
        username = tree.item(row, 0).text() if tree.item(row, 0) else ""
        reply = QtWidgets.QMessageBox.question(win, "Confirm", f"Delete user '{username}'?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            try:
                delete_user(username)
                refresh_from_db()
            except Exception:
                logging.exception("Failed to delete user")
                QtWidgets.QMessageBox.critical(win, "Error", "Failed to delete user")

    def change_password():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.critical(win, "Select", "Select a user")
            return
        row = selected_rows[0].row()
        username = tree.item(row, 0).text() if tree.item(row, 0) else ""
        new_pw, ok = QtWidgets.QInputDialog.getText(win, "New Password", f"New password for {username}:",
                                                     QtWidgets.QLineEdit.Password)
        if not ok or not new_pw:
            return

        is_valid, error_msg = validate_password_strength(new_pw)
        if not is_valid:
            QtWidgets.QMessageBox.critical(win, "Weak Password", error_msg)
            return

        confirm_pw, ok = QtWidgets.QInputDialog.getText(win, "Confirm Password", f"Confirm new password:",
                                                         QtWidgets.QLineEdit.Password)
        if not ok or not confirm_pw or confirm_pw != new_pw:
            QtWidgets.QMessageBox.critical(win, "Error", "Passwords do not match")
            return

        try:
            set_password(username, new_pw)
            QtWidgets.QMessageBox.information(win, "Password", f"Password for '{sanitize_for_display(username)}' updated successfully")
        except Exception as e:
            logging.exception("Failed to set password")
            QtWidgets.QMessageBox.critical(win, "Error", f"Failed to set password: {str(e)}")

    btn_frame = QtWidgets.QWidget()
    btn_layout = QtWidgets.QHBoxLayout(btn_frame)
    btn_layout.setContentsMargins(0, 0, 0, 0)

    add_btn = QtWidgets.QPushButton("Add")
    add_btn.clicked.connect(add_user)
    add_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px; border-radius: 3px;")
    btn_layout.addWidget(add_btn)

    delete_btn = QtWidgets.QPushButton("Delete")
    delete_btn.clicked.connect(remove_user)
    delete_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 5px 15px; border-radius: 3px;")
    btn_layout.addWidget(delete_btn)

    change_pw_btn = QtWidgets.QPushButton("Change Password")
    change_pw_btn.clicked.connect(change_password)
    change_pw_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    btn_layout.addWidget(change_pw_btn)

    main_layout.addWidget(btn_frame)

    refresh_from_db()

    if isinstance(win, QtWidgets.QDialog):
        win.setLayout(main_layout)
        win.exec()

    return win
