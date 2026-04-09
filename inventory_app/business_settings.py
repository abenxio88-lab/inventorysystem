"""
Mintaka Sphere - Business Settings Component
=============================================
Professional business configuration panel for dashboard.

All industry config/state comes from industry_service.py — single source of truth.

Usage:
    from inventory_app.business_settings import create_business_card
    card_frame = create_business_card(parent, dashboard_frame)
"""

from PySide6.QtWidgets import (QFrame, QLabel, QPushButton, QDialog, QVBoxLayout, QHBoxLayout,
                               QMessageBox)
from PySide6.QtCore import Qt
from typing import Callable, Optional
import logging

from industry_service import (
    get_config, get_all_configs, get_current_industry_id, change_industry,
)

try:
    from .ui_theme import (
        make_card, make_glass_card, make_button, styled_label,
        create_divider, get_color, FONT_HEADING, SUBHEADING_FONT,
        FONT_SMALL, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY
    )
except (ImportError, ModuleNotFoundError):
    from ui_theme import (
        make_card, make_glass_card, make_button, styled_label,
        create_divider, get_color, FONT_HEADING, SUBHEADING_FONT,
        FONT_SMALL, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY
    )


def get_current_industry() -> str:
    """Get current industry type from database via service layer."""
    return get_current_industry_id()


def get_enabled_verticals() -> list:
    """Get list of enabled verticals"""
    try:
        from database import get_db_cursor
        import json
        with get_db_cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = 'enabled_verticals'")
            row = cur.fetchone()
            if row and row["value"]:
                return json.loads(row["value"])
        return ["retail"]
    except Exception:
        return ["retail"]


def open_industry_change_dialog(parent, on_confirm: Callable = None):
    """
    Open industry change dialog.
    All persistence/tab-reload/AppState-sync is handled by IndustryService.
    The on_confirm callback fires only after a successful change.
    """
    from industry_selector import create_industry_selector_card

    def on_industry_selected(new_industry_id):
        # IndustryService.change_industry already persisted, synced AppState, and reloaded tabs.
        # Just notify the caller and close.
        try:
            if on_confirm:
                on_confirm(new_industry_id)
        except Exception as e:
            logging.error(f"Industry change callback error: {e}", exc_info=True)

    # Show industry selector card — actually pack it so it's visible
    selector_frame = create_industry_selector_card(
        parent,
        on_industry_changed=on_industry_selected
    )
    layout = QVBoxLayout(parent)
    layout.addWidget(selector_frame)


