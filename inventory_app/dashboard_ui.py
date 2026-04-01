import tkinter as tk
from tkinter import ttk

try:
    from .ui_theme import (
        make_card, styled_label, FONT_HEADING, COLOR_TEXT_MUTED,
        FONT_BOLD, COLOR_PRIMARY, COLOR_TEXT_MAIN, COLOR_BORDER,
        SUBHEADING_FONT, FONT_SMALL, create_divider, make_button,
        COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_INFO,
        SPACING_DEFAULT, SPACING_LARGE
    )
except (ImportError, ModuleNotFoundError):
    from ui_theme import (
        make_card, styled_label, FONT_HEADING, COLOR_TEXT_MUTED,
        FONT_BOLD, COLOR_PRIMARY, COLOR_TEXT_MAIN, COLOR_BORDER,
        SUBHEADING_FONT, FONT_SMALL, create_divider, make_button,
        COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_INFO,
        SPACING_DEFAULT, SPACING_LARGE
    )

try:
    from .utils import load_settings, save_settings
except (ImportError, ModuleNotFoundError):
    try:
        from utils import load_settings, save_settings
    except Exception:
        load_settings = lambda: {"backup_hour": 2, "backup_minute": 0, "backup_retention": 30}
        save_settings = lambda s: s

    try:
        from users_ui import open_user_manager
    except Exception:
        open_user_manager = None

try:
    from .inventory_ui import load_inventory
except (ImportError, ModuleNotFoundError):
    try: from inventory_ui import load_inventory
    except: load_inventory = lambda: []

try:
    from .sales_ui import load_sales
except (ImportError, ModuleNotFoundError):
    try: from sales_ui import load_sales
    except: load_sales = lambda: []

from tkinter import simpledialog, messagebox

