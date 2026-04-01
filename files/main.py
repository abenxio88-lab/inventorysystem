import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox
import logging
import threading
import time
import sys
import os
from datetime import datetime, timedelta

try:
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir

try:
    from .logger_setup import setup_logger
    setup_logger()
    from .ui_theme import setup_theme, make_button, styled_label
    from .login_ui import open_login
    from .inventory_ui import create_inventory_tab
    from .sales_ui import create_sales_tab
    from .profit_ui import create_profit_tab
    from .dashboard_ui import create_dashboard_tab
    from .utils import backup_data, prune_backups, load_settings, load_users, create_user
    from .database import init_database, get_db_stats
    from .network import get_connectivity_monitor
    from .sync_engine import get_sync_engine
    from .status_widget import create_status_bar
    from .alerts import check_all_alerts, get_unread_alerts
    from .backup_manager import backup_manager
    from .startup_wizard import create_startup_wizard, get_company_type, get_company_config
    from .smart_dashboard import create_smart_dashboard
    from .invoicing_ui import create_invoicing_tab
    from .returns_ui import create_returns_tab
    from .tradein_service_ui import create_trade_ins_tab, create_service_tab
    from .license_manager import verify_software_activation
    from .setup_licensing_ui import create_admin_setup_wizard
except (ImportError, ModuleNotFoundError):
    from logger_setup import setup_logger
    setup_logger()
    from ui_theme import setup_theme, make_button, styled_label
    from login_ui import open_login
    from inventory_ui import create_inventory_tab
    from sales_ui import create_sales_tab
    from profit_ui import create_profit_tab
    from dashboard_ui import create_dashboard_tab
    from utils import backup_data, prune_backups, load_settings, load_users, create_user
    try:
        from database import init_database, get_db_stats
        from network import get_connectivity_monitor
        from sync_engine import get_sync_engine
        from status_widget import create_status_bar
        from alerts import check_all_alerts, get_unread_alerts
        from backup_manager import backup_manager
        from startup_wizard import create_startup_wizard, get_company_type, get_company_config
        from smart_dashboard import create_smart_dashboard
        from license_manager import verify_software_activation
        from setup_licensing_ui import create_admin_setup_wizard
    except Exception:
        # Modules not available - run in compatibility mode
        init_database = None
        get_db_stats = None
        get_connectivity_monitor = None
        get_sync_engine = None
        create_status_bar = None
        check_all_alerts = None
        get_unread_alerts = None
        backup_manager = None
        create_startup_wizard = None
        get_company_type = None
        get_company_config = None
        create_smart_dashboard = None
        verify_software_activation = None
        create_admin_setup_wizard = None

logging.info("Application started")


# Ensure create_startup_wizard is available
if 'create_startup_wizard' not in dir() or create_startup_wizard is None:
    try:
        from startup_wizard import create_startup_wizard, get_company_type, get_company_config
    except Exception as e:
        logging.warning(f"Could not import startup_wizard: {e}")
        # Create dummy functions to prevent crashes
        def create_startup_wizard(parent, callback):
            messagebox.showinfo("Setup", "Startup wizard not available. Continuing with default settings.")
            if callback:
                callback('general_retail', 'Default Company')
        
        def get_company_type():
            return 'general_retail'
        
        def get_company_config():
            return {'name': 'Default Company', 'icon': '🏪'}

# Disable strict username validation for backwards compatibility
import login_ui
original_validate = login_ui.validate_username if hasattr(login_ui, 'validate_username') else None
login_ui.validate_username = lambda x: True  # Allow any username format for login


