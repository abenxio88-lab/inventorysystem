"""Centralized UI theming helper with Premium Glassmorphism Design.
Fixed for robust button rendering and theme switching.
"""
import logging
try:
    import ttkbootstrap as tb
    from ttkbootstrap import Style
    USING_BOOTSTRAP = True
except Exception:
    tb = None
    Style = None
    USING_BOOTSTRAP = False

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

# ============================================
# THEME STATE MANAGEMENT
# ============================================
_current_theme = "light"  # "light" or "dark"

def get_current_theme():
    return _current_theme

def set_current_theme(theme_name):
    global _current_theme
    _current_theme = theme_name

# ============================================
# COLOR PALETTES (Static Values for Stability)
# ============================================
# Light Mode - Premium White/Blue Glass
COLOR_APP_BG_LIGHT = "#F0F4F8"
COLOR_CARD_BG_LIGHT = "#FFFFFF"
COLOR_PRIMARY_LIGHT = "#2563EB"
COLOR_PRIMARY_HOVER_LIGHT = "#1D4ED8"
COLOR_TEXT_MAIN_LIGHT = "#1E293B"
COLOR_TEXT_MUTED_LIGHT = "#64748B"
COLOR_BORDER_LIGHT = "#E2E8F0"
COLOR_SHADOW_LIGHT = "#000000"
COLOR_GLASS_LIGHT = "#FFFFFF"

# Dark Mode - Windows 11 Deep Mica
COLOR_APP_BG_DARK = "#202020"
COLOR_CARD_BG_DARK = "#2C2C2C"
COLOR_PRIMARY_DARK = "#4CC2FF"
COLOR_PRIMARY_HOVER_DARK = "#2DA5E9"
COLOR_TEXT_MAIN_DARK = "#FFFFFF"
COLOR_TEXT_MUTED_DARK = "#CCCCCC"
COLOR_BORDER_DARK = "#404040"
COLOR_SHADOW_DARK = "#000000"
COLOR_GLASS_DARK = "#2C2C2C"

# Current Resolved Colors (Updated on theme switch)
COLOR_APP_BG = COLOR_APP_BG_LIGHT
COLOR_CARD_BG = COLOR_CARD_BG_LIGHT
COLOR_PRIMARY = COLOR_PRIMARY_LIGHT
COLOR_PRIMARY_HOVER = COLOR_PRIMARY_HOVER_LIGHT
COLOR_TEXT_MAIN = COLOR_TEXT_MAIN_LIGHT
COLOR_TEXT_MUTED = COLOR_TEXT_MUTED_LIGHT
COLOR_BORDER = COLOR_BORDER_LIGHT
COLOR_GLASS = COLOR_GLASS_LIGHT

def update_theme_colors():
    """Updates global color variables based on current theme."""
    global COLOR_APP_BG, COLOR_CARD_BG, COLOR_PRIMARY, COLOR_PRIMARY_HOVER
    global COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_GLASS
    
    if _current_theme == "dark":
        COLOR_APP_BG = COLOR_APP_BG_DARK
        COLOR_CARD_BG = COLOR_CARD_BG_DARK
        COLOR_PRIMARY = COLOR_PRIMARY_DARK
        COLOR_PRIMARY_HOVER = COLOR_PRIMARY_HOVER_DARK
        COLOR_TEXT_MAIN = COLOR_TEXT_MAIN_DARK
        COLOR_TEXT_MUTED = COLOR_TEXT_MUTED_DARK
        COLOR_BORDER = COLOR_BORDER_DARK
        COLOR_GLASS = COLOR_GLASS_DARK
    else:
        COLOR_APP_BG = COLOR_APP_BG_LIGHT
        COLOR_CARD_BG = COLOR_CARD_BG_LIGHT
        COLOR_PRIMARY = COLOR_PRIMARY_LIGHT
        COLOR_PRIMARY_HOVER = COLOR_PRIMARY_HOVER_LIGHT
        COLOR_TEXT_MAIN = COLOR_TEXT_MAIN_LIGHT
        COLOR_TEXT_MUTED = COLOR_TEXT_MUTED_LIGHT
        COLOR_BORDER = COLOR_BORDER_LIGHT
        COLOR_GLASS = COLOR_GLASS_LIGHT

