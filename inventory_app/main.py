"""
Mintaka Sphere - Main Entry Point
==================================
Industrial-grade inventory management system.
"""
import sys
import os
import logging
import threading
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
    close_connection, ensure_default_admin,
)
from services import svc

# ---------------------------------------------------------------------------
# Industry & tab management
# ---------------------------------------------------------------------------
from tab_manager import reload_tabs_for_new_industry
from industry_service import set_tab_reload_fn

def reload_industry_tabs() -> bool:
    """
    Reload ALL tabs based on current industry config.
    Uses NEW config-driven tab manager.
    """
    try:
        from database import db
        
        # Get current industry from DB
        industry_id = db.get_industry_type()
        
        # Remove ALL tabs and rebuild from config
        return reload_tabs_for_new_industry(
            industry_id,
            app_state.main_notebook,
            app_state.username,
            app_state.role,
            app_state.switch_tab
        )
    except Exception as e:
        logging.error(f"Tab reload failed: {e}")
        return False

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

    # ── Build ALL tabs from config (ELECTRONICS is default) ─────────
    try:
        from tab_manager import build_tabs_for_industry
        from config import get_default_industry
        
        # Get default industry (Electronics)
        industry_id = get_default_industry()
        
        # Build all tabs based on industry config
        success = build_tabs_for_industry(
            industry_id, notebook, username, role,
            switch_tab_callback=app_state.switch_tab
        )
        
        if not success:
            logging.error("Failed to build tabs from config")
            
    except Exception as exc:
        logging.error("Tab building failed: %s", exc)

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
    _stats_running = True

    def update_stats():
        """Robust periodic stats updater with proper error handling."""
        if not _stats_running or not root.winfo_exists():
            return
        
        try:
            stats = get_db_stats()
            low = stats.get("low_stock_count", 0)
            tot = stats.get("total_products", 0)
            if root.winfo_exists():
                stats_var.set(f"\u26a0\ufe0f Low Stock: {low} | Products: {tot}")
        except Exception as exc:
            logging.debug("Stats update failed: %s", exc)
            if root.winfo_exists():
                stats_var.set("Stats unavailable")
        finally:
            if _stats_running and root.winfo_exists():
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
        ensure_default_admin()

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

            # Run backup in background thread to prevent UI freeze
            try:
                if backup_manager:
                    def run_backup():
                        try:
                            backup_manager.create_backup(backup_type="auto")
                            report_info("Initial backup completed", module="Main")
                        except Exception as exc:
                            logging.warning("Backup failed: %s", exc)
                    
                    threading.Thread(target=run_backup, daemon=True).start()
            except Exception as exc:
                logging.warning("Failed to start backup: %s", exc)

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
