"""Centralized UI theming helper with Premium Glassmorphism Design (PySide6).

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
from PySide6 import QtWidgets, QtCore, QtGui

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

def get_palette():
    """Get the current theme's color palette as a dictionary.
    
    Returns color constants for the current theme (light or dark).
    """
    is_dark = _current_theme == "dark"
    
    return {
        # Background colors
        "app_bg": COLOR_APP_BG_DARK if is_dark else COLOR_APP_BG_LIGHT,
        "card_bg": COLOR_CARD_BG_DARK if is_dark else COLOR_CARD_BG_LIGHT,
        "glass_bg": COLOR_GLASS_BG_DARK if is_dark else COLOR_GLASS_BG_LIGHT,
        
        # Primary colors
        "primary": COLOR_PRIMARY_DARK if is_dark else COLOR_PRIMARY_LIGHT,
        "primary_dark": COLOR_PRIMARY_DARKER if is_dark else COLOR_PRIMARY_DARK_LIGHT,
        "primary_light": COLOR_PRIMARY_LIGHT_ACCENT,
        "secondary": COLOR_SECONDARY_DARK if is_dark else COLOR_SECONDARY_LIGHT,
        
        # Status colors
        "success": COLOR_SUCCESS_DARK if is_dark else COLOR_SUCCESS_LIGHT,
        "danger": COLOR_DANGER_DARK if is_dark else COLOR_DANGER_LIGHT,
        "warning": COLOR_WARNING_DARK if is_dark else COLOR_WARNING_LIGHT,
        "info": COLOR_INFO_DARK if is_dark else COLOR_INFO_LIGHT,
        
        # Text colors
        "text_main": COLOR_TEXT_MAIN_DARK if is_dark else COLOR_TEXT_MAIN_LIGHT,
        "text_muted": COLOR_TEXT_MUTED_DARK if is_dark else COLOR_TEXT_MUTED_LIGHT,
        
        # Border & effects
        "border": COLOR_BORDER_DARK if is_dark else COLOR_BORDER_LIGHT,
        "shadow": COLOR_SHADOW_DARK if is_dark else COLOR_SHADOW_LIGHT,
    }

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

# Color constants - using light mode values as static defaults
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

# Theme-aware color functions (use these for dynamic theme switching)
def get_COLOR_APP_BG(): return get_color('app_bg')
def get_COLOR_CARD_BG(): return get_color('card_bg')
def get_COLOR_PRIMARY(): return get_color('primary')
def get_COLOR_PRIMARY_DARK(): return get_color('primary_dark')
def get_COLOR_PRIMARY_LIGHT(): return get_color('primary_light')
def get_COLOR_SECONDARY(): return get_color('secondary')
def get_COLOR_SUCCESS(): return get_color('success')
def get_COLOR_DANGER(): return get_color('danger')
def get_COLOR_WARNING(): return get_color('warning')
def get_COLOR_INFO(): return get_color('info')
def get_COLOR_TEXT_MAIN(): return get_color('text_main')
def get_COLOR_TEXT_MUTED(): return get_color('text_muted')
def get_COLOR_BORDER(): return get_color('border')
def get_COLOR_SHADOW(): return get_color('shadow')
def get_COLOR_GLASS_BG(): return get_color('glass_bg')
def get_COLOR_GLASS_CARD(): return get_color('glass_card')
def get_COLOR_GLASS_HOVER(): return get_color('glass_hover')
def get_GRADIENT_START(): return get_color('gradient_start')
def get_GRADIENT_END(): return get_color('gradient_end')

# Typography - Qt font tuples: (family, size, weight)
FONT_FAMILY_PRIMARY = "Segoe UI Variable"
FONT_FAMILY_SECONDARY = "Segoe UI"
DEFAULT_FONT = (FONT_FAMILY_SECONDARY, 11)
HEADING_FONT = (FONT_FAMILY_PRIMARY, 24, 700)  # 700 = bold
SUBHEADING_FONT = (FONT_FAMILY_PRIMARY, 16, 700)
FONT_REGULAR = (FONT_FAMILY_SECONDARY, 11)
FONT_BOLD = (FONT_FAMILY_SECONDARY, 12, 700)
FONT_HEADING = (FONT_FAMILY_PRIMARY, 26, 700)
FONT_SMALL = (FONT_FAMILY_SECONDARY, 9)
FONT_LARGE = (FONT_FAMILY_PRIMARY, 14, 700)

# Spacing system
SPACING_XS = 4
SPACING_SMALL = 8
SPACING_DEFAULT = 16
SPACING_LARGE = 24
SPACING_XL = 32
SPACING_XXL = 48

# Border radius (for QSS border-radius)
RADIUS_SMALL = 6
RADIUS_DEFAULT = 10
RADIUS_LARGE = 16
RADIUS_XL = 24

# Shadow definitions (QSS box-shadow)
SHADOW_SMALL = "0 1px 3px rgba(0,0,0,0.08)"
SHADOW_DEFAULT = "0 4px 12px rgba(0,0,0,0.1)"
SHADOW_LARGE = "0 8px 24px rgba(0,0,0,0.12)"
SHADOW_GLASS = "0 8px 32px rgba(31, 38, 135, 0.15)"


def _build_stylesheet(is_dark):
    """Build a complete QSS stylesheet string for the theme."""
    # Resolve colors
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
    glass_bg = get_color('glass_bg')
    glass_card = get_color('glass_card')
    glass_hover = get_color('glass_hover')

    font_family = FONT_FAMILY_SECONDARY
    font_size = 11

    return f"""
    /* ===== Application ===== */
    QMainWindow, QDialog, QWidget {{
        background-color: {app_bg};
        color: {text_main};
        font-family: "{font_family}";
        font-size: {font_size}px;
    }}

    /* ===== Frames / Containers ===== */
    QFrame {{
        background-color: {app_bg};
        border: none;
    }}

    /* ===== Labels ===== */
    QLabel {{
        background-color: transparent;
        color: {text_main};
        font-family: "{font_family}";
        font-size: {font_size}px;
    }}
    QLabel#heading {{
        font-family: "{FONT_FAMILY_PRIMARY}";
        font-size: 26px;
        font-weight: 700;
        color: {text_main};
    }}
    QLabel#subheading {{
        font-family: "{FONT_FAMILY_PRIMARY}";
        font-size: 16px;
        font-weight: 700;
        color: {text_main};
    }}
    QLabel#muted {{
        color: {text_muted};
    }}

    /* ===== LineEdits / Entries ===== */
    QLineEdit {{
        background-color: {card_bg};
        color: {text_main};
        border: 1px solid {border};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 10px 14px;
        font-family: "{font_family}";
        font-size: {font_size}px;
        selection-background-color: {primary};
    }}
    QLineEdit:focus {{
        border: 2px solid {primary};
    }}
    QLineEdit:disabled {{
        background-color: {glass_bg};
        color: {text_muted};
    }}

    /* ===== Buttons ===== */
    QPushButton {{
        background-color: {primary};
        color: #FFFFFF;
        border: none;
        border-radius: {RADIUS_DEFAULT}px;
        padding: 10px 20px;
        font-family: "{font_family}";
        font-size: 12px;
        font-weight: 700;
    }}
    QPushButton:hover {{
        background-color: {primary_light};
    }}
    QPushButton:pressed {{
        background-color: {primary_dark};
    }}
    QPushButton:disabled {{
        background-color: {border};
        color: {text_muted};
    }}

    QPushButton#secondary {{
        background-color: {card_bg};
        color: {text_main};
        border: 1px solid {border};
    }}
    QPushButton#secondary:hover {{
        border-color: {primary};
        background-color: {app_bg};
    }}
    QPushButton#secondary:pressed {{
        border-color: {secondary};
        background-color: {border};
    }}

    QPushButton#success {{
        background-color: {success};
        color: #FFFFFF;
    }}
    QPushButton#success:hover {{
        background-color: #059669;
    }}
    QPushButton#success:pressed {{
        background-color: #047857;
    }}

    QPushButton#danger {{
        background-color: {danger};
        color: #FFFFFF;
    }}
    QPushButton#danger:hover {{
        background-color: #DC2626;
    }}
    QPushButton#danger:pressed {{
        background-color: #B91C1C;
    }}

    QPushButton#info {{
        background-color: {info};
        color: #FFFFFF;
    }}
    QPushButton#info:hover {{
        background-color: #0284C7;
    }}
    QPushButton#info:pressed {{
        background-color: #0369A1;
    }}

    QPushButton#warning {{
        background-color: {get_color('warning')};
        color: #FFFFFF;
    }}

    /* ===== ComboBox ===== */
    QComboBox {{
        background-color: {card_bg};
        color: {text_main};
        border: 1px solid {border};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 12px;
        font-family: "{font_family}";
        font-size: {font_size}px;
    }}
    QComboBox:hover {{
        border-color: {primary};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {card_bg};
        color: {text_main};
        border: 1px solid {border};
        selection-background-color: {primary};
        selection-color: #FFFFFF;
    }}

    /* ===== TreeView / Table ===== */
    QTreeView, QTableView {{
        background-color: {card_bg};
        color: {text_main};
        gridline-color: {border};
        border: 1px solid {border};
        border-radius: {RADIUS_DEFAULT}px;
        font-family: "{font_family}";
        font-size: {font_size}px;
    }}
    QTreeView::item, QTableView::item {{
        padding: 8px;
    }}
    QTreeView::item:selected, QTableView::item:selected {{
        background-color: {primary};
        color: #FFFFFF;
    }}
    QHeaderView::section {{
        background-color: {app_bg};
        color: {text_main};
        font-weight: 700;
        padding: 10px 12px;
        border: none;
        border-bottom: 2px solid {border};
        font-family: "{font_family}";
        font-size: {font_size}px;
    }}

    /* ===== TabWidget ===== */
    QTabWidget::pane {{
        border: none;
        background-color: {app_bg};
    }}
    QTabBar::tab {{
        background-color: {card_bg};
        color: {text_muted};
        padding: 10px 20px;
        border: none;
        border-bottom: 3px solid transparent;
        font-family: "{font_family}";
        font-size: 14px;
        font-weight: 700;
        margin-right: 4px;
    }}
    QTabBar::tab:hover {{
        color: {text_main};
    }}
    QTabBar::tab:selected {{
        background-color: {primary};
        color: #FFFFFF;
        border-bottom: 3px solid {primary_dark};
    }}

    /* ===== ScrollBar ===== */
    QScrollBar:vertical {{
        background-color: {app_bg};
        width: 10px;
        border-radius: 5px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {border};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {text_muted};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {app_bg};
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {border};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {text_muted};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ===== CheckBox / RadioButton ===== */
    QCheckBox, QRadioButton {{
        color: {text_main};
        spacing: 8px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {border};
        border-radius: 4px;
        background-color: {card_bg};
    }}
    QCheckBox::indicator:checked {{
        background-color: {primary};
        border-color: {primary};
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    QRadioButton::indicator:checked {{
        background-color: {primary};
        border-color: {primary};
    }}

    /* ===== SpinBox / DoubleSpinBox ===== */
    QSpinBox, QDoubleSpinBox {{
        background-color: {card_bg};
        color: {text_main};
        border: 1px solid {border};
        border-radius: {RADIUS_DEFAULT}px;
        padding: 8px 12px;
        font-family: "{font_family}";
        font-size: {font_size}px;
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {primary};
    }}

    /* ===== ToolTip ===== */
    QToolTip {{
        background-color: {card_bg};
        color: {text_main};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 6px 10px;
    }}

    /* ===== Separator / Line ===== */
    QFrame[frameShape="4"], QFrame[frameShape="5"] {{
        background-color: {border};
    }}

    /* ===== Glassmorphism Cards ===== */
    QFrame#glass_card {{
        background-color: {glass_card};
        border: 1px solid {border};
        border-radius: {RADIUS_LARGE}px;
    }}
    QFrame#card {{
        background-color: {card_bg};
        border: 1px solid {border};
        border-radius: {RADIUS_DEFAULT}px;
    }}

    /* ===== Status Badge ===== */
    QLabel#badge {{
        background-color: {primary};
        color: #FFFFFF;
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 9px;
        font-weight: 700;
    }}
    """


def setup_theme(root=None, theme_name="litera", is_dark=False):
    """Setup application-wide premium theme. Safe to call multiple times.

    Args:
        root: The main window (QMainWindow or QWidget)
        theme_name: Ignored in PySide6 (kept for API compatibility)
        is_dark: Boolean to enable dark mode
    """
    global _current_theme

    # Update theme state
    if is_dark is True:
        _current_theme = "dark"
    elif is_dark is False:
        _current_theme = "light"

    active_is_dark = (_current_theme == "dark")

    # Build and apply QSS stylesheet
    stylesheet = _build_stylesheet(active_is_dark)

    app = QtWidgets.QApplication.instance()
    if app is not None:
        app.setStyleSheet(stylesheet)
        logging.info("QSS stylesheet applied (dark=%s)", active_is_dark)

    # Set root window palette/background if provided
    if root is not None:
        app_bg = get_color('app_bg')
        palette = root.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(app_bg))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(get_color('text_main')))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(get_color('card_bg')))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(get_color('text_main')))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(get_color('primary')))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor("#FFFFFF"))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(get_color('primary')))
        palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#FFFFFF"))
        root.setPalette(palette)
        root.setAutoFillBackground(True)


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

    # Update root window palette
    if root is not None:
        app_bg = get_color('app_bg')
        palette = root.palette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(app_bg))
        root.setPalette(palette)

        # Re-apply theme styles
        setup_theme(root=root, is_dark=is_dark)

    logging.info("Theme toggled to: %s", "dark" if is_dark else "light")
    return is_dark


def detect_system_theme():
    """Detect system dark/light mode using Qt palette."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        return "light"
    palette = app.palette()
    window_text = palette.color(QtGui.QPalette.WindowText)
    # If text is lighter than background, system is likely dark
    window_bg = palette.color(QtGui.QPalette.Window)
    return "dark" if window_text.lightness() > window_bg.lightness() else "light"


