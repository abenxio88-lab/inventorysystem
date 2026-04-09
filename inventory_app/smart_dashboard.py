"""
Smart Dashboard Module
=======================
Adaptive dashboard that changes based on company type.
Shows relevant KPIs, widgets, and quick actions for each business type.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging

try:
    from .database import get_db_cursor
    from .ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, FONT_REGULAR, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from .startup_wizard import get_company_config, get_dashboard_widgets, get_quick_actions
except (ImportError, ModuleNotFoundError):
    from database import get_db_cursor
    from ui_theme import make_card, styled_label, make_button, FONT_HEADING, FONT_BOLD, FONT_REGULAR, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    from startup_wizard import get_company_config, get_dashboard_widgets, get_quick_actions


def create_smart_dashboard(parent, username, role, company_type=None, switch_tab_callback=None):
    """
    Create adaptive dashboard based on company type.

    Args:
        parent: Parent widget
        username: Current username
        role: User role
        company_type: Override company type (optional)

    Returns:
        Dashboard frame
    """
    dashboard_frame = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(dashboard_frame)
    main_layout.setContentsMargins(30, 30, 30, 30)

    # Get company configuration
    config = get_company_config()
    company_name = config.get('name', 'Inventory System')
    company_icon = config.get('icon', '\U0001f3ea')

    # Header with company info
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QVBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    # Company name and icon
    company_header = QtWidgets.QWidget()
    company_header_layout = QtWidgets.QHBoxLayout(company_header)
    company_header_layout.setContentsMargins(0, 0, 0, 0)

    icon_label = styled_label(company_header, text=company_icon, font=("Segoe UI", 32))
    company_header_layout.addWidget(icon_label)

    info_frame = QtWidgets.QWidget()
    info_layout = QtWidgets.QVBoxLayout(info_frame)
    info_layout.setContentsMargins(0, 0, 0, 0)

    welcome_label = styled_label(info_frame, text=f"Welcome to {company_name}", font=FONT_HEADING)
    welcome_label.setAlignment(QtCore.Qt.AlignLeft)
    info_layout.addWidget(welcome_label)

    user_label = styled_label(info_frame, text=f"Logged in as: {username.capitalize()} ({role.title()})",
                foreground="#6c757d")
    user_label.setAlignment(QtCore.Qt.AlignLeft)
    info_layout.addWidget(user_label)

    company_header_layout.addWidget(info_frame, stretch=1)
    header_layout.addWidget(company_header, alignment=QtCore.Qt.AlignLeft)

    # Quick actions bar
    quick_actions = get_quick_actions()
    if quick_actions:
        actions_frame = QtWidgets.QWidget()
        actions_layout = QtWidgets.QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(0, 15, 0, 0)

        actions_label = styled_label(actions_frame, text="\u26a1 Quick Actions:", font=FONT_BOLD)
        actions_layout.addWidget(actions_label)

        action_buttons = {
            'create_lease': ("\u2795 New Lease", lambda: switch_tab_callback("Leases") if switch_tab_callback else None),
            'record_payment': ("\U0001f4b0 Record Payment", lambda: switch_tab_callback("Leases") if switch_tab_callback else None),
            'scan_barcode': ("\U0001f4f7 Scan Barcode", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'view_due': ("\U0001f4cb View Due", lambda: switch_tab_callback("Leases") if switch_tab_callback else None),
            'add_product': ("\U0001f4e6 Add Product", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'record_sale': ("\U0001f4b0 Record Sale", lambda: switch_tab_callback("Sales") if switch_tab_callback else None),
            'view_low_stock': ("\u26a0\ufe0f Low Stock", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'view_expiry': ("\u23f0 Expiry Alert", lambda: switch_tab_callback("Alerts") if switch_tab_callback else None),
            'check_stock': ("\U0001f4ca Check Stock", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'create_po': ("\U0001f4cb Create PO", lambda: switch_tab_callback("Purchase Orders") if switch_tab_callback else None),
            'create_sales_order': ("\U0001f4bc Create Order", lambda: switch_tab_callback("Sales Orders") if switch_tab_callback else None),
            'view_inventory': ("\U0001f4e6 Inventory", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'check_orders': ("\U0001f4cb Orders", lambda: switch_tab_callback("Sales Orders") if switch_tab_callback else None),
        }

        for action in quick_actions[:4]:  # Show max 4 quick actions
            if action in action_buttons:
                label, command = action_buttons[action]
                btn = make_button(actions_frame, label, command=command, kind="secondary")
                actions_layout.addWidget(btn)

        header_layout.addWidget(actions_frame, alignment=QtCore.Qt.AlignLeft)

    main_layout.addWidget(header_frame)
    main_layout.addSpacing(20)

    # Get dashboard widgets for this company type
    widgets = get_dashboard_widgets()

    # KPI Cards Row
    kpi_frame = QtWidgets.QWidget()
    kpi_layout = QtWidgets.QGridLayout(kpi_frame)
    kpi_layout.setContentsMargins(0, 0, 0, 0)

    # Create KPI cards based on company type
    kpi_data = get_kpi_data(company_type)

    kpi_labels = {}
    for i, kpi_key in enumerate(widgets[:4]):
        if kpi_key in kpi_data:
            kpi = kpi_data[kpi_key]
            card = make_card(kpi_frame, padding=20)
            card_layout = QtWidgets.QVBoxLayout(card)

            # Icon and title
            title_frame = QtWidgets.QWidget()
            title_layout = QtWidgets.QHBoxLayout(title_frame)
            title_layout.setContentsMargins(0, 0, 0, 0)

            icon_label = styled_label(title_frame, text=kpi['icon'], font=("Segoe UI", 24))
            title_layout.addWidget(icon_label)
            title_layout.addWidget(styled_label(title_frame, text=kpi['title'], font=FONT_BOLD))
            title_layout.addStretch()

            card_layout.addWidget(title_frame)

            # Value
            value_label = styled_label(card, text=str(kpi['value']),
                                      font=("Segoe UI", 28, "bold"),
                                      foreground=kpi.get('color', COLOR_PRIMARY))
            value_label.setAlignment(QtCore.Qt.AlignLeft)
            card_layout.addWidget(value_label)
            card_layout.addSpacing(10)

            # Change indicator
            if 'change' in kpi:
                change_color = COLOR_SUCCESS if kpi['change'] >= 0 else COLOR_DANGER
                change_icon = "\u2191" if kpi['change'] >= 0 else "\u2193"
                change_label = styled_label(card, text=f"{change_icon} {abs(kpi['change'])}%",
                            font=("Segoe UI", 10), foreground=change_color)
                change_label.setAlignment(QtCore.Qt.AlignLeft)
                card_layout.addWidget(change_label)

            kpi_layout.addWidget(card, 0, i)
            kpi_labels[kpi_key] = value_label

    main_layout.addWidget(kpi_frame)
    main_layout.addSpacing(20)

    # Main content area with charts and lists
    content_frame = QtWidgets.QWidget()
    content_layout = QtWidgets.QHBoxLayout(content_frame)
    content_layout.setContentsMargins(0, 0, 0, 0)

    # Left column - Charts
    left_col = QtWidgets.QWidget()
    left_layout = QtWidgets.QVBoxLayout(left_col)
    left_layout.setContentsMargins(0, 0, 0, 0)

    # Revenue/Performance chart placeholder
    chart_card = make_card(left_col, padding=20)
    chart_layout = QtWidgets.QVBoxLayout(chart_card)

    styled_label(chart_card, text="\U0001f4c8 Performance Overview", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    chart_layout.addSpacing(10)

    # Chart placeholder
    chart_placeholder = QtWidgets.QLabel("[Chart Area - Integrates with matplotlib]")
    chart_placeholder.setStyleSheet("color: #6c757d;")
    chart_placeholder.setAlignment(QtCore.Qt.AlignCenter)
    chart_layout.addWidget(chart_placeholder, stretch=1)

    left_layout.addWidget(chart_card, stretch=1)

    content_layout.addWidget(left_col, stretch=1)

    # Right column - Alerts and Activity
    right_col = QtWidgets.QWidget()
    right_layout = QtWidgets.QVBoxLayout(right_col)
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_col.setFixedWidth(300)

    # Alerts card
    alerts_card = make_card(right_col, padding=20)
    alerts_layout = QtWidgets.QVBoxLayout(alerts_card)

    styled_label(alerts_card, text="\U0001f514 Recent Alerts", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    alerts_layout.addSpacing(10)

    alerts_list = get_recent_alerts()
    if alerts_list:
        for alert in alerts_list[:5]:
            alert_frame = QtWidgets.QWidget()
            alert_layout = QtWidgets.QHBoxLayout(alert_frame)
            alert_layout.setContentsMargins(0, 0, 0, 0)

            icon = "\u26a0\ufe0f" if alert['severity'] == 'high' else "\u2139\ufe0f"
            alert_label = styled_label(alert_frame, text=f"{icon} {alert['message']}",
                        font=("Segoe UI", 9))
            alert_label.setAlignment(QtCore.Qt.AlignLeft)
            alert_layout.addWidget(alert_label)
            alerts_layout.addWidget(alert_frame)
    else:
        check_label = styled_label(alerts_card, text="\u2713 No new alerts",
                    foreground=COLOR_SUCCESS)
        check_label.setAlignment(QtCore.Qt.AlignLeft)
        alerts_layout.addWidget(check_label)

    right_layout.addWidget(alerts_card)

    # Activity feed
    activity_card = make_card(right_col, padding=20)
    activity_layout = QtWidgets.QVBoxLayout(activity_card)

    styled_label(activity_card, text="\U0001f4dd Recent Activity", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    activity_layout.addSpacing(10)

    activity_list = get_recent_activity()
    if activity_list:
        for activity in activity_list[:5]:
            activity_label = styled_label(activity_card, text=f"\u2022 {activity}",
                        font=("Segoe UI", 9))
            activity_label.setAlignment(QtCore.Qt.AlignLeft)
            activity_layout.addWidget(activity_label)
    else:
        no_activity_label = styled_label(activity_card, text="No recent activity",
                    foreground="#6c757d")
        no_activity_label.setAlignment(QtCore.Qt.AlignLeft)
        activity_layout.addWidget(no_activity_label)

    right_layout.addWidget(activity_card, stretch=1)

    content_layout.addWidget(right_col)

    main_layout.addWidget(content_frame, stretch=1)

    # Store KPI labels for updates
    dashboard_frame.kpi_labels = kpi_labels
    dashboard_frame.refresh = lambda: refresh_dashboard(dashboard_frame, company_type)

    return dashboard_frame


def get_kpi_data(company_type=None):
    """Get KPI data based on company type."""
    with get_db_cursor() as cur:
        kpi_data = {}

        # Items Leased (for lease businesses)
        try:
            cur.execute("SELECT COUNT(*) as count FROM leases WHERE status = 'active'")
            row = cur.fetchone()
            kpi_data['items_leased'] = {
                'icon': '\U0001f3af',
                'title': 'Active Leases',
                'value': row['count'] if row else 0,
                'color': COLOR_PRIMARY,
                'change': 12
            }
        except Exception as e:
            logging.debug(f"Failed to get items_leased KPI: {e}")

        # Due Collections
        try:
            cur.execute("""
                SELECT COUNT(*) as count FROM leases
                WHERE status = 'active'
                AND last_payment_date < date('now', '-7 days')
            """)
            row = cur.fetchone()
            kpi_data['due_collections'] = {
                'icon': '\U0001f4b0',
                'title': 'Due Collections',
                'value': row['count'] if row else 0,
                'color': COLOR_DANGER,
                'change': -5
            }
        except Exception as e:
            logging.debug(f"Failed to get due_collections KPI: {e}")

        # Monthly Revenue
        try:
            cur.execute("""
                SELECT SUM(amount_paid) as total FROM lease_payments
                WHERE payment_date >= date('now', '-30 days')
            """)
            row = cur.fetchone()
            revenue = row['total'] if row and row['total'] else 0
            kpi_data['revenue'] = {
                'icon': '\U0001f4ca',
                'title': 'Monthly Revenue',
                'value': f'Rs. {revenue:,.0f}',
                'color': COLOR_SUCCESS,
                'change': 18
            }
        except Exception as e:
            logging.debug(f"Failed to get revenue KPI: {e}")

        # Collection Rate
        try:
            cur.execute("""
                SELECT
                    (SELECT SUM(amount_paid) FROM lease_payments
                     WHERE payment_date >= date('now', '-30 days')) as collected,
                    (SELECT SUM(monthly_amount) FROM leases WHERE status = 'active') as expected
            """)
            row = cur.fetchone()
            if row and row['expected'] and row['expected'] > 0:
                rate = (row['collected'] or 0) / row['expected'] * 100
            else:
                rate = 0
            kpi_data['collection_rate'] = {
                'icon': '\u2713',
                'title': 'Collection Rate',
                'value': f'{rate:.1f}%',
                'color': COLOR_PRIMARY if rate >= 80 else COLOR_WARNING,
                'change': 5
            }
        except Exception as e:
            logging.debug(f"Failed to get collection_rate KPI: {e}")

        # Low Stock (for retail)
        try:
            cur.execute("""
                SELECT COUNT(*) as count FROM products
                WHERE stock <= reorder_point AND status = 'active'
            """)
            row = cur.fetchone()
            kpi_data['low_stock'] = {
                'icon': '\u26a0\ufe0f',
                'title': 'Low Stock Items',
                'value': row['count'] if row else 0,
                'color': COLOR_WARNING,
                'change': -10
            }
        except Exception as e:
            logging.debug(f"Failed to get low_stock KPI: {e}")

        # Today's Sales
        try:
            cur.execute("""
                SELECT COUNT(*) as count, SUM(total) as total
                FROM sales WHERE date = date('now')
            """)
            row = cur.fetchone()
            kpi_data['today_sales'] = {
                'icon': '\U0001f4b0',
                'title': "Today's Sales",
                'value': f"{row['count']} ({row['total']:,.0f})" if row and row['count'] else '0',
                'color': COLOR_SUCCESS,
                'change': 25
            }
        except Exception as e:
            logging.debug(f"Failed to get today_sales KPI: {e}")

        # Top Products
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT model) as count FROM sales
                WHERE date >= date('now', '-7 days')
            """)
            row = cur.fetchone()
            kpi_data['top_products'] = {
                'icon': '\U0001f3c6',
                'title': 'Active Products',
                'value': row['count'] if row else 0,
                'color': COLOR_PRIMARY,
                'change': 8
            }
        except Exception as e:
            logging.debug(f"Failed to get top_products KPI: {e}")

        return kpi_data


def get_recent_alerts(limit=5):
    """Get recent alerts."""
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT alert_type, severity, message, created_at
                FROM alerts
                WHERE is_read = 0
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            return [{
                'type': row['alert_type'],
                'severity': row['severity'],
                'message': row['message'],
                'date': row['created_at']
            } for row in cur.fetchall()]
    except Exception as e:
        logging.debug(f"Failed to get recent alerts: {e}")
        return []


def get_recent_activity(limit=5):
    """Get recent activity from audit log."""
    try:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT action, target, timestamp
                FROM audit_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [f"{row['action']} - {row['target'] or 'System'}" for row in cur.fetchall()]
    except Exception as e:
        logging.debug(f"Failed to get recent activity: {e}")
        return []


def refresh_dashboard(dashboard_frame, company_type=None):
    """Refresh dashboard KPIs."""
    kpi_data = get_kpi_data(company_type)

    if hasattr(dashboard_frame, 'kpi_labels'):
        for kpi_key, label in dashboard_frame.kpi_labels.items():
            if kpi_key in kpi_data:
                label.setText(str(kpi_data[kpi_key]['value']))
                label.setStyleSheet(f"color: {kpi_data[kpi_key].get('color', COLOR_PRIMARY)};")
