"""Centralized UI theming helper with Premium Glassmorphism Design.

Modern premium design system featuring:
- Glassmorphism effects with backdrop blur simulation
- White/Blue premium color palette
- Windows 11 inspired Dark Mode
- Smooth animations and transitions
- Interlinked navigation system
- Professional typography and spacing
- Runtime theme switching (Light/Dark)
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
    """Get current theme name."""
    return _current_theme

def set_current_theme(theme_name):
    """Set current theme name."""
    global _current_theme
    _current_theme = theme_name

# ============================================
# LIGHT MODE - Glassmorphism White & Blue
# ============================================
COLOR_APP_BG_LIGHT = "#F0F4F8"        # Soft blue-gray background
COLOR_CARD_BG_LIGHT = "#FFFFFF"       # Pure white cards
COLOR_PRIMARY_LIGHT = "#2563EB"       # Premium Royal Blue
COLOR_PRIMARY_DARK_LIGHT = "#1E40AF"  # Darker blue for hover
COLOR_PRIMARY_LIGHT_ACCENT = "#3B82F6" # Lighter blue for accents
COLOR_SECONDARY_LIGHT = "#64748B"     # Slate gray secondary
COLOR_SUCCESS_LIGHT = "#10B981"       # Emerald green
COLOR_DANGER_LIGHT = "#EF4444"        # Coral red
COLOR_WARNING_LIGHT = "#F59E0B"       # Amber yellow
COLOR_INFO_LIGHT = "#0EA5E9"          # Sky blue
COLOR_TEXT_MAIN_LIGHT = "#1E293B"     # Slate dark text
COLOR_TEXT_MUTED_LIGHT = "#64748B"    # Muted slate text
COLOR_BORDER_LIGHT = "#E2E8F0"        # Light border
COLOR_SHADOW_LIGHT = "rgba(0, 0, 0, 0.1)"

# Glassmorphism light
COLOR_GLASS_BG_LIGHT = "rgba(255, 255, 255, 0.85)"
COLOR_GLASS_CARD_LIGHT = "rgba(255, 255, 255, 0.95)"
COLOR_GLASS_HOVER_LIGHT = "rgba(255, 255, 255, 0.7)"

# Gradient light
GRADIENT_START_LIGHT = "#3B82F6"
GRADIENT_END_LIGHT = "#2563EB"

# ============================================
# DARK MODE - Windows 11 Mica Inspired (Deep & Rich)
# ============================================
COLOR_APP_BG_DARK = "#202020"         # Deep charcoal (Win11 base)
COLOR_CARD_BG_DARK = "#2C2C2C"        # Slightly lighter for cards
COLOR_PRIMARY_DARK = "#4CC2FF"        # Bright Cyan-Blue (Win11 accent)
COLOR_PRIMARY_DARK_HOVER = "#2DA5E9"  # Standard blue hover
COLOR_PRIMARY_DARK_ACCENT = "#0078D4" # Microsoft blue
COLOR_SECONDARY_DARK = "#A0A0A0"      # Light gray secondary
COLOR_SUCCESS_DARK = "#00E676"        # Bright green for dark
COLOR_DANGER_DARK = "#FF5252"         # Bright red for dark
COLOR_WARNING_DARK = "#FFAB40"        # Bright orange for dark
COLOR_INFO_DARK = "#40C4FF"           # Bright sky blue
COLOR_TEXT_MAIN_DARK = "#FFFFFF"      # Pure white
COLOR_TEXT_MUTED_DARK = "#CCCCCC"     # Light gray
COLOR_BORDER_DARK = "rgba(255, 255, 255, 0.08)"  # Subtle white border
COLOR_SHADOW_DARK = "rgba(0, 0, 0, 0.4)"

# Glassmorphism dark
COLOR_GLASS_BG_DARK = "rgba(44, 44, 44, 0.85)"
COLOR_GLASS_CARD_DARK = "rgba(44, 44, 44, 0.95)"
COLOR_GLASS_HOVER_DARK = "rgba(55, 55, 55, 0.7)"

# Gradient dark
GRADIENT_START_DARK = "#4CC2FF"
GRADIENT_END_DARK = "#0078D4"

# ============================================
# DYNAMIC COLOR RESOLVERS (Theme-aware)
# ============================================
def get_color(name):
    """Get color based on current theme."""
    light_colors = {
        'app_bg': COLOR_APP_BG_LIGHT,
        'card_bg': COLOR_CARD_BG_LIGHT,
        'primary': COLOR_PRIMARY_LIGHT,
        'primary_dark': COLOR_PRIMARY_DARK_LIGHT,
        'primary_light': COLOR_PRIMARY_LIGHT_ACCENT,
        'secondary': COLOR_SECONDARY_LIGHT,
        'success': COLOR_SUCCESS_LIGHT,
        'danger': COLOR_DANGER_LIGHT,
        'warning': COLOR_WARNING_LIGHT,
        'info': COLOR_INFO_LIGHT,
        'text_main': COLOR_TEXT_MAIN_LIGHT,
        'text_muted': COLOR_TEXT_MUTED_LIGHT,
        'border': COLOR_BORDER_LIGHT,
        'shadow': COLOR_SHADOW_LIGHT,
        'glass_bg': COLOR_GLASS_BG_LIGHT,
        'glass_card': COLOR_GLASS_CARD_LIGHT,
        'glass_hover': COLOR_GLASS_HOVER_LIGHT,
        'gradient_start': GRADIENT_START_LIGHT,
        'gradient_end': GRADIENT_END_LIGHT,
    }
    
    dark_colors = {
        'app_bg': COLOR_APP_BG_DARK,
        'card_bg': COLOR_CARD_BG_DARK,
        'primary': COLOR_PRIMARY_DARK,
        'primary_dark': COLOR_PRIMARY_DARK_HOVER,
        'primary_light': COLOR_PRIMARY_DARK_ACCENT,
        'secondary': COLOR_SECONDARY_DARK,
        'success': COLOR_SUCCESS_DARK,
        'danger': COLOR_DANGER_DARK,
        'warning': COLOR_WARNING_DARK,
        'info': COLOR_INFO_DARK,
        'text_main': COLOR_TEXT_MAIN_DARK,
        'text_muted': COLOR_TEXT_MUTED_DARK,
        'border': COLOR_BORDER_DARK,
        'shadow': COLOR_SHADOW_DARK,
        'glass_bg': COLOR_GLASS_BG_DARK,
        'glass_card': COLOR_GLASS_CARD_DARK,
        'glass_hover': COLOR_GLASS_HOVER_DARK,
        'gradient_start': GRADIENT_START_DARK,
        'gradient_end': GRADIENT_END_DARK,
    }
    
    if _current_theme == "dark":
        return dark_colors.get(name, dark_colors.get('app_bg'))
    return light_colors.get(name, light_colors.get('app_bg'))

# Backward compatibility aliases (resolve to current theme)
@property
def COLOR_APP_BG():
    return get_color('app_bg')
    
@property
def COLOR_CARD_BG():
    return get_color('card_bg')
    
@property
def COLOR_PRIMARY():
    return get_color('primary')
    
@property
def COLOR_PRIMARY_DARK():
    return get_color('primary_dark')
    
@property
def COLOR_PRIMARY_LIGHT():
    return get_color('primary_light')
    
@property
def COLOR_SECONDARY():
    return get_color('secondary')
    
@property
def COLOR_SUCCESS():
    return get_color('success')
    
@property
def COLOR_DANGER():
    return get_color('danger')
    
@property
def COLOR_WARNING():
    return get_color('warning')
    
@property
def COLOR_INFO():
    return get_color('info')
    
@property
def COLOR_TEXT_MAIN():
    return get_color('text_main')
    
@property
def COLOR_TEXT_MUTED():
    return get_color('text_muted')
    
@property
def COLOR_BORDER():
    return get_color('border')
    
@property
def COLOR_SHADOW():
    return get_color('shadow')
    
@property
def COLOR_GLASS_BG():
    return get_color('glass_bg')
    
@property
def COLOR_GLASS_CARD():
    return get_color('glass_card')
    
@property
def COLOR_GLASS_HOVER():
    return get_color('glass_hover')
    
@property
def GRADIENT_START():
    return get_color('gradient_start')
    
@property
def GRADIENT_END():
    return get_color('gradient_end')

# For direct access, use the light mode values as defaults (backward compat)
# Note: For dynamic theme switching, use get_color() function instead
COLOR_APP_BG = COLOR_APP_BG_LIGHT
COLOR_CARD_BG = COLOR_CARD_BG_LIGHT
COLOR_PRIMARY = COLOR_PRIMARY_LIGHT
COLOR_PRIMARY_DARK = COLOR_PRIMARY_DARK_LIGHT
COLOR_PRIMARY_LIGHT = COLOR_PRIMARY_LIGHT_ACCENT
COLOR_SECONDARY = COLOR_SECONDARY_LIGHT
COLOR_SUCCESS = COLOR_SUCCESS_LIGHT
COLOR_DANGER = COLOR_DANGER_LIGHT
COLOR_WARNING = COLOR_WARNING_LIGHT
COLOR_INFO = COLOR_INFO_LIGHT
COLOR_TEXT_MAIN = COLOR_TEXT_MAIN_LIGHT
COLOR_TEXT_MUTED = COLOR_TEXT_MUTED_LIGHT
COLOR_BORDER = COLOR_BORDER_LIGHT
COLOR_SHADOW = COLOR_SHADOW_LIGHT
COLOR_GLASS_BG = COLOR_GLASS_BG_LIGHT
COLOR_GLASS_CARD = COLOR_GLASS_CARD_LIGHT
COLOR_GLASS_HOVER = COLOR_GLASS_HOVER_LIGHT
GRADIENT_START = GRADIENT_START_LIGHT
GRADIENT_END = GRADIENT_END_LIGHT

# Typography
FONT_FAMILY_PRIMARY = "Segoe UI Variable"
FONT_FAMILY_SECONDARY = "Segoe UI"
DEFAULT_FONT = (FONT_FAMILY_SECONDARY, 11)
HEADING_FONT = (FONT_FAMILY_PRIMARY, 24, "bold")
SUBHEADING_FONT = (FONT_FAMILY_PRIMARY, 16, "bold")
FONT_REGULAR = (FONT_FAMILY_SECONDARY, 11)
FONT_BOLD = (FONT_FAMILY_SECONDARY, 12, "bold")
FONT_HEADING = (FONT_FAMILY_PRIMARY, 26, "bold")
FONT_SMALL = (FONT_FAMILY_SECONDARY, 9)
FONT_LARGE = (FONT_FAMILY_PRIMARY, 14, "bold")

# Spacing system
SPACING_XS = 4
SPACING_SMALL = 8
SPACING_DEFAULT = 16
SPACING_LARGE = 24
SPACING_XL = 32
SPACING_XXL = 48

# Border radius
RADIUS_SMALL = 6
RADIUS_DEFAULT = 10
RADIUS_LARGE = 16
RADIUS_XL = 24

# Shadow definitions
SHADOW_SMALL = "0 1px 3px rgba(0,0,0,0.08)"
SHADOW_DEFAULT = "0 4px 12px rgba(0,0,0,0.1)"
SHADOW_LARGE = "0 8px 24px rgba(0,0,0,0.12)"
SHADOW_GLASS = "0 8px 32px rgba(31, 38, 135, 0.15)"


def setup_theme(root=None, theme_name="litera", is_dark=False):
    """Setup application-wide premium theme. Safe to call multiple times.
    
    Args:
        root: The root window
        theme_name: ttkbootstrap theme name (used if bootstrap available)
        is_dark: Boolean to enable dark mode
    """
    global _current_theme
    
    # Update theme state
    if is_dark:
        _current_theme = "dark"
    else:
        _current_theme = "light"
    
    # Get current colors based on theme
    app_bg = get_color('app_bg')
    card_bg = get_color('card_bg')
    text_main = get_color('text_main')
    text_muted = get_color('text_muted')
    primary = get_color('primary')
    primary_dark = get_color('primary_dark')
    primary_light = get_color('primary_light')
    secondary = get_color('secondary')
    success = get_color('success')
    danger = get_color('danger')
    info = get_color('info')
    border = get_color('border')
    
    if USING_BOOTSTRAP:
        try:
            global STYLE
            # Use appropriate bootstrap theme based on mode
            if is_dark:
                bootstrap_theme = "cyborg"  # Dark bootstrap theme
            else:
                bootstrap_theme = theme_name if theme_name else "litera"
            
            STYLE = Style(theme=bootstrap_theme)
            logging.info("ttkbootstrap theme applied: %s (dark=%s)", bootstrap_theme, is_dark)
            if root is not None:
                try:
                    root.configure(bg=app_bg)
                except Exception:
                    pass
            return
        except Exception:
            logging.warning("ttkbootstrap present but failed to apply theme", exc_info=True)

    # Fallback: configure ttk styles with premium look
    try:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        if root is not None:
            try:
                root.configure(bg=app_bg)
            except Exception:
                pass

        # Premium Frame styling
        style.configure("TFrame", background=app_bg)
        
        # Premium Label styling
        style.configure("TLabel", font=DEFAULT_FONT, background=app_bg, foreground=text_main)
        style.configure("Heading.TLabel", font=SUBHEADING_FONT, background=app_bg, foreground=text_main)
        style.configure("Muted.TLabel", font=DEFAULT_FONT, background=app_bg, foreground=text_muted)
        
        # Premium Entry styling
        style.configure("TEntry", font=DEFAULT_FONT, padding=14, fieldbackground=card_bg, 
                       foreground=text_main, borderwidth=1, relief="flat")
        
        # Premium Button styling with rounded corners
        style.configure("TButton", font=FONT_BOLD, padding=14, borderwidth=0, focuscolor=primary)
        style.configure("Primary.TButton", background=primary, foreground="#FFFFFF")
        style.map("Primary.TButton", 
                 background=[('active', primary_light), ('pressed', primary_dark)], 
                 foreground=[('!disabled', '#FFFFFF')])
        
        style.configure("Secondary.TButton", background=card_bg, foreground=text_main, 
                       borderwidth=1, bordercolor=border)
        style.map("Secondary.TButton", 
                 background=[('active', app_bg), ('pressed', border)], 
                 bordercolor=[('active', primary), ('pressed', secondary)])
        
        style.configure("Success.TButton", background=success, foreground="#FFFFFF")
        style.map("Success.TButton", background=[('active', '#059669'), ('pressed', '#047857')])
        
        style.configure("Danger.TButton", background=danger, foreground="#FFFFFF")
        style.map("Danger.TButton", background=[('active', '#DC2626'), ('pressed', '#B91C1C')])
        
        style.configure("Info.TButton", background=info, foreground="#FFFFFF")
        style.map("Info.TButton", background=[('active', '#0284C7'), ('pressed', '#0369A1')])

        # Premium Treeview styling
        style.configure("Treeview", font=DEFAULT_FONT, rowheight=36, background=card_bg, 
                       fieldbackground=card_bg, foreground=text_main,
                       borderwidth=0, relief="flat")
        style.configure("Treeview.Heading", font=FONT_BOLD, background=app_bg, 
                       foreground=text_main, padding=12)
        style.map("Treeview", 
                 background=[('selected', primary)], 
                 foreground=[('selected', '#FFFFFF')])
        
        # Premium Combobox
        style.configure("TCombobox", font=DEFAULT_FONT, padding=12, fieldbackground=card_bg,
                       foreground=text_main, borderwidth=1, relief="flat")
        style.configure("Combobox.PopdownFrame", background=card_bg, borderwidth=1)
        
        # Premium Notebook (Tabs)
        style.configure("TNotebook", background=app_bg, borderwidth=0)
        style.configure("TNotebook.Tab", font=FONT_BOLD, padding=[20, 12], background=card_bg,
                       foreground=text_muted, borderwidth=0, focuscolor=primary)
        style.map("TNotebook.Tab",
                 background=[('selected', primary)],
                 foreground=[('selected', '#FFFFFF'), ('!selected', text_muted)],
                 expand=[('selected', [1, 1, 1, 0])])

        logging.info("Premium ttk fallback theme configured (dark=%s)", is_dark)
    except Exception:
        logging.error("Failed to configure premium ttk style", exc_info=True)


def switch_theme(is_dark=None):
    """Switch between light and dark mode at runtime.
    
    Args:
        is_dark: If True, switch to dark mode. If False, switch to light.
                 If None, toggle current mode.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global _current_theme
    
    if is_dark is None:
        # Toggle current theme
        is_dark = (_current_theme != "dark")
    
    # Update theme state
    set_current_theme("dark" if is_dark else "light")
    
    # Re-setup theme with new colors
    # Note: This requires access to the root window which should be passed by caller
    logging.info("Theme switched to: %s", "dark" if is_dark else "light")
    return True