def _make_font(font_tuple):
    """Convert a font tuple (family, size, weight) to QtGui.QFont."""
    if isinstance(font_tuple, tuple) and len(font_tuple) >= 2:
        family = font_tuple[0]
        size = font_tuple[1]
        weight = font_tuple[2] if len(font_tuple) > 2 else 400  # 400 = normal
        font = QtGui.QFont(family, size)
        font.setBold(weight >= 700)
        return font
    return QtGui.QFont()


def styled_label(parent, text="", kind="regular", **kwargs):
    """Create a QLabel with premium theme fonts applied."""
    lbl = QtWidgets.QLabel(text, parent, **kwargs)

    # Determine font based on kind
    if kind == "heading":
        font = FONT_HEADING
        lbl.setObjectName("heading")
    elif kind == "subheading":
        font = SUBHEADING_FONT
        lbl.setObjectName("subheading")
    elif kind == "large":
        font = FONT_LARGE
    elif kind == "bold":
        font = FONT_BOLD
    elif kind == "small":
        font = FONT_SMALL
    elif kind == "muted":
        font = FONT_REGULAR
        lbl.setObjectName("muted")
    else:
        font = FONT_REGULAR

    lbl.setFont(_make_font(font))
    return lbl


def styled_entry(parent, text="", **kwargs):
    """Create a QLineEdit with premium theme styling."""
    entry = QtWidgets.QLineEdit(parent, **kwargs)
    entry.setText(text)
    entry.setFont(_make_font(FONT_REGULAR))
    return entry


