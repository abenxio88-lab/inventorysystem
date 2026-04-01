import tkinter as tk
from tkinter import ttk

try:
    from .ui_theme import make_card, styled_label, FONT_HEADING, COLOR_TEXT_MUTED
except (ImportError, ModuleNotFoundError):
    from ui_theme import make_card, styled_label, FONT_HEADING, COLOR_TEXT_MUTED

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
    Creates the main dashboard tab with instructional information.
    """
    dashboard_frame = ttk.Frame(parent, padding=40)

    # --- Header ---
    header_frame = ttk.Frame(dashboard_frame)
    header_frame.pack(fill='x', pady=(0, 20))
    styled_label(header_frame, f"Welcome, {username.capitalize()}!", font=FONT_HEADING).pack(anchor="w")
    styled_label(header_frame, f"Enterprise Mode: {role.upper()}", foreground="#28a745", font=FONT_BOLD).pack(anchor="w")
    
    # --- ENTERPRISE STATS CARDS ---
    stats_frame = ttk.Frame(dashboard_frame)
    stats_frame.pack(fill='x', pady=(0, 30))
    
    inventory = load_inventory()
    total_items = sum(int(item.get('stock', 0)) for item in inventory)
    low_stock = len([item for item in inventory if int(item.get('stock', 0)) <= 5])
    
    # Product Card
    prod_card = make_card(stats_frame, padding=15)
    prod_card.pack(side="left", expand=True, fill="both", padx=(0, 10))
    styled_label(prod_card, "📦 Total Products", font=FONT_BOLD).pack()
    styled_label(prod_card, str(len(inventory)), font=FONT_HEADING, foreground="#007bff").pack()
    if switch_tab_callback:
        for w in [prod_card] + list(prod_card.winfo_children()):
            w.bind("<Button-1>", lambda e: switch_tab_callback("Inventory"))
    
    # Stock Card
    stock_card = make_card(stats_frame, padding=15)
    stock_card.pack(side="left", expand=True, fill="both", padx=(0, 10))
    styled_label(stock_card, "📈 Total Stock", font=FONT_BOLD).pack()
    styled_label(stock_card, str(total_items), font=FONT_HEADING, foreground="#28a745").pack()
    if switch_tab_callback:
        for w in [stock_card] + list(stock_card.winfo_children()):
            w.bind("<Button-1>", lambda e: switch_tab_callback("Inventory"))
    
    # Alert Card
    alert_card = make_card(stats_frame, padding=15)
    alert_card.pack(side="left", expand=True, fill="both")
    styled_label(alert_card, "⚠️ Low Stock", font=FONT_BOLD).pack()
    styled_label(alert_card, str(low_stock), font=FONT_HEADING, foreground="#dc3545").pack()
    if switch_tab_callback:
        for w in [alert_card] + list(alert_card.winfo_children()):
            w.bind("<Button-1>", lambda e: switch_tab_callback("Inventory"))
    
    # --- Instructional Text and Copyright ---
    info_frame = make_card(dashboard_frame, padding=20)
    info_frame.pack(fill='x', pady=(10, 40))
    styled_label(info_frame, "Application Information", font=FONT_HEADING).pack(anchor='w', pady=(0, 10))
    
    instruction_text = """
    This Inventory Management System is designed to help you efficiently track products, manage sales, and analyze profitability.
    
    • Manufactured by: Minataka Sphere
    • Owned By: Abenxio
    • Copyright © 2026 All Rights Reserved.
    
    Use the tabs at the top to navigate between different functionalities:
    • 'Inventory' tab: Manage product stock, add, update, and delete items.
    • 'Sales' tab: View and record new sales transactions.
    • 'Profitability' tab (Admins only): Access detailed financial reports and visualizations.
    """
    styled_label(info_frame, instruction_text, justify="left").pack(anchor='w')
    # Contact information line under copyright
    styled_label(info_frame, "Contact: usmansaeed.1988@gmail.com  Phone No. +92-344-4560738", foreground=COLOR_TEXT_MUTED).pack(anchor='w', pady=(10,0))
    # Admin controls: Settings and User Management
    if role in ["admin", "OWNER_ADMIN"]:
        ctrl_frame = ttk.Frame(dashboard_frame)
        ctrl_frame.pack(fill="x", pady=(10, 0))

        def open_settings():
            s = load_settings()
            hour = simpledialog.askinteger("Backup Hour", "Hour of day for daily backup (0-23):", initialvalue=s.get("backup_hour", 2), minvalue=0, maxvalue=23)
            if hour is None:
                return
            minute = simpledialog.askinteger("Backup Minute", "Minute of hour for daily backup (0-59):", initialvalue=s.get("backup_minute", 0), minvalue=0, maxvalue=59)
            if minute is None:
                return
            retention = simpledialog.askinteger("Retention", "Number of backup folders to keep:", initialvalue=s.get("backup_retention", 30), minvalue=1)
            if retention is None:
                return
            save_settings({"backup_hour": hour, "backup_minute": minute, "backup_retention": retention})
            messagebox.showinfo("Settings", "Backup settings saved. Scheduler will pick them up automatically.")

        if open_user_manager is not None:
            btn_manage = ttk.Button(ctrl_frame, text="Manage Users", command=lambda: open_user_manager(dashboard_frame, current_user=username))
            btn_manage.pack(side="left", padx=(0, 8))

        # Audit viewer (admin only)
        try:
            from .audit_ui import open_audit_viewer
        except Exception:
            try:
                from audit_ui import open_audit_viewer
            except Exception:
                open_audit_viewer = None

        if open_audit_viewer is not None:
            btn_audit = ttk.Button(ctrl_frame, text="View Audit", command=lambda: open_audit_viewer(dashboard_frame, current_user=username))
            btn_audit.pack(side="left", padx=(0, 8))

        btn_settings = ttk.Button(ctrl_frame, text="Backup Settings", command=open_settings)
        btn_settings.pack(side="left")
    
    return dashboard_frame

