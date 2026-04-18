"""
Mintaka Sphere - Main Entry Point
==================================
Industrial-grade inventory management system (PySide6).
"""
import sys
import os
import logging
import threading
import importlib
import inspect

from PySide6 import QtWidgets, QtCore, QtGui

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
    FONT_HEADING, FONT_SMALL, COLOR_PRIMARY, COLOR_TEXT_MUTED,
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
# Helper utilities
# ============================================================================

def center_window_on_screen(widget, width, height):
    """Center a QWidget on the primary screen."""
    widget.resize(width, height)
    screen = QtWidgets.QApplication.primaryScreen().geometry()
    x = (screen.width() - width) // 2
    y = (screen.height() - height) // 2
    widget.move(x, y)


# ============================================================================
# Dashboard builder
# ============================================================================

class DashboardBuilder:
    """Builds and manages the main application dashboard."""

    def __init__(self, main_window, username, role):
        self.main_window = main_window
        self.username = username
        self.role = role
        self.central_widget = None
        self.top_bar_layout = None
        self.stats_var = None
        self.notebook = None
        self.stats_timer = None
        self._stats_running = True

    def build(self):
        """Build the complete dashboard UI."""
        logging.info("Building dashboard contents for %s", self.username)

        # ── Central widget ──────────────────────────────────────────────
        self.central_widget = QtWidgets.QWidget(self.main_window)
        self.main_window.setCentralWidget(self.central_widget)

        main_layout = QtWidgets.QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top bar ─────────────────────────────────────────────────────
        self._build_top_bar(main_layout)

        # ── Notebook (tab container) ────────────────────────────────────
        self._build_notebook(main_layout)

        # ── Status Bar (bottom of window) ──────────────────────────────
        self._build_status_bar()

        # ── Keyboard Shortcuts ─────────────────────────────────────────
        self._bind_shortcuts()

        # ── Periodic stats ticker ──────────────────────────────────────
        self._start_stats_ticker()

    def _build_top_bar(self, parent_layout):
        """Build the top action bar."""
        top_bar = QtWidgets.QWidget(self.central_widget)
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet(f"background-color: {get_color('app_bg')};")

        top_layout = QtWidgets.QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        top_layout.setSpacing(8)

        # Title label
        title_lbl = QtWidgets.QLabel("MINTAKA SPHERE", top_bar)
        title_lbl.setFont(QtGui.QFont(FONT_HEADING[0], FONT_HEADING[1]))
        title_lbl.setStyleSheet(f"color: {COLOR_PRIMARY}; font-weight: 700;")
        top_layout.addWidget(title_lbl)

        top_layout.addStretch()

        # Stats label
        self.stats_lbl = styled_label(
            top_bar, text="Loading stats...",
        )
        self.stats_lbl.setFont(QtGui.QFont(FONT_SMALL[0], FONT_SMALL[1]))
        self.stats_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        top_layout.addWidget(self.stats_lbl)

        # Industry switcher dialog
        def on_industry_switch():
            try:
                from industry_selector import create_industry_selector_card
            except ImportError:
                QtWidgets.QMessageBox.critical(
                    self.main_window, "Error", "Industry selector not available."
                )
                return

            switch_win = QtWidgets.QDialog(self.main_window)
            switch_win.setWindowTitle("Business Mode Selection")
            center_window_on_screen(switch_win, 800, 600)

            def handle_change(new_id):
                switch_win.close()
                from industry_service import get_config
                cfg = get_config(new_id)
                QtWidgets.QMessageBox.information(
                    self.main_window,
                    "Mode Updated",
                    f"System operating mode changed to: {cfg['name']}\n"
                    f"All tabs and forms updated.",
                )

            card = create_industry_selector_card(
                switch_win, on_industry_changed=handle_change,
            )
            dlg_layout = QtWidgets.QVBoxLayout(switch_win)
            dlg_layout.setContentsMargins(20, 20, 20, 20)
            dlg_layout.addWidget(card)
            switch_win.exec()

        # Action buttons
        btn_quick = make_button(top_bar, "Quick Item", kind="primary")
        btn_quick.clicked.connect(lambda: self.switch_tab("Inventory"))
        top_layout.addWidget(btn_quick)

        btn_mode = make_button(top_bar, "Mode", kind="secondary")
        btn_mode.clicked.connect(on_industry_switch)
        top_layout.addWidget(btn_mode)

        btn_theme = make_button(top_bar, "Theme", kind="secondary")
        btn_theme.clicked.connect(lambda: toggle_theme(self.main_window))
        top_layout.addWidget(btn_theme)

        btn_logout = make_button(top_bar, "Logout", kind="danger")
        btn_logout.clicked.connect(self.main_window.close)
        top_layout.addWidget(btn_logout)

        parent_layout.addWidget(top_bar)

    def _build_notebook(self, parent_layout):
        """Build the tab notebook and populate tabs."""
        self.notebook = QtWidgets.QTabWidget(self.central_widget)

        # Store references for the rest of the app
        app_state.main_notebook = self.notebook
        app_state.username = self.username
        app_state.role = self.role
        app_state.switch_tab = self.switch_tab

        # Build ALL tabs from config (ELECTRONICS is default)
        try:
            from tab_manager import build_tabs_for_industry
            from config import get_default_industry

            industry_id = get_default_industry()

            success = build_tabs_for_industry(
                industry_id, self.notebook, self.username, self.role,
                switch_tab_callback=self.switch_tab
            )

            if not success:
                logging.error("Failed to build tabs from config")

        except Exception as exc:
            logging.error("Tab building failed: %s", exc)

        parent_layout.addWidget(self.notebook)

    def _build_status_bar(self):
        """Build the status bar at the bottom."""
        try:
            from status_widget import create_status_bar
            status_bar = create_status_bar(self.main_window, "Mintaka Sphere IMS")
            self.main_window.statusBar().addWidget(status_bar)
        except Exception as exc:
            logging.warning("Failed to load status bar: %s", exc)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        try:
            from business_settings import bind_industry_shortcut
            bind_industry_shortcut(self.main_window, dashboard_frame=None)
        except Exception as exc:
            logging.warning("Failed to bind Ctrl+I shortcut: %s", exc)

    def switch_tab(self, target_text):
        """Switch to a tab whose title contains target_text."""
        for i in range(self.notebook.count()):
            tab_text = self.notebook.tabText(i)
            if target_text.lower() in tab_text.lower():
                self.notebook.setCurrentIndex(i)
                return True
        return False

    def _start_stats_ticker(self):
        """Start periodic stats updates using QTimer."""
        self.stats_timer = QtCore.QTimer(self.main_window)
        self.stats_timer.timeout.connect(self._update_stats)
        self.stats_timer.start(30000)  # Every 30 seconds
        self._update_stats()  # Initial call

    def _update_stats(self):
        """Update stats label with current database stats."""
        if not self._stats_running:
            return

        try:
            stats = get_db_stats()
            low = stats.get("low_stock_count", 0)
            tot = stats.get("total_products", 0)
            if hasattr(self, 'stats_lbl') and self.stats_lbl is not None:
                self.stats_lbl.setText(f"\u26a0\ufe0f Low Stock: {low} | Products: {tot}")
        except Exception as exc:
            logging.debug("Stats update failed: %s", exc)
            if hasattr(self, 'stats_lbl') and self.stats_lbl is not None:
                self.stats_lbl.setText("Stats unavailable")

    def stop_stats_timer(self):
        """Stop the stats update timer."""
        self._stats_running = False
        if self.stats_timer is not None:
            self.stats_timer.stop()


