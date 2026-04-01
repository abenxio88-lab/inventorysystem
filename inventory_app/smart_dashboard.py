"""
Smart Dashboard Module
=======================
Adaptive dashboard that changes based on company type.
Shows relevant KPIs, widgets, and quick actions for each business type.
"""

import tkinter as tk
from tkinter import ttk
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
    dashboard_frame = ttk.Frame(parent, padding=30)
    
    # Get company configuration
    config = get_company_config()
    company_name = config.get('name', 'Inventory System')
    company_icon = config.get('icon', '🏪')
    
    # Header with company info
    header_frame = ttk.Frame(dashboard_frame)
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Company name and icon
    company_header = ttk.Frame(header_frame)
    company_header.pack(anchor=tk.W)
    
    styled_label(company_header, text=company_icon, font=("Segoe UI", 32)).pack(side=tk.LEFT, padx=(0, 15))
    
    info_frame = ttk.Frame(company_header)
    info_frame.pack(side=tk.LEFT)
    
    styled_label(info_frame, text=f"Welcome to {company_name}", font=FONT_HEADING).pack(anchor=tk.W)
    styled_label(info_frame, text=f"Logged in as: {username.capitalize()} ({role.title()})", 
                foreground="#6c757d").pack(anchor=tk.W)
    
    # Quick actions bar
    quick_actions = get_quick_actions()
    if quick_actions:
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(anchor=tk.W, pady=(15, 0))
        
        styled_label(actions_frame, text="⚡ Quick Actions:", font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 10))
        
        action_buttons = {
            'create_lease': ("➕ New Lease", lambda: switch_tab_callback("Leases") if switch_tab_callback else None),
            'record_payment': ("💰 Record Payment", lambda: switch_tab_callback("Leases") if switch_tab_callback else None),
            'scan_barcode': ("📷 Scan Barcode", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'view_due': ("📋 View Due", lambda: switch_tab_callback("Leases") if switch_tab_callback else None),
            'add_product': ("📦 Add Product", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'record_sale': ("💰 Record Sale", lambda: switch_tab_callback("Sales") if switch_tab_callback else None),
            'view_low_stock': ("⚠️ Low Stock", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'view_expiry': ("⏰ Expiry Alert", lambda: switch_tab_callback("Alerts") if switch_tab_callback else None),
            'check_stock': ("📊 Check Stock", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'create_po': ("📋 Create PO", lambda: switch_tab_callback("Purchase Orders") if switch_tab_callback else None),
            'create_sales_order': ("💼 Create Order", lambda: switch_tab_callback("Sales Orders") if switch_tab_callback else None),
            'view_inventory': ("📦 Inventory", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
            'check_orders': ("📋 Orders", lambda: switch_tab_callback("Sales Orders") if switch_tab_callback else None),
        }
        
        for action in quick_actions[:4]:  # Show max 4 quick actions
            if action in action_buttons:
                label, command = action_buttons[action]
                make_button(actions_frame, label, command=command, kind="secondary").pack(side=tk.LEFT, padx=5)
    
    # Get dashboard widgets for this company type
    widgets = get_dashboard_widgets()
    
    # KPI Cards Row
    kpi_frame = ttk.Frame(dashboard_frame)
    kpi_frame.pack(fill=tk.X, pady=(0, 20))
    kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
    
    # Create KPI cards based on company type
    kpi_data = get_kpi_data(company_type)
    
    kpi_labels = {}
    for i, kpi_key in enumerate(widgets[:4]):
        if kpi_key in kpi_data:
            kpi = kpi_data[kpi_key]
            card = make_card(kpi_frame, padding=20)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            
            # Icon and title
            title_frame = ttk.Frame(card)
            title_frame.pack(fill=tk.X)
            
            styled_label(title_frame, text=kpi['icon'], font=("Segoe UI", 24)).pack(side=tk.LEFT, padx=(0, 10))
            styled_label(title_frame, text=kpi['title'], font=FONT_BOLD).pack(side=tk.LEFT)
            
            # Value
            value_label = styled_label(card, text=str(kpi['value']), 
                                      font=("Segoe UI", 28, "bold"), 
                                      foreground=kpi.get('color', COLOR_PRIMARY))
            value_label.pack(anchor=tk.W, pady=(10, 0))
            
            # Change indicator
            if 'change' in kpi:
                change_color = COLOR_SUCCESS if kpi['change'] >= 0 else COLOR_DANGER
                change_icon = "↑" if kpi['change'] >= 0 else "↓"
                styled_label(card, text=f"{change_icon} {abs(kpi['change'])}%", 
                            font=("Segoe UI", 10), foreground=change_color).pack(anchor=tk.W)
            
            kpi_labels[kpi_key] = value_label
    
    # Main content area with charts and lists
    content_frame = ttk.Frame(dashboard_frame)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    # Left column - Charts
    left_col = ttk.Frame(content_frame)
    left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    
    # Revenue/Performance chart placeholder
    chart_card = make_card(left_col, padding=20)
    chart_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    styled_label(chart_card, text="📈 Performance Overview", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 10))
    
    # Chart placeholder
    chart_placeholder = ttk.Frame(chart_card)
    chart_placeholder.pack(fill=tk.BOTH, expand=True)
    
    styled_label(chart_placeholder, text="[Chart Area - Integrates with matplotlib]", 
                foreground="#6c757d").pack(expand=True)
    
    # Right column - Alerts and Activity
    right_col = ttk.Frame(content_frame)
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))
    right_col.config(width=300)
    
    # Alerts card
    alerts_card = make_card(right_col, padding=20)
    alerts_card.pack(fill=tk.X, pady=(0, 10))
    
    styled_label(alerts_card, text="🔔 Recent Alerts", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 10))
    
    alerts_list = get_recent_alerts()
    if alerts_list:
        for alert in alerts_list[:5]:
            alert_frame = ttk.Frame(alerts_card)
            alert_frame.pack(fill=tk.X, pady=3)
            
            icon = "⚠️" if alert['severity'] == 'high' else "ℹ️"
            styled_label(alert_frame, text=f"{icon} {alert['message']}", 
                        font=("Segoe UI", 9)).pack(anchor=tk.W)
    else:
        styled_label(alerts_card, text="✓ No new alerts", 
                    foreground=COLOR_SUCCESS).pack(anchor=tk.W)
    
    # Activity feed
    activity_card = make_card(right_col, padding=20)
    activity_card.pack(fill=tk.BOTH, expand=True)
    
    styled_label(activity_card, text="📝 Recent Activity", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 10))
    
    activity_list = get_recent_activity()
    if activity_list:
        for activity in activity_list[:5]:
            activity_frame = ttk.Frame(activity_card)
            activity_frame.pack(fill=tk.X, pady=3)
            
            styled_label(activity_frame, text=f"• {activity}", 
                        font=("Segoe UI", 9)).pack(anchor=tk.W)
    else:
        styled_label(activity_card, text="No recent activity", 
                    foreground="#6c757d").pack(anchor=tk.W)
    
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
                'icon': '🎯',
                'title': 'Active Leases',
                'value': row['count'] if row else 0,
                'color': COLOR_PRIMARY,
                'change': 12
            }
        except:
            pass
        
        # Due Collections
        try:
            cur.execute("""
                SELECT COUNT(*) as count FROM leases 
                WHERE status = 'active' 
                AND last_payment_date < date('now', '-7 days')
            """)
            row = cur.fetchone()
            kpi_data['due_collections'] = {
                'icon': '💰',
                'title': 'Due Collections',
                'value': row['count'] if row else 0,
                'color': COLOR_DANGER,
                'change': -5
            }
        except:
            pass
        
        # Monthly Revenue
        try:
            cur.execute("""
                SELECT SUM(amount_paid) as total FROM lease_payments
                WHERE payment_date >= date('now', '-30 days')
            """)
            row = cur.fetchone()
            revenue = row['total'] if row and row['total'] else 0
            kpi_data['revenue'] = {
                'icon': '📊',
                'title': 'Monthly Revenue',
                'value': f'Rs. {revenue:,.0f}',
                'color': COLOR_SUCCESS,
                'change': 18
            }
        except:
            pass
        
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
                'icon': '✓',
                'title': 'Collection Rate',
                'value': f'{rate:.1f}%',
                'color': COLOR_PRIMARY if rate >= 80 else COLOR_WARNING,
                'change': 5
            }
        except:
            pass
        
        # Low Stock (for retail)
        try:
            cur.execute("""
                SELECT COUNT(*) as count FROM products 
                WHERE stock <= reorder_point AND status = 'active'
            """)
            row = cur.fetchone()
            kpi_data['low_stock'] = {
                'icon': '⚠️',
                'title': 'Low Stock Items',
                'value': row['count'] if row else 0,
                'color': COLOR_WARNING,
                'change': -10
            }
        except:
            pass
        
        # Today's Sales
        try:
            cur.execute("""
                SELECT COUNT(*) as count, SUM(total) as total 
                FROM sales WHERE date = date('now')
            """)
            row = cur.fetchone()
            kpi_data['today_sales'] = {
                'icon': '💰',
                'title': "Today's Sales",
                'value': f"{row['count']} ({row['total']:,.0f})" if row and row['count'] else '0',
                'color': COLOR_SUCCESS,
                'change': 25
            }
        except:
            pass
        
        # Top Products
        try:
            cur.execute("""
                SELECT COUNT(DISTINCT model) as count FROM sales
                WHERE date >= date('now', '-7 days')
            """)
            row = cur.fetchone()
            kpi_data['top_products'] = {
                'icon': '🏆',
                'title': 'Active Products',
                'value': row['count'] if row else 0,
                'color': COLOR_PRIMARY,
                'change': 8
            }
        except:
            pass
        
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
    except:
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
    except:
        return []


def refresh_dashboard(dashboard_frame, company_type=None):
    """Refresh dashboard KPIs."""
    kpi_data = get_kpi_data(company_type)
    
    if hasattr(dashboard_frame, 'kpi_labels'):
        for kpi_key, label in dashboard_frame.kpi_labels.items():
            if kpi_key in kpi_data:
                label.config(text=str(kpi_data[kpi_key]['value']),
                            foreground=kpi_data[kpi_key].get('color', COLOR_PRIMARY))
