"""Centralized UI theming helper.

Attempts to use `ttkbootstrap` for a modern look. If unavailable,
falls back to standard `ttk` with improved styles.

Provides `setup_theme()` to be called once at startup and
`make_button()` helper to create themed buttons.
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

# Light theme palette (Litera-inspired)
COLOR_APP_BG = "#F8F9FA"        # Lightest gray
COLOR_CARD_BG = "#FFFFFF"       # White
COLOR_PRIMARY = "#2C3E50"       # Dark blue (for accents)
COLOR_SUCCESS = "#28A745"       # Green
COLOR_DANGER = "#DC3545"        # Red
COLOR_WARNING = "#FFC107"       # Yellow
COLOR_INFO = "#17A2B8"          # Cyan
COLOR_TEXT_MAIN = "#212529"     # Dark gray (almost black)
COLOR_TEXT_MUTED = "#6C757D"    # Gray
COLOR_BORDER = "#DEE2E6"        # Light gray

DEFAULT_FONT = ("Segoe UI", 12)
HEADING_FONT = ("Segoe UI", 20, "bold")
FONT_REGULAR = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 13, "bold")
FONT_HEADING = ("Segoe UI", 22, "bold")

SPACING_SMALL = 8
SPACING_DEFAULT = 16
SPACING_LARGE = 24


def setup_theme(root=None, theme_name="cosmo"):
    """Setup application-wide theme. Safe to call multiple times.

    If a `root` Tk instance is provided and `ttkbootstrap` is available,
    initialize the `Style` with that root.
    """
    if USING_BOOTSTRAP:
        try:
            # Initialize ttkbootstrap Style using theme name.
            global STYLE
            STYLE = Style(theme=theme_name)
            logging.info("ttkbootstrap theme applied: %s", theme_name)
            # If a root is supplied, try to set its background for consistency
            if root is not None:
                try:
                    # Use a color that matches the new light theme
                    root.configure(bg=COLOR_APP_BG)
                except Exception:
                    pass
            return
        except Exception:
            logging.warning("ttkbootstrap present but failed to apply theme", exc_info=True)

    # Fallback: configure ttk styles
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

        style.configure("TFrame", background=COLOR_APP_BG)
        style.configure("TLabel", font=DEFAULT_FONT, background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN)
        style.configure("TEntry", font=DEFAULT_FONT, padding=8, fieldbackground=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN) # Ensure entry has proper colors

        # PanedWindow Sash styling
        style.configure("TPane", background=COLOR_APP_BG) # Ensure PanedWindow background is consistent
        style.configure("TPane.sash", sashthickness=8, sashrelief="raised", background=COLOR_BORDER) # Make sash thicker, raised, and visible


        # Buttons
        style.configure("TButton", font=DEFAULT_FONT, padding=10, borderwidth=0)
        
        # Mapping primary, success, etc. (Enhanced for light mode)
        style.configure("Primary.TButton", background=COLOR_PRIMARY, foreground="#ffffff") # White text on primary
        style.map("Primary.TButton", background=[('active', '#34495E'), ('pressed', '#2C3E50')], foreground=[('!disabled', '#ffffff')])

        style.configure("Success.TButton", background=COLOR_SUCCESS, foreground="#ffffff")
        style.map("Success.TButton", background=[('active', '#208734'), ('pressed', '#1B6A2B')], foreground=[('!disabled', '#ffffff')])

        style.configure("Danger.TButton", background=COLOR_DANGER, foreground="#ffffff")
        style.map("Danger.TButton", background=[('active', '#B42C3A'), ('pressed', '#9A2430')], foreground=[('!disabled', '#ffffff')])

        style.configure("Secondary.TButton", background=COLOR_TEXT_MUTED, foreground="#ffffff")
        style.map("Secondary.TButton", background=[('active', '#565E65'), ('pressed', '#494F54')], foreground=[('!disabled', '#ffffff')])

        # Treeview (Clean light appearance)
        style.configure("Treeview", font=DEFAULT_FONT, rowheight=35, background=COLOR_CARD_BG, fieldbackground=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN)
        style.configure("Treeview.Heading", font=FONT_BOLD, background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN)
        # Disable explicit mapping for selection to let ttkbootstrap handle it naturally
        # style.map("Treeview", background=[('selected', COLOR_PRIMARY)], foreground=[('selected', COLOR_APP_BG)])

        logging.info("ttk fallback theme configured")
    except Exception:
        logging.error("Failed to configure ttk style", exc_info=True)


def switch_theme(theme_name):
    """Switch theme at runtime. If ttkbootstrap is available, use it; else no-op."""
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
        "muted": COLOR_TEXT_MUTED,
        "text": COLOR_TEXT_MAIN,
        # Light-theme friendly low stock colors
        "low_stock_bg": "#FEE2E2", # Light Red
        "low_stock_fg": "#991B1B", # Dark Red
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
    """Create a ttk.Label with theme fonts applied."""
    # Prioritize 'font' from kwargs if it exists.
    font = kwargs.pop('font', None)
    
    if font is None:
        if kind == "heading":
            font = FONT_HEADING
        elif kind == "bold":
            font = FONT_BOLD
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


def make_button(master, text, command=None, kind="primary", **kwargs):
    """Return a themed button. `kind` can be 'primary', 'success', 'danger', 'secondary', 'info', 'warning'."""
    if USING_BOOTSTRAP and tb is not None:
        # Map our internal kinds to bootstrap bootstyles
        boot_map = {
            "primary": "primary",
            "success": "success",
            "danger": "danger",
            "secondary": "secondary",
            "info": "info",
            "warning": "warning",
            "card": "success" # backward compatibility
        }
        boot = boot_map.get(kind, "secondary")

        local_kw = kwargs.copy()
        font_kw = local_kw.pop("font", None)
        width_kw = local_kw.pop("width", None)

        try:
            btn = tb.Button(master, text=text, command=command, bootstyle=boot, **local_kw)
        except Exception:
            btn = tb.Button(master, text=text, command=command, bootstyle=boot)

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
        # Fallback to standard ttk.Button with custom styles
        style_map = {
            "primary": "Primary.TButton",
            "success": "Success.TButton",
            "danger": "Danger.TButton",
            "secondary": "Secondary.TButton",
            "card": "Success.TButton" # backward compatibility
        }
        style = style_map.get(kind, "TButton")
        
        local_kw = kwargs.copy()
        font_val = local_kw.pop("font", None)
        width_val = local_kw.pop("width", None)
        
        btn = ttk.Button(master, text=text, command=command, style=style, **local_kw)
        
        if width_val:
            try: btn.configure(width=width_val)
            except: pass
        # Apply font when provided for ttk fallback buttons
        if font_val:
            try:
                f = tkfont.Font(font=font_val)
                btn.configure(font=f)
            except:
                try: btn.configure(font=font_val)
                except: pass
        return btn


def make_card(master, **kwargs):
    """Create a Frame that looks like a card."""
    # Prioritize 'padding' if it's explicitly passed in kwargs
    padding_val = kwargs.pop("padding", None)
    
    px = kwargs.pop("padx", 15)
    py = kwargs.pop("pady", 15)

    if padding_val is None:
        padding_val = (px, py)

    if USING_BOOTSTRAP and tb is not None:
        # Use a light card style from ttkbootstrap for 'litera' theme
        return tb.Frame(master, bootstyle="light", padding=padding_val, **kwargs)
    else:
        # Fallback light card style
        return tk.Frame(master, bg=COLOR_CARD_BG, highlightbackground=COLOR_BORDER, highlightthickness=1, padx=px, pady=py, **kwargs)

