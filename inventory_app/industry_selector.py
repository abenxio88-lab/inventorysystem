"""
Industry Selector Component
============================
Modern industry selection for dashboard using standard ttk.
All industry config/state comes from industry_service.py — single source of truth.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui_theme import (
    make_card, make_button, styled_label, get_color,
    FONT_HEADING, FONT_BOLD, FONT_SMALL, COLOR_PRIMARY, COLOR_BORDER
)
from industry_service import change_industry, get_current_industry_id, get_config, get_all_configs

def create_industry_selector_card(parent, on_industry_changed=None):
    """
    Creates a modern industry selection card for the dashboard.
    Renamed to match dashboard_ui expectations.
    """
    container = make_card(parent, padx=30, pady=30)

    # Title & Subtitle
    header_frame = ttk.Frame(container)
    header_frame.pack(fill="x", pady=(0, 20))

    styled_label(header_frame, "🎯 Industry vertical", font=FONT_HEADING).pack(anchor="w")
    styled_label(header_frame, "Select your primary business type to enable specialized features",
                font=FONT_SMALL, foreground=get_color('text_muted')).pack(anchor="w")

    # Grid for industry options
    grid_frame = ttk.Frame(container)
    grid_frame.pack(fill="x")

    current_industry = get_current_industry_id()
    all_configs = get_all_configs()

    # Create 3 columns
    for i in range(3):
        grid_frame.columnconfigure(i, weight=1)

    row, col = 0, 0
    for industry_id, config in all_configs.items():
        # Individual industry card
        opt_card = tk.Frame(grid_frame, bg=get_color('app_bg'),
                           highlightbackground=COLOR_PRIMARY if current_industry == industry_id else COLOR_BORDER,
                           highlightthickness=2 if current_industry == industry_id else 1,
                           padx=15, pady=15)
        opt_card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Icon & Name
        styled_label(opt_card, f"{config['icon']} {config['name']}", font=FONT_BOLD,
                    background=get_color('app_bg')).pack(anchor="w")

        # Description
        styled_label(opt_card, config['description'], font=FONT_SMALL,
                    foreground=get_color('text_muted'), background=get_color('app_bg'),
                    wraplength=200).pack(anchor="w", pady=(5, 10))

        # Select Button
        btn_text = "✓ Current" if current_industry == industry_id else "Select"
        btn_kind = "success" if current_industry == industry_id else "secondary"

        def make_select_cmd(iid=industry_id):
            if change_industry(iid):
                if on_industry_changed:
                    on_industry_changed(iid)
                cfg = get_config(iid)
                messagebox.showinfo("Industry Updated",
                                  f"Business mode set to {cfg['name']}.\nAll tabs and forms updated.")
            else:
                messagebox.showerror("Error", "Failed to update industry setting.")

        btn = make_button(opt_card, btn_text, command=make_select_cmd, kind=btn_kind)
        btn.pack(fill="x", pady=(5))

        col += 1
        if col > 2:
            col = 0
            row += 1

    return container

def get_current_industry():
    return get_current_industry_id()

def save_industry(industry_id):
    """Save industry — delegates to IndustryService."""
    return change_industry(industry_id)