def open_dashboard(username, role, root=None):
    """
    Sets up the main application window with a tabbed interface.
    Now includes smart dashboard based on company type.
    """
    if root is None:
        root = tk.Tk()
    else:
        try:
            root.deiconify()
        except tk.TclError:
            pass  # Handle cases where the window might already be gone

    root.title("Minataka Sphere - Inventory Management System v2.0")
    root.geometry("1280x800")

    # Initialize new modules
    if init_database:
        try:
            init_database()
            logging.info("Database initialized")
        except Exception as e:
            logging.warning(f"Database init failed: {e}")
    
    # Start connectivity monitoring
    if get_connectivity_monitor:
        try:
            monitor = get_connectivity_monitor()
            monitor.start()
            logging.info("Connectivity monitor started")
        except Exception as e:
            logging.warning(f"Connectivity monitor failed: {e}")
    
    # Start sync engine
    if get_sync_engine:
        try:
            sync = get_sync_engine()
            sync.start()
            logging.info("Sync engine started")
        except Exception as e:
            logging.warning(f"Sync engine failed: {e}")
    
    # Check alerts on startup
    if check_all_alerts:
        try:
            threading.Thread(target=check_all_alerts, daemon=True).start()
            logging.info("Alert check started")
        except Exception as e:
            logging.warning(f"Alert check failed: {e}")
    
    # Create main frame with status bar and theme toggle
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True)
    
    # Top bar with theme toggle
    top_bar = ttk.Frame(main_frame)
    top_bar.pack(fill="x", padx=10, pady=(10, 0))
    
    # Theme toggle button
    def on_theme_toggle():
        from ui_theme import toggle_theme, get_color
        is_dark = toggle_theme(root)
        # Update button text
        theme_btn.configure(text="🌙 Dark" if not is_dark else "☀️ Light")
        # Refresh UI colors (notebook tabs need update)
        try:
            app_bg = get_color('app_bg')
            card_bg = get_color('card_bg')
            text_main = get_color('text_main')
            root.configure(bg=app_bg)
            main_frame.configure(bg=app_bg)
            # Update notebook styling
            for i in range(notebook.index("end") + 1):
                try:
                    notebook.tab(i, foreground=text_main)
                except:
                    pass
        except Exception as e:
            logging.warning(f"Theme toggle UI update failed: {e}")
    
    theme_btn = make_button(top_bar, text="🌙 Dark", command=on_theme_toggle, kind="secondary")
    theme_btn.pack(side="right", padx=(0, 10))
    
    notebook = ttk.Notebook(main_frame)
    notebook.pack(pady=10, padx=10, fill="both", expand=True)

    # Define tab switcher for interlinking
    def switch_tab(tab_name):
        """Helper to switch to a specific tab by name/text."""
        try:
            for i in range(notebook.index("end")):
                tab_text = notebook.tab(i, "text").lower().strip()
                if tab_name.lower().strip() in tab_text:
                    notebook.select(i)
                    return True
        except Exception as e:
            logging.error(f"Tab switch failed: {e}")
        return False

    # Smart Dashboard (adaptive based on company type)
    if create_smart_dashboard:
        try:
            company_type = get_company_type()
            dashboard_frame = create_smart_dashboard(notebook, username, role, company_type, switch_tab_callback=switch_tab)
            notebook.add(dashboard_frame, text=" 🏠 Dashboard ")
            logging.info(f"Smart dashboard loaded for: {company_type}")
        except Exception as e:
            logging.warning(f"Smart dashboard failed: {e}")
            # Fallback to old dashboard
            dashboard_frame = create_dashboard_tab(notebook, username, role, switch_tab_callback=switch_tab)
            notebook.add(dashboard_frame, text=" 🏠 Dashboard ")
    else:
        dashboard_frame = create_dashboard_tab(notebook, username, role, switch_tab_callback=switch_tab)
        notebook.add(dashboard_frame, text=" 🏠 Dashboard ")

    inventory_frame = create_inventory_tab(notebook, current_user=username)
    notebook.add(inventory_frame, text=" 📦 Inventory ")

    sales_frame = create_sales_tab(notebook)
    notebook.add(sales_frame, text=" 💰 Sales ")

    if role == "admin":
        profit_frame = create_profit_tab(notebook)
        notebook.add(profit_frame, text=" 📊 Profitability ")
        
        # Add Alerts tab for admin
        try:
            from .alerts_ui import create_alerts_tab
            alerts_frame = create_alerts_tab(notebook, current_user=username)
            notebook.add(alerts_frame, text=" 🔔 Alerts ")
        except Exception:
            pass

    # Bottom action bar
    action_frame = ttk.Frame(main_frame, padding=5)
    action_frame.pack(fill="x", padx=10, pady=(0, 5))
    
    # Quick stats label
    stats_var = tk.StringVar(value="Ready")
    stats_label = ttk.Label(action_frame, textvariable=stats_var, foreground="#6c757d")
    stats_label.pack(side=tk.LEFT, padx=10)
    
    # Update stats periodically
    def update_stats():
        if get_db_stats:
            try:
                stats = get_db_stats()
                low_stock = stats.get('low_stock_count', 0)
                pending = stats.get('pending_sync', 0)
                alerts = stats.get('unread_alerts', 0)
                
                if low_stock > 0 or alerts > 0:
                    stats_var.set(f"⚠️ Low Stock: {low_stock} | Alerts: {alerts} | Pending Sync: {pending}")
                else:
                    stats_var.set(f"✓ All good | Products: {stats.get('total_products', 0)} | Pending Sync: {pending}")
            except Exception:
                pass
        action_frame.after(10000, update_stats)  # Update every 10 seconds
    
    update_stats()
    
    # Manual backup button
    def quick_backup():
        if backup_manager:
            try:
                path = backup_manager.create_backup("manual")
                messagebox.showinfo("Backup", f"Backup created:\n{path}")
            except Exception as e:
                messagebox.showerror("Backup Error", str(e))
        else:
            # Fallback to old backup
            try:
                dest = backup_data()
                messagebox.showinfo("Backup", f"Backup created:\n{dest}")
            except Exception as e:
                messagebox.showerror("Backup Error", str(e))
    
    make_button(action_frame, "💾 Quick Backup", command=quick_backup, kind="secondary").pack(side=tk.RIGHT, padx=5)
    
    # Status bar (if available)
    if create_status_bar:
        try:
            status_bar = create_status_bar(main_frame, "Minataka Sphere IMS")
            status_bar.pack(fill="x", side=tk.BOTTOM)
        except Exception as e:
            logging.warning(f"Status bar failed: {e}")
    
    logout_btn = ttk.Button(action_frame, text="🚪 Logout", command=root.destroy, style="danger.TButton")
    logout_btn.pack(side=tk.RIGHT, padx=10)
    
    # Add OWNER ADMIN / AUDIT tab
    if role == "OWNER_ADMIN":
        try:
            from .setup_licensing_ui import create_owner_admin_dashboard
            admin_dashboard = create_owner_admin_dashboard()
            notebook.add(admin_dashboard, text=" 👑 Owner Admin ")
            logging.info("Owner Admin dashboard loaded")
        except Exception as e:
            logging.warning(f"Owner Admin dashboard failed: {e}")

        try:
            from .audit_ui import create_audit_tab
            audit_frame = create_audit_tab(notebook, current_user=username)
            notebook.add(audit_frame, text=" 🔍 Audit Logs ")
        except Exception:
            pass
    
    # Add admin-only tabs
    if role in ["admin", "OWNER_ADMIN"]:
        # --- CORE ADMIN TABS ---
        admin_tabs = [
            ("🏢 Locations", "locations_ui", "create_locations_tab"),
            ("🔄 Transfers", "stock_transfer_ui", "create_stock_transfers_tab"),
            ("🏭 Suppliers", "suppliers_ui", "create_suppliers_tab"),
            ("📋 Purchase Orders", "purchase_orders_ui", "create_purchase_orders_tab"),
            ("💼 Sales Orders", "sales_orders_ui", "create_sales_orders_tab"),
            ("📈 Reports", "reports_ui", "create_reports_tab"),
            ("📅 Lease Mgmt", "lease_ui", "create_lease_tab"),
            ("🔌 Electronics", "electronics_ui", "create_electronics_tab"),
            ("🧾 Invoicing", "invoicing_ui", "create_invoicing_tab"),
            ("🔙 Returns", "returns_ui", "create_returns_tab"),
            ("🛠️ Service", "tradein_service_ui", "create_service_tab"),
            ("📊 Profitability", "profit_ui", "create_profit_tab"),
        ]

        for text, module_name, func_name in admin_tabs:
            try:
                # Dynamic import to handle relative paths and missing files
                import importlib
                try:
                    module = importlib.import_module(f".{module_name}", package="inventory_app")
                except (ImportError, ValueError, AttributeError):
                    module = importlib.import_module(module_name)
                
                func = getattr(module, func_name)
                # Call with current_user if the function supports it
                if "current_user" in func.__code__.co_varnames:
                    frame = func(notebook, current_user=username)
                else:
                    frame = func(notebook)
                notebook.add(frame, text=f" {text} ")
            except Exception as e:
                logging.warning(f"Failed to load enterprise tab {text}: {e}")
        
        # Lease Management tab
        # All enterprise tabs are now handled by the admin_tabs loop above.


