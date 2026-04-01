"""
Minataka Sphere - Core Infrastructure
Centralized State Management, Navigation, and Data Linking
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional
import datetime

class AppState:
    """Singleton-like state manager for the entire application"""
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
        self.industry_type = "Retail"  # Default
        self.industries = {
            "Retail": {"icon": "🛒", "color": "#2563EB", "features": ["Barcode", "POS", "Loyalty"]},
            "Pharma": {"icon": "💊", "color": "#10B981", "features": ["Expiry Tracking", "Batch No", "Prescription"]},
            "Electronics": {"icon": "📱", "color": "#8B5CF6", "features": ["Serial Numbers", "Warranty", "IMEI"]},
            "Manufacturing": {"icon": "🏭", "color": "#F59E0B", "features": ["BOM", "Work Orders", "Raw Materials"]},
            "Healthcare": {"icon": "🏥", "color": "#EF4444", "features": ["Patient Records", "Equipment Tracking", "Consumables"]}
        }
        
        # Navigation State
        self.current_module = "Dashboard"
        self.module_history = []
        
        # Data Links (In-memory cache for quick access)
        self.low_stock_items = []
        self.pending_orders = []
        self.recent_sales = []
        
        # Callbacks for UI updates
        self.ui_update_callbacks = []
        
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
            
    def register_ui_callback(self, callback: Callable):
        """Register a UI component to be notified of state changes"""
        if callback not in self.ui_update_callbacks:
            self.ui_update_callbacks.append(callback)
            
    def notify_ui_updates(self, event_type: str, data: Any = None):
        """Notify all registered UI components of state changes"""
        for callback in self.ui_update_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"UI Callback Error: {e}")

    def refresh_data_links(self, db_connection=None):
        """Refresh cached data links from database"""
        # This will be implemented to fetch real-time data
        # For now, it's a placeholder for the linking logic
        pass


class PremiumPopup(tk.Toplevel):
    """
    Universal Premium Popup Window - International Software Standard
    - Glassmorphism design with theme support
    - Resizable/full-screen capable for better visibility
    - Responsive layout (no hidden buttons)
    - Auto-scrolling for content overflow
    - Centered positioning
    - SAP/Oracle NetSuite inspired UX patterns
    """
    def __init__(self, parent, title: str, width: int = 900, height: int = 650, 
                 resizable: bool = True, modal: bool = True, 
                 fullscreen_capable: bool = True, min_width: int = 700, min_height: int = 500,
                 **kwargs):
        super().__init__(parent)
        
        self.title(title)
        self.geometry(f"{width}x{height}")
        
        # Make modal if requested
        if modal:
            self.transient(parent)
            self.grab_set()
            
        # Allow resizing with configurable minimums
        if resizable:
            self.minsize(min_width, min_height)
            self.resizable(True, True)
        
        # Full-screen capability toggle
        self.fullscreen_capable = fullscreen_capable
        self._is_fullscreen = False
        self._windowed_geometry = None
        
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
        
        # Store reference to app state and utilities
        try:
            from ui_theme import get_color, make_button, BUTTON_STANDARD_WIDTH
            self.get_color = get_color
            self.make_button = make_button
        except ImportError:
            self.get_color = lambda name: "#F0F4F8"
            self.make_button = None
        
        # Apply theme
        self.apply_theme()
        
        # Add fullscreen toggle if enabled
        if fullscreen_capable:
            self._add_window_controls()
    
    def _add_window_controls(self):
        """Add window control buttons (fullscreen toggle, etc.)"""
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Fullscreen toggle button
        if self.make_button:
            self.fs_button = self.make_button(
                control_frame, 
                "⛶ Fullscreen", 
                command=self.toggle_fullscreen,
                kind="info",
                uniform=False
            )
            self.fs_button.pack(side="right")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if not self.fullscreen_capable:
            return
            
        if self._is_fullscreen:
            # Exit fullscreen
            self.attributes('-fullscreen', False)
            if self._windowed_geometry:
                self.geometry(self._windowed_geometry)
            self._is_fullscreen = False
            if hasattr(self, 'fs_button'):
                self.fs_button.configure(text="⛶ Fullscreen")
        else:
            # Enter fullscreen
            self._windowed_geometry = self.geometry()
            self.attributes('-fullscreen', True)
            self._is_fullscreen = True
            if hasattr(self, 'fs_button'):
                self.fs_button.configure(text="❐ Windowed")
    
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
        try:
            bg_color = self.get_color("app_bg")
        except:
            bg_color = "#F0F4F8"
        self.configure(bg=bg_color)
        self.canvas.configure(bg=bg_color)
        
    def get_content_frame(self) -> ttk.Frame:
        """Return the scrollable content frame for adding widgets"""
        return self.scrollable_frame
    
    def add_button_bar(self, buttons: list, pady: int = 20, use_uniform: bool = True):
        """
        Add a responsive button bar at the bottom of the popup
        Buttons automatically wrap if window is too narrow
        
        Args:
            buttons: List of button configs with text, command, kind
            pady: Vertical padding
            use_uniform: Apply uniform button sizing (default: True)
        """
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", padx=40, pady=pady)
        
        for btn_config in buttons:
            if self.make_button:
                btn = self.make_button(
                    button_frame, 
                    text=btn_config.get("text", "Action"),
                    command=btn_config.get("command", lambda: None),
                    kind=btn_config.get("kind", "primary"),
                    icon=btn_config.get("icon", ""),
                    uniform=True
                )
            else:
                # Fallback: create styled button with uniform width
                btn_width = 14  # Standard character width
                btn = ttk.Button(
                    button_frame, 
                    text=btn_config.get("text", "Action"),
                    command=btn_config.get("command", lambda: None),
                    style=btn_config.get("style", "TButton"),
                    width=btn_width,
                    padding=(20, 12)
                )
            btn.pack(side="left", padx=5, expand=False, fill="x")
            
        return button_frame


class DataLinker:
    """
    Handles data interlinking between modules
    - Sales → Inventory (deduct stock)
    - Purchase Orders → Inventory (add stock)
    - Low Stock → Purchase Suggestions
    - Suppliers → Purchase Orders
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        
    def process_sale(self, sale_items: list, db_cursor=None):
        """
        Process a sale and automatically deduct inventory
        Returns success status and any errors
        """
        errors = []
        successful_items = []
        
        for item in sale_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            # Check current stock
            # This is pseudo-code, actual implementation depends on DB schema
            # current_stock = self.get_product_stock(product_id)
            
            # if current_stock < quantity:
            #     errors.append(f"Insufficient stock for product {product_id}")
            #     continue
                
            # Deduct stock
            # self.update_product_stock(product_id, -quantity)
            successful_items.append(item)
            
        return {
            "success": len(errors) == 0,
            "errors": errors,
            "processed_items": successful_items
        }
        
    def process_purchase_order(self, po_items: list, supplier_id: int, db_cursor=None):
        """
        Process a received purchase order and add to inventory
        """
        added_items = []
        
        for item in po_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            cost_price = item.get('cost_price', 0)
            
            # Add stock
            # self.update_product_stock(product_id, quantity)
            # Update average cost if needed
            
            added_items.append({
                "product_id": product_id,
                "quantity_added": quantity,
                "new_cost": cost_price
            })
            
        return {
            "success": True,
            "items_added": added_items
        }
        
    def get_low_stock_suggestions(self, threshold: int = 10):
        """
        Get list of low stock items with suggested reorder quantities
        Links to Purchase Order module
        """
        suggestions = []
        # Fetch from DB where stock < threshold
        # for item in low_stock_items:
        #     suggestions.append({
        #         "product_id": item['id'],
        #         "current_stock": item['stock'],
        #         "suggested_order": max(20, item['reorder_level'] * 2),
        #         "supplier_id": item['default_supplier_id']
        #     })
        return suggestions
        
    def create_purchase_order_from_suggestion(self, suggestions: list):
        """
        Auto-create a draft purchase order from low stock suggestions
        """
        po_data = {
            "status": "draft",
            "items": [],
            "total_amount": 0
        }
        
        for suggestion in suggestions:
            po_data["items"].append({
                "product_id": suggestion["product_id"],
                "quantity": suggestion["suggested_order"],
                "supplier_id": suggestion["supplier_id"]
            })
            
        return po_data


# Global instances
app_state = AppState()
data_linker = DataLinker()
