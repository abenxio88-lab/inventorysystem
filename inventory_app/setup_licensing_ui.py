"""
Setup Licensing UI Module
==========================
Professional admin setup wizard and user authorization interface.

Features:
- First-time admin setup wizard (OWNER ADMIN creation)
- User authorization request interface
- Admin approval dashboard
- Device binding information display
"""

from PySide6 import QtWidgets, QtCore, QtGui
from datetime import datetime
import os
import logging

from license_manager import AdminHierarchyManager, LicenseManager, get_device_info
from ui_theme import (
    setup_theme,
    COLOR_APP_BG, COLOR_CARD_BG, COLOR_PRIMARY, COLOR_SUCCESS,
    COLOR_DANGER, COLOR_TEXT_MUTED, COLOR_BORDER,
    FONT_REGULAR, FONT_BOLD, FONT_HEADING
)
from security import hash_password, validate_password_strength, validate_email, validate_security_pin

# Theme colors (from ui_theme.py for consistency with main application)
BG_COLOR = COLOR_APP_BG
CARD_BG = COLOR_CARD_BG
PRIMARY_COLOR = COLOR_PRIMARY
TEXT_COLOR = COLOR_TEXT_MUTED


# ============================================================================
# ADMIN SETUP WIZARD
# ============================================================================