def create_dashboard_tab(parent, username, role, switch_tab_callback=None):
    """
    Creates the premium dashboard tab with glassmorphism cards and interlinked navigation.
    """
    dashboard_frame = ttk.Frame(parent, padding=30)

    # --- Premium Header ---
    header_frame = ttk.Frame(dashboard_frame)
    header_frame.pack(fill='x', pady=(0, 30))
    
    welcome_label = styled_label(header_frame, f"Welcome back, {username.capitalize()}", font=FONT_HEADING, foreground=COLOR_PRIMARY)
    welcome_label.pack(anchor="w")
    
    role_badge = create_divider(header_frame, orientation="horizontal", color=COLOR_BORDER, thickness=1)
    role_badge.pack(fill='x', pady=(10, 15))
    
    styled_label(header_frame, f"Role: {role.upper()}", font=FONT_BOLD, foreground=COLOR_TEXT_MUTED).pack(anchor="w")
    
    # --- PREMIUM STATS CARDS WITH GLASSMORPHISM ---
    stats_frame = ttk.Frame(dashboard_frame)
    stats_frame.pack(fill='x', pady=(20, 40))
    
    inventory = load_inventory()
    total_items = sum(int(item.get('stock', 0)) for item in inventory)
    low_stock = len([item for item in inventory if int(item.get('stock', 0)) <= 5])
    
    # Card data with icons and colors
    card_configs = [
        {
            "title": "📦 Products",
            "value": str(len(inventory)),
            "color": COLOR_PRIMARY,
            "icon": "📦"
        },
        {
            "title": "📊 Total Items",
            "value": str(total_items),
            "color": COLOR_INFO,
            "icon": "📊"
        },
        {
            "title": "⚠️ Low Stock",
            "value": str(low_stock),
            "color": COLOR_DANGER if low_stock > 0 else COLOR_SUCCESS,
            "icon": "⚠️"
        }
    ]
    
    # Create stat cards dynamically
    for config in card_configs:
        card_container = ttk.Frame(stats_frame)
        card_container.pack(side="left", expand=True, fill="both", padx=(0, 15))
        
        # Glass card with premium styling
        card = make_card(card_container, padx=25, pady=25)
        card.pack(fill="both", expand=True)
        
        # Card icon
        icon_label = styled_label(card, config["icon"], font=("Segoe UI", 32))
        icon_label.pack(pady=(0, 10))
        
        # Card title
        styled_label(card, config["title"].split(" ", 1)[-1] if " " in config["title"] else config["title"], 
                    font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack()
        
        # Card value with color
        value_label = styled_label(card, config["value"], font=FONT_HEADING, foreground=config["color"])
        value_label.pack(pady=(5, 0))
        
        # Make entire card clickable for navigation
        if switch_tab_callback:
            def navigate(e, title=config["title"]):
                if "Product" in title or "Items" in title or "Stock" in title:
                    switch_tab_callback("Inventory")
            
            card.bind("<Button-1>", navigate)
            for widget in card.winfo_children():
                widget.bind("<Button-1>", navigate)
                # Add hover effect
                widget.bind("<Enter>", lambda e, c=card: c.configure(bg="#F8FAFC"))
                widget.bind("<Leave>", lambda e, c=card: c.configure(bg=COLOR_CARD_BG))
    
    # --- Quick Actions Section ---
    actions_frame = make_card(dashboard_frame, padx=25, pady=20)
    actions_frame.pack(fill='x', pady=(0, 30))
    
    styled_label(actions_frame, "⚡ Quick Actions", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=(0, 15))
    
    quick_actions = ttk.Frame(actions_frame)
    quick_actions.pack(fill='x')
    
    action_buttons = [
        ("➕ Add Product", lambda: switch_tab_callback("Inventory") if switch_tab_callback else None),
        ("💰 New Sale", lambda: switch_tab_callback("Sales") if switch_tab_callback else None),
        ("📋 View Reports", lambda: switch_tab_callback("Reports") if switch_tab_callback else None),
    ]
    
    for i, (text, cmd) in enumerate(action_buttons):
        btn = make_button(quick_actions, text=text, command=cmd, kind="secondary" if i > 0 else "primary")
        btn.pack(side="left", padx=(0, 10) if i < len(action_buttons) - 1 else (0, 0))
    
    # --- System Overview Card ---
    info_frame = make_card(dashboard_frame, padx=25, pady=20)
    info_frame.pack(fill='x', pady=(0, 20))
    
    styled_label(info_frame, "📌 System Overview", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MAIN).pack(anchor='w', pady=(0, 15))
    
    overview_text = """
    Navigate through the system using the tabs above or quick actions:
    • 📦 Inventory: Manage products, stock levels, and categories
    • 💰 Sales: Process transactions and view sales history  
    • 📊 Reports: Analyze profitability and generate insights
    
    💡 Tip: Click on any stat card to quickly navigate to that section.
    """
    styled_label(info_frame, overview_text.strip(), justify="left", foreground=COLOR_TEXT_MUTED).pack(anchor='w')
    
    # Contact information
    contact_divider = create_divider(info_frame, orientation="horizontal", color=COLOR_BORDER, thickness=1)
    contact_divider.pack(fill='x', pady=(15, 15))
    
    styled_label(info_frame, "📧 Support: usmansaeed.1988@gmail.com | 📱 +92-344-4560738", 
                font=FONT_SMALL, foreground=COLOR_TEXT_MUTED).pack(anchor='w')
    
    # Admin controls
    if role in ["admin", "OWNER_ADMIN"]:
        ctrl_frame = ttk.Frame(dashboard_frame)
        ctrl_frame.pack(fill="x", pady=(20, 0))

        def open_settings():
            s = load_settings()
            hour = simpledialog.askinteger("Backup Hour", "Hour of day for daily backup (0-23):", 
                                          initialvalue=s.get("backup_hour", 2), minvalue=0, maxvalue=23)
            if hour is None:
                return
            minute = simpledialog.askinteger("Backup Minute", "Minute of hour for daily backup (0-59):", 
                                            initialvalue=s.get("backup_minute", 0), minvalue=0, maxvalue=59)
            if minute is None:
                return
            retention = simpledialog.askinteger("Retention", "Number of backup folders to keep:", 
                                               initialvalue=s.get("backup_retention", 30), minvalue=1)
            if retention is None:
                return
            save_settings({"backup_hour": hour, "backup_minute": minute, "backup_retention": retention})
            messagebox.showinfo("Settings", "Backup settings saved. Scheduler will pick them up automatically.")

        if open_user_manager is not None:
            btn_manage = make_button(ctrl_frame, text="👥 Manage Users", 
                                    command=lambda: open_user_manager(dashboard_frame, current_user=username), 
                                    kind="secondary")
            btn_manage.pack(side="left", padx=(0, 10))

        try:
            from .audit_ui import open_audit_viewer
        except Exception:
            try:
                from audit_ui import open_audit_viewer
            except Exception:
                open_audit_viewer = None

        if open_audit_viewer is not None:
            btn_audit = make_button(ctrl_frame, text="🔍 Audit Log", 
                                   command=lambda: open_audit_viewer(dashboard_frame, current_user=username), 
                                   kind="secondary")
            btn_audit.pack(side="left", padx=(0, 10))

        btn_settings = make_button(ctrl_frame, text="⚙️ Backup Settings", 
                                  command=open_settings, kind="secondary")
        btn_settings.pack(side="left")
    
    return dashboard_frame

