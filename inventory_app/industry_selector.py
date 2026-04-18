"""
Industry Selector Component
============================
Modern industry selection for dashboard using PySide6.
All industry config/state comes from industry_service.py — single source of truth.
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QMessageBox
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
    container = make_card(parent, padding=30)
    layout = QVBoxLayout(container)

    # Title & Subtitle
    header_frame = QFrame()
    header_layout = QVBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    styled_label(header_frame, "🎯 Industry vertical", font=FONT_HEADING)
    styled_label(header_frame, "Select your primary business type to enable specialized features",
                font=FONT_SMALL)

    layout.addWidget(header_frame)

    # Grid for industry options
    grid_frame = QFrame()
    grid_layout = QGridLayout(grid_frame)
    for i in range(3):
        grid_layout.setColumnStretch(i, 1)

    current_industry = get_current_industry_id()
    all_configs = get_all_configs()

    row, col = 0, 0
    for industry_id, config in all_configs.items():
        # Individual industry card
        opt_card = QFrame()
        opt_card.setFrameShape(QFrame.StyledPanel)
        opt_card.setStyleSheet(f"""
            QFrame {{
                background-color: {get_color('app_bg')};
                border: 2px solid {COLOR_PRIMARY if current_industry == industry_id else COLOR_BORDER};
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        card_layout = QVBoxLayout(opt_card)

        # Icon & Name
        styled_label(opt_card, f"{config['icon']} {config['name']}", font=FONT_BOLD)

        # Description
        desc_label = styled_label(opt_card, config['description'], font=FONT_SMALL)
        desc_label.setWordWrap(True)
        desc_label.setMaximumWidth(200)

        # Select Button
        btn_text = "✓ Current" if current_industry == industry_id else "Select"
        btn_kind = "success" if current_industry == industry_id else "secondary"

        def make_select_cmd(iid=industry_id):
            if change_industry(iid):
                if on_industry_changed:
                    on_industry_changed(iid)
            else:
                QMessageBox.critical(container, "Error", "Failed to update industry setting.")

        make_button(opt_card, btn_text, slot=make_select_cmd, kind=btn_kind)

        grid_layout.addWidget(opt_card, row, col)

        col += 1
        if col > 2:
            col = 0
            row += 1

    layout.addWidget(grid_frame)

    return container

def get_current_industry():
    return get_current_industry_id()

def save_industry(industry_id):
    """Save industry — delegates to IndustryService."""
    return change_industry(industry_id)