def create_business_card(parent, dashboard_frame, switch_tab_callback: Optional[Callable] = None):
    """
    Create business settings card for dashboard

    Args:
        parent: Parent widget
        dashboard_frame: Dashboard frame for context
        switch_tab_callback: Optional callback for tab switching

    Returns:
        Created card frame
    """
    # Create card container
    card_container = make_glass_card(parent, padx=25, pady=20)
    layout = QVBoxLayout(card_container)

    # Header
    header_frame = QFrame()
    header_layout = QVBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    # Title with icon
    title_label = styled_label(
        header_layout,
        "🏢 Business Configuration",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )

    # Create divider
    create_divider(header_layout, orientation="horizontal")

    layout.addWidget(header_frame)

    # Current industry display
    industry_frame = QFrame()
    industry_layout = QVBoxLayout(industry_frame)
    industry_layout.setContentsMargins(0, 0, 0, 0)

    # Get current industry
    current_industry = get_current_industry()
    industry_config = get_config(current_industry)

    # Industry icon and name
    industry_display = QFrame()
    industry_display_layout = QHBoxLayout(industry_display)
    industry_display_layout.setContentsMargins(0, 0, 0, 0)

    industry_icon = styled_label(
        industry_display_layout,
        industry_config.get("icon", "🏪"),
        font=("Segoe UI", 32)
    )

    industry_info = QFrame()
    info_layout = QVBoxLayout(industry_info)
    info_layout.setContentsMargins(0, 0, 0, 0)

    industry_name = styled_label(
        info_layout,
        current_industry,
        font=FONT_HEADING,
        foreground=get_color('primary')
    )

    industry_desc = styled_label(
        info_layout,
        industry_config.get("description", "Business configuration"),
        font=FONT_SMALL,
        foreground=get_color('text_muted'),
    )
    industry_desc.setWordWrap(True)
    industry_desc.setMaximumWidth(400)

    industry_display_layout.addWidget(industry_info)
    industry_layout.addWidget(industry_display)
    layout.addWidget(industry_frame)

    # Enabled verticals
    verticals_frame = QFrame()
    verticals_layout = QVBoxLayout(verticals_frame)
    verticals_layout.setContentsMargins(0, 0, 0, 0)

    enabled_verticals = get_enabled_verticals()

    verticals_title = styled_label(
        verticals_layout,
        f"✅ {len(enabled_verticals)} Features Enabled",
        font=FONT_SMALL,
        foreground=get_color('success')
    )

    # Show vertical badges
    badges_frame = QFrame()
    badges_layout = QHBoxLayout(badges_frame)
    badges_layout.setContentsMargins(0, 0, 0, 0)

    for i, vertical_name in enumerate(enabled_verticals[:4]):  # Show max 4
        # Get vertical display name
        vertical_display = vertical_name.replace("_", " ").title()
        if vertical_name == "lease_rental":
            vertical_display = "Lease & Rental"

        # Create badge
        badge = styled_label(
            badges_layout,
            f"✓ {vertical_display}",
            font=FONT_SMALL,
            foreground=get_color('text_muted'),
            background=get_color('card_bg')
        )

    if len(enabled_verticals) > 4:
        more_label = styled_label(
            badges_layout,
            f"+{len(enabled_verticals) - 4} more",
            font=FONT_SMALL,
            foreground=get_color('text_muted')
        )

    verticals_layout.addWidget(badges_frame)
    layout.addWidget(verticals_frame)

    # Action buttons
    buttons_frame = QFrame()
    buttons_layout = QHBoxLayout(buttons_frame)
    buttons_layout.setContentsMargins(0, 0, 0, 0)

    # Change industry button (primary)
    def on_change_industry():
        dialog = QDialog(parent)
        dialog.setWindowTitle("Change Business Type")
        dialog.resize(800, 600)
        dialog.setModal(True)

        dialog_layout = QVBoxLayout(dialog)

        def on_confirm(industry_id):
            dialog.accept()
            refresh_card()

        open_industry_change_dialog(dialog, on_confirm=on_confirm)
        dialog.exec()

    change_btn = make_button(
        buttons_layout,
        "🔄 Change Business Type",
        on_change_industry,
        kind="primary"
    )

    # Configure features button (secondary)
    def on_configure():
        # Navigate to settings or show configuration dialog
        if switch_tab_callback:
            switch_tab_callback("Settings")
        else:
            QMessageBox.information(
                parent,
                "Configure Features",
                "Feature configuration will be available in the Settings tab.\n\n"
                "You can enable/disable specific features for each vertical module.",
            )

    configure_btn = make_button(
        buttons_layout,
        "⚙️ Configure",
        on_configure,
        kind="secondary"
    )

    layout.addWidget(buttons_frame)

    # Helper function to refresh card content
    def refresh_card():
        """Refresh card content after industry change"""
        # Clear layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Recreate card content
        current_industry = get_current_industry()
        industry_config = get_config(current_industry)
        enabled_verticals = get_enabled_verticals()

        # Update industry display
        industry_name.setText(current_industry)
        industry_desc.setText(industry_config.get("description", "Business configuration"))
        industry_icon.setText(industry_config.get("icon", "🏪"))

        verticals_title.setText(f"✅ {len(enabled_verticals)} Features Enabled")

    # Store refresh function for keyboard shortcut
    card_container.refresh = refresh_card

    return card_container


def bind_industry_shortcut(root, dashboard_frame=None):
    """
    Bind keyboard shortcut for industry selector (Ctrl+I)

    Args:
        root: Root window
        dashboard_frame: Optional dashboard frame
    """
    from PySide6.QtGui import QKeySequence, QShortcut

    def on_shortcut():
        """Handle Ctrl+I shortcut"""
        def on_confirm(industry_id):
            # Callback expects single industry_id parameter
            # Refresh dashboard if available
            if dashboard_frame and hasattr(dashboard_frame, 'refresh'):
                dashboard_frame.refresh()

        dialog = QDialog(root)
        dialog.setWindowTitle("Change Industry")
        dialog.resize(800, 600)
        dialog.setModal(True)
        dialog_layout = QVBoxLayout(dialog)
        open_industry_change_dialog(dialog, on_confirm=on_confirm)
        dialog.exec()

    # Bind Ctrl+I
    shortcut = QShortcut(QKeySequence("Ctrl+I"), root)
    shortcut.activated.connect(on_shortcut)


