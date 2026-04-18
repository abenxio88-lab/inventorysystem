"""
Premium Dashboard UI with Interactive Charts, AI Insights, and Glassmorphism
"""
import os
from datetime import datetime, timedelta
import logging

from PySide6 import QtWidgets, QtCore, QtGui

# Project imports
from services import svc
from ui_theme import (
    make_button, make_card, styled_label,
    COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_APP_BG, COLOR_INFO,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
    BTN_WIDTH, FONT_BOLD, FONT_HEADING, FONT_REGULAR, SUBHEADING_FONT, FONT_SMALL
)
from migration_add_industry_type import get_industry_type, get_industry_metadata
from industry_selector import create_industry_selector_card
from users_ui import open_user_manager
from audit_ui import open_audit_viewer
from setup_licensing_ui import open_owner_dashboard
from utils import load_settings, save_settings


def create_dashboard_tab(parent, username, role, switch_tab_callback=None):
    """
    Creates the premium dashboard tab with glassmorphism cards and industry-specific context.
    Returns a QtWidgets.QWidget.
    """
    dashboard_widget = QtWidgets.QWidget()
    dashboard_widget.setObjectName("dashboard_tab")
    main_layout = QtWidgets.QVBoxLayout(dashboard_widget)
    main_layout.setContentsMargins(30, 30, 30, 30)
    main_layout.setSpacing(20)

    # --- Header Information ---
    from config import get_industry_config, get_default_industry

    # Get industry config (from DB or default)
    try:
        from database import db
        industry_id = db.get_industry_type()
    except Exception:
        logging.warning("Failed to get industry from DB, using default")
        industry_id = get_default_industry()

    config = get_industry_config(industry_id)

    # --- Premium Header ---
    header_layout = QtWidgets.QHBoxLayout()
    header_layout.setSpacing(20)

    # Left side: Welcome & Role
    user_info_widget = QtWidgets.QWidget()
    user_info_layout = QtWidgets.QVBoxLayout(user_info_widget)
    user_info_layout.setContentsMargins(0, 0, 0, 0)
    user_info_layout.setSpacing(5)

    welcome_label = styled_label(user_info_widget, f"Welcome back, {username.capitalize()}", font=FONT_HEADING, foreground=COLOR_PRIMARY)
    user_info_layout.addWidget(welcome_label)

    role_label = styled_label(user_info_widget, f"Role: {role.upper()}", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED)
    user_info_layout.addWidget(role_label)
    user_info_layout.addStretch()

    header_layout.addWidget(user_info_widget, stretch=1)

    # Right side: Current Industry Badge (from config)
    industry_badge = create_status_badge(
        dashboard_widget,
        text=config.industry_name.upper(),
        icon=config.icon,
        color=config.color
    )
    header_layout.addWidget(industry_badge, alignment=QtCore.Qt.AlignTop)

    main_layout.addLayout(header_layout)

    # Divider
    divider = create_divider(dashboard_widget, orientation="horizontal", color=COLOR_BORDER, thickness=1)
    main_layout.addWidget(divider)

    # --- PREMIUM STATS CARDS (config-driven) ---
    stats_layout = QtWidgets.QHBoxLayout()
    stats_layout.setSpacing(15)

    label_refs = {}
    card_widgets = []

    # Build KPI cards from industry config
    # Each industry can define its own KPI structure
    if industry_id == "electronics":
        # Electronics KPIs
        card_configs = [
            {"id": "products", "title": "Products", "value": "...", "color": COLOR_PRIMARY, "icon": "\U0001F4E6", "tab": "Inventory"},
            {"id": "stock", "title": "Total Stock", "value": "...", "color": COLOR_INFO, "icon": "\U0001F4CA", "tab": "Inventory"},
            {"id": "warranty", "title": "Expiring Warranty", "value": "...", "color": COLOR_DANGER, "icon": "\U0001F527", "tab": "Warranty"},
            {"id": "sales", "title": "Sales", "value": "...", "color": "#10B981", "icon": "\U0001F4B8", "tab": "Sales"},
        ]
    elif industry_id == "pharma":
        # Pharma KPIs
        card_configs = [
            {"id": "products", "title": "Products", "value": "...", "color": COLOR_PRIMARY, "icon": "\U0001F4E6", "tab": "Inventory"},
            {"id": "expired", "title": "Expired", "value": "...", "color": COLOR_DANGER, "icon": "\U0001F480", "tab": "Expiry Alerts"},
            {"id": "expiring", "title": "Expiring Soon", "value": "...", "color": COLOR_WARNING, "icon": "\u23F0", "tab": "Expiry Alerts"},
            {"id": "sales", "title": "Sales", "value": "...", "color": "#10B981", "icon": "\U0001F4B8", "tab": "Sales"},
        ]
    else:
        # Retail/Default KPIs
        card_configs = [
            {"id": "products", "title": "Products", "value": "...", "color": COLOR_PRIMARY, "icon": "\U0001F4E6", "tab": "Inventory"},
            {"id": "stock", "title": "Total Stock", "value": "...", "color": COLOR_INFO, "icon": "\U0001F4CA", "tab": "Inventory"},
            {"id": "low_stock", "title": "Low Stock", "value": "...", "color": COLOR_SUCCESS, "icon": "\u26A0\uFE0F", "tab": "Inventory"},
            {"id": "sales", "title": "Sales", "value": "...", "color": "#10B981", "icon": "\U0001F4B8", "tab": "Sales"},
        ]

    # Create stats cards with responsive layout
    for idx, card_config in enumerate(card_configs):
        card = make_card(dashboard_widget, padx=25, pady=25)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setSpacing(10)

        icon_label = styled_label(card, card_config["icon"], font=("Segoe UI", 32))
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(icon_label)

        title_label = styled_label(card, card_config["title"], font=FONT_SMALL, foreground=COLOR_TEXT_MUTED)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(title_label)

        value_label = styled_label(card, card_config["value"], font=FONT_HEADING, foreground=card_config["color"])
        value_label.setAlignment(QtCore.Qt.AlignCenter)
        card_layout.addWidget(value_label)

        label_refs[card_config["id"]] = value_label
        card_widgets.append((card, card_config.get("tab")))

        stats_layout.addWidget(card, stretch=1)

    main_layout.addLayout(stats_layout)

    def refresh_dashboard_kpis(*args):
        """Dynamic KPI refresh - reads from industry-specific service."""
        try:
            products = svc.inventory.get_all_products(active_only=True)
            orders = svc.sales.get_all_orders()
            total_items = sum(int(p.get('stock', 0)) for p in products)
            low_stock = len([p for p in products if int(p.get('stock', 0)) <= p.get('reorder_point', 5)])
            total_sales = len(orders)

            # Update base KPIs (all industries)
            if "products" in label_refs:
                label_refs["products"].setText(str(len(products)))
            if "stock" in label_refs:
                label_refs["stock"].setText(str(total_items))
            if "low_stock" in label_refs:
                lbl = label_refs["low_stock"]
                lbl.setText(str(low_stock))
                lbl.setStyleSheet(lbl.styleSheet().replace(
                    f"color: {COLOR_SUCCESS};", f"color: {COLOR_DANGER};"
                ) if low_stock > 0 else lbl.styleSheet().replace(
                    f"color: {COLOR_DANGER};", f"color: {COLOR_SUCCESS};"
                ))
                lbl.setProperty("foreground", COLOR_DANGER if low_stock > 0 else COLOR_SUCCESS)
                lbl.style().unpolish(lbl)
                lbl.style().polish(lbl)
            if "sales" in label_refs:
                label_refs["sales"].setText(str(total_sales))

            # Industry-specific KPIs
            if industry_id == "electronics":
                # Warranty expiring
                expiring_warranty = len([p for p in products if p.get('warranty_expiry')])
                if "warranty" in label_refs:
                    label_refs["warranty"].setText(str(expiring_warranty))

            elif industry_id == "pharma":
                # Expired products
                expired = len([p for p in products if p.get('expiry_date') and p.get('expiry_date') < datetime.now().strftime('%Y-%m-%d')])
                if "expired" in label_refs:
                    label_refs["expired"].setText(str(expired))
                    label_refs["expired"].setStyleSheet(label_refs["expired"].styleSheet().replace(
                        f"color: {COLOR_DANGER};", f"color: {COLOR_DANGER};"
                    ))
                    label_refs["expired"].setProperty("foreground", COLOR_DANGER)
                    label_refs["expired"].style().unpolish(label_refs["expired"])
                    label_refs["expired"].style().polish(label_refs["expired"])

                # Expiring soon (30 days)
                thirty_days = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                expiring = len([p for p in products if p.get('expiry_date') and p.get('expiry_date') < thirty_days and p.get('expiry_date') >= datetime.now().strftime('%Y-%m-%d')])
                if "expiring" in label_refs:
                    label_refs["expiring"].setText(str(expiring))
                    label_refs["expiring"].setStyleSheet(label_refs["expiring"].styleSheet().replace(
                        f"color: {COLOR_WARNING};", f"color: {COLOR_WARNING};"
                    ))
                    label_refs["expiring"].setProperty("foreground", COLOR_WARNING)
                    label_refs["expiring"].style().unpolish(label_refs["expiring"])
                    label_refs["expiring"].style().polish(label_refs["expiring"])

        except Exception as e:
            logging.error(f"Failed to refresh dashboard stats: {e}")
            # Set fallback values
            for key, lbl in label_refs.items():
                try:
                    lbl.setText("Error")
                    lbl.setProperty("foreground", COLOR_DANGER)
                    lbl.style().unpolish(lbl)
                    lbl.style().polish(lbl)
                except Exception:
                    logging.debug(f"Failed to update label {key}")

    # Register for real-time updates and fetch initial
    from app_core import app_state
    app_state.register_ui_callback("db_changed", refresh_dashboard_kpis)

    # Initial fetch
    refresh_dashboard_kpis()

    # Set up a secondary periodic refresh as backup (every 60 seconds)
    # This ensures KPIs stay fresh even if db_changed notifications are missed
    refresh_timer = QtCore.QTimer(dashboard_widget)
    refresh_timer.timeout.connect(refresh_dashboard_kpis)
    refresh_timer.start(60000)  # Refresh every 60 seconds

    # Make cards clickable for navigation
    for card_widget, tab_name in card_widgets:
        if switch_tab_callback and tab_name:
            def make_nav(target):
                return lambda: switch_tab_callback(target)
            card_widget.setCursor(QtCore.Qt.PointingHandCursor)
            # Store the callback on the widget for click handling
            card_widget.setProperty("nav_target", tab_name)
            card_widget.mousePressEvent = make_nav(tab_name)

    # --- INDUSTRY SELECTOR ---
    if create_industry_selector_card:
        def on_industry_changed(new_industry_id):
            """Handle industry change confirmation.

            The actual industry persistence + tab reload is handled by
            IndustryService.change_industry() called inside the selector.
            This callback only confirms success to the user.
            """
            try:
                from industry_service import get_config
                config = get_config(new_industry_id)
                QtWidgets.QMessageBox.information(
                    dashboard_widget,
                    "Mode Switched",
                    f"System operating mode changed to: {config['name']}\n"
                    f"All tabs and forms have been updated."
                )
            except Exception as e:
                logging.error(f"Industry change confirmation error: {e}", exc_info=True)
                QtWidgets.QMessageBox.warning(
                    dashboard_widget,
                    "Update",
                    "Industry may have changed. Please verify in the tabs shown."
                )

        industry_section = create_industry_selector_card(dashboard_widget, on_industry_changed=on_industry_changed)
        main_layout.addWidget(industry_section)

    # --- Business Configuration Card ---
    try:
        from business_settings import create_business_card
        business_card = create_business_card(
            dashboard_widget, dashboard_widget, switch_tab_callback
        )
        main_layout.addWidget(business_card)
    except ImportError:
        logging.debug("Business settings card not available")

    # --- Quick Actions Section ---
    actions_card = make_card(dashboard_widget, padx=25, pady=20)
    actions_layout = QtWidgets.QVBoxLayout(actions_card)
    actions_layout.setSpacing(15)

    actions_title = styled_label(actions_card, "Quick Actions", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN)
    actions_layout.addWidget(actions_title)

    quick_actions_layout = QtWidgets.QHBoxLayout()
    quick_actions_layout.setSpacing(15)

    action_buttons = [
        ("Add Product", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None, "primary"),
        ("New Sale", lambda: switch_tab_callback("Sales") if switch_tab_callback else None, "secondary"),
        ("Reports", lambda: switch_tab_callback("Reports") if switch_tab_callback else None, "secondary"),
    ]

    for text, cmd, kind in action_buttons:
        btn = make_button(actions_card, text=text, command=cmd, kind=kind)
        quick_actions_layout.addWidget(btn)

    quick_actions_layout.addStretch()
    actions_layout.addLayout(quick_actions_layout)
    main_layout.addWidget(actions_card)

    # --- System & Owner Information Card ---
    info_card = make_card(dashboard_widget, padx=25, pady=20)
    info_layout = QtWidgets.QVBoxLayout(info_card)
    info_layout.setSpacing(10)

    info_title = styled_label(info_card, "System Overview", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN)
    info_layout.addWidget(info_title)

    # Two-column layout for info
    info_cols_layout = QtWidgets.QHBoxLayout()
    info_cols_layout.setSpacing(20)

    left_col = QtWidgets.QWidget()
    left_col_layout = QtWidgets.QVBoxLayout(left_col)
    left_col_layout.setContentsMargins(0, 0, 0, 0)
    left_col_layout.setSpacing(5)

    right_col = QtWidgets.QWidget()
    right_col_layout = QtWidgets.QVBoxLayout(right_col)
    right_col_layout.setContentsMargins(0, 0, 0, 0)
    right_col_layout.setSpacing(5)

    settings = load_settings()
    company_name = settings.get("company_name", "Mintaka Sphere Inventory System")
    support_email = settings.get("support_email", "support@mintakasphere.com")
    currency = settings.get("currency", "PKR")
    tax_rate = settings.get("tax_rate", "0")

    # Left column - System Info
    left_col_layout.addWidget(styled_label(left_col, f"Company: {company_name}", font=FONT_SMALL, foreground=COLOR_TEXT_MAIN))
    left_col_layout.addWidget(styled_label(left_col, f"Support: {support_email}", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED))
    left_col_layout.addWidget(styled_label(left_col, f"Currency: {currency} | Tax: {float(tax_rate):.1f}%", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED))
    left_col_layout.addStretch()

    # Right column - Industry & User Info
    right_col_layout.addWidget(styled_label(right_col, f"Industry: {config.industry_name} {config.icon}", font=FONT_SMALL, foreground=COLOR_TEXT_MAIN))
    right_col_layout.addWidget(styled_label(right_col, f"User: {username.capitalize()} | Role: {role.upper()}", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED))
    right_col_layout.addWidget(styled_label(right_col, "Software: Mintaka Sphere IMS v1.0.0 | Status: Active", font=FONT_SMALL, foreground=COLOR_SUCCESS))
    right_col_layout.addStretch()

    info_cols_layout.addWidget(left_col, stretch=1)
    info_cols_layout.addWidget(right_col, stretch=1)
    info_layout.addLayout(info_cols_layout)
    main_layout.addWidget(info_card)

    # --- Administrative Panel (Admins Only) ---
    if role in ["admin", "OWNER_ADMIN"]:
        admin_card = make_card(dashboard_widget, padx=25, pady=20)
        admin_layout = QtWidgets.QVBoxLayout(admin_card)
        admin_layout.setSpacing(15)

        admin_title = styled_label(admin_card, "Administrative Controls", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN)
        admin_layout.addWidget(admin_title)

        admin_controls_layout = QtWidgets.QHBoxLayout()
        admin_controls_layout.setSpacing(15)

        # User Management
        if open_user_manager:
            admin_controls_layout.addWidget(
                make_button(admin_card, "Manage Users",
                           command=lambda: open_user_manager(dashboard_widget, current_user=username),
                           kind="secondary")
            )

        # Audit Log
        if open_audit_viewer:
            admin_controls_layout.addWidget(
                make_button(admin_card, "Audit Logs",
                           command=lambda: open_audit_viewer(dashboard_widget, current_user=username),
                           kind="secondary")
            )

        # Owner Specific Tools
        if role == "OWNER_ADMIN" and open_owner_dashboard:
            admin_controls_layout.addWidget(
                make_button(admin_card, "Owner Dashboard",
                           command=lambda: open_owner_dashboard(dashboard_widget),
                           kind="primary")
            )

        # Quick Settings
        def open_settings():
            s = load_settings()
            hour, ok = QtWidgets.QInputDialog.getInt(
                dashboard_widget,
                "Backup Hour",
                "Hour (0-23):",
                value=s.get("backup_hour", 2),
                min=0,
                max=23
            )
            if ok:
                save_settings({"backup_hour": hour})
                QtWidgets.QMessageBox.information(dashboard_widget, "Settings", "Backup settings saved.")

        admin_controls_layout.addWidget(
            make_button(admin_card, "Settings", command=open_settings, kind="secondary")
        )

        # System Health Check
        try:
            from auto_issue_finder import check_and_show_issues
            admin_controls_layout.addWidget(
                make_button(admin_card, "Health Check",
                           command=lambda: check_and_show_issues(dashboard_widget),
                           kind="secondary")
            )
        except ImportError:
            pass

        # Developer Dashboard
        try:
            from dev_dashboard import open_dev_dashboard
            admin_controls_layout.addWidget(
                make_button(admin_card, "Dev Tools",
                           command=lambda: open_dev_dashboard(dashboard_widget),
                           kind="secondary")
            )
        except ImportError:
            pass

        # Error Dashboard
        try:
            from error_dashboard_widget import open_error_dashboard
            admin_controls_layout.addWidget(
                make_button(admin_card, "Error Dashboard",
                           command=lambda: open_error_dashboard(dashboard_widget),
                           kind="secondary")
            )
        except ImportError:
            pass

        admin_controls_layout.addStretch()
        admin_layout.addLayout(admin_controls_layout)
        main_layout.addWidget(admin_card)

    main_layout.addStretch()

    return dashboard_widget
