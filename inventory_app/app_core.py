"""
Mintaka Sphere - Core Infrastructure
Centralized State Management, Navigation, and Data Linking

CLEANED UP: Removed stale cached data lists (low_stock_items, pending_orders,
recent_sales) that were never refreshed and caused UI desynchronization.
All data now reads directly from the database through the service layer.
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional
import datetime

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


class PremiumPopup(tk.Toplevel):
    """
    Universal Premium Popup Window
    - Glassmorphism design
    - Responsive layout (no hidden buttons)
    - Auto-scrolling for content overflow
    - Centered positioning
    """
    def __init__(self, parent, title: str, width: int = 900, height: int = 700,
                 resizable: bool = True, modal: bool = True, **kwargs):
        super().__init__(parent)

        self.title(title)
        self.geometry(f"{width}x{height}")

        # Make modal if requested
        if modal:
            self.transient(parent)
            self.grab_set()

        # Allow resizing but set min size
        if resizable:
            self.minsize(700, 550)
            self.resizable(True, True)
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{x}+{y}")
        
        # Apply glassmorphism background (if supported by OS)
        # Note: Real blur requires platform-specific code, using semi-transparent fallback
        self.configure(bg="#F0F4F8")  # Light mode default
        
        # Create main scrollable container
        self.canvas = tk.Canvas(self, bg="#F0F4F8", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind canvas resize to adjust frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)  # Linux
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)  # Linux
        
        # Layout
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Store reference to app state
        from ui_theme import get_color
        self.get_color = get_color
        
        # Apply theme
        self.apply_theme()
        
    def _on_canvas_configure(self, event):
        """Adjust scrollable frame width to match canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
            
    def apply_theme(self):
        """Apply current theme colors"""
        bg_color = self.get_color("bg_primary")
        self.configure(bg=bg_color)
        self.canvas.configure(bg=bg_color)
        
    def get_content_frame(self) -> ttk.Frame:
        """Return the scrollable content frame for adding widgets"""
        return self.scrollable_frame
    
    def add_button_bar(self, buttons: list, pady: int = 20):
        """
        Add a responsive button bar at the bottom of the popup
        Buttons automatically wrap if window is too narrow
        """
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", padx=40, pady=pady)
        
        for btn_config in buttons:
            btn = ttk.Button(
                button_frame, 
                text=btn_config.get("text", "Action"),
                command=btn_config.get("command", lambda: None),
                style=btn_config.get("style", "Accent.TButton")
            )
            btn.pack(side="left", padx=5, expand=False, fill="x")
            
        return button_frame


# Global instance
app_state = AppState()