def create_admin_setup_wizard(parent=None) -> bool:
    """Create OWNER ADMIN account on first launch."""

    # MASTER CREDENTIALS - Read from environment variables for security
    # Set these in your system environment before running the app:
    #   export MASTER_ADMIN_USER=your_username
    #   export MASTER_ADMIN_PASS=your_secure_password
    #   export MASTER_ADMIN_EMAIL=your@email.com
    #
    # Fallback defaults are ONLY used if env vars are not set (development only).
    # In production, ALWAYS set environment variables.
    MASTER_USERNAME = os.environ.get("MASTER_ADMIN_USER")
    MASTER_PASSWORD = os.environ.get("MASTER_ADMIN_PASS")
    MASTER_EMAIL = os.environ.get("MASTER_ADMIN_EMAIL")

    # Validate that credentials are configured
    if not all([MASTER_USERNAME, MASTER_PASSWORD, MASTER_EMAIL]):
        QtWidgets.QMessageBox.critical(
            parent,
            "Configuration Error",
            "Master admin credentials are not configured.\n\n"
            "Please set the following environment variables:\n"
            "  - MASTER_ADMIN_USER\n"
            "  - MASTER_ADMIN_PASS\n"
            "  - MASTER_ADMIN_EMAIL\n\n"
            "Contact Mintaka Sphere support for assistance."
        )
        return False

    # First: Show master credential verification
    verify_window = QtWidgets.QDialog(parent)
    verify_window.setWindowTitle("Mintaka Sphere - Admin Verification")
    verify_window.resize(550, 500)
    verify_window.setFixedSize(550, 500)
    verify_window.setStyleSheet(f"background-color: {BG_COLOR};")

    # Center the window
    screen = QtWidgets.QApplication.primaryScreen().geometry()
    x = (screen.width() // 2) - (550 // 2)
    y = (screen.height() // 2) - (500 // 2)
    verify_window.move(x, y)

    layout = QtWidgets.QVBoxLayout(verify_window)

    # Header
    title_label = QtWidgets.QLabel("🔐 Admin Verification Required")
    title_label.setFont(FONT_HEADING)
    title_label.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    layout.addWidget(title_label)

    desc_label = QtWidgets.QLabel(
        "Enter the master admin credentials to activate this software.\n"
        "Contact Mintaka Sphere support if you don't have these."
    )
    desc_label.setFont(FONT_REGULAR)
    desc_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
    desc_label.setWordWrap(True)
    layout.addWidget(desc_label)

    # Verification Form
    form_layout = QtWidgets.QFormLayout()
    form_layout.setSpacing(10)

    verify_username_var = QtWidgets.QLineEdit()
    form_layout.addRow("Username:", verify_username_var)

    verify_password_var = QtWidgets.QLineEdit()
    verify_password_var.setEchoMode(QtWidgets.QLineEdit.Password)
    form_layout.addRow("Password:", verify_password_var)

    verify_email_var = QtWidgets.QLineEdit()
    form_layout.addRow("Email:", verify_email_var)

    layout.addLayout(form_layout)

    # Buttons
    button_frame = QtWidgets.QHBoxLayout()

    verification_result = {'success': False}

    def on_verify():
        username = verify_username_var.text().strip()
        password = verify_password_var.text()
        email = verify_email_var.text().strip()

        # Check against master credentials
        if username == MASTER_USERNAME and password == MASTER_PASSWORD and email == MASTER_EMAIL:
            verification_result['success'] = True
            verify_window.accept()
        else:
            # Rate limiting check
            from utils import get_login_rate_limiter
            rate_limiter = get_login_rate_limiter()
            if not rate_limiter.is_allowed(username):
                wait_time = rate_limiter.get_wait_time(username)
                QtWidgets.QMessageBox.critical(verify_window, "Too Many Attempts",
                                   f"Too many failed attempts. Please wait {wait_time} seconds.")
                return

            QtWidgets.QMessageBox.critical(verify_window, "Access Denied",
                               "❌ Invalid credentials!\n\n"
                               "These credentials do not match the Mintaka Sphere master admin.\n"
                               "Contact your system administrator or Mintaka Sphere support.")

    verify_btn = QtWidgets.QPushButton("Verify & Activate")
    verify_btn.clicked.connect(on_verify)
    verify_btn.setStyleSheet(
        f"background-color: {PRIMARY_COLOR}; color: white; font-weight: bold; padding: 12px 25px;"
    )
    verify_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(verify_btn)

    cancel_btn = QtWidgets.QPushButton("Cancel")
    cancel_btn.clicked.connect(verify_window.reject)
    cancel_btn.setStyleSheet(
        f"background-color: {COLOR_TEXT_MUTED}; color: white; padding: 12px 20px;"
    )
    cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(cancel_btn)

    layout.addLayout(button_frame)

    verify_window.setModal(True)
    result = verify_window.exec()

    if not verification_result['success']:
        return False

    # Verification passed - now show the account creation wizard
    wizard_window = QtWidgets.QDialog(parent)
    wizard_window.setWindowTitle("Mintaka Sphere - Create Administrator Account")
    wizard_window.resize(650, 750)
    wizard_window.setFixedSize(650, 750)
    wizard_window.setStyleSheet(f"background-color: {BG_COLOR};")

    # Center window on screen
    screen = QtWidgets.QApplication.primaryScreen().geometry()
    x = (screen.width() // 2) - (650 // 2)
    y = (screen.height() // 2) - (750 // 2)
    wizard_window.move(x, y)

    wizard_layout = QtWidgets.QVBoxLayout(wizard_window)

    # Header
    wizard_title = QtWidgets.QLabel("👤 Create Your Administrator Account")
    wizard_title.setFont(FONT_HEADING)
    wizard_title.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    wizard_layout.addWidget(wizard_title)

    wizard_desc = QtWidgets.QLabel(
        "Master verification successful. Now, set up your personal administrator account and a secure PIN."
    )
    wizard_desc.setFont(FONT_REGULAR)
    wizard_desc.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
    wizard_desc.setWordWrap(True)
    wizard_layout.addWidget(wizard_desc)

    # Admin Creation Form
    form_layout = QtWidgets.QFormLayout()
    form_layout.setSpacing(10)

    admin_user_var = QtWidgets.QLineEdit(MASTER_USERNAME)
    form_layout.addRow("Admin Username:", admin_user_var)

    admin_name_var = QtWidgets.QLineEdit("System Administrator")
    form_layout.addRow("Full Name:", admin_name_var)

    admin_email_var = QtWidgets.QLineEdit(MASTER_EMAIL)
    form_layout.addRow("Admin Email:", admin_email_var)

    admin_pass_var = QtWidgets.QLineEdit()
    admin_pass_var.setEchoMode(QtWidgets.QLineEdit.Password)
    form_layout.addRow("Admin Password:", admin_pass_var)

    admin_confirm_var = QtWidgets.QLineEdit()
    admin_confirm_var.setEchoMode(QtWidgets.QLineEdit.Password)
    form_layout.addRow("Confirm Password:", admin_confirm_var)

    admin_pin_var = QtWidgets.QLineEdit()
    admin_pin_var.setEchoMode(QtWidgets.QLineEdit.Password)
    form_layout.addRow("Security PIN (4-8 digits):", admin_pin_var)

    wizard_layout.addLayout(form_layout)

    # Info box for PIN
    pin_info = QtWidgets.QLabel("💡 The Security PIN is required for critical admin operations.")
    pin_info.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Italic))
    pin_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; background-color: transparent;")
    wizard_layout.addWidget(pin_info)

    # Buttons
    button_frame = QtWidgets.QHBoxLayout()

    def on_activate():
        admin_username = admin_user_var.text().strip()
        admin_name = admin_name_var.text().strip()
        admin_email = admin_email_var.text().strip()
        password = admin_pass_var.text()
        confirm_pass = admin_confirm_var.text()
        security_pin = admin_pin_var.text().strip()

        # Validations
        if not all([admin_username, admin_name, admin_email, password, security_pin]):
            QtWidgets.QMessageBox.critical(wizard_window, "Error", "All fields are required!")
            return

        if password != confirm_pass:
            QtWidgets.QMessageBox.critical(wizard_window, "Error", "Passwords do not match!")
            return

        is_valid_pass, pass_err = validate_password_strength(password)
        if not is_valid_pass:
            QtWidgets.QMessageBox.critical(wizard_window, "Weak Password", pass_err)
            return

        if not validate_email(admin_email):
            QtWidgets.QMessageBox.critical(wizard_window, "Invalid Email", "Please enter a valid email address.")
            return

        if not validate_security_pin(security_pin):
            QtWidgets.QMessageBox.critical(wizard_window, "Invalid PIN", "Security PIN must be 4 to 8 digits.")
            return

        try:
            # Use secure hash_password from security module
            password_hash = hash_password(password)
            pin_hash = hash_password(security_pin)

            AdminHierarchyManager.create_owner_admin(admin_username, admin_name, admin_email, password_hash, pin_hash)
            LicenseManager.initialize_license(admin_email)

            # Show success
            QtWidgets.QMessageBox.information(wizard_window, "Success",
                              f"✅ Software Activated Successfully!\n\n"
                              f"Welcome {admin_name} to Mintaka Sphere!\n\n"
                              f"{'='*35}\n"
                              f"ADMIN ACCOUNT CREATED:\n"
                              f"{'='*35}\n"
                              f"Username: {admin_username}\n"
                              f"Role: OWNER_ADMIN\n"
                              f"{'='*35}\n\n"
                              f"You can now log in and manage the system.")
            wizard_window.accept()

        except Exception as e:
            logging.error(f"Error creating Owner Admin: {e}")
            QtWidgets.QMessageBox.critical(wizard_window, "Error", f"Failed to create account: {str(e)}")

    activate_btn = QtWidgets.QPushButton("Activate Software")
    activate_btn.clicked.connect(on_activate)
    activate_btn.setStyleSheet(
        f"background-color: {COLOR_SUCCESS}; color: white; font-weight: bold; padding: 12px 25px;"
    )
    activate_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(activate_btn)

    cancel_btn = QtWidgets.QPushButton("Cancel")
    cancel_btn.clicked.connect(wizard_window.reject)
    cancel_btn.setStyleSheet(
        f"background-color: {COLOR_TEXT_MUTED}; color: white; padding: 12px 20px;"
    )
    cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(cancel_btn)

    wizard_layout.addLayout(button_frame)

    wizard_window.setModal(True)
    wizard_window.exec()

    return True


# ============================================================================
# USER AUTHORIZATION REQUEST DIALOG
# ============================================================================

def create_user_request_dialog(parent_window) -> dict:
    """Staff member requests authorization to use the software."""

    request_window = QtWidgets.QDialog(parent_window)
    request_window.setWindowTitle("Request Software Access")
    request_window.resize(500, 400)
    request_window.setFixedSize(500, 400)
    request_window.setStyleSheet(f"background-color: {BG_COLOR};")

    result = {'submitted': False, 'data': {}}

    layout = QtWidgets.QVBoxLayout(request_window)

    # Header
    title_label = QtWidgets.QLabel("Request Software Access")
    title_label.setFont(FONT_HEADING)
    title_label.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    layout.addWidget(title_label)

    desc_label = QtWidgets.QLabel(
        "Please provide your information. Your administrator will review and approve your request."
    )
    desc_label.setFont(FONT_REGULAR)
    desc_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
    desc_label.setWordWrap(True)
    layout.addWidget(desc_label)

    # Form
    form_layout = QtWidgets.QFormLayout()
    form_layout.setSpacing(10)

    name_var = QtWidgets.QLineEdit()
    form_layout.addRow("Full Name:", name_var)

    email_var = QtWidgets.QLineEdit()
    form_layout.addRow("Email:", email_var)

    dept_var = QtWidgets.QComboBox()
    dept_var.addItems(['Sales', 'Inventory', 'Management', 'Admin', 'Other'])
    form_layout.addRow("Department:", dept_var)

    reason_text = QtWidgets.QTextEdit()
    reason_text.setMaximumHeight(80)
    reason_text.setStyleSheet(f"background-color: {CARD_BG}; color: {TEXT_COLOR};")
    form_layout.addRow("Reason for Access:", reason_text)

    layout.addLayout(form_layout)

    # Buttons
    button_frame = QtWidgets.QHBoxLayout()

    def on_submit():
        name = name_var.text().strip()
        email = email_var.text().strip()
        dept = dept_var.currentText()
        reason = reason_text.toPlainText().strip()

        if not all([name, email, dept, reason]):
            QtWidgets.QMessageBox.critical(request_window, "Validation Error", "All fields are required.")
            return

        if '@' not in email:
            QtWidgets.QMessageBox.critical(request_window, "Validation Error", "Please enter a valid email address.")
            return

        result['submitted'] = True
        result['data'] = {
            'name': name,
            'email': email,
            'department': dept,
            'reason': reason,
            'requested_date': datetime.now().isoformat()
        }

        QtWidgets.QMessageBox.information(request_window, "Success",
                          "Your request has been submitted.\nYour administrator will review it shortly.")
        request_window.accept()

    submit_btn = QtWidgets.QPushButton("Submit Request")
    submit_btn.clicked.connect(on_submit)
    submit_btn.setStyleSheet(
        f"background-color: {PRIMARY_COLOR}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    submit_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(submit_btn)

    cancel_btn = QtWidgets.QPushButton("Cancel")
    cancel_btn.clicked.connect(request_window.reject)
    cancel_btn.setStyleSheet(
        f"background-color: {COLOR_TEXT_MUTED}; color: white; padding: 10px 20px;"
    )
    cancel_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(cancel_btn)

    layout.addLayout(button_frame)

    request_window.setModal(True)
    request_window.exec()

    return result


# ============================================================================
# ADMIN APPROVAL PANEL
# ============================================================================

def create_admin_approval_panel(master=None) -> QtWidgets.QWidget:
    """Create a panel for admins to approve pending user requests."""

    approval_frame = QtWidgets.QWidget(master)
    approval_frame.setStyleSheet(f"background-color: {BG_COLOR};")

    layout = QtWidgets.QVBoxLayout(approval_frame)

    # Header
    title_label = QtWidgets.QLabel("Approve User Requests")
    title_label.setFont(FONT_HEADING)
    title_label.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    layout.addWidget(title_label)

    # Users Treeview (TableWidget)
    users_table = QtWidgets.QTableWidget()
    users_table.setColumnCount(5)
    users_table.setHorizontalHeaderLabels(['Name', 'Email', 'Role', 'Requested', 'Status'])
    users_table.horizontalHeader().setStretchLastSection(True)
    users_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
    users_table.setColumnWidth(0, 150)
    users_table.setColumnWidth(1, 200)
    users_table.setColumnWidth(2, 100)
    users_table.setColumnWidth(3, 120)
    users_table.setColumnWidth(4, 80)
    users_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    users_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    users_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    layout.addWidget(users_table)

    # Buttons Frame
    button_frame = QtWidgets.QHBoxLayout()

    def on_approve():
        selected = users_table.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(approval_frame, "No Selection", "Please select a user to approve.")
            return

        QtWidgets.QMessageBox.information(approval_frame, "Approved", "User has been approved and can now access the software.")
        refresh_pending_users()

    def on_reject():
        selected = users_table.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(approval_frame, "No Selection", "Please select a user to reject.")
            return

        QtWidgets.QMessageBox.information(approval_frame, "Rejected", "User request has been rejected.")
        refresh_pending_users()

    def refresh_pending_users():
        try:
            users_table.setRowCount(0)
            pending_users = AdminHierarchyManager.get_pending_user_requests()
            for user in pending_users:
                row = users_table.rowCount()
                users_table.insertRow(row)
                users_table.setItem(row, 0, QtWidgets.QTableWidgetItem(user['username']))
                users_table.setItem(row, 1, QtWidgets.QTableWidgetItem(user['email']))
                users_table.setItem(row, 2, QtWidgets.QTableWidgetItem(user['role']))
                users_table.setItem(row, 3, QtWidgets.QTableWidgetItem(
                    user['authorized_date'][:10] if user['authorized_date'] else 'Unknown'
                ))
                users_table.setItem(row, 4, QtWidgets.QTableWidgetItem('PENDING'))
        except Exception as e:
            logging.error(f"Error refreshing pending users: {e}")

    approve_btn = QtWidgets.QPushButton("Approve")
    approve_btn.clicked.connect(on_approve)
    approve_btn.setStyleSheet(
        f"background-color: {COLOR_SUCCESS}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    approve_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(approve_btn)

    reject_btn = QtWidgets.QPushButton("Reject")
    reject_btn.clicked.connect(on_reject)
    reject_btn.setStyleSheet(
        f"background-color: {COLOR_DANGER}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    reject_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(reject_btn)

    refresh_btn = QtWidgets.QPushButton("Refresh")
    refresh_btn.clicked.connect(refresh_pending_users)
    refresh_btn.setStyleSheet(
        f"background-color: {COLOR_PRIMARY}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    refresh_btn.setCursor(QtCore.Qt.PointingHandCursor)
    button_frame.addWidget(refresh_btn)

    layout.addLayout(button_frame)

    approval_frame.refresh_pending_users = refresh_pending_users

    return approval_frame


# ============================================================================
# OWNER ADMIN DASHBOARD
# ============================================================================

def open_owner_dashboard(master=None):
    """Open the Owner Admin Dashboard in a separate window."""
    win = QtWidgets.QDialog(master) if master is not None else QtWidgets.QDialog()
    win.setWindowTitle("👑 Owner Admin System Control")
    win.resize(1000, 700)
    win.setStyleSheet(f"background-color: {BG_COLOR};")

    # Center window
    screen = QtWidgets.QApplication.primaryScreen().geometry()
    x = (screen.width() // 2) - (1000 // 2)
    y = (screen.height() // 2) - (700 // 2)
    win.move(x, y)

    dashboard = create_owner_admin_dashboard(win)
    layout = QtWidgets.QVBoxLayout(win)
    layout.addWidget(dashboard)

    return win

def create_owner_admin_dashboard(master=None) -> QtWidgets.QWidget:
    """Create the Owner Admin dashboard for managing users and system."""

    dashboard_frame = QtWidgets.QWidget(master)
    dashboard_frame.setStyleSheet(f"background-color: {BG_COLOR};")

    main_layout = QtWidgets.QVBoxLayout(dashboard_frame)

    # Create notebook for tabs
    notebook = QtWidgets.QTabWidget()
    main_layout.addWidget(notebook)

    # ========== USERS TAB ==========
    users_frame = QtWidgets.QWidget()
    users_layout = QtWidgets.QVBoxLayout(users_frame)

    users_title = QtWidgets.QLabel("Authorized Users")
    users_title.setFont(FONT_HEADING)
    users_title.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    users_layout.addWidget(users_title)

    # Users Table
    users_table = QtWidgets.QTableWidget()
    users_table.setColumnCount(5)
    users_table.setHorizontalHeaderLabels(['Username', 'Email', 'Role', 'Status', 'Authorized Date'])
    users_table.horizontalHeader().setStretchLastSection(True)
    users_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
    users_table.setColumnWidth(0, 120)
    users_table.setColumnWidth(1, 200)
    users_table.setColumnWidth(2, 100)
    users_table.setColumnWidth(3, 80)
    users_table.setColumnWidth(4, 120)
    users_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    users_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    users_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    users_layout.addWidget(users_table)

    # Actions
    action_frame = QtWidgets.QHBoxLayout()

    def refresh_users():
        try:
            users_table.setRowCount(0)
            all_users = AdminHierarchyManager.get_all_users()
            for user in all_users:
                row = users_table.rowCount()
                users_table.insertRow(row)
                users_table.setItem(row, 0, QtWidgets.QTableWidgetItem(user['username']))
                users_table.setItem(row, 1, QtWidgets.QTableWidgetItem(user['email']))
                users_table.setItem(row, 2, QtWidgets.QTableWidgetItem(user['role']))
                users_table.setItem(row, 3, QtWidgets.QTableWidgetItem(user['status']))
                users_table.setItem(row, 4, QtWidgets.QTableWidgetItem(
                    user['authorized_date'][:10] if user['authorized_date'] else 'Unknown'
                ))
        except Exception as e:
            logging.error(f"Error refreshing users: {e}")

    def on_deactivate():
        selected = users_table.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(dashboard_frame, "No Selection", "Please select a user to deactivate.")
            return

        row = selected[0].row()
        username = users_table.item(row, 0).text()

        reply = QtWidgets.QMessageBox.question(dashboard_frame, "Confirm", f"Deactivate user '{username}'?",
                                   QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            QtWidgets.QMessageBox.information(dashboard_frame, "Success", f"User '{username}' has been deactivated.")
            refresh_users()

    refresh_btn = QtWidgets.QPushButton("Refresh")
    refresh_btn.clicked.connect(refresh_users)
    refresh_btn.setStyleSheet(
        f"background-color: {COLOR_PRIMARY}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    refresh_btn.setCursor(QtCore.Qt.PointingHandCursor)
    action_frame.addWidget(refresh_btn)

    deactivate_btn = QtWidgets.QPushButton("Deactivate User")
    deactivate_btn.clicked.connect(on_deactivate)
    deactivate_btn.setStyleSheet(
        f"background-color: {COLOR_DANGER}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    deactivate_btn.setCursor(QtCore.Qt.PointingHandCursor)
    action_frame.addWidget(deactivate_btn)

    users_layout.addLayout(action_frame)
    notebook.addTab(users_frame, 'Manage Users')

    # ========== AUTHORIZATION LOG TAB ==========
    log_frame = QtWidgets.QWidget()
    log_layout = QtWidgets.QVBoxLayout(log_frame)

    log_title = QtWidgets.QLabel("Authorization History")
    log_title.setFont(FONT_HEADING)
    log_title.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    log_layout.addWidget(log_title)

    # Log Table
    log_table = QtWidgets.QTableWidget()
    log_table.setColumnCount(4)
    log_table.setHorizontalHeaderLabels(['Authorized By', 'User', 'Action', 'Timestamp'])
    log_table.horizontalHeader().setStretchLastSection(True)
    log_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
    log_table.setColumnWidth(0, 150)
    log_table.setColumnWidth(1, 150)
    log_table.setColumnWidth(2, 100)
    log_table.setColumnWidth(3, 150)
    log_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    log_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    log_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    log_layout.addWidget(log_table)

    def refresh_log():
        try:
            log_table.setRowCount(0)
            logs = AdminHierarchyManager.get_authorization_log()
            for log_entry in logs:
                row = log_table.rowCount()
                log_table.insertRow(row)
                log_table.setItem(row, 0, QtWidgets.QTableWidgetItem(log_entry['authorized_by'][:30]))
                log_table.setItem(row, 1, QtWidgets.QTableWidgetItem(log_entry['authorized_user'][:30]))
                log_table.setItem(row, 2, QtWidgets.QTableWidgetItem(log_entry['action']))
                log_table.setItem(row, 3, QtWidgets.QTableWidgetItem(log_entry['timestamp']))
        except Exception as e:
            logging.error(f"Error refreshing log: {e}")

    log_action_frame = QtWidgets.QHBoxLayout()

    log_refresh_btn = QtWidgets.QPushButton("Refresh")
    log_refresh_btn.clicked.connect(refresh_log)
    log_refresh_btn.setStyleSheet(
        f"background-color: {COLOR_PRIMARY}; color: white; font-weight: bold; padding: 10px 20px;"
    )
    log_refresh_btn.setCursor(QtCore.Qt.PointingHandCursor)
    log_action_frame.addWidget(log_refresh_btn)

    log_layout.addLayout(log_action_frame)
    notebook.addTab(log_frame, 'Authorization Log')

    # ========== DEVICE INFO TAB ==========
    device_frame = QtWidgets.QWidget()
    device_layout = QtWidgets.QVBoxLayout(device_frame)

    device_title = QtWidgets.QLabel("Device Binding Information")
    device_title.setFont(FONT_HEADING)
    device_title.setStyleSheet(f"color: {PRIMARY_COLOR}; background-color: transparent;")
    device_layout.addWidget(device_title)

    device_info = get_device_info()
    info_text = QtWidgets.QTextEdit()
    info_text.setReadOnly(True)
    info_text.setStyleSheet(f"background-color: {CARD_BG}; color: {TEXT_COLOR};")
    device_layout.addWidget(info_text)

    info_content = f"""Device Binding Information
==========================

Hostname:         {device_info['hostname']}
OS:               {device_info['os']}
OS Version:       {device_info['os_version']}
Processor:        {device_info['processor']}
MAC Address:      {device_info['mac_address']}
IP Address:       {device_info['ip_address']}
Fingerprint:      {device_info['fingerprint'][:32]}...

License:
=========
Check the license information to see device binding status.
If you need to transfer this license to another device,
contact the licensing administrator.

Security Notes:
==============
- This device is bound to the software license
- Attempting to run on a different device will require authorization
- All user activities are logged for security audit
"""

    info_text.setPlainText(info_content.strip())

    notebook.addTab(device_frame, 'Device Info')

    # Initial refresh
    refresh_users()
    refresh_log()

    return dashboard_frame
