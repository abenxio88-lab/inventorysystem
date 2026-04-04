"""
Industry-Specific Interface Module
===================================
Adapt UI and features based on business type.
All industry config/state comes from industry_service.py — single source of truth.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import logging

from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY
from industry_service import (
    get_config, get_all_configs, get_current_industry_id, change_industry,
    INDUSTRY_CONFIG as INDUSTRY_CONFIGS,
)

from services import svc


def create_industry_selector(parent, on_select_callback=None):
    """
    Create industry selection dialog.
    Shows on first run or when user wants to change industry.
    """
    dlg = tk.Toplevel(parent)
    dlg.title("Select Your Business Type")
    dlg.geometry("1100x800")
    dlg.resizable(True, True)
    dlg.transient(parent)
    dlg.grab_set()

    # Content
    content = ttk.Frame(dlg, padding=30)
    content.pack(fill=tk.BOTH, expand=True)

    # Header
    header_frame = ttk.Frame(content)
    header_frame.pack(fill=tk.X, pady=(0, 20))

    styled_label(header_frame, "🎯 Select Your Industry", font=FONT_BOLD).pack(anchor=tk.W)
    styled_label(header_frame, "Choose the option that best describes your business",
                 foreground="#6c757d").pack(anchor=tk.W, pady=(5, 0))

    # Industry cards
    cards_frame = ttk.Frame(content)
    cards_frame.pack(fill=tk.BOTH, expand=True)

    selected_industry = {'value': None}

    def select_industry(industry_id):
        selected_industry['value'] = industry_id

    # Create cards in grid
    industries = list(INDUSTRY_CONFIGS.items())
    row = 0
    col = 0

    for industry_id, config in industries:
        # Create card
        card = make_card(cards_frame, padding=20)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Configure grid
        if col == 0:
            cards_frame.grid_columnconfigure(0, weight=1)
        if col == 1:
            cards_frame.grid_columnconfigure(1, weight=1)

        # Icon and name
        name_frame = ttk.Frame(card)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        styled_label(name_frame, text=config['icon'], font=("Segoe UI", 32)).pack(side=tk.LEFT, padx=(0, 10))

        info_frame = ttk.Frame(name_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        styled_label(info_frame, text=config['name'], font=FONT_BOLD).pack(anchor=tk.W)
        styled_label(info_frame, text=config['description'],
                    foreground="#6c757d", font=("Segoe UI", 9)).pack(anchor=tk.W)

        # Features preview
        features = config['features']
        enabled_features = [k.replace('track_', '').replace('_', ' ').title()
                           for k, v in features.items() if v]

        if enabled_features:
            features_text = " • ".join(enabled_features[:3])
            styled_label(card, text=features_text, font=("Segoe UI", 8),
                        foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(5, 10))

        # Select button
        make_button(card, "Select", command=lambda iid=industry_id: (select_industry(iid), dlg.destroy()),
                   kind="primary").pack(anchor=tk.E)

        # Grid positioning
        col += 1
        if col > 1:
            col = 0
            row += 1

    # Footer
    footer_frame = ttk.Frame(content)
    footer_frame.pack(fill=tk.X, pady=(20, 0))

    styled_label(footer_frame, "You can change this later in Settings",
                foreground="#6c757d", font=("Segoe UI", 9)).pack(side=tk.LEFT)

    # Wait for dialog to close
    dlg.wait_window()

    # Call callback if industry was selected
    if selected_industry['value'] and on_select_callback:
        on_select_callback(selected_industry['value'])

    return selected_industry['value']


def save_industry_setting(industry_id: str):
    """Save industry setting — delegates to IndustryService."""
    return change_industry(industry_id)


def get_current_industry() -> str:
    """Get current industry via service layer."""
    return get_current_industry_id()


def get_industry_config(industry_id: str = None) -> dict:
    """Get configuration for current or specified industry."""
    if industry_id is None:
        industry_id = get_current_industry_id()
    return get_config(industry_id)


def get_custom_fields(industry_id: str = None) -> list:
    """Get custom fields for current industry."""
    config = get_industry_config(industry_id)
    return config.get('custom_fields', [])


def is_feature_enabled(feature: str, industry_id: str = None) -> bool:
    """Check if a feature is enabled for current industry."""
    config = get_industry_config(industry_id)
    features = config.get('features', {})
    return features.get(feature, False)


def create_industry_settings_tab(parent, current_user=None):
    """
    Creates the industry settings tab.
    Allows changing industry and configuring industry-specific settings.
    """
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "⚙️ Industry Settings", font=FONT_BOLD).pack(side=tk.LEFT)

    # Current industry
    current_industry = get_current_industry()
    config = get_industry_config(current_industry)

    info_frame = make_card(window, padding=20)
    info_frame.pack(fill="x", pady=(0, 15))

    styled_label(info_frame, "Current Industry", font=FONT_BOLD).pack(anchor=tk.W)
    styled_label(info_frame, f"{config['icon']} {config['name']}",
                font=("Segoe UI", 18), foreground=COLOR_PRIMARY).pack(anchor=tk.W, pady=(5, 10))
    styled_label(info_frame, config['description']).pack(anchor=tk.W)

    # Features enabled
    features_frame = ttk.LabelFrame(info_frame, text="Enabled Features", padding=15)
    features_frame.pack(fill="x", pady=(15, 0))

    features = config.get('features', {})
    enabled = [k.replace('track_', '').replace('_', ' ').title() for k, v in features.items() if v]

    if enabled:
        for i, feature in enumerate(enabled):
            styled_label(features_frame, f"✓ {feature}", foreground=COLOR_PRIMARY).pack(anchor=tk.W)
    else:
        styled_label(features_frame, "No special features enabled", foreground="#6c757d").pack()

    # Change industry
    change_frame = ttk.LabelFrame(window, text="Change Industry", padding=15)
    change_frame.pack(fill="x", pady=(15, 0))

    styled_label(change_frame, "Select a different industry type:").pack(anchor=tk.W, pady=(0, 10))

    industry_var = tk.StringVar(value=current_industry)
    industry_combo = ttk.Combobox(
        change_frame,
        textvariable=industry_var,
        values=[f"{conf['icon']} {conf['name']}" for conf in INDUSTRY_CONFIGS.values()],
        state="readonly",
        width=40
    )
    industry_combo.pack(anchor=tk.W, pady=(0, 10))

    # Set current selection
    for i, (iid, conf) in enumerate(INDUSTRY_CONFIGS.items()):
        if iid == current_industry:
            industry_combo.current(i)
            break

    def change_industry():
        selection = industry_combo.get()

        # Find industry ID from selection
        selected_id = None
        for iid, conf in INDUSTRY_CONFIGS.items():
            if f"{conf['icon']} {conf['name']}" == selection:
                selected_id = iid
                break

        if selected_id and selected_id != current_industry:
            if messagebox.askyesno("Confirm Change",
                                  "Changing industry will add new categories and fields.\nContinue?"):
                # Use IndustryService — single source of truth
                # Handles: validate -> persist -> AppState sync -> tab reload -> notify
                try:
                    from industry_service import change_industry as switch_industry
                    if switch_industry(selected_id):
                        messagebox.showinfo("Success",
                            f"Industry changed to {INDUSTRY_CONFIGS[selected_id]['name']}")
                    else:
                        messagebox.showerror("Error",
                            f"Failed to switch industry to '{selected_id}'. Check logs.")
                except Exception as e:
                    logging.error(f"Industry switch error: {e}", exc_info=True)
                    messagebox.showerror("Error", f"Failed to change industry: {e}")
        else:
            messagebox.showinfo("Info", "No change selected")

    make_button(change_frame, "Change Industry", command=change_industry, kind="primary").pack(anchor=tk.W)

    # Custom fields info
    fields_frame = ttk.LabelFrame(window, text="Custom Fields", padding=15)
    fields_frame.pack(fill="both", expand=True, pady=(15, 0))

    custom_fields = get_custom_fields(current_industry)

    if custom_fields:
        # Create treeview
        columns = ("name", "type", "description")
        tree = ttk.Treeview(fields_frame, columns=columns, show="headings", height=10)

        for col in columns:
            tree.heading(col, text=col.title())
            tree.column(col, width=150)

        tree.pack(fill=tk.BOTH, expand=True)

        for field_id, field_name, field_type in custom_fields:
            tree.insert("", "end", values=(field_name, field_type.title(), ""))
    else:
        styled_label(fields_frame, "No custom fields for this industry",
                    foreground="#6c757d").pack(pady=20)

    return window


def apply_industry_settings():
    """Apply industry-specific settings to the application."""
    industry_id = get_current_industry()
    config = get_industry_config(industry_id)

    logging.info(f"Applied industry settings: {config['name']}")

    # Return config for use in other modules
    return config