def make_button(parent, text="", slot=None, kind="primary", icon=None, **kwargs):
    """Create a premium themed button with optional icon."""
    btn = QtWidgets.QPushButton(text, parent, **kwargs)

    # Apply object name for QSS targeting
    kind_map = {
        "primary": "",
        "success": "success",
        "danger": "danger",
        "secondary": "secondary",
        "info": "info",
        "warning": "warning",
        "card": "success",
    }
    obj_name = kind_map.get(kind, "")
    if obj_name:
        btn.setObjectName(obj_name)

    if icon is not None:
        if isinstance(icon, QtGui.QIcon):
            btn.setIcon(icon)
        elif isinstance(icon, str):
            btn.setIcon(QtGui.QIcon(icon))

    if slot is not None:
        btn.clicked.connect(slot)

    btn.setFont(_make_font(FONT_BOLD))
    return btn


def make_card(parent, padding=None, elevation="default", **kwargs):
    """Create a premium card frame with glassmorphism effect."""
    card = QtWidgets.QFrame(parent, **kwargs)
    card.setObjectName("card")
    card.setFrameShape(QtWidgets.QFrame.StyledPanel)

    if padding is not None:
        if isinstance(padding, int):
            card.setContentsMargins(padding, padding, padding, padding)
        elif isinstance(padding, (list, tuple)) and len(padding) == 4:
            card.setContentsMargins(*padding)
        elif isinstance(padding, (list, tuple)) and len(padding) == 2:
            card.setContentsMargins(padding[0], padding[1], padding[0], padding[1])

    return card


