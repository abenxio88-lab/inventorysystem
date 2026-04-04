"""
Mintaka Sphere - Business Settings Component
=============================================
Professional business configuration panel for dashboard.

All industry config/state comes from industry_service.py — single source of truth.

Usage:
    from inventory_app.business_settings import create_business_card
    card_frame = create_business_card(parent, dashboard_frame)
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
    selector_frame.pack(fill="both", expand=True, padx=10, pady=10)


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
    
    # Header
    header_frame = ttk.Frame(card_container)
    header_frame.pack(fill="x", pady=(0, 15))
    
    # Title with icon
    title_label = styled_label(
        header_frame,
        "🏢 Business Configuration",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )
    title_label.pack(anchor="w")
    
    # Create divider
    create_divider(header_frame, orientation="horizontal").pack(fill="x", pady=(8, 15))
    
    # Current industry display
    industry_frame = ttk.Frame(card_container)
    industry_frame.pack(fill="x", pady=(0, 15))
    
    # Get current industry
    current_industry = get_current_industry()
    industry_config = get_config(current_industry)
    
    # Industry icon and name
    industry_display = ttk.Frame(industry_frame)
    industry_display.pack(anchor="w")
    
    industry_icon = styled_label(
        industry_display,
        industry_config.get("icon", "🏪"),
        font=("Segoe UI", 32)
    )
    industry_icon.pack(side="left", padx=(0, 12))
    
    industry_info = ttk.Frame(industry_display)
    industry_info.pack(side="left", fill="x", expand=True)
    
    industry_name = styled_label(
        industry_info,
        current_industry,
        font=FONT_HEADING,
        foreground=get_color('primary')
    )
    industry_name.pack(anchor="w")
    
    industry_desc = styled_label(
        industry_info,
        industry_config.get("description", "Business configuration"),
        font=FONT_SMALL,
        foreground=get_color('text_muted'),
        wraplength=400
    )
    industry_desc.pack(anchor="w", pady=(4, 0))
    
    # Enabled verticals
    verticals_frame = ttk.Frame(card_container)
    verticals_frame.pack(fill="x", pady=(15, 20))
    
    enabled_verticals = get_enabled_verticals()
    
    verticals_title = styled_label(
        verticals_frame,
        f"✅ {len(enabled_verticals)} Features Enabled",
        font=FONT_SMALL,
        foreground=get_color('success')
    )
    verticals_title.pack(anchor="w", pady=(0, 10))
    
    # Show vertical badges
    badges_frame = ttk.Frame(verticals_frame)
    badges_frame.pack(anchor="w", fill="x")
    
    for i, vertical_name in enumerate(enabled_verticals[:4]):  # Show max 4
        # Get vertical display name
        vertical_display = vertical_name.replace("_", " ").title()
        if vertical_name == "lease_rental":
            vertical_display = "Lease & Rental"
        
        # Create badge
        badge = styled_label(
            badges_frame,
            f"✓ {vertical_display}",
            font=FONT_SMALL,
            foreground=get_color('text_muted'),
            background=get_color('card_bg')
        )
        badge.pack(side="left", padx=(0, 10) if i < len(enabled_verticals) - 1 and i < 3 else (0, 0))
    
    if len(enabled_verticals) > 4:
        more_label = styled_label(
            badges_frame,
            f"+{len(enabled_verticals) - 4} more",
            font=FONT_SMALL,
            foreground=get_color('text_muted')
        )
        more_label.pack(side="left", padx=(10, 0))
    
    # Action buttons
    buttons_frame = ttk.Frame(card_container)
    buttons_frame.pack(fill="x", pady=(10, 0))
    
    # Change industry button (primary)
    def on_change_industry():
        open_industry_change_dialog(
            parent,
            on_confirm=lambda industry_id: refresh_card()
        )
    
    change_btn = make_button(
        buttons_frame,
        "🔄 Change Business Type",
        on_change_industry,
        kind="primary"
    )
    change_btn.pack(side="left", padx=(0, 10))
    
    # Configure features button (secondary)
    def on_configure():
        # Navigate to settings or show configuration dialog
        if switch_tab_callback:
            switch_tab_callback("Settings")
        else:
            messagebox.showinfo(
                "Configure Features",
                "Feature configuration will be available in the Settings tab.\n\n"
                "You can enable/disable specific features for each vertical module.",
                parent=parent
            )
    
    configure_btn = make_button(
        buttons_frame,
        "⚙️ Configure",
        on_configure,
        kind="secondary"
    )
    configure_btn.pack(side="left")
    
    # Helper function to refresh card content
    def refresh_card():
        """Refresh card content after industry change"""
        for widget in card_container.winfo_children():
            widget.destroy()
        
        # Recreate card content
        new_card = create_business_card(parent, dashboard_frame, switch_tab_callback)
        new_card.pack(fill="x", pady=(10, 0))
    
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
    def on_shortcut(event=None):
        """Handle Ctrl+I shortcut"""
        def on_confirm(industry, verticals):
            # Refresh dashboard if available
            if dashboard_frame and hasattr(dashboard_frame, 'refresh'):
                dashboard_frame.refresh()
        
        open_industry_change_dialog(root, on_confirm=on_confirm)
    
    # Bind Ctrl+I
    root.bind("<Control-i>", on_shortcut)
    root.bind("<Control-I>", on_shortcut)


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
        messagebox.showerror("Permission Denied", "Only administrators can change business configuration.")
        return
    
    # Create configuration window
    win = tk.Toplevel(parent) if parent else tk.Toplevel()
    win.title("⚙️ Business Configuration")
    win.geometry("700x600")
    win.minsize(600, 500)
    win.resizable(True, True)
    
    # Modal
    win.transient(parent)
    win.grab_set()
    
    # Center on parent
    if parent:
        win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 700) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        win.geometry(f"+{x}+{y}")
    
    # Theme-aware background
    win.configure(bg=get_color('app_bg'))
    
    # Main container
    main_frame = make_glass_card(win, padx=30, pady=30)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    
    title_label = styled_label(
        header_frame,
        "🏢 Business Configuration",
        font=FONT_HEADING,
        foreground=get_color('text_main')
    )
    title_label.pack(anchor="w")
    
    subtitle_label = styled_label(
        header_frame,
        "Configure your business type and enabled features",
        font=FONT_SMALL,
        foreground=get_color('text_muted')
    )
    subtitle_label.pack(anchor="w", pady=(8, 0))
    
    create_divider(header_frame, orientation="horizontal").pack(fill="x", pady=(15, 25))
    
    # Current configuration section
    config_frame = ttk.Frame(main_frame)
    config_frame.pack(fill="x", pady=(0, 25))
    
    current_industry = get_current_industry()
    industry_config = get_config(current_industry)
    
    config_title = styled_label(
        config_frame,
        "Current Configuration",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )
    config_title.pack(anchor="w", pady=(0, 15))
    
    # Industry display
    industry_display = ttk.Frame(config_frame)
    industry_display.pack(fill="x", pady=(0, 15))
    
    industry_icon_label = styled_label(
        industry_display,
        industry_config.get("icon", "🏪"),
        font=("Segoe UI", 48)
    )
    industry_icon_label.pack(side="left", padx=(0, 16))
    
    industry_info = ttk.Frame(industry_display)
    industry_info.pack(side="left", fill="x", expand=True)
    
    industry_name_label = styled_label(
        industry_info,
        current_industry,
        font=FONT_HEADING,
        foreground=get_color('primary')
    )
    industry_name_label.pack(anchor="w")
    
    industry_desc_label = styled_label(
        industry_info,
        industry_config.get("description", ""),
        font=FONT_SMALL,
        foreground=get_color('text_muted'),
        wraplength=500
    )
    industry_desc_label.pack(anchor="w", pady=(6, 0))
    
    # Enabled verticals
    enabled_verticals = get_enabled_verticals()
    
    verticals_title = styled_label(
        config_frame,
        f"✅ Enabled Modules ({len(enabled_verticals)})",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )
    verticals_title.pack(anchor="w", pady=(20, 12))
    
    # List verticals
    for vertical in enabled_verticals:
        vertical_display = vertical.replace("_", " ").title()
        if vertical == "lease_rental":
            vertical_display = "Lease & Rental"
        
        vertical_item = styled_label(
            config_frame,
            f"✓ {vertical_display}",
            font=FONT_SMALL,
            foreground=get_color('success')
        )
        vertical_item.pack(anchor="w", pady=2)
    
    # Action buttons
    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(fill="x", pady=(30, 0))
    
    def on_change_industry():
        def on_confirm(industry_id):
            # Refresh display
            for widget in main_frame.winfo_children():
                widget.destroy()
            # Recreate content
            open_business_configuration(parent, current_user)

        open_industry_change_dialog(win, on_confirm=on_confirm)
    
    change_btn = make_button(
        buttons_frame,
        "🔄 Change Business Type",
        on_change_industry,
        kind="primary"
    )
    change_btn.pack(side="left", padx=(0, 10))
    
    close_btn = make_button(
        buttons_frame,
        "Close",
        lambda: win.destroy(),
        kind="secondary"
    )
    close_btn.pack(side="left")
    
    # Show window
    win.wait_window()


__all__ = [
    "create_business_card",
    "open_industry_change_dialog",
    "bind_industry_shortcut",
    "get_current_industry",
    "get_enabled_verticals",
    "open_business_configuration"
]
