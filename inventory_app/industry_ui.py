"""
Industry-Specific Interface Module
===================================
Adapt UI and features based on business type.
All industry config/state comes from industry_service.py — single source of truth.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging

from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_PRIMARY
from industry_service import (
    get_config, get_all_configs, get_current_industry_id, change_industry,
    INDUSTRY_CONFIG as INDUSTRY_CONFIGS,
)


def create_industry_selector(parent, on_select_callback=None):
    """
    Create industry selection dialog.
    Shows on first run or when user wants to change industry.
    """
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Select Your Business Type")
    dlg.resize(1100, 800)
    dlg.setModal(True)

    # Content
    content = QtWidgets.QWidget()
    content_layout = QtWidgets.QVBoxLayout(content)
    content_layout.setContentsMargins(30, 30, 30, 30)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QVBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 20)

    title_label = styled_label(header_frame, "\U0001f3af Select Your Industry", font=FONT_BOLD)
    title_label.setAlignment(QtCore.Qt.AlignLeft)
    header_layout.addWidget(title_label)

    subtitle_label = styled_label(header_frame, "Choose the option that best describes your business",
                 foreground="#6c757d")
    subtitle_label.setAlignment(QtCore.Qt.AlignLeft)
    header_layout.addWidget(subtitle_label)

    content_layout.addWidget(header_frame)

    # Industry cards
    cards_scroll = QtWidgets.QScrollArea()
    cards_scroll.setWidgetResizable(True)
    cards_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    cards_frame = QtWidgets.QWidget()
    cards_layout = QtWidgets.QGridLayout(cards_frame)
    cards_layout.setContentsMargins(0, 0, 0, 0)

    selected_industry = {'value': None}

    def select_industry(industry_id):
        selected_industry['value'] = industry_id
        dlg.accept()

    # Create cards in grid
    industries = list(INDUSTRY_CONFIGS.items())
    row = 0
    col = 0

    for industry_id, config in industries:
        # Create card
        card = make_card(cards_frame, padding=20)
        card_layout = QtWidgets.QVBoxLayout(card)

        # Icon and name
        name_frame = QtWidgets.QWidget()
        name_layout = QtWidgets.QHBoxLayout(name_frame)
        name_layout.setContentsMargins(0, 0, 0, 10)

        icon_label = styled_label(name_frame, text=config['icon'], font=("Segoe UI", 32))
        name_layout.addWidget(icon_label)

        info_frame = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name_label = styled_label(info_frame, text=config['name'], font=FONT_BOLD)
        name_label.setAlignment(QtCore.Qt.AlignLeft)
        info_layout.addWidget(name_label)

        desc_label = styled_label(info_frame, text=config['description'],
                    foreground="#6c757d", font=("Segoe UI", 9))
        desc_label.setAlignment(QtCore.Qt.AlignLeft)
        info_layout.addWidget(desc_label)

        name_layout.addWidget(info_frame, stretch=1)
        card_layout.addWidget(name_frame)

        # Features preview
        features = config['features']
        enabled_features = [k.replace('track_', '').replace('_', ' ').title()
                           for k, v in features.items() if v]

        if enabled_features:
            features_text = " \u2022 ".join(enabled_features[:3])
            feat_label = styled_label(card, text=features_text, font=("Segoe UI", 8),
                        foreground=COLOR_PRIMARY)
            feat_label.setAlignment(QtCore.Qt.AlignLeft)
            card_layout.addWidget(feat_label)
            card_layout.addSpacing(10)

        # Select button
        select_btn = make_button(card, "Select", command=lambda iid=industry_id: select_industry(iid),
                   kind="primary")
        card_layout.addWidget(select_btn, alignment=QtCore.Qt.AlignRight)

        # Grid positioning
        cards_layout.addWidget(card, row, col)

        col += 1
        if col > 1:
            col = 0
            row += 1

    cards_layout.setRowStretch(row + 1, 1)
    cards_scroll.setWidget(cards_frame)
    content_layout.addWidget(cards_scroll, stretch=1)

    # Footer
    footer_frame = QtWidgets.QWidget()
    footer_layout = QtWidgets.QHBoxLayout(footer_frame)
    footer_layout.setContentsMargins(0, 20, 0, 0)

    footer_label = styled_label(footer_frame, "You can change this later in Settings",
                foreground="#6c757d", font=("Segoe UI", 9))
    footer_layout.addWidget(footer_label)
    footer_layout.addStretch()

    content_layout.addWidget(footer_frame)

    dlg.setLayout(content_layout)

    # Wait for dialog to close
    result = dlg.exec()

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
    window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 15)

    styled_label(header_frame, "\u2699\ufe0f Industry Settings", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    header_layout.addWidget(styled_label(header_frame, "\u2699\ufe0f Industry Settings", font=FONT_BOLD))
    header_layout.addStretch()

    main_layout.addWidget(header_frame)

    # Current industry
    current_industry = get_current_industry()
    config = get_industry_config(current_industry)

    info_frame = make_card(window, padding=20)
    info_layout = QtWidgets.QVBoxLayout(info_frame)

    styled_label(info_frame, "Current Industry", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    info_layout.addWidget(styled_label(info_frame, f"{config['icon']} {config['name']}",
                font=("Segoe UI", 18), foreground=COLOR_PRIMARY))
    info_layout.addWidget(styled_label(info_frame, config['description']))
    info_layout.addSpacing(15)

    # Features enabled
    features_group = QtWidgets.QGroupBox("Enabled Features")
    features_group_layout = QtWidgets.QVBoxLayout(features_group)

    features = config.get('features', {})
    enabled = [k.replace('track_', '').replace('_', ' ').title() for k, v in features.items() if v]

    if enabled:
        for feature in enabled:
            feat_label = styled_label(features_group, f"\u2713 {feature}", foreground=COLOR_PRIMARY)
            feat_label.setAlignment(QtCore.Qt.AlignLeft)
            features_group_layout.addWidget(feat_label)
    else:
        no_feat_label = styled_label(features_group, "No special features enabled", foreground="#6c757d")
        no_feat_label.setAlignment(QtCore.Qt.AlignLeft)
        features_group_layout.addWidget(no_feat_label)

    info_layout.addWidget(features_group)

    main_layout.addWidget(info_frame)

    # Change industry
    change_group = QtWidgets.QGroupBox("Change Industry")
    change_group_layout = QtWidgets.QVBoxLayout(change_group)

    styled_label(change_group, "Select a different industry type:").setAlignment(QtCore.Qt.AlignLeft)
    change_group_layout.addWidget(styled_label(change_group, "Select a different industry type:"))

    industry_combo = QtWidgets.QComboBox()
    industry_combo.addItems([f"{conf['icon']} {conf['name']}" for conf in INDUSTRY_CONFIGS.values()])
    industry_combo.setEditable(False)
    change_group_layout.addWidget(industry_combo)

    # Set current selection
    for i, (iid, conf) in enumerate(INDUSTRY_CONFIGS.items()):
        if iid == current_industry:
            industry_combo.setCurrentIndex(i)
            break

    def change_industry_action():
        selection = industry_combo.currentText()

        # Find industry ID from selection
        selected_id = None
        for iid, conf in INDUSTRY_CONFIGS.items():
            if f"{conf['icon']} {conf['name']}" == selection:
                selected_id = iid
                break

        if selected_id and selected_id != current_industry:
            reply = QtWidgets.QMessageBox.question(window, "Confirm Change",
                                  "Changing industry will add new categories and fields.\nContinue?",
                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                # Use IndustryService — single source of truth
                # Handles: validate -> persist -> AppState sync -> tab reload -> notify
                try:
                    from industry_service import change_industry as switch_industry
                    if switch_industry(selected_id):
                        QtWidgets.QMessageBox.information(window, "Success",
                            f"Industry changed to {INDUSTRY_CONFIGS[selected_id]['name']}")
                    else:
                        QtWidgets.QMessageBox.critical(window, "Error",
                            f"Failed to switch industry to '{selected_id}'. Check logs.")
                except Exception as e:
                    logging.error(f"Industry switch error: {e}", exc_info=True)
                    QtWidgets.QMessageBox.critical(window, "Error", f"Failed to change industry: {e}")
        else:
            QtWidgets.QMessageBox.information(window, "Info", "No change selected")

    change_btn = make_button(change_group, "Change Industry", command=change_industry_action, kind="primary")
    change_group_layout.addWidget(change_btn)

    main_layout.addWidget(change_group)

    # Custom fields info
    fields_group = QtWidgets.QGroupBox("Custom Fields")
    fields_group_layout = QtWidgets.QVBoxLayout(fields_group)

    custom_fields = get_custom_fields(current_industry)

    if custom_fields:
        # Create treeview
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderLabels(["Name", "Type", "Description"])
        tree.setColumnWidth(0, 150)
        tree.setColumnWidth(1, 150)
        tree.setColumnWidth(2, 150)

        for field_id, field_name, field_type in custom_fields:
            item = QtWidgets.QTreeWidgetItem([field_name, field_type.title(), ""])
            tree.addTopLevelItem(item)

        fields_group_layout.addWidget(tree)
    else:
        no_fields_label = styled_label(fields_group, "No custom fields for this industry",
                    foreground="#6c757d")
        no_fields_label.setAlignment(QtCore.Qt.AlignCenter)
        fields_group_layout.addWidget(no_fields_label)

    main_layout.addWidget(fields_group, stretch=1)

    return window


def apply_industry_settings():
    """Apply industry-specific settings to the application."""
    industry_id = get_current_industry()
    config = get_industry_config(industry_id)

    logging.info(f"Applied industry settings: {config['name']}")

    # Return config for use in other modules
    return config