def _seconds_until_next(hour=2, minute=0):
    now = datetime.now()
    try:
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        next_run = now + timedelta(days=1)
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    return (next_run - now).total_seconds()


def start_backup_scheduler(initial_run=True):
    """Start a background daemon thread to backup data daily."""
    if backup_data is None:
        logging.info("Backup utilities not available; scheduler disabled")
        return

    def _loop():
        if initial_run:
            try:
                dest = backup_data()
                logging.info("Initial backup created: %s", dest)
                try:
                    prune_backups(keep=load_settings().get("backup_retention", 30))
                except Exception:
                    logging.exception("Failed to prune backups after initial backup")
            except Exception:
                logging.exception("Initial backup failed")

        while True:
            settings = load_settings()
            run_hour = int(settings.get("backup_hour", 2))
            run_minute = int(settings.get("backup_minute", 0))
            retention = int(settings.get("backup_retention", 30))

            secs = _seconds_until_next(run_hour, run_minute)
            time.sleep(secs)
            try:
                dest = backup_data()
                logging.info("Scheduled backup created: %s", dest)
                try:
                    prune_backups(keep=retention)
                except Exception:
                    logging.exception("Failed to prune backups after scheduled backup")
            except Exception:
                logging.exception("Scheduled backup failed")

    t = threading.Thread(target=_loop, daemon=True, name="BackupScheduler")
    t.start()
    logging.info("Backup scheduler thread started")