def toggle_theme(root=None):
    """Toggle between light and dark mode and update UI.
    
    Args:
        root: The root window to update
    
    Returns:
        bool: True if switched to dark, False if switched to light
    """
    global _current_theme
    
    # Toggle
    is_dark = (_current_theme != "dark")
    _current_theme = "dark" if is_dark else "light"
    
    # Update root window background
    if root is not None:
        app_bg = get_color('app_bg')
        try:
            root.configure(bg=app_bg)
        except Exception:
            pass
        
        # Re-apply theme styles
        setup_theme(root=root, is_dark=is_dark)
    
    logging.info("Theme toggled to: %s", "dark" if is_dark else "light")
    return is_dark


def is_bootstrap():
    return USING_BOOTSTRAP


def frame(master, **kwargs):
    if USING_BOOTSTRAP and tb is not None:
        return tb.Frame(master, **kwargs)
    return ttk.Frame(master, **kwargs)


def label(master, text, kind="regular", **kwargs):
    if USING_BOOTSTRAP and tb is not None:
        boot = None
        if kind == 'heading':
            boot = 'primary'
        try:
            return tb.Label(master, text=text, bootstyle=boot, **kwargs)
        except Exception:
            pass
    return styled_label(master, text, kind=kind, **kwargs)


def entry(master, **kwargs):
    if USING_BOOTSTRAP and tb is not None:
        try:
            return tb.Entry(master, **kwargs)
        except Exception:
            pass
    return styled_entry(master, **kwargs)


