from PySide6 import QtWidgets, QtCore, QtGui
import logging

from ui_theme import (
    make_button, setup_theme, make_card, styled_label,
    styled_entry, FONT_HEADING, FONT_REGULAR,
    COLOR_TEXT_MUTED, FONT_BOLD, COLOR_APP_BG, COLOR_PRIMARY,
    SUBHEADING_FONT, FONT_SMALL, create_divider, COLOR_TEXT_MAIN,
    COLOR_BORDER, COLOR_PRIMARY_LIGHT
)
from database import verify_user_db
from utils import get_login_rate_limiter


def center_on_screen(dialog):
    """Center a dialog on the primary screen."""
    screen = QtWidgets.QApplication.primaryScreen().geometry()
    dialog_size = dialog.sizeHint()
    w = max(dialog_size.width(), 550)
    h = max(dialog_size.height(), 750)
    dialog.resize(w, h)
    x = screen.center().x() - w // 2
    y = screen.center().y() - h // 2
    dialog.move(x, y)


def open_login(on_success, parent=None):
    """
    Creates and displays the premium login window with glassmorphism design.

    Args:
        on_success (function): The callback function to execute upon successful login.
                               It receives `username`, `role`, `user_id`, and `master`.
        parent (QtWidgets.QWidget, optional): The parent window if this is part of
                                              a larger app.
    """
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Mintaka Sphere - Premium Access")
    dialog.setMinimumSize(500, 650)
    dialog.setModal(True)

    # Configure window background
    dialog.setStyleSheet(f"QDialog {{ background-color: {COLOR_APP_BG}; }}")

    # --- Main layout ---
    main_layout = QtWidgets.QVBoxLayout(dialog)
    main_layout.setContentsMargins(30, 30, 30, 30)
    main_layout.setSpacing(0)

    # --- Header section with logo/icon ---
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QVBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(5)

    # Premium icon/emoji display
    icon_label = QtWidgets.QLabel("\U0001F510")
    icon_label.setFont(QtGui.QFont("Segoe UI", 56))
    icon_label.setAlignment(QtCore.Qt.AlignCenter)
    header_layout.addWidget(icon_label)

    # Company name with premium typography
    title_label = styled_label(header_frame, "Mintaka Sphere", font=FONT_HEADING)
    title_label.setStyleSheet(f"QLabel {{ color: {COLOR_PRIMARY}; }}")
    title_label.setAlignment(QtCore.Qt.AlignCenter)
    header_layout.addWidget(title_label)

    subtitle_label = styled_label(header_frame, "Inventory Management System", font=SUBHEADING_FONT)
    subtitle_label.setStyleSheet(f"QLabel {{ color: {COLOR_TEXT_MUTED}; }}")
    subtitle_label.setAlignment(QtCore.Qt.AlignCenter)
    header_layout.addWidget(subtitle_label)

    # Decorative line
    divider = create_divider(header_frame, orientation="horizontal")
    divider.setStyleSheet(f"QFrame {{ background-color: {COLOR_BORDER}; }}")
    header_layout.addWidget(divider)

    # Add spacing around divider
    header_layout.setSpacing(0)
    header_layout.insertSpacing(0, 20)  # top padding
    header_layout.insertSpacing(2, 10)  # between icon and title
    header_layout.insertSpacing(5, 20)  # below divider

    main_layout.addWidget(header_frame)

    # --- Login Form Card ---
    card = make_card(main_frame := QtWidgets.QWidget(), padding=30)
    card_layout = QtWidgets.QVBoxLayout(card)
    card_layout.setSpacing(15)

    # Username field
    username_label = styled_label(card, "Username", font=FONT_BOLD)
    username_label.setStyleSheet(f"QLabel {{ color: {COLOR_TEXT_MAIN}; }}")
    card_layout.addWidget(username_label)

    username_entry = styled_entry(card)
    username_entry.setMinimumHeight(40)
    card_layout.addWidget(username_entry)

    # Password field with visibility toggle
    password_label = styled_label(card, "Password", font=FONT_BOLD)
    password_label.setStyleSheet(f"QLabel {{ color: {COLOR_TEXT_MAIN}; }}")
    card_layout.addWidget(password_label)

    password_row = QtWidgets.QWidget()
    password_row_layout = QtWidgets.QHBoxLayout(password_row)
    password_row_layout.setContentsMargins(0, 0, 0, 0)
    password_row_layout.setSpacing(8)

    password_entry = styled_entry(password_row)
    password_entry.setMinimumHeight(40)
    password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
    password_row_layout.addWidget(password_entry)

    # Password visibility toggle button
    toggle_btn = QtWidgets.QPushButton("\U0001F441")
    toggle_btn.setFixedSize(40, 40)
    toggle_btn.setCursor(QtCore.Qt.PointingHandCursor)
    toggle_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_APP_BG};
            border: 1px solid {COLOR_BORDER};
            border-radius: 8px;
            font-size: 16px;
        }}
        QPushButton:hover {{
            border-color: {COLOR_PRIMARY};
        }}
    """)
    password_row_layout.addWidget(toggle_btn)

    password_visible = False

    def toggle_password_visibility():
        nonlocal password_visible
        password_visible = not password_visible
        if password_visible:
            password_entry.setEchoMode(QtWidgets.QLineEdit.Normal)
            toggle_btn.setText("\U0001F441\u200D\U0001F5E8")
        else:
            password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
            toggle_btn.setText("\U0001F441")

    toggle_btn.clicked.connect(toggle_password_visibility)

    card_layout.addWidget(password_row)

    # Login button
    def do_login():
        """Handles the login logic using database authentication with rate limiting."""
        username = username_entry.text().strip()
        password = password_entry.text()

        if not username or not password:
            QtWidgets.QMessageBox.warning(
                dialog,
                "Input Required",
                "Please enter both username and password."
            )
            return

        # Check rate limiting
        rate_limiter = get_login_rate_limiter()
        if not rate_limiter.is_allowed(username):
            wait_time = rate_limiter.get_wait_time(username)
            QtWidgets.QMessageBox.critical(
                dialog,
                "Too Many Attempts",
                f"Too many failed login attempts for '{username}'.\n"
                f"Please wait {wait_time} seconds before trying again."
            )
            return

        # Authenticate against database
        success, role, user_id = verify_user_db(username, password)
        if success:
            logging.info(f"Login successful for user: {username}")
            rate_limiter.reset(username)  # Reset counter on success
            dialog.accept()
            on_success(username, role, user_id, parent)
        else:
            logging.warning(f"Login failed for user: {username}")
            rate_limiter.record_attempt(username)
            remaining = rate_limiter.get_remaining_attempts(username)
            if remaining is not None and remaining <= 0:
                QtWidgets.QMessageBox.critical(
                    dialog,
                    "Account Locked",
                    f"Account '{username}' has been locked due to too many failed attempts.\n"
                    f"Please wait before trying again."
                )
            else:
                msg = "Invalid username or password"
                if remaining is not None:
                    msg += f"\n({remaining} attempts remaining before lockout)"
                QtWidgets.QMessageBox.critical(dialog, "Login Failed", msg)
            password_entry.clear()
            password_entry.setFocus()

    login_btn = make_button(card, text="SIGN IN", slot=do_login, kind="primary")
    login_btn.setMinimumHeight(44)
    card_layout.addWidget(login_btn)

    # Helper text
    help_text = styled_label(card, "Need help? Contact your administrator", font=FONT_SMALL)
    help_text.setStyleSheet(f"QLabel {{ color: {COLOR_TEXT_MUTED}; }}")
    help_text.setAlignment(QtCore.Qt.AlignCenter)
    card_layout.addWidget(help_text)

    # Add spacer to push content up
    card_layout.addStretch()

    main_layout.addWidget(card)

    # --- Bindings ---
    username_entry.returnPressed.connect(lambda: password_entry.setFocus())
    password_entry.returnPressed.connect(do_login)

    # --- Center and show dialog ---
    center_on_screen(dialog)
    username_entry.setFocus()

    return dialog


if __name__ == '__main__':
    # This allows the login UI to be tested standalone
    import sys
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    setup_theme(None, "superhero")

    def on_login_success(username, role, user_id, master):
        print(f"Login successful for {username} ({role}), user_id={user_id}")
        app.quit()

    dlg = open_login(on_login_success)
    dlg.exec()
    sys.exit()