# ============================================
# TYPOGRAPHY
# ============================================
FONT_FAMILY = "Segoe UI Variable" if "Segoe UI Variable" in tkfont.families() else "Segoe UI"
FONT_HEADING = (FONT_FAMILY, 24, "bold")
FONT_SUBHEADING = (FONT_FAMILY, 14, "bold")
FONT_REGULAR = (FONT_FAMILY, 11)
FONT_SMALL = (FONT_FAMILY, 9)

# ============================================
# PREMIUM WIDGET FACTORY (Robust Implementation)
# ============================================

class PremiumButton(tk.Canvas):
    """A custom drawn button that guarantees perfect rendering regardless of ttk themes."""
    def __init__(self, master, text, command=None, width=200, height=45, bg_color=None, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, **kwargs)
        self.command = command
        self.text = text
        self.base_color = bg_color or COLOR_PRIMARY
        self.hover_color = COLOR_PRIMARY_HOVER
        self.current_color = self.base_color
        self.is_hovered = False
        
        # Draw initial state
        self.draw_button()
        
        # Bind events
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        
        # Text label
        self.text_id = self.create_text(
            width//2, height//2, 
            text=text, 
            fill="#FFFFFF", 
            font=(FONT_FAMILY, 11, "bold"),
            tags="btn_text"
        )

    def draw_button(self):
        self.delete("all")
        # Rounded rectangle
        r = 8 # radius
        w, h = int(self['width']), int(self['height'])
        self.create_rounded_rect(2, 2, w-2, h-2, r, fill=self.current_color, outline="", tags="btn_bg")
        # Redraw text on top
        self.text_id = self.create_text(w//2, h//2, text=self.text, fill="#FFFFFF", font=(FONT_FAMILY, 11, "bold"))
        self.tag_bind("btn_bg", "<Enter>", self.on_enter)
        self.tag_bind("btn_bg", "<Leave>", self.on_leave)
        self.tag_bind("btn_bg", "<Button-1>", self.on_click)
        self.tag_bind("btn_bg", "<ButtonRelease-1>", self.on_release)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event=None):
        self.is_hovered = True
        self.current_color = self.hover_color
        self.draw_button()
        self.config(cursor="hand2")

    def on_leave(self, event=None):
        self.is_hovered = False
        self.current_color = self.base_color
        self.draw_button()
        self.config(cursor="")

    def on_click(self, event=None):
        self.current_color = "#1E40AF" if _current_theme == "light" else "#005A9E" # Darker press state
        self.draw_button()
        if self.command:
            self.command()

    def on_release(self, event=None):
        self.current_color = self.hover_color if self.is_hovered else self.base_color
        self.draw_button()

    def update_colors(self):
        """Call this when theme changes."""
        self.base_color = COLOR_PRIMARY
        self.hover_color = COLOR_PRIMARY_HOVER
        self.current_color = self.base_color
        self.draw_button()

