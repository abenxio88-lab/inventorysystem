"""
Premium Dashboard UI with Interactive Charts, AI Insights, and Glassmorphism
"""
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
from datetime import datetime, timedelta
import logging

# Project imports
from services import svc
from ui_theme import (
    toggle_theme, get_color, make_button, make_card, styled_label, styled_entry,
    frame, label, entry, combobox, treeview,
    COLOR_PRIMARY, COLOR_BORDER, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_APP_BG, COLOR_INFO,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_CARD_BG,
    BTN_WIDTH, FONT_BOLD, FONT_HEADING, FONT_REGULAR, SUBHEADING_FONT, FONT_SMALL,
    get_palette, create_divider, make_glass_card, create_badge, create_status_badge
)
from migration_add_industry_type import get_industry_type, get_industry_metadata
from industry_selector import create_industry_selector_card
from users_ui import open_user_manager
from audit_ui import open_audit_viewer
from setup_licensing_ui import open_owner_dashboard
from utils import load_settings, save_settings, get_data_dir, load_json_file


def create_dashboard_tab(parent, username, role, switch_tab_callback=None):
    """
    Creates the premium dashboard tab with glassmorphism cards and industry-specific context.
    """
    dashboard_frame = ttk.Frame(parent, padding=30)

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
    header_frame = ttk.Frame(dashboard_frame)
    header_frame.pack(fill='x', pady=(0, 30))

    # Left side: Welcome & Role
    user_info_frame = ttk.Frame(header_frame)
    user_info_frame.pack(side="left", fill="x", expand=True)

    welcome_label = styled_label(user_info_frame, f"Welcome back, {username.capitalize()}", font=FONT_HEADING, foreground=COLOR_PRIMARY)
    welcome_label.pack(anchor="w")

    role_info_frame = ttk.Frame(user_info_frame)
    role_info_frame.pack(anchor="w", pady=(5, 0))

    styled_label(role_info_frame, f"Role: {role.upper()}", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack(side="left")

    # Right side: Current Industry Badge (from config)
    badge_container = ttk.Frame(header_frame)
    badge_container.pack(side="right", anchor="n", padx=(10, 0))

    industry_badge = create_status_badge(
        badge_container,
        text=config.industry_name.upper(),
        icon=config.icon,
        color=config.color
    )
    industry_badge.pack()

    create_divider(dashboard_frame, orientation="horizontal", color=COLOR_BORDER, thickness=1).pack(fill='x', pady=(0, 30))

    # --- PREMIUM STATS CARDS (config-driven) ---
    stats_canvas_frame = ttk.Frame(dashboard_frame)
    stats_canvas_frame.pack(fill='x', pady=(0, 40))

    label_refs = {}

    # Build KPI cards from industry config
    # Each industry can define its own KPI structure
    if industry_id == "electronics":
        # Electronics KPIs
        card_configs = [
            {"id": "products", "title": "📦 Products", "value": "...", "color": COLOR_PRIMARY, "icon": "📦", "tab": "Inventory"},
            {"id": "stock", "title": "📊 Total Stock", "value": "...", "color": COLOR_INFO, "icon": "📊", "tab": "Inventory"},
            {"id": "warranty", "title": "⚠️ Expiring Warranty", "value": "...", "color": COLOR_DANGER, "icon": "🔧", "tab": "Warranty"},
            {"id": "sales", "title": "💰 Sales", "value": "...", "color": "#10B981", "icon": "💸", "tab": "Sales"},
        ]
    elif industry_id == "pharma":
        # Pharma KPIs
        card_configs = [
            {"id": "products", "title": "📦 Products", "value": "...", "color": COLOR_PRIMARY, "icon": "📦", "tab": "Inventory"},
            {"id": "expired", "title": "❌ Expired", "value": "...", "color": COLOR_DANGER, "icon": "💀", "tab": "Expiry Alerts"},
            {"id": "expiring", "title": "⚠️ Expiring Soon", "value": "...", "color": COLOR_WARNING, "icon": "⏰", "tab": "Expiry Alerts"},
            {"id": "sales", "title": "💰 Sales", "value": "...", "color": "#10B981", "icon": "💸", "tab": "Sales"},
        ]
    else:
        # Retail/Default KPIs
        card_configs = [
            {"id": "products", "title": "📦 Products", "value": "...", "color": COLOR_PRIMARY, "icon": "📦", "tab": "Inventory"},
            {"id": "stock", "title": "📊 Total Stock", "value": "...", "color": COLOR_INFO, "icon": "📊", "tab": "Inventory"},
            {"id": "low_stock", "title": "⚠️ Low Stock", "value": "...", "color": COLOR_SUCCESS, "icon": "⚠️", "tab": "Inventory"},
            {"id": "sales", "title": "💰 Sales", "value": "...", "color": "#10B981", "icon": "💸", "tab": "Sales"},
        ]

    # Create stats cards with responsive layout
    for idx, config in enumerate(card_configs):
        card_container = ttk.Frame(stats_canvas_frame)
        card_container.pack(side="left", expand=True, fill="both", padx=(0, 15))

        card = make_card(card_container, padx=25, pady=25)
        card.pack(fill="both", expand=True)

        icon_label = styled_label(card, config["icon"], font=("Segoe UI", 32))
        icon_label.pack(pady=(0, 10))

        styled_label(card, config["title"].split(" ", 1)[-1], font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack()

        value_label = styled_label(card, config["value"], font=FONT_HEADING, foreground=config["color"])
        value_label.pack(pady=(5, 0))
        label_refs[config["id"]] = value_label

        if switch_tab_callback:
            def make_nav(target): return lambda e: switch_tab_callback(target)
            card.bind("<Button-1>", make_nav(config["tab"]))
            for w in card.winfo_children(): w.bind("<Button-1>", make_nav(config["tab"]))

    def refresh_dashboard_kpis(*args):
        """Dynamic KPI refresh - reads from industry-specific service."""
        try:
            products = svc.inventory.get_all_products(active_only=True)
            orders = svc.sales.get_all_orders()
            total_items = sum(int(p.get('stock', 0)) for p in products)
            low_stock = len([p for p in products if int(p.get('stock', 0)) <= p.get('reorder_point', 5)])
            total_sales = len(orders)

            # Update base KPIs (all industries)
            if "products" in label_refs: label_refs["products"].config(text=str(len(products)))
            if "stock" in label_refs: label_refs["stock"].config(text=str(total_items))
            if "low_stock" in label_refs:
                label_refs["low_stock"].config(text=str(low_stock), foreground=COLOR_DANGER if low_stock > 0 else COLOR_SUCCESS)
            if "sales" in label_refs: label_refs["sales"].config(text=str(total_sales))

            # Industry-specific KPIs
            if industry_id == "electronics":
                # Warranty exping
                expiring_warranty = len([p for p in products if p.get('warranty_expiry')])
                if "warranty" in label_refs:
                    label_refs["warranty"].config(text=str(expiring_warranty))
                    
            elif industry_id == "pharma":
                # Expired products
                expired = len([p for p in products if p.get('expiry_date') and p.get('expiry_date') < datetime.now().strftime('%Y-%m-%d')])
                if "expired" in label_refs:
                    label_refs["expired"].config(text=str(expired), foreground=COLOR_DANGER)
                
                # Expiring soon (30 days)
                from datetime import timedelta
                thirty_days = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                expiring = len([p for p in products if p.get('expiry_date') and p.get('expiry_date') < thirty_days and p.get('expiry_date') >= datetime.now().strftime('%Y-%m-%d')])
                if "expiring" in label_refs:
                    label_refs["expiring"].config(text=str(expiring), foreground=COLOR_WARNING)
                    
        except Exception as e:
            logging.error(f"Failed to refresh dashboard stats: {e}")
            # Set fallback values
            for key, lbl in label_refs.items():
                try:
                    lbl.config(text="Error", foreground=COLOR_DANGER)
                except Exception:
                    logging.debug(f"Failed to update label {key}")

    # Register for real-time updates and fetch initial
    from app_core import app_state
    app_state.register_ui_callback("db_changed", refresh_dashboard_kpis)
    
    # Initial fetch
    refresh_dashboard_kpis()
    
    # Set up a secondary periodic refresh as backup (every 60 seconds)
    # This ensures KPIs stay fresh even if db_changed notifications are missed
    def periodic_refresh():
        if dashboard_frame.winfo_exists():
            refresh_dashboard_kpis()
            dashboard_frame.after(60000, periodic_refresh)  # Refresh every 60 seconds
    
    periodic_refresh()

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
                messagebox.showinfo("Mode Switched",
                    f"System operating mode changed to: {config['name']}\n"
                    f"All tabs and forms have been updated.")
            except Exception as e:
                logging.error(f"Industry change confirmation error: {e}", exc_info=True)
                messagebox.showwarning("Update",
                    "Industry may have changed. Please verify in the tabs shown.")

        industry_section = create_industry_selector_card(dashboard_frame, on_industry_changed=on_industry_changed)
        industry_section.pack(fill='x', pady=(0, 30))

    # --- Business Configuration Card ---
    try:
        from business_settings import create_business_card
        business_card = create_business_card(
            dashboard_frame, dashboard_frame, switch_tab_callback
        )
        business_card.pack(fill='x', pady=(0, 30))
    except ImportError:
        logging.debug("Business settings card not available")

    # --- Quick Actions Section ---
    actions_frame = make_card(dashboard_frame, padx=25, pady=20)
    actions_frame.pack(fill='x', pady=(0, 30))

    styled_label(actions_frame, "⚡ Quick Actions", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=(0, 15))

    quick_actions = ttk.Frame(actions_frame)
    quick_actions.pack(fill='x')

    action_buttons = [
        ("📦 Add Product", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
        ("💰 New Sale", lambda: switch_tab_callback("Sales") if switch_tab_callback else None),
        ("📊 Reports", lambda: switch_tab_callback("Reports") if switch_tab_callback else None),
    ]

    for i, (text, cmd) in enumerate(action_buttons):
        btn = make_button(quick_actions, text=text, command=cmd, kind="secondary" if i > 0 else "primary")
        btn.pack(side="left", padx=(0, 15))

    # --- System & Owner Information Card ---
    info_frame = make_card(dashboard_frame, padx=25, pady=20)
    info_frame.pack(fill='x', pady=(0, 20))

    styled_label(info_frame, "📌 System Overview", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=(0, 15))

    # Two-column layout for info
    info_cols = ttk.Frame(info_frame)
    info_cols.pack(fill='x')
    
    left_col = ttk.Frame(info_cols)
    left_col.pack(side="left", fill="x", expand=True)
    
    right_col = ttk.Frame(info_cols)
    right_col.pack(side="left", fill="x", expand=True)

    settings = load_settings()
    company_name = settings.get("company_name", "Mintaka Sphere Inventory System")
    support_email = settings.get("support_email", "support@mintakasphere.com")
    currency = settings.get("currency", "PKR")
    tax_rate = settings.get("tax_rate", "0")

    # Left column - System Info
    styled_label(left_col, f"🏢 Company: {company_name}", font=FONT_SMALL, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=2)
    styled_label(left_col, f"📧 Support: {support_email}", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack(anchor='w', pady=2)
    styled_label(left_col, f"💰 Currency: {currency} | Tax: {float(tax_rate):.1f}%", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack(anchor='w', pady=2)

    # Right column - Industry & User Info
    styled_label(right_col, f"🏭 Industry: {config.industry_name} {config.icon}", font=FONT_SMALL, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=2)
    styled_label(right_col, f"👤 User: {username.capitalize()} | Role: {role.upper()}", font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack(anchor='w', pady=2)
    styled_label(right_col, f"💾 Software: Mintaka Sphere IMS v1.0.0 | Status: Active", font=FONT_SMALL, foreground=COLOR_SUCCESS).pack(anchor='w', pady=2)
    
    # --- Administrative Panel (Admins Only) ---
    if role in ["admin", "OWNER_ADMIN"]:
        admin_card = make_card(dashboard_frame, padx=25, pady=20)
        admin_card.pack(fill='x', pady=(0, 20))
        
        styled_label(admin_card, "🛠️ Administrative Controls", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=(0, 15))
        
        admin_controls = ttk.Frame(admin_card)
        admin_controls.pack(fill='x')
        
        # User Management
        if open_user_manager:
            make_button(admin_controls, "👥 Manage Users", 
                       command=lambda: open_user_manager(dashboard_frame, current_user=username), 
                       kind="secondary").pack(side="left", padx=(0, 15))
            
        # Audit Log
        if open_audit_viewer:
            make_button(admin_controls, "🔍 Audit Logs", 
                       command=lambda: open_audit_viewer(dashboard_frame, current_user=username), 
                       kind="secondary").pack(side="left", padx=(0, 15))
            
        # Owner Specific Tools
        if role == "OWNER_ADMIN" and open_owner_dashboard:
            make_button(admin_controls, "👑 Owner Dashboard", 
                       command=lambda: open_owner_dashboard(dashboard_frame), 
                       kind="primary").pack(side="left", padx=(0, 15))
            
        # Quick Settings
        def open_settings():
            s = load_settings()
            hour = simpledialog.askinteger("Backup Hour", "Hour (0-23):", initialvalue=s.get("backup_hour", 2))
            if hour is not None:
                save_settings({"backup_hour": hour})
                messagebox.showinfo("Settings", "Backup settings saved.")

        make_button(admin_controls, "⚙️ Settings", command=open_settings, kind="secondary").pack(side="left")

        # System Health Check
        try:
            from auto_issue_finder import check_and_show_issues
            make_button(admin_controls, "🩺 Health Check",
                       command=lambda: check_and_show_issues(dashboard_frame),
                       kind="secondary").pack(side="left", padx=(0, 15))
        except ImportError:
            pass

        # Developer Dashboard
        try:
            from dev_dashboard import open_dev_dashboard
            make_button(admin_controls, "🛠️ Dev Tools",
                       command=lambda: open_dev_dashboard(dashboard_frame),
                       kind="secondary").pack(side="left", padx=(0, 15))
        except ImportError:
            pass

        # Error Dashboard
        try:
            from error_dashboard_widget import open_error_dashboard
            make_button(admin_controls, "🚨 Error Dashboard",
                       command=lambda: open_error_dashboard(dashboard_frame),
                       kind="secondary").pack(side="left", padx=(0, 15))
        except ImportError:
            pass

    return dashboard_frame
