"""
Mintaka Sphere - Main Entry Point
==================================
Industrial-grade inventory management system.
"""
import sys
import os
import logging
import importlib
import inspect

import tkinter as tk
from tkinter import ttk, messagebox

# ---------------------------------------------------------------------------
# Path setup (must run before any local imports)
# ---------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# ---------------------------------------------------------------------------
# Core framework
# ---------------------------------------------------------------------------
from app_core import app_state
from ui_theme import (
    setup_theme, toggle_theme, get_color, make_button, styled_label,
    center_window, FONT_HEADING, FONT_SMALL, COLOR_PRIMARY, COLOR_TEXT_MUTED,
    label, frame,
)

# ---------------------------------------------------------------------------
# Database & services
# ---------------------------------------------------------------------------
from database import (
    init_database, migrate_database, get_db_stats, migrate_json_users_to_db,
    close_connection,
)
from services import svc

# ---------------------------------------------------------------------------
# Industry & tab management
# ---------------------------------------------------------------------------
from migration_add_industry_type import get_industry_type
from main_tabs import add_industry_tabs
from tab_manager import reload_industry_tabs as _reload_tabs, tag_dashboard_tab
from industry_service import set_tab_reload_fn

def reload_industry_tabs() -> bool:
    """Reload industry-specific tabs via the tab manager."""
    return _reload_tabs(
        notebook=app_state.main_notebook,
        app_state=app_state,
        get_industry_type_fn=get_industry_type,
        add_industry_tabs_fn=add_industry_tabs,
        username=app_state.username,
        role=app_state.role,
        switch_tab_callback=app_state.switch_tab,
    )

# Register tab-reload callback (avoids service -> main circular import)
set_tab_reload_fn(reload_industry_tabs)

# ---------------------------------------------------------------------------
# UI modules (login, dashboards, error reporting, networking)
# ---------------------------------------------------------------------------
from login_ui import open_login
from dashboard_ui import create_dashboard_tab
from tradein_service_ui import create_trade_ins_tab, create_service_tab
from error_manager import install_global_hook, report_info, report_error
from network import ConnectivityMonitor

# ---------------------------------------------------------------------------
# Optional modules (graceful fallback if missing)
# ---------------------------------------------------------------------------
try:
    from sync_engine import get_sync_engine
except ImportError:
    get_sync_engine = None  # type: ignore[misc]

try:
    from backup_manager import BackupManager
    backup_manager = BackupManager()
except ImportError:
    backup_manager = None

# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------
install_global_hook()

connectivity_monitor = ConnectivityMonitor()
sync_engine = get_sync_engine() if get_sync_engine else None

report_info("Industrial Core starting up...", module="Main")


# ============================================================================
# Dashboard builder
# ============================================================================