# ============================================================================
# Main application class
# ============================================================================

class MintakaSphereApp:
    """Main application controller for Mintaka Sphere IMS."""

    def __init__(self):
        self.app = None
        self.main_window = None
        self.dashboard = None

    def run(self):
        """Run the application."""
        import os
        debug_file = os.path.join(os.path.dirname(__file__), "app_debug.log")
        with open(debug_file, "w") as f:
            f.write("App starting...\n")
            f.flush()
            
            try:
                # Create Qt application
                f.write("Creating QApplication...\n")
                f.flush()
                self.app = QtWidgets.QApplication.instance()
                if self.app is None:
                    self.app = QtWidgets.QApplication(sys.argv)
                f.write(f"QApplication created: {self.app}\n")
                f.flush()

                # 1. Database
                f.write("Initializing database...\n")
                f.flush()
                init_database()
                migrate_database()
                ensure_default_admin()
                f.write("Database initialized\n")
                f.flush()

                # 2. One-time JSON user migration
                try:
                    count = migrate_json_users_to_db()
                    if count > 0:
                        report_info(f"Migrated {count} users from JSON to database", module="Auth")
                except Exception as exc:
                    logging.warning("User migration failed: %s", exc)

                # 3. Check if first-run wizard is needed
                f.write("Checking first-run status...\n")
                f.flush()
                show_wizard = self._check_first_run()
                
                # 4. Create main window
                f.write("Creating main window...\n")
                f.flush()
                self.main_window = QtWidgets.QMainWindow()
                self.main_window.setWindowTitle("Mintaka Sphere IMS - Loading...")
                self.main_window.setWindowState(QtCore.Qt.WindowMinimized)
                f.write("Main window created\n")
                f.flush()

                # Setup theme
                f.write("Setting up theme...\n")
                f.flush()
                setup_theme(self.main_window, is_dark=(get_color("text_main") == "#FFFFFF"))
                f.write("Theme setup done\n")
                f.flush()

                # 5. Show startup wizard if first run
                if show_wizard:
                    f.write("Showing startup wizard...\n")
                    f.flush()
                    self._show_startup_wizard()
                
                # 6. Show login
                f.write("Showing login dialog...\n")
                f.flush()
                self._show_login()
                f.write("Login dialog shown\n")
                f.flush()

                # 7. Start event loop
                f.write("Starting event loop...\n")
                f.flush()
                sys.exit(self.app.exec())

            except Exception as exc:
                import traceback
                error_msg = f"CRITICAL ERROR: {exc}\n{traceback.format_exc()}"
                f.write(error_msg)
                f.flush()
                report_error("Critical application crash during startup", exception=exc, module="Main")
                try:
                    QtWidgets.QMessageBox.critical(
                        None,
                        "Critical Error",
                        f"The application failed to start:\n{exc}\n\nCheck 'app.log' for details.",
                    )
                except Exception:
                    print(error_msg)

    def _show_login(self):
        """Show the login dialog."""
        def on_login_success(username, role, user_id, login_win=None):
            self._on_login_success(username, role, user_id)

        # Show PySide6 login dialog (NO parent = always visible on top)
        open_login(on_success=on_login_success, parent=None)

    def _check_first_run(self) -> bool:
        """Check if this is first run (no company configured)."""
        try:
            from database import db, get_db_cursor
            # Check if company settings exist
            cur = get_db_cursor()
            cur.execute("SELECT COUNT(*) FROM business_settings")
            count = cur.fetchone()[0]
            return count == 0
        except Exception:
            # If table doesn't exist yet, assume first run
            return True

    def _show_startup_wizard(self):
        """Show the startup wizard for first-time setup."""
        try:
            from startup_wizard import create_startup_wizard
            
            def on_wizard_complete():
                report_info("Startup wizard completed - company configured", module="Main")
            
            # Create modal wizard dialog
            wizard_dialog = QtWidgets.QDialog(self.main_window)
            wizard_dialog.setWindowTitle("Welcome to Mintaka Sphere")
            wizard_dialog.setModal(True)
            wizard_dialog.setMinimumSize(700, 550)
            
            # Build wizard UI
            wizard_content = create_startup_wizard(wizard_dialog, on_wizard_complete)
            if wizard_content:
                layout = QtWidgets.QVBoxLayout(wizard_dialog)
                layout.addWidget(wizard_content)
                wizard_dialog.exec()
        except Exception as exc:
            logging.warning(f"Failed to show startup wizard: {exc}")
            # Continue anyway - wizard is optional

    def _on_login_success(self, username, role, user_id):
        """Handle successful login and build dashboard."""
        self.main_window.setWindowTitle(f"Mintaka Sphere IMS - {username.upper()}")
        center_window_on_screen(self.main_window, 1400, 900)
        self.main_window.show()

        # Build dashboard
        self.dashboard = DashboardBuilder(self.main_window, username, role)
        self.dashboard.build()

        app_state.user_id = user_id
        report_info(f"User {username} logged in successfully (ID: {user_id}).", module="Auth")

        # Start background services
        self._start_services()

        # Connect close event for graceful shutdown
        self.main_window.closeEvent = self._on_closing

    def _start_services(self):
        """Start connectivity monitor, sync engine, and backup."""
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
                def run_backup():
                    try:
                        backup_manager.create_backup(backup_type="auto")
                        report_info("Initial backup completed", module="Main")
                    except Exception as exc:
                        logging.warning("Backup failed: %s", exc)

                threading.Thread(target=run_backup, daemon=True).start()
        except Exception as exc:
            logging.warning("Failed to start backup: %s", exc)

    def _on_closing(self, event):
        """Handle graceful application shutdown."""
        report_info("Application shutting down...", module="Main")

        # Stop stats timer
        if self.dashboard is not None:
            self.dashboard.stop_stats_timer()

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

        # Accept the close event
        event.accept()


# ============================================================================
# Main entry point
# ============================================================================

def main():
    """Industrial-grade main entry point."""
    app = MintakaSphereApp()
    app.run()


if __name__ == "__main__":
    main()