def open_business_configuration(parent, current_user=None):
    """
    Open full business configuration window

    Args:
        parent: Parent window
        current_user: Current username (for admin check)
    """
    # Check admin permission
    try:
        from .utils import load_users
    except (ImportError, ModuleNotFoundError):
        from utils import load_users

    users = load_users()
    if current_user and users.get(current_user, {}).get("role") not in ["admin", "OWNER_ADMIN"]:
        QMessageBox.critical(parent, "Permission Denied", "Only administrators can change business configuration.")
        return

    # Create configuration window
    win = QDialog(parent) if parent else QDialog()
    win.setWindowTitle("⚙️ Business Configuration")
    win.resize(700, 600)
    win.setMinimumSize(600, 500)
    win.setModal(True)

    # Theme-aware background
    win.setStyleSheet(f"background-color: {get_color('app_bg')};")

    # Main container
    main_frame = make_glass_card(win, padx=30, pady=30)
    main_layout = QVBoxLayout(main_frame)

    # Header
    header_frame = QFrame()
    header_layout = QVBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    title_label = styled_label(
        header_layout,
        "🏢 Business Configuration",
        font=FONT_HEADING,
        foreground=get_color('text_main')
    )

    subtitle_label = styled_label(
        header_layout,
        "Configure your business type and enabled features",
        font=FONT_SMALL,
        foreground=get_color('text_muted')
    )

    create_divider(header_layout, orientation="horizontal")

    main_layout.addWidget(header_frame)

    # Current configuration section
    config_frame = QFrame()
    config_layout = QVBoxLayout(config_frame)
    config_layout.setContentsMargins(0, 0, 0, 0)

    current_industry = get_current_industry()
    industry_config = get_config(current_industry)

    config_title = styled_label(
        config_layout,
        "Current Configuration",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )

    # Industry display
    industry_display = QFrame()
    industry_display_layout = QHBoxLayout(industry_display)
    industry_display_layout.setContentsMargins(0, 0, 0, 0)

    industry_icon_label = styled_label(
        industry_display_layout,
        industry_config.get("icon", "🏪"),
        font=("Segoe UI", 48)
    )

    industry_info = QFrame()
    info_layout = QVBoxLayout(industry_info)
    info_layout.setContentsMargins(0, 0, 0, 0)

    industry_name_label = styled_label(
        info_layout,
        current_industry,
        font=FONT_HEADING,
        foreground=get_color('primary')
    )

    industry_desc_label = styled_label(
        info_layout,
        industry_config.get("description", ""),
        font=FONT_SMALL,
        foreground=get_color('text_muted'),
    )
    industry_desc_label.setWordWrap(True)
    industry_desc_label.setMaximumWidth(500)

    industry_display_layout.addWidget(industry_info)
    config_layout.addWidget(industry_display)

    # Enabled verticals
    enabled_verticals = get_enabled_verticals()

    verticals_title = styled_label(
        config_layout,
        f"✅ Enabled Modules ({len(enabled_verticals)})",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )

    # List verticals
    for vertical in enabled_verticals:
        vertical_display = vertical.replace("_", " ").title()
        if vertical == "lease_rental":
            vertical_display = "Lease & Rental"

        vertical_item = styled_label(
            config_layout,
            f"✓ {vertical_display}",
            font=FONT_SMALL,
            foreground=get_color('success')
        )

    main_layout.addWidget(config_frame)

    # Action buttons
    buttons_frame = QFrame()
    buttons_layout = QHBoxLayout(buttons_frame)
    buttons_layout.setContentsMargins(0, 0, 0, 0)

    def on_change_industry():
        def on_confirm(industry_id):
            # Refresh display
            while main_layout.count():
                item = main_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            # Recreate content
            open_business_configuration(parent, current_user)

        dialog = QDialog(win)
        dialog.setWindowTitle("Change Business Type")
        dialog.resize(800, 600)
        dialog.setModal(True)
        dialog_layout = QVBoxLayout(dialog)
        open_industry_change_dialog(dialog, on_confirm=on_confirm)
        dialog.exec()

    change_btn = make_button(
        buttons_layout,
        "🔄 Change Business Type",
        on_change_industry,
        kind="primary"
    )

    close_btn = make_button(
        buttons_layout,
        "Close",
        lambda: win.reject(),
        kind="secondary"
    )

    main_layout.addWidget(buttons_frame)

    win.setLayout(main_layout)
    win.exec()


__all__ = [
    "create_business_card",
    "open_industry_change_dialog",
    "bind_industry_shortcut",
    "get_current_industry",
    "get_enabled_verticals",
    "open_business_configuration"
]