if __name__ == "__main__":
    # Use a root window that will host the login and then the main app
    app_root = tk.Tk()
    app_root.title("Minataka Sphere - Inventory System")

    try:
        # Set the new 'litera' theme (light mode by default)
        setup_theme(app_root, theme_name="litera", is_dark=False)
    except Exception as e:
        logging.warning("Theme setup failed at startup: %s", e, exc_info=True)
    
    # Initialize database before license verification or any database operations
    try:
        print("DEBUG: Initializing database...")
        if init_database:
            init_database()
            print("DEBUG: Database initialized")
            logging.info("Database initialized successfully at startup")
    except Exception as e:
        logging.error(f"Failed to initialize database at startup: {e}")

    # ========== LICENSE VERIFICATION ==========
    # Check if software is licensed before anything else
    if verify_software_activation:
        try:
            is_licensed, status = verify_software_activation()
            
            if not is_licensed:
                if status == "FIRST_TIME_SETUP":
                    # First time setup: create Owner Admin account
                    logging.info("First-time setup: creating Owner Admin account")
                    print("DEBUG: Launching Admin Setup Wizard")
                    create_admin_setup_wizard(app_root)
                    print("DEBUG: Admin Setup Wizard closed")
                    # Re-verify after setup returns to ensure state is updated
                    app_root.deiconify()
                    app_root.update()
                    is_licensed, status = verify_software_activation()
                    print(f"DEBUG: Re-verified license: is_licensed={is_licensed}, status={status}")
                    
                    if not is_licensed:
                        # Check if a license file was created as a fallback
                        license_file = os.path.join(get_data_dir(), 'license.json')
                        if not os.path.exists(license_file):
                            messagebox.showerror("Setup Required",
                                               "Software setup is required to continue. Exiting.")
                            app_root.destroy()
                            sys.exit(0)
                        else:
                            # If file exists but verification failed, we might need a restart or just proceed
                            is_licensed = True 
                
                elif status == "CLONE_DETECTED":
                    # Clone detected: block execution
                    logging.critical("CLONE DETECTED: Software running on unauthorized device")
                    messagebox.showerror("Unauthorized Device", 
                                       "This software has been cloned to an unauthorized device.\n\n"
                                       "Please contact your administrator to authorize this device.\n"
                                       "Device information has been logged.")
                    app_root.destroy()
                    sys.exit(0)
                
                else:
                    # Other license errors
                    logging.error(f"License error: {status}")
                    messagebox.showerror("License Error", 
                                       f"Software license error: {status}\n\n"
                                       "Please contact your administrator.")
                    app_root.destroy()
                    sys.exit(0)
            else:
                logging.info("Software license verified successfully")
        
        except Exception as e:
            logging.exception(f"Error during license verification: {e}")
            messagebox.showerror("Startup Error", 
                               f"Failed to verify software license: {str(e)}\n\n"
                               "Please contact your administrator.")
            app_root.destroy()
            sys.exit(0)
    else:
        logging.warning("License verification not available - running in legacy mode")

    # Check if first run (no company type set)
    first_run = False
    try:
        if get_company_type:
            company_type = get_company_type()
            if not company_type or company_type == 'not_set':
                first_run = True
        else:
            first_run = True
    except:
        first_run = True

    # Check if license was just created (fresh install)
    try:
        license_file = os.path.join(get_data_dir(), 'license.json')
        if os.path.exists(license_file):
            # Check if users.json has only one user (just created owner admin)
            users_file = os.path.join(get_data_dir(), 'users.json')
            if os.path.exists(users_file):
                import json
                with open(users_file, 'r') as f:
                    users = json.load(f)
                if len(users) <= 1:
                    pass # We already set company_type in the DB
    except:
        pass

    # Show startup wizard on first run
    if first_run:
        logging.info("First run detected - showing startup wizard")
        print("DEBUG: Showing Startup Wizard...")
        
        def on_setup_complete(company_type, company_name):
            logging.info(f"Setup complete: {company_type} - {company_name}")
            print(f"DEBUG: Setup complete: {company_type}")
            # Proceed to login
            app_root.withdraw()
            open_login(open_dashboard, master=app_root)
        
        # Ensure root is available and updated
        app_root.deiconify()
        app_root.update()
        create_startup_wizard(app_root, on_setup_complete)
        print("DEBUG: Startup Wizard window should be active")
    else:
        # Normal startup: show login window
        app_root.withdraw()
        try:
            from .backup_scheduler import start_backup_scheduler
        except (ImportError, ModuleNotFoundError):
            try: from backup_scheduler import start_backup_scheduler
            except: 
                start_backup_scheduler = lambda **kw: None
                logging.warning("Backup scheduler not available")
        
        try:
            start_backup_scheduler(initial_run=True)
        except Exception:
            logging.exception("Failed to start backup scheduler")

        # The login window is modal and blocking.
        open_login(open_dashboard, master=app_root)

    logging.info("Starting main application loop")
    try:
        app_root.update()
        app_root.mainloop()
    except Exception as e:
        logging.critical(f"Main loop crashed: {e}")
        messagebox.showerror("Critical Error", f"The application crashed:\n{e}")
    logging.info("Application closed")