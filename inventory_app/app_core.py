"""
Mintaka Sphere - Core Infrastructure
Centralized State Management, Navigation, and Data Linking

CLEANED UP: Removed stale cached data lists (low_stock_items, pending_orders,
recent_sales) that were never refreshed and caused UI desynchronization.
All data now reads directly from the database through the service layer.

CONVERTED: tkinter to PySide6/Qt
"""
import logging
from typing import Dict, Any, Callable, Optional
import datetime

from PySide6 import QtWidgets, QtCore, QtGui


class AppState:
    """
    Singleton-like state manager for the entire application.

    ONLY holds TRUE application state (user identity, navigation, industry).
    NEVER holds business data (products, sales, etc.) — that lives in the DB
    and is read through the service layer (services.py).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Current Industry/Nature of Business
        # Derived from industry_service — single source of truth
        self._industry_service_config = None  # Lazy-loaded reference
        self.industry_type = "Retail"  # Default (display name)
        # Industry display options — built from industry_service canonical config
        self.industries = self._build_industries_from_service()

        # Navigation State
        self.current_module = "Dashboard"
        self.module_history = []

        # Global UI references
        self.main_notebook = None
        self.username = None
        self.role = None
        self.user_id = None  # Database user ID for audit trail linkage
        self.switch_tab = None

        # Callbacks for UI updates (e.g. industry change notifications)
        self.ui_update_callbacks = []

    def _build_industries_from_service(self) -> Dict[str, Dict[str, Any]]:
        """Build AppState industries dict from industry_service canonical config.

        Uses capitalized display names (app_state_name) as keys for backward compatibility.
        """
        try:
            from industry_service import get_all_configs
            all_configs = get_all_configs()
            result = {}
            for industry_id, config in all_configs.items():
                display_name = config.get("app_state_name", config["name"])
                result[display_name] = {
                    "icon": config["icon"],
                    "color": config["color"],
                    "features": list(config.get("features", {}).keys()),
                }
            return result
        except Exception:
            # Fallback if industry_service not available
            return {
                "Retail": {"icon": "🛒", "color": "#2563EB", "features": ["barcode", "pos", "loyalty"]},
                "Pharma": {"icon": "💊", "color": "#10B981", "features": ["track_expiry", "track_batch", "track_prescription"]},
                "Electronics": {"icon": "📱", "color": "#8B5CF6", "features": ["track_serial", "track_repairs", "track_trade_in"]},
            }

    def set_industry(self, industry: str):
        """Change industry type and trigger UI updates"""
        if industry in self.industries:
            self.industry_type = industry
            self.notify_ui_updates("industry_change")

    def get_industry_config(self) -> Dict[str, Any]:
        """Get current industry configuration"""
        return self.industries.get(self.industry_type, self.industries["Retail"])

    def navigate_to(self, module_name: str, parent_window=None):
        """Handle navigation with history tracking"""
        if self.current_module != module_name:
            self.module_history.append(self.current_module)
            self.current_module = module_name
            self.notify_ui_updates("navigation", module_name)

    def go_back(self):
        """Navigate back to previous module"""
        if self.module_history:
            prev_module = self.module_history.pop()
            self.current_module = prev_module
            self.notify_ui_updates("navigation", prev_module)

    def register_ui_callback(self, callback_or_event=None, callback=None):
        """Register a UI component to be notified of state changes.

        Supports two call patterns:
          - register_ui_callback(callable)          # old style: subscribe to ALL events
          - register_ui_callback(event_name, callable)  # new style: subscribe to specific event
        """
        # Normalize arguments
        if callback is not None:
            # Called as register_ui_callback("event_name", callable)
            event_name = callback_or_event
            target = callback
            # Store as (event_name, callable) tuple
            entry = (event_name, target)
            if entry not in self.ui_update_callbacks:
                self.ui_update_callbacks.append(entry)
        elif callable(callback_or_event):
            # Called as register_ui_callback(callable) — legacy: listen to everything
            target = callback_or_event
            if target not in self.ui_update_callbacks:
                self.ui_update_callbacks.append(target)

    def notify_ui_updates(self, event_type: str, data: Any = None):
        """Notify all registered UI components of state changes."""
        for entry in list(self.ui_update_callbacks):
            try:
                if isinstance(entry, tuple) and len(entry) == 2:
                    # (event_name, callback) — only fire if event matches
                    event_name, cb = entry
                    if event_name == event_type:
                        cb(event_type, data)
                elif callable(entry):
                    # Legacy: fire for every event
                    entry(event_type, data)
            except Exception as e:
                logging.error(f"UI Callback Error: {e}")


class PremiumPopup(QtWidgets.QDialog):
    """
    Universal Premium Popup Window (PySide6/Qt version)
    - Glassmorphism design
    - Responsive layout (no hidden buttons)
    - Auto-scrolling for content overflow
    - Centered positioning
    """
    def __init__(self, parent, title: str, width: int = 900, height: int = 700,
                 resizable: bool = True, modal: bool = True, **kwargs):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.resize(width, height)

        # Make modal if requested
        if modal:
            self.setModal(True)

        # Allow resizing but set min size
        if resizable:
            self.setMinimumSize(700, 550)
        else:
            self.setFixedSize(width, height)

        # Apply glassmorphism background
        self.setStyleSheet("background-color: #F0F4F8;")

        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create scroll area
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #F0F4F8; border: none; }")

        # Create scrollable content frame
        self.scrollable_frame = QtWidgets.QWidget()
        self.scrollable_layout = QtWidgets.QVBoxLayout(self.scrollable_frame)
        self.scrollable_layout.setContentsMargins(20, 20, 20, 20)
        self.scrollable_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scrollable_frame)

        main_layout.addWidget(self.scroll_area)

        # Store reference to app state
        from ui_theme import get_color
        self.get_color = get_color

        # Apply theme
        self.apply_theme()

    def apply_theme(self):
        """Apply current theme colors"""
        bg_color = self.get_color("bg_primary")
        self.setStyleSheet(f"background-color: {bg_color};")
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background-color: {bg_color}; border: none; }}")

    def get_content_frame(self) -> QtWidgets.QWidget:
        """Return the scrollable content frame for adding widgets"""
        return self.scrollable_frame

    def add_button_bar(self, buttons: list, pady: int = 20):
        """
        Add a responsive button bar at the bottom of the popup
        """
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        button_layout.setContentsMargins(40, pady, 40, pady)
        button_layout.setSpacing(10)

        for btn_config in buttons:
            btn = QtWidgets.QPushButton(btn_config.get("text", "Action"))
            btn.clicked.connect(btn_config.get("command", lambda: None))

            # Apply accent style if specified
            if btn_config.get("style") == "Accent.TButton":
                btn.setProperty("class", "accent-button")

            button_layout.addWidget(btn)

        # Add spacer to push buttons to the left (or center if desired)
        button_layout.addStretch()

        # Add to scrollable content
        self.scrollable_layout.addWidget(button_widget)

        return button_widget


# Global instance
app_state = AppState()