def build_dashboard(root, username, role):
    """Build the main application dashboard after login."""
    logging.info("Building dashboard contents for %s", username)

    # ── Core frame ──────────────────────────────────────────────────────
    app_container = ttk.Frame(root)
    app_container.pack(fill="both", expand=True)

    # ── Top bar ─────────────────────────────────────────────────────────
    top_bar = tk.Frame(app_container, bg=get_color("app_bg"), height=60)
    top_bar.pack(fill="x", side="top", padx=20, pady=10)

    label(top_bar, "MINTAKA SPHERE", kind="heading", foreground=COLOR_PRIMARY).pack(side="left")

    action_frame = tk.Frame(top_bar, bg=get_color("app_bg"))
    action_frame.pack(side="right")

    stats_var = tk.StringVar(value="Loading stats...")
    styled_label(
        action_frame, textvariable=stats_var,
        font=FONT_SMALL, foreground=COLOR_TEXT_MUTED,
    ).pack(side="left", padx=20)

    # ── Industry switcher dialog ────────────────────────────────────────
    def on_industry_switch():
        try:
            from industry_selector import create_industry_selector_card
        except ImportError:
            messagebox.showerror("Error", "Industry selector not available.")
            return

        switch_win = tk.Toplevel(root)
        switch_win.title("Business Mode Selection")
        center_window(switch_win, 800, 600)

        def handle_change(new_id):
            switch_win.destroy()
            from industry_service import get_config
            cfg = get_config(new_id)
            messagebox.showinfo(
                "Mode Updated",
                f"System operating mode changed to: {cfg['name']}\n"
                f"All tabs and forms updated.",
            )

        create_industry_selector_card(
            switch_win, on_industry_changed=handle_change,
        ).pack(fill="both", expand=True, padx=20, pady=20)

    # ── Top-bar buttons ─────────────────────────────────────────────────
    make_button(
        action_frame, "➕ Quick Item",
        command=lambda: switch_tab("Inventory"), kind="primary",
    ).pack(side="left", padx=5)
    make_button(
        action_frame, "🔄 Mode",
        command=on_industry_switch, kind="secondary",
    ).pack(side="left", padx=5)
    make_button(
        action_frame, "🌓 Theme",
        command=lambda: toggle_theme(root), kind="secondary",
    ).pack(side="left", padx=5)
    make_button(
        action_frame, "🚪 Logout",
        command=root.destroy, kind="danger",
    ).pack(side="left", padx=5)

    # ── Notebook (tab container) ────────────────────────────────────────
    notebook = ttk.Notebook(app_container)
    notebook.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def switch_tab(target_text):
        for i in range(notebook.index("end")):
            if target_text.lower() in notebook.tab(i, "text").lower():
                notebook.select(i)
                return True
        return False

    # Store references for the rest of the app
    app_state.main_notebook = notebook
    app_state.username = username
    app_state.role = role
    app_state.switch_tab = switch_tab

    # ── Dashboard tab ───────────────────────────────────────────────────
    try:
        dash_frame = create_dashboard_tab(
            notebook, username, role,
            switch_tab_callback=app_state.switch_tab,
        )
        notebook.add(dash_frame, text=" \U0001f3e0 Dashboard ")
        tag_dashboard_tab(notebook)
    except Exception as exc:
        logging.error("Dashboard load failed: %s", exc)

    # ── Core operational tabs ───────────────────────────────────────────
    core_modules = [
        ("\U0001f4e6 Inventory", "inventory_ui", "create_inventory_tab"),
        ("\U0001f4b0 Sales", "sales_ui", "create_sales_tab"),
        ("\U0001f3e2 Locations", "locations_ui", "create_locations_tab"),
        ("\U0001f3ed Suppliers", "suppliers_ui", "create_suppliers_tab"),
        ("\U0001f4cb Purchase Orders", "purchase_orders_ui", "create_purchase_orders_tab"),
        ("\U0001f6d2 Sales Orders", "sales_orders_ui", "create_sales_orders_tab"),
        ("\U0001f504 Stock Transfers", "stock_transfer_ui", "create_stock_transfers_tab"),
        ("\U0001f9fe Invoicing", "invoicing_ui", "create_invoicing_tab"),
        ("\U000021a9\ufe0f Returns/RMA", "returns_ui", "create_returns_tab"),
        ("\U0001f4ca Reports", "reports_ui", "create_reports_tab"),
        ("\U0001f4b5 Profit Analysis", "profit_ui", "create_profit_tab"),
        ("\U0001f514 Alerts", "alerts_ui", "create_alerts_tab"),
        ("\U0001f916 Smart Analytics", "smart_analytics_ui", "create_smart_analytics_tab"),
        ("\u2699\ufe0f Industry Settings", "industry_ui", "create_industry_settings_tab"),
    ]

    for text, module_name, func_name in core_modules:
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
            sig = inspect.signature(func)
            if "current_user" in sig.parameters:
                frame = func(notebook, current_user=username)
            else:
                frame = func(notebook)
            notebook.add(frame, text=f" {text} ")
        except Exception as exc:
            logging.warning("Failed to load %s: %s", text, exc)

    # ── Trade-in & Service tabs ─────────────────────────────────────────
    for tab_text, tab_func in [
        ("\U0001f504 Trade-ins", create_trade_ins_tab),
        ("\U0001f527 Service Tickets", create_service_tab),
    ]:
        try:
            frame = tab_func(notebook, current_user=username)
            notebook.add(frame, text=f" {tab_text} ")
        except Exception as exc:
            logging.warning("Failed to load %s: %s", tab_text, exc)

    # ── Industry vertical tabs ──────────────────────────────────────────
    add_industry_tabs(notebook, get_industry_type(), username)

    # ── Status Bar (bottom of window) ──────────────────────────────────
    try:
        from status_widget import create_status_bar
        status_bar = create_status_bar(root, "Mintaka Sphere IMS")
        status_bar.pack(fill="x", side="bottom")
    except Exception as exc:
        logging.warning("Failed to load status bar: %s", exc)

    # ── Keyboard Shortcuts ─────────────────────────────────────────────
    try:
        from business_settings import bind_industry_shortcut
        bind_industry_shortcut(root, dashboard_frame=None)
    except Exception as exc:
        logging.warning("Failed to bind Ctrl+I shortcut: %s", exc)

    # ── Periodic stats ticker ───────────────────────────────────────────
    def update_stats():
        try:
            stats = get_db_stats()
            low = stats.get("low_stock_count", 0)
            tot = stats.get("total_products", 0)
            if root.winfo_exists():
                stats_var.set(f"\u26a0\ufe0f Low Stock: {low} | Products: {tot}")
        except Exception as exc:
            logging.debug("Stats update failed: %s", exc)
        finally:
            if root.winfo_exists():
                root.after(30000, update_stats)

    update_stats()


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Industrial-grade main entry point."""
    try:
        # 1. Database
        init_database()
        migrate_database()

        # 2. One-time JSON user migration
        try:
            count = migrate_json_users_to_db()
            if count > 0:
                report_info(f"Migrated {count} users from JSON to database", module="Auth")
        except Exception as exc:
            logging.warning("User migration failed: %s", exc)

        # 3. UI
        root = tk.Tk()
        root.withdraw()
        setup_theme(root, is_dark=(get_color("text_main") == "#FFFFFF"))

        def on_login_success(username, role, user_id, login_win=None):
            root.title(f"Mintaka Sphere IMS - {username.upper()}")
            root.geometry("1400x900")
            center_window(root, 1400, 900)
            root.deiconify()

            build_dashboard(root, username, role)
            app_state.user_id = user_id
            report_info(f"User {username} logged in successfully (ID: {user_id}).", module="Auth")

            # Start background services
            try:
                connectivity_monitor.start()
                report_info("Connectivity monitor started", module="Main")
            except Exception as exc:
                logging.warning("Failed to start connectivity monitor: %s", exc)

            try:
                if sync_engine:
                    sync_engine.start()
                    report_info("Sync engine started", module="Main")
            except Exception as exc:
                logging.warning("Failed to start sync engine: %s", exc)

            try:
                if backup_manager:
                    backup_manager.create_backup(backup_type="auto")
                    report_info("Initial backup completed", module="Main")
            except Exception as exc:
                logging.warning("Backup failed: %s", exc)

            # Graceful shutdown
            def on_closing():
                report_info("Application shutting down...", module="Main")

                try:
                    connectivity_monitor.stop()
                except Exception as exc:
                    logging.error("Error stopping connectivity monitor: %s", exc)

                try:
                    if sync_engine:
                        sync_engine.stop()
                except Exception as exc:
                    logging.error("Error stopping sync engine: %s", exc)

                try:
                    close_connection()
                except Exception as exc:
                    logging.error("Error closing database: %s", exc)

                root.destroy()

            root.protocol("WM_DELETE_WINDOW", on_closing)

        open_login(on_success=on_login_success, master=root)
        root.mainloop()

    except Exception as exc:
        report_error("Critical application crash during startup", exception=exc, module="Main")
        # Final fallback — print to console when GUI itself has failed
        try:
            messagebox.showerror(
                "Critical Error",
                f"The application failed to start:\n{exc}\n\nCheck 'app.log' for details.",
            )
        except Exception:
            print(f"CRITICAL ERROR: {exc}")


if __name__ == "__main__":
    main()
