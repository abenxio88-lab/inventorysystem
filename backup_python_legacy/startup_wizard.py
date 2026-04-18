"""
Startup Wizard Module
======================
First-run company setup with industry selection and smart configuration.
Adapts the entire application based on business type.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import json
import os
import logging

try:
    from .database import init_database, get_db_cursor
    from .ui_theme import (
        make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD,
        FONT_HEADING, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_APP_BG,
        COLOR_TEXT_MAIN, COLOR_TEXT_MUTED
    )
except (ImportError, ModuleNotFoundError):
    from database import init_database, get_db_cursor
    from ui_theme import (
        make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD,
        FONT_HEADING, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_APP_BG,
        COLOR_TEXT_MAIN, COLOR_TEXT_MUTED
    )


# Company type configurations with workflow adaptations
COMPANY_TYPES = {
    'lease_rental': {
        'name': 'Lease & Rental Business',
        'icon': '\U0001f3af',
        'description': 'Equipment rental, lease management, collections',
        'priority_tabs': ['dashboard', 'lease', 'collections', 'reports'],
        'hidden_tabs': ['suppliers', 'purchase_orders'],
        'features': {
            'leasing': True,
            'collections': True,
            'invoicing': True,
            'purchase_orders': False,
            'multi_location': False,
            'barcode_scanning': True,
        },
        'dashboard_widgets': ['items_leased', 'due_collections', 'revenue', 'collection_rate'],
        'quick_actions': ['create_lease', 'record_payment', 'scan_barcode', 'view_due'],
    },

    'electronics_retail': {
        'name': 'Electronics & Mobile Retail',
        'icon': '\U0001f4f1',
        'description': 'Mobile phones, computers, electronics store',
        'priority_tabs': ['dashboard', 'inventory', 'sales', 'electronics'],
        'hidden_tabs': ['lease'],
        'features': {
            'leasing': False,
            'collections': False,
            'invoicing': False,
            'purchase_orders': True,
            'multi_location': True,
            'barcode_scanning': True,
            'serial_tracking': True,
        },
        'dashboard_widgets': ['low_stock', 'today_sales', 'top_products', 'warranty_alerts'],
        'quick_actions': ['add_product', 'record_sale', 'scan_barcode', 'view_low_stock'],
    },

    'pharmacy': {
        'name': 'Pharmacy & Medical',
        'icon': '\U0001f48a',
        'description': 'Pharmacy, medical supplies, healthcare',
        'priority_tabs': ['dashboard', 'inventory', 'sales', 'reports'],
        'hidden_tabs': ['lease', 'electronics'],
        'features': {
            'leasing': False,
            'collections': False,
            'invoicing': False,
            'purchase_orders': True,
            'multi_location': False,
            'barcode_scanning': True,
            'expiry_tracking': True,
            'batch_tracking': True,
        },
        'dashboard_widgets': ['expiring_soon', 'low_stock', 'today_sales', 'prescription_alerts'],
        'quick_actions': ['add_product', 'record_sale', 'view_expiry', 'check_stock'],
    },

    'general_retail': {
        'name': 'General Retail / Shop',
        'icon': '\U0001f3ea',
        'description': 'Retail store, general merchandise',
        'priority_tabs': ['dashboard', 'inventory', 'sales', 'reports'],
        'hidden_tabs': ['lease', 'electronics'],
        'features': {
            'leasing': False,
            'collections': False,
            'invoicing': False,
            'purchase_orders': True,
            'multi_location': False,
            'barcode_scanning': True,
        },
        'dashboard_widgets': ['today_sales', 'low_stock', 'top_products', 'revenue'],
        'quick_actions': ['add_product', 'record_sale', 'view_stock', 'create_po'],
    },

    'wholesale': {
        'name': 'Wholesale & Distribution',
        'icon': '\U0001f4e6',
        'description': 'Wholesale trading, bulk distribution',
        'priority_tabs': ['dashboard', 'inventory', 'purchase_orders', 'sales_orders'],
        'hidden_tabs': ['lease', 'electronics'],
        'features': {
            'leasing': False,
            'collections': True,
            'invoicing': True,
            'purchase_orders': True,
            'multi_location': True,
            'barcode_scanning': True,
        },
        'dashboard_widgets': ['pending_orders', 'low_stock', 'receivables', 'shipments'],
        'quick_actions': ['create_po', 'create_sales_order', 'view_inventory', 'check_orders'],
    },
}


def create_startup_wizard(parent, on_complete_callback=None):
    """
    Create first-run startup wizard.
    Guides user through company type selection and initial setup.
    """
    wizard = QtWidgets.QDialog(parent)
    wizard.setWindowTitle("Core Platform Intelligence - Initial Setup")
    wizard.resize(900, 700)
    wizard.setModal(True)

    # Center window
    screen = QtWidgets.QApplication.primaryScreen().geometry()
    x = (screen.width() // 2) - (900 // 2)
    y = (screen.height() // 2) - (700 // 2)
    wizard.move(x, y)

    state = {
        'step': 1,
        'company_type': None,
        'company_name': '',
    }

    # Main layout
    main_layout = QtWidgets.QVBoxLayout(wizard)
    main_layout.setContentsMargins(30, 30, 30, 30)

    # Progress bar
    progress_var = 1
    progress_bar = QtWidgets.QProgressBar()
    progress_bar.setRange(1, 3)
    progress_bar.setValue(1)
    main_layout.addWidget(progress_bar)

    progress_label = QtWidgets.QLabel("PHASE 1: SYSTEM IDENTIFICATION")
    progress_label.setStyleSheet("color: #6c757d; font-size: 9pt; font-family: 'Segoe UI';")
    main_layout.addWidget(progress_label)

    # Step container
    step_frame = QtWidgets.QWidget()
    step_layout = QtWidgets.QVBoxLayout(step_frame)
    step_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(step_frame, stretch=1)

    def show_step(step_num):
        """Show specific step."""
        # Clear step frame
        for i in reversed(range(step_layout.count())):
            widget = step_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        progress_bar.setValue(step_num)
        if step_num > 1:
            progress_label.setText(f"PHASE {step_num}: SYSTEM CALIBRATION")
        else:
            progress_label.setText("PHASE 1: SYSTEM IDENTIFICATION")

        if step_num == 1:
            show_welcome()
        elif step_num == 2:
            show_company_type()
        elif step_num == 3:
            show_features()

    def show_welcome():
        """Step 1: Welcome screen."""
        # Header
        header_frame = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 20, 0, 40)

        title_label = styled_label(header_frame, text="\u2728 INITIALIZING PLATFORM", font=FONT_HEADING, foreground=COLOR_PRIMARY)
        title_label.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(title_label)

        subtitle_label = styled_label(header_frame,
                    text="Configure your enterprise environment parameters",
                    foreground=COLOR_TEXT_MUTED)
        subtitle_label.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(subtitle_label)

        step_layout.addWidget(header_frame)

        # Info cards
        info_frame = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        info_layout.setContentsMargins(0, 20, 0, 20)

        features = [
            ("\U0001f4e6", "Inventory Management", "Track products across locations"),
            ("\U0001f4b0", "Sales & Orders", "Manage sales and customer orders"),
            ("\U0001f4ca", "Reports & Analytics", "Business insights and exports"),
            ("\U0001f3af", "Lease & Rental", "Complete lease management"),
            ("\U0001f514", "Smart Alerts", "Low stock and expiry warnings"),
            ("\u2601\ufe0f", "Cloud Backup", "Google Drive integration"),
        ]

        for i in range(0, len(features), 2):
            row_frame = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_frame)
            row_layout.setContentsMargins(0, 0, 0, 0)

            for j in range(2):
                if i + j < len(features):
                    icon, title, desc = features[i + j]
                    card = make_card(row_frame, padding=15)
                    card_layout = QtWidgets.QVBoxLayout(card)

                    icon_label = styled_label(card, text=icon, font=("Segoe UI", 24))
                    icon_label.setAlignment(QtCore.Qt.AlignLeft)
                    card_layout.addWidget(icon_label)

                    title_label = styled_label(card, text=title, font=FONT_BOLD)
                    title_label.setAlignment(QtCore.Qt.AlignLeft)
                    card_layout.addWidget(title_label)

                    desc_label = styled_label(card, text=desc, font=("Segoe UI", 9),
                                foreground="#6c757d")
                    desc_label.setAlignment(QtCore.Qt.AlignLeft)
                    card_layout.addWidget(desc_label)

                    row_layout.addWidget(card, stretch=1)

            row_layout.addStretch()
            info_layout.addWidget(row_frame)

        step_layout.addWidget(info_frame, stretch=1)

        # Next button
        button_frame = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.addStretch()

        def next_step():
            state['step'] = 2
            show_step(2)

        next_btn = make_button(button_frame, "Get Started \u2192", command=next_step,
                   kind="success")
        button_layout.addWidget(next_btn)

        step_layout.addWidget(button_frame)

    def show_company_type():
        """Step 2: Select company type."""
        # Header
        header_frame = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 20, 0, 20)

        title_label = styled_label(header_frame, text="\U0001f3e2 SELECT BUSINESS PROFILE", font=FONT_HEADING, foreground=COLOR_PRIMARY)
        title_label.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(title_label)

        subtitle_label = styled_label(header_frame,
                    text="Select the operational parameters for your enterprise",
                    foreground=COLOR_TEXT_MUTED)
        subtitle_label.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(subtitle_label)

        step_layout.addWidget(header_frame)

        # Company type cards
        cards_scroll = QtWidgets.QScrollArea()
        cards_scroll.setWidgetResizable(True)
        cards_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        cards_frame = QtWidgets.QWidget()
        cards_layout = QtWidgets.QVBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        # Shared variable for radio buttons
        type_var = QtCore.QSignalMapper()
        selected_type = [state.get('company_type') or 'general_retail']

        def select_type(type_id):
            selected_type[0] = type_id
            state['company_type'] = type_id
            logging.debug(f"Selected company type: {type_id}")

        # Create cards
        for type_id, config in COMPANY_TYPES.items():
            card = make_card(cards_frame, padding=20)
            card_layout = QtWidgets.QVBoxLayout(card)

            # Icon and name
            header = QtWidgets.QWidget()
            header_layout_inner = QtWidgets.QHBoxLayout(header)
            header_layout_inner.setContentsMargins(0, 0, 0, 0)

            icon_label = styled_label(header, text=config['icon'], font=("Segoe UI", 32))
            header_layout_inner.addWidget(icon_label)

            info = QtWidgets.QWidget()
            info_layout_inner = QtWidgets.QVBoxLayout(info)
            info_layout_inner.setContentsMargins(0, 0, 0, 0)

            name_label = styled_label(info, text=config['name'], font=FONT_BOLD)
            name_label.setAlignment(QtCore.Qt.AlignLeft)
            info_layout_inner.addWidget(name_label)

            desc_label = styled_label(info, text=config['description'], font=("Segoe UI", 9),
                        foreground="#6c757d")
            desc_label.setAlignment(QtCore.Qt.AlignLeft)
            info_layout_inner.addWidget(desc_label)

            header_layout_inner.addWidget(info, stretch=1)
            card_layout.addWidget(header)

            # Features
            features = [k.replace('_', ' ').title() for k, v in config['features'].items() if v][:4]
            features_text = " \u2022 ".join(features)

            f_lbl = styled_label(card, text=features_text, font=("Segoe UI", 8),
                                foreground=COLOR_PRIMARY)
            f_lbl.setAlignment(QtCore.Qt.AlignLeft)
            card_layout.addWidget(f_lbl)

            # Radio button
            radio = QtWidgets.QRadioButton()
            if type_id == selected_type[0]:
                radio.setChecked(True)
            radio.toggled.connect(lambda checked, tid=type_id: select_type(tid) if checked else None)
            card_layout.addWidget(radio, alignment=QtCore.Qt.AlignRight)

            # Make the entire card clickable
            card.mousePressEvent = lambda e, tid=type_id: (select_type(tid), setattr(radio, '_clicked', True))

            cards_layout.addWidget(card)

        cards_layout.addStretch()
        cards_scroll.setWidget(cards_frame)
        step_layout.addWidget(cards_scroll, stretch=1)

        # Navigation
        button_frame = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 0, 0)

        def back():
            state['step'] = 1
            show_step(1)

        def next_step():
            if state.get('company_type'):
                state['step'] = 3
                show_step(3)
            else:
                QtWidgets.QMessageBox.information(wizard, "Select", "Please select a business type")

        back_btn = make_button(button_frame, "\u2190 Back", command=back, kind="secondary")
        button_layout.addWidget(back_btn)
        button_layout.addStretch()

        next_btn = make_button(button_frame, "Next \u2192", command=next_step, kind="primary")
        button_layout.addWidget(next_btn)

        step_layout.addWidget(button_frame)

    def show_features():
        """Step 3: Feature confirmation."""
        # Header
        header_frame = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 20, 0, 20)

        config = COMPANY_TYPES.get(state['company_type'], {})

        title_label = styled_label(header_frame, text="\u2705 SYSTEM CONFIGURATION OVERVIEW", font=FONT_HEADING, foreground=COLOR_SUCCESS)
        title_label.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(title_label)

        subtitle_label = styled_label(header_frame,
                    text=f"Selected Environment: {config['icon']} {config['name'].upper()}",
                    foreground=COLOR_TEXT_MUTED)
        subtitle_label.setAlignment(QtCore.Qt.AlignLeft)
        header_layout.addWidget(subtitle_label)

        step_layout.addWidget(header_frame)

        # Features list
        features_frame = make_card(step_frame, padding=20)
        features_layout = QtWidgets.QVBoxLayout(features_frame)

        styled_label(features_frame, text="Enabled Features:", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
        features_layout.addSpacing(15)

        enabled = [k.replace('_', ' ').title() for k, v in config['features'].items() if v]

        for feature in enabled:
            feature_frame = QtWidgets.QWidget()
            feature_layout = QtWidgets.QHBoxLayout(feature_frame)
            feature_layout.setContentsMargins(0, 5, 0, 5)

            check_label = styled_label(feature_frame, text="\u2713", foreground=COLOR_SUCCESS,
                        font=FONT_BOLD)
            feature_layout.addWidget(check_label)
            feature_layout.addWidget(styled_label(feature_frame, text=feature))
            feature_layout.addStretch()

            features_layout.addWidget(feature_frame)

        step_layout.addWidget(features_frame, stretch=1)

        # Company name input
        name_group = QtWidgets.QGroupBox("Company Name (Optional)")
        name_group_layout = QtWidgets.QVBoxLayout(name_group)
        name_group_layout.setContentsMargins(15, 15, 15, 15)

        company_name_edit = QtWidgets.QLineEdit()
        company_name_edit.setPlaceholderText("Enter company name")
        name_group_layout.addWidget(company_name_edit)

        step_layout.addWidget(name_group)

        # Navigation
        button_frame = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 20, 0, 0)

        def back():
            state['step'] = 2
            show_step(2)

        def finish():
            # Save company type
            company_name = company_name_edit.text().strip()
            save_company_config(state['company_type'], company_name)

            # Initialize database
            init_database()

            QtWidgets.QMessageBox.information(wizard, "Complete", "Setup complete! Starting application...")
            wizard.accept()

            # Call completion callback
            if on_complete_callback:
                on_complete_callback(state['company_type'], company_name)

        back_btn = make_button(button_frame, "\u2190 Back", command=back, kind="secondary")
        button_layout.addWidget(back_btn)
        button_layout.addStretch()

        finish_btn = make_button(button_frame, "\u2713 Complete Setup", command=finish, kind="success")
        button_layout.addWidget(finish_btn)

        step_layout.addWidget(button_frame)

    # Show first step
    show_step(1)


def save_company_config(company_type: str, company_name: str = ''):
    """Save company configuration to database."""
    with get_db_cursor() as cur:
        # Save company type
        cur.execute("""
            INSERT OR REPLACE INTO settings (key, value, category, description)
            VALUES ('company_type', ?, 'general', 'Selected business type')
        """, (company_type,))

        # Save company name
        if company_name:
            cur.execute("""
                INSERT OR REPLACE INTO settings (key, value, category, description)
                VALUES ('company_name', ?, 'general', 'Company name')
            """, (company_name,))

        # Save feature flags
        config = COMPANY_TYPES.get(company_type, {})
        for feature, enabled in config.get('features', {}).items():
            cur.execute("""
                INSERT OR REPLACE INTO settings (key, value, category)
                VALUES (?, ?, 'features')
            """, (f'feature_{feature}', '1' if enabled else '0'))


def get_company_type() -> str:
    """Get current company type."""
    with get_db_cursor() as cur:
        cur.execute("SELECT value FROM settings WHERE key = 'company_type'")
        row = cur.fetchone()
        return row['value'] if row else 'not_set'


def get_company_config() -> dict:
    """Get configuration for current company type."""
    company_type = get_company_type()
    return COMPANY_TYPES.get(company_type, COMPANY_TYPES['general_retail'])


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled for current company type."""
    config = get_company_config()
    return config['features'].get(feature, False)


def get_priority_tabs() -> list:
    """Get ordered list of priority tabs for current company type."""
    config = get_company_config()
    return config.get('priority_tabs', [])


def get_hidden_tabs() -> list:
    """Get list of tabs to hide for current company type."""
    config = get_company_config()
    return config.get('hidden_tabs', [])


def get_dashboard_widgets() -> list:
    """Get list of dashboard widgets for current company type."""
    config = get_company_config()
    return config.get('dashboard_widgets', [])


def get_quick_actions() -> list:
    """Get list of quick actions for current company type."""
    config = get_company_config()
    return config.get('quick_actions', [])