def make_glass_card(parent, padding=None, **kwargs):
    """Create a glassmorphism-style card with semi-transparent background."""
    card = QtWidgets.QFrame(parent, **kwargs)
    card.setObjectName("glass_card")
    card.setFrameShape(QtWidgets.QFrame.StyledPanel)

    if padding is not None:
        if isinstance(padding, int):
            card.setContentsMargins(padding, padding, padding, padding)
        elif isinstance(padding, (list, tuple)) and len(padding) == 4:
            card.setContentsMargins(*padding)
        elif isinstance(padding, (list, tuple)) and len(padding) == 2:
            card.setContentsMargins(padding[0], padding[1], padding[0], padding[1])

    return card


def create_divider(parent, orientation="horizontal", **kwargs):
    """Create a premium divider line."""
    if orientation == "horizontal":
        line = QtWidgets.QFrame(parent, **kwargs)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
    else:
        line = QtWidgets.QFrame(parent, **kwargs)
        line.setFrameShape(QtWidgets.QFrame.VLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

    return line


def create_badge(parent, text, kind="primary", **kwargs):
    """Create a premium badge/pill component."""
    badge = QtWidgets.QLabel(text, parent, **kwargs)
    badge.setObjectName("badge")
    badge.setFont(_make_font(FONT_SMALL))
    badge.setAlignment(QtCore.Qt.AlignCenter)

    # Set inline style for badge color
    colors = {
        "primary": get_color('primary'),
        "success": get_color('success'),
        "danger": get_color('danger'),
        "warning": get_color('warning'),
        "info": get_color('info'),
        "secondary": get_color('secondary'),
    }
    bg_color = colors.get(kind, colors["primary"])
    badge.setStyleSheet(f"""
        QLabel {{
            background-color: {bg_color};
            color: #FFFFFF;
            border-radius: 12px;
            padding: 4px 12px;
            font-size: 9px;
            font-weight: 700;
        }}
    """)

    return badge


def create_status_badge(parent, text, icon="", color=None, **kwargs):
    """Create a more descriptive status badge with an icon and custom color."""
    bg = color if color else get_color('primary')
    display_text = f"{icon} {text}" if icon else text

    badge = QtWidgets.QLabel(display_text, parent, **kwargs)
    badge.setFont(_make_font(FONT_BOLD))
    badge.setAlignment(QtCore.Qt.AlignCenter)
    badge.setStyleSheet(f"""
        QLabel {{
            background-color: {bg};
            color: #FFFFFF;
            border-radius: 12px;
            padding: 6px 15px;
        }}
    """)

    return badge


def create_table(parent, columns, **kwargs):
    """Create a premium themed table/tree view.

    Args:
        parent: Parent widget
        columns: List of column header strings
        **kwargs: Additional kwargs passed to QTreeView

    Returns:
        QTreeView with model configured
    """
    view = QtWidgets.QTreeView(parent, **kwargs)
    view.setUniformRowHeights(True)
    view.setAlternatingRowColors(True)
    view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
    view.setSortingEnabled(True)
    view.setFont(_make_font(FONT_REGULAR))

    # Set header labels
    model = QtGui.QStandardItemModel(0, len(columns), parent)
    model.setHorizontalHeaderLabels(columns)
    view.setModel(model)

    # Resize header to fit
    header = view.header()
    header.setStretchLastSection(True)
    header.setMinimumSectionSize(80)

    return view


def animate_hover(widget, on_enter, on_leave):
    """Add hover animation to a widget using Qt event filters.

    Args:
        widget: The Qt widget to add hover effects to
        on_enter: Callable to invoke on hover enter
        on_leave: Callable to invoke on hover leave
    """
    widget.setMouseTracking(True)

    original_enter = widget.enterEvent
    original_leave = widget.leaveEvent

    def new_enter(event):
        on_enter()
        if callable(original_enter):
            original_enter(event)

    def new_leave(event):
        on_leave()
        if callable(original_leave):
            original_leave(event)

    widget.enterEvent = new_enter
    widget.leaveEvent = new_leave


def apply_property(widget, prop_name, value):
    """Set a Qt dynamic property on a widget and update style."""
    widget.setProperty(prop_name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


# ============================================
# STANDARD BUTTON WIDTHS FOR CONSISTENCY
# ============================================
# Qt uses fixed widths in pixels rather than character widths
BTN_WIDTH = {
    'xs': 32,      # Extra small - icons, close buttons
    'sm': 80,      # Small - secondary actions
    'md': 120,     # Medium - standard buttons
    'lg': 160,     # Large - primary actions
    'xl': 200,     # Extra large - prominent actions
    'action': 130, # Standard action button
    'dialog': 120, # Dialog buttons (Cancel/Save/etc)
}


# ============================================
# BACKWARDS COMPATIBILITY ALIASES
# ============================================
def label(parent, text="", **kwargs):
    return styled_label(parent, text, **kwargs)


def entry(parent, text="", **kwargs):
    return styled_entry(parent, text, **kwargs)


def frame(parent, **kwargs):
    return make_card(parent, **kwargs)


def combobox(parent, items=None, **kwargs):
    """Create a styled QComboBox."""
    cb = QtWidgets.QComboBox(parent, **kwargs)
    cb.setFont(_make_font(FONT_REGULAR))
    if items is not None:
        cb.addItems(items)
    return cb


def treeview(parent, **kwargs):
    """Create a styled QTreeView."""
    tv = QtWidgets.QTreeView(parent, **kwargs)
    tv.setFont(_make_font(FONT_REGULAR))
    tv.setUniformRowHeights(True)
    return tv
