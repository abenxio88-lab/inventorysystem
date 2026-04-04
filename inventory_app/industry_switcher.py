"""
Mintaka Sphere - Simple Industry Switcher
==========================================
Quick industry change dialog - WORKING VERSION
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

try:
    from .ui_theme import (
        make_card, make_button, styled_label, create_divider,
        get_color, FONT_HEADING, FONT_SMALL
    )
except (ImportError, ModuleNotFoundError):
    from ui_theme import (
        make_card, make_button, styled_label, create_divider,
        get_color, FONT_HEADING, FONT_SMALL
    )


try:
    from industry_service import (
        get_current_industry_id, change_industry, get_all_configs
    )
except (ImportError, ModuleNotFoundError):
    from .industry_service import (
        get_current_industry_id, change_industry, get_all_configs
    )

ALL_CONFIGS = get_all_configs()


def get_current_industry() -> str:
    """Get current industry id from database"""
    return get_current_industry_id()


def set_industry(industry_id: str) -> bool:
    """Set industry id in database — delegates to IndustryService."""
    return change_industry(industry_id)


def open_industry_switcher(parent, on_confirm: Callable = None):
    """
    Open simple industry switcher dialog
    
    Args:
        parent: Parent window
        on_confirm: Callback(industry_name) when confirmed
    """
    dialog = tk.Toplevel(parent)
    dialog.title("🔄 Change Industry")
    dialog.geometry("500x600")
    dialog.minsize(450, 550)
    dialog.resizable(False, False)
    
    if parent:
        dialog.transient(parent)
        dialog.grab_set()
    
    # Center on parent
    if parent:
        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        dialog.geometry(f"+{x}+{y}")
    
    # Main frame
    main_frame = ttk.Frame(dialog, padding=30)
    main_frame.pack(fill="both", expand=True)
    
    # Header
    header_label = styled_label(
        main_frame,
        "🔄 Select Your Industry",
        font=FONT_HEADING,
        foreground=get_color('text_main')
    )
    header_label.pack(anchor="w", pady=(0, 10))
    
    subtitle_label = styled_label(
        main_frame,
        "Choose the industry that matches your business",
        font=FONT_SMALL,
        foreground=get_color('text_muted')
    )
    subtitle_label.pack(anchor="w", pady=(0, 20))
    
    create_divider(main_frame, orientation="horizontal").pack(fill="x", pady=(0, 20))
    
    # Industry list
    industries_frame = ttk.Frame(main_frame)
    industries_frame.pack(fill="both", expand=True)
    
    selected_industry = tk.StringVar(value=get_current_industry())
    
    # Create radio buttons for each industry
    for industry_id, industry_data in ALL_CONFIGS.items():
        industry_frame = make_card(industries_frame, padx=15, pady=12)
        industry_frame.pack(fill="x", pady=4)

        # Radio button
        radio = ttk.Radiobutton(
            industry_frame,
            variable=selected_industry,
            value=industry_id,
            text=f"{industry_data['icon']}  {industry_data['name']}",
            command=lambda: None
        )
        radio.pack(anchor="w")

        # Description
        desc_label = styled_label(
            industry_frame,
            industry_data['description'],
            font=FONT_SMALL,
            foreground=get_color('text_muted')
        )
        desc_label.pack(anchor="w", padx=(30, 0))
    
    # Buttons
    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(fill="x", pady=(20, 0))
    
    def on_cancel():
        dialog.destroy()
    
    def on_ok():
        industry_id = selected_industry.get()
        success = set_industry(industry_id)

        if success:
            industry_name = ALL_CONFIGS.get(industry_id, {}).get('name', industry_id)
            messagebox.showinfo(
                "Industry Changed",
                f"✅ Industry changed to {industry_name}\n\n"
                f"Tabs and forms have been updated.",
                parent=dialog
            )
            
            if on_confirm:
                on_confirm(industry_id)
            
            dialog.destroy()
        else:
            messagebox.showerror(
                "Error",
                f"Failed to change industry.\n\nPlease try again.",
                parent=dialog
            )
    
    cancel_btn = make_button(buttons_frame, "Cancel", on_cancel, kind="secondary")
    cancel_btn.pack(side="left", padx=(0, 10))
    
    ok_btn = make_button(buttons_frame, "✓ Change Industry", on_ok, kind="primary")
    ok_btn.pack(side="right")
    
    # Wait for dialog
    dialog.wait_window()


def bind_ctrl_i_shortcut(root):
    """
    Bind Ctrl+I to open industry switcher
    
    Args:
        root: Root window
    """
    def on_ctrl_i(event=None):
        """Handle Ctrl+I"""
        open_industry_switcher(root)
    
    # Bind Ctrl+I (case insensitive)
    root.bind("<Control-i>", on_ctrl_i)
    root.bind("<Control-I>", on_ctrl_i)
    
    print("✅ Ctrl+I shortcut bound - opens industry switcher")


__all__ = [
    "open_industry_switcher",
    "bind_ctrl_i_shortcut",
    "get_current_industry",
    "set_industry"
]