def combobox(master, **kwargs):
    if USING_BOOTSTRAP and tb is not None:
        try:
            return tb.Combobox(master, **kwargs)
        except Exception:
            pass
    return ttk.Combobox(master, **kwargs)


def treeview(master, **kwargs):
    if USING_BOOTSTRAP and tb is not None:
        try:
            return tb.Treeview(master, **kwargs)
        except Exception:
            pass
    return ttk.Treeview(master, **kwargs)


def get_palette():
    """Get current theme palette (theme-aware)."""
    return {
        "app_bg": get_color('app_bg'),
        "card_bg": get_color('card_bg'),
        "border": get_color('border'),
        "primary": get_color('primary'),
        "primary_light": get_color('primary_light'),
        "primary_dark": get_color('primary_dark'),
        "muted": get_color('text_muted'),
        "text": get_color('text_main'),
        "success": get_color('success'),
        "danger": get_color('danger'),
        "warning": get_color('warning'),
        "info": get_color('info'),
        "glass_bg": get_color('glass_bg'),
        "shadow": SHADOW_DEFAULT,
        "is_dark": (_current_theme == "dark"),
    }


def center_window(win, width=None, height=None):
    try:
        win.update_idletasks()
        if width is None:
            width = win.winfo_width()
        if height is None:
            height = win.winfo_height()
        ws = win.winfo_screenwidth()
        hs = win.winfo_screenheight()
        x = (ws // 2) - (width // 2)
        y = (hs // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        pass


def styled_label(master, text, kind="regular", **kwargs):
    """Create a ttk.Label with premium theme fonts applied."""
    font = kwargs.pop('font', None)
    
    if font is None:
        if kind == "heading":
            font = FONT_HEADING
        elif kind == "subheading":
            font = SUBHEADING_FONT
        elif kind == "large":
            font = FONT_LARGE
        elif kind == "bold":
            font = FONT_BOLD
        elif kind == "small":
            font = FONT_SMALL
        else:
            font = FONT_REGULAR
    
    lbl = ttk.Label(master, text=text, font=font, **kwargs)
    return lbl


def styled_entry(master, **kwargs):
    e = ttk.Entry(master, **kwargs)
    try:
        e.configure(font=FONT_REGULAR)
    except Exception:
        pass
    return e


def make_button(master, text, command=None, kind="primary", icon="", **kwargs):
    """Return a premium themed button with optional icon."""
    if USING_BOOTSTRAP and tb is not None:
        boot_map = {
            "primary": "primary",
            "success": "success",
            "danger": "danger",
            "secondary": "secondary",
            "info": "info",
            "warning": "warning",
            "card": "success"
        }
        boot = boot_map.get(kind, "secondary")

        local_kw = kwargs.copy()
        font_kw = local_kw.pop("font", None)
        width_kw = local_kw.pop("width", None)

        btn_text = f"{icon} {text}" if icon else text
        
        try:
            btn = tb.Button(master, text=btn_text, command=command, bootstyle=boot, **local_kw)
        except Exception:
            btn = tb.Button(master, text=btn_text, command=command, bootstyle=boot)

        if font_kw:
            try:
                f = tkfont.Font(font=font_kw)
                btn.configure(font=f)
            except:
                try: btn.configure(font=font_kw)
                except: pass
        if width_kw:
            try: btn.configure(width=width_kw)
            except: pass

        return btn
    else:
        style_map = {
            "primary": "Primary.TButton",
            "success": "Success.TButton",
            "danger": "Danger.TButton",
            "secondary": "Secondary.TButton",
            "info": "Info.TButton",
            "card": "Success.TButton"
        }
        style = style_map.get(kind, "TButton")
        
        local_kw = kwargs.copy()
        font_val = local_kw.pop("font", None)
        width_val = local_kw.pop("width", None)
        
        btn_text = f"{icon} {text}" if icon else text
        btn = ttk.Button(master, text=btn_text, command=command, style=style, **local_kw)
        
        if width_val:
            try: btn.configure(width=width_val)
            except: pass
        if font_val:
            try:
                f = tkfont.Font(font=font_val)
                btn.configure(font=f)
            except:
                try: btn.configure(font=font_val)
                except: pass
        return btn


def make_card(master, padding_val=None, elevation="default", **kwargs):
    """Create a premium card with glassmorphism effect (theme-aware)."""
    if padding_val is None:
        px = kwargs.pop("padx", 20)
        py = kwargs.pop("pady", 20)
        padding_val = (px, py)
    else:
        px = kwargs.pop("padx", 0)
        py = kwargs.pop("pady", 0)

    # Get theme-aware colors
    card_bg = get_color('card_bg')
    border = get_color('border')

    if USING_BOOTSTRAP and tb is not None:
        return tb.Frame(master, bootstyle="default", padding=padding_val, **kwargs)
    else:
        # Premium card with subtle border and shadow simulation
        card_frame = tk.Frame(master, bg=card_bg, 
                             highlightbackground=border, 
                             highlightthickness=1,
                             padx=px, pady=py, **kwargs)
        return card_frame


def make_glass_card(master, padding_val=None, **kwargs):
    """Create a glassmorphism-style card with semi-transparent background (theme-aware)."""
    if padding_val is None:
        px = kwargs.pop("padx", 24)
        py = kwargs.pop("pady", 24)
        padding_val = (px, py)
    else:
        px = kwargs.pop("padx", 0)
        py = kwargs.pop("pady", 0)
    
    # Get theme-aware colors
    card_bg = get_color('card_bg')
    border = get_color('border')
    
    # Glass card with lighter border for ethereal effect
    glass_frame = tk.Frame(master, bg=card_bg,
                          highlightbackground=border,
                          highlightthickness=1,
                          padx=px, pady=py, **kwargs)
    return glass_frame


def create_divider(master, orientation="horizontal", **kwargs):
    """Create a premium divider line (theme-aware)."""
    color = kwargs.pop("color", get_color('border'))
    thickness = kwargs.pop("thickness", 1)
    
    if orientation == "horizontal":
        divider = tk.Frame(master, bg=color, height=thickness, **kwargs)
    else:
        divider = tk.Frame(master, bg=color, width=thickness, **kwargs)
    
    return divider


def create_badge(master, text, kind="primary", **kwargs):
    """Create a premium badge/pill component (theme-aware)."""
    # Theme-aware colors
    colors = {
        "primary": (get_color('primary'), "#FFFFFF"),
        "success": (get_color('success'), "#FFFFFF"),
        "danger": (get_color('danger'), "#FFFFFF"),
        "warning": (get_color('warning'), "#FFFFFF"),
        "info": (get_color('info'), "#FFFFFF"),
        "secondary": (get_color('secondary'), "#FFFFFF"),
    }
    
    bg, fg = colors.get(kind, colors["primary"])
    
    badge_frame = tk.Frame(master, bg=bg, padx=12, pady=4, **kwargs)
    label = tk.Label(badge_frame, text=text, font=FONT_SMALL, bg=bg, fg=fg, bd=0)
    label.pack()
    
    return badge_frame


def animate_hover(widget, on_enter, on_leave):
    """Add hover animation to a widget."""
    def enter_handler(e):
        on_enter()
    
    def leave_handler(e):
        on_leave()
    
    widget.bind("<Enter>", enter_handler)
    widget.bind("<Leave>", leave_handler)