def setup_theme(root, is_dark=False):
    """Initialize the root window with the selected theme."""
    global _current_theme
    _current_theme = "dark" if is_dark else "light"
    update_theme_colors()
    
    root.configure(bg=COLOR_APP_BG)
    
    # Configure ttk styles to match our custom colors as a fallback
    style = ttk.Style()
    style.theme_use('clam') # Use a neutral base
    
    # Common configurations
    style.configure(".", background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN, font=FONT_REGULAR)
    style.configure("TFrame", background=COLOR_APP_BG)
    style.configure("TLabel", background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN, font=FONT_REGULAR)
    style.configure("Title.TLabel", font=FONT_HEADING, foreground=COLOR_TEXT_MAIN)
    style.configure("Subtitle.TLabel", font=FONT_SUBHEADING, foreground=COLOR_TEXT_MUTED)
    
    # Card Style
    style.configure("Card.TFrame", background=COLOR_CARD_BG)
    style.map("Card.TFrame", background=[('!active', COLOR_CARD_BG)])
    
    # Entry Style
    style.configure("TEntry", fieldbackground=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN, bordercolor=COLOR_BORDER, focuscolor=COLOR_PRIMARY)
    
    # Treeview Style
    style.configure("Treeview", background=COLOR_CARD_BG, fieldbackground=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN, rowheight=30)
    style.configure("Treeview.Heading", background=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN, font=FONT_SUBHEADING)
    style.map("Treeview", background=[('selected', COLOR_PRIMARY)], foreground=[('selected', '#FFFFFF')])

def toggle_theme(root):
    """Switch between light and dark mode and update all widgets."""
    global _current_theme
    _current_theme = "dark" if _current_theme == "light" else "light"
    update_theme_colors()
    
    # Re-apply theme settings
    setup_theme(root, is_dark=(_current_theme == "dark"))
    root.configure(bg=COLOR_APP_BG)
    
    # Update all custom buttons recursively
    for widget in root.winfo_children():
        update_widget_theme(widget)

def update_widget_theme(widget):
    """Recursively update colors for custom widgets."""
    if isinstance(widget, PremiumButton):
        widget.update_colors()
    elif isinstance(widget, tk.Label):
        try:
            if widget.cget('bg') == COLOR_APP_BG_LIGHT or widget.cget('bg') == COLOR_APP_BG_DARK:
                widget.configure(bg=COLOR_APP_BG, fg=COLOR_TEXT_MAIN)
        except: pass
    elif isinstance(widget, tk.Frame) or isinstance(widget, ttk.Frame):
        try:
            widget.configure(bg=COLOR_APP_BG)
        except: pass
        
    for child in widget.winfo_children():
        update_widget_theme(child)

# Legacy compatibility functions
def make_card(master, **kwargs):
    kwargs.setdefault('style', 'Card.TFrame')
    return ttk.Frame(master, **kwargs)

def make_glass_card(master, **kwargs):
    return make_card(master, **kwargs)

def styled_label(master, text, font=None, **kwargs):
    if font is None:
        font = FONT_REGULAR
    return ttk.Label(master, text=text, font=font, **kwargs)

def styled_entry(master, **kwargs):
    e = ttk.Entry(master, **kwargs)
    try:
        e.configure(font=FONT_REGULAR)
    except Exception:
        pass
    return e

def make_button(master, text, command=None, kind="primary", icon="", **kwargs):
    """Return a premium themed button - NOW USES PremiumButton by default for consistency"""
    # Use our custom PremiumButton for guaranteed professional look
    btn = PremiumButton(master, text=text, command=command, **kwargs)
    return btn

def create_divider(master, orientation="horizontal", color=None, thickness=2, **kwargs):
    if color is None:
        color = COLOR_BORDER
    if orientation == "horizontal":
        kwargs['height'] = thickness
        kwargs['bg'] = color
        return tk.Frame(master, **kwargs)
    else:
        kwargs['width'] = thickness
        kwargs['bg'] = color
        return tk.Frame(master, **kwargs)

def create_badge(master, text, kind="info"):
    colors = {
        "success": "#10B981",
        "danger": "#EF4444",
        "warning": "#F59E0B",
        "info": "#0EA5E9",
        "primary": COLOR_PRIMARY,
    }
    bg = colors.get(kind, colors['info'])
    
    frame = tk.Frame(master, bg=bg, relief='flat', borderwidth=0)
    lbl = tk.Label(frame, text=text, bg=bg, fg="#FFFFFF", font=(FONT_FAMILY, 9, "bold"), padx=8, pady=2, relief='flat')
    lbl.pack(side='left')
    return frame
