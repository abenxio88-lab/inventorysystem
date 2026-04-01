"""Centralized UI theming helper with Premium Glassmorphism Design.

Modern premium design system featuring:
- Glassmorphism effects with backdrop blur simulation
- White/Blue premium color palette
- Smooth animations and transitions
- Interlinked navigation system
- Professional typography and spacing
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
# PREMIUM COLOR PALETTE - White & Blue Theme
# ============================================
COLOR_APP_BG = "#F0F4F8"           # Soft blue-gray background
COLOR_CARD_BG = "#FFFFFF"          # Pure white cards
COLOR_PRIMARY = "#2563EB"          # Premium Royal Blue
COLOR_PRIMARY_DARK = "#1E40AF"     # Darker blue for hover
COLOR_PRIMARY_LIGHT = "#3B82F6"    # Lighter blue for accents
COLOR_SECONDARY = "#64748B"        # Slate gray secondary
COLOR_SUCCESS = "#10B981"          # Emerald green
COLOR_DANGER = "#EF4444"           # Coral red
COLOR_WARNING = "#F59E0B"          # Amber yellow
COLOR_INFO = "#0EA5E9"             # Sky blue
COLOR_TEXT_MAIN = "#1E293B"        # Slate dark text
COLOR_TEXT_MUTED = "#64748B"       # Muted slate text
COLOR_BORDER = "#E2E8F0"           # Light border
COLOR_SHADOW = "rgba(0, 0, 0, 0.1)" # Soft shadow

# Glassmorphism colors (semi-transparent)
COLOR_GLASS_BG = "rgba(255, 255, 255, 0.85)"
COLOR_GLASS_CARD = "rgba(255, 255, 255, 0.95)"
COLOR_GLASS_HOVER = "rgba(255, 255, 255, 0.7)"

# Gradient colors for premium buttons
GRADIENT_START = "#3B82F6"
GRADIENT_END = "#2563EB"

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


def setup_theme(root=None, theme_name="litera"):
    """Setup application-wide premium theme. Safe to call multiple times."""
    if USING_BOOTSTRAP:
        try:
            global STYLE
            STYLE = Style(theme=theme_name)
            logging.info("ttkbootstrap theme applied: %s", theme_name)
            if root is not None:
                try:
                    root.configure(bg=COLOR_APP_BG)
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
                root.configure(bg=COLOR_APP_BG)
            except Exception:
                pass

        # Premium Frame styling
        style.configure("TFrame", background=COLOR_APP_BG)
        
        # Premium Label styling
        style.configure("TLabel", font=DEFAULT_FONT, background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN)
        style.configure("Heading.TLabel", font=SUBHEADING_FONT, background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN)
        style.configure("Muted.TLabel", font=DEFAULT_FONT, background=COLOR_APP_BG, foreground=COLOR_TEXT_MUTED)
        
        # Premium Entry styling
        style.configure("TEntry", font=DEFAULT_FONT, padding=14, fieldbackground=COLOR_CARD_BG, 
                       foreground=COLOR_TEXT_MAIN, borderwidth=1, relief="flat")
        
        # Premium Button styling with rounded corners
        style.configure("TButton", font=FONT_BOLD, padding=14, borderwidth=0, focuscolor=COLOR_PRIMARY)
        style.configure("Primary.TButton", background=COLOR_PRIMARY, foreground="#FFFFFF")
        style.map("Primary.TButton", 
                 background=[('active', COLOR_PRIMARY_LIGHT), ('pressed', COLOR_PRIMARY_DARK)], 
                 foreground=[('!disabled', '#FFFFFF')])
        
        style.configure("Secondary.TButton", background=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN, 
                       borderwidth=1, bordercolor=COLOR_BORDER)
        style.map("Secondary.TButton", 
                 background=[('active', COLOR_APP_BG), ('pressed', COLOR_BORDER)], 
                 bordercolor=[('active', COLOR_PRIMARY), ('pressed', COLOR_SECONDARY)])
        
        style.configure("Success.TButton", background=COLOR_SUCCESS, foreground="#FFFFFF")
        style.map("Success.TButton", background=[('active', '#059669'), ('pressed', '#047857')])
        
        style.configure("Danger.TButton", background=COLOR_DANGER, foreground="#FFFFFF")
        style.map("Danger.TButton", background=[('active', '#DC2626'), ('pressed', '#B91C1C')])
        
        style.configure("Info.TButton", background=COLOR_INFO, foreground="#FFFFFF")
        style.map("Info.TButton", background=[('active', '#0284C7'), ('pressed', '#0369A1')])

        # Premium Treeview styling
        style.configure("Treeview", font=DEFAULT_FONT, rowheight=36, background=COLOR_CARD_BG, 
                       fieldbackground=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN,
                       borderwidth=0, relief="flat")
        style.configure("Treeview.Heading", font=FONT_BOLD, background=COLOR_APP_BG, 
                       foreground=COLOR_TEXT_MAIN, padding=12)
        style.map("Treeview", 
                 background=[('selected', COLOR_PRIMARY)], 
                 foreground=[('selected', '#FFFFFF')])
        
        # Premium Combobox
        style.configure("TCombobox", font=DEFAULT_FONT, padding=12, fieldbackground=COLOR_CARD_BG,
                       foreground=COLOR_TEXT_MAIN, borderwidth=1, relief="flat")
        style.configure("Combobox.PopdownFrame", background=COLOR_CARD_BG, borderwidth=1)
        
        # Premium Notebook (Tabs)
        style.configure("TNotebook", background=COLOR_APP_BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=FONT_BOLD, padding=[20, 12], background=COLOR_CARD_BG,
                       foreground=COLOR_TEXT_MUTED, borderwidth=0, focuscolor=COLOR_PRIMARY)
        style.map("TNotebook.Tab",
                 background=[('selected', COLOR_PRIMARY)],
                 foreground=[('selected', '#FFFFFF'), ('!selected', COLOR_TEXT_MUTED)],
                 expand=[('selected', [1, 1, 1, 0])])

        logging.info("Premium ttk fallback theme configured")
    except Exception:
        logging.error("Failed to configure premium ttk style", exc_info=True)


def switch_theme(theme_name):
    """Switch theme at runtime."""
    global STYLE
    if USING_BOOTSTRAP and Style is not None:
        try:
            if 'STYLE' in globals() and STYLE is not None:
                try:
                    STYLE.theme_use(theme_name)
                except Exception:
                    STYLE = Style(theme=theme_name)
            else:
                STYLE = Style(theme=theme_name)
            logging.info("Switched ttkbootstrap theme: %s", theme_name)
            return True
        except Exception:
            logging.exception("Failed to switch theme")
            return False
    return False


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
    return {
        "app_bg": COLOR_APP_BG,
        "card_bg": COLOR_CARD_BG,
        "border": COLOR_BORDER,
        "primary": COLOR_PRIMARY,
        "primary_light": COLOR_PRIMARY_LIGHT,
        "primary_dark": COLOR_PRIMARY_DARK,
        "muted": COLOR_TEXT_MUTED,
        "text": COLOR_TEXT_MAIN,
        "success": COLOR_SUCCESS,
        "danger": COLOR_DANGER,
        "warning": COLOR_WARNING,
        "info": COLOR_INFO,
        "glass_bg": COLOR_GLASS_BG,
        "shadow": SHADOW_DEFAULT,
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
    """Create a premium card with glassmorphism effect."""
    if padding_val is None:
        px = kwargs.pop("padx", 20)
        py = kwargs.pop("pady", 20)
        padding_val = (px, py)
    else:
        px = kwargs.pop("padx", 0)
        py = kwargs.pop("pady", 0)

    if USING_BOOTSTRAP and tb is not None:
        return tb.Frame(master, bootstyle="default", padding=padding_val, **kwargs)
    else:
        # Premium card with subtle border and shadow simulation
        card_frame = tk.Frame(master, bg=COLOR_CARD_BG, 
                             highlightbackground=COLOR_BORDER, 
                             highlightthickness=1,
                             padx=px, pady=py, **kwargs)
        return card_frame


def make_glass_card(master, padding_val=None, **kwargs):
    """Create a glassmorphism-style card with semi-transparent background."""
    if padding_val is None:
        px = kwargs.pop("padx", 24)
        py = kwargs.pop("pady", 24)
        padding_val = (px, py)
    else:
        px = kwargs.pop("padx", 0)
        py = kwargs.pop("pady", 0)
    
    # Glass card with lighter border for ethereal effect
    glass_frame = tk.Frame(master, bg=COLOR_CARD_BG,
                          highlightbackground="rgba(255, 255, 255, 0.5)",
                          highlightthickness=2,
                          padx=px, pady=py, **kwargs)
    return glass_frame


def create_divider(master, orientation="horizontal", **kwargs):
    """Create a premium divider line."""
    color = kwargs.pop("color", COLOR_BORDER)
    thickness = kwargs.pop("thickness", 1)
    
    if orientation == "horizontal":
        divider = tk.Frame(master, bg=color, height=thickness, **kwargs)
    else:
        divider = tk.Frame(master, bg=color, width=thickness, **kwargs)
    
    return divider


def create_badge(master, text, kind="primary", **kwargs):
    """Create a premium badge/pill component."""
    colors = {
        "primary": (COLOR_PRIMARY, "#FFFFFF"),
        "success": (COLOR_SUCCESS, "#FFFFFF"),
        "danger": (COLOR_DANGER, "#FFFFFF"),
        "warning": (COLOR_WARNING, "#FFFFFF"),
        "info": (COLOR_INFO, "#FFFFFF"),
        "secondary": (COLOR_SECONDARY, "#FFFFFF"),
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

