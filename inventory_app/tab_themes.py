"""
Unique UI Themes Per Tab
=========================
Each tab gets its own distinct visual identity with:
- Unique color schemes
- Custom card designs
- Tab-specific styling
- Icon-based headers
- Different layouts

No more "everything looks the same"!
"""

import customtkinter as ctk
from typing import Dict, Any, Optional


# ============================================================================
# TAB THEME CONFIGURATIONS
# ============================================================================

class TabThemes:
    """Theme configurations for each tab."""
    
    THEMES = {
        'dashboard': {
            'name': 'Dashboard',
            'primary_color': '#2196F3',      # Blue
            'secondary_color': '#1976D2',     # Darker Blue
            'accent_color': '#64B5F6',        # Light Blue
            'bg_color': '#1E1E1E',            # Dark Gray
            'card_color': '#2C2C2C',          # Medium Gray
            'text_color': '#FFFFFF',          # White
            'icon': '🏠',
            'gradient': True,
            'card_style': 'elevated',
            'header_style': 'gradient'
        },
        
        'inventory': {
            'name': 'Inventory',
            'primary_color': '#4CAF50',      # Green
            'secondary_color': '#388E3C',     # Darker Green
            'accent_color': '#81C784',        # Light Green
            'bg_color': '#1A231A',            # Dark Green-Gray
            'card_color': '#2D382D',          # Medium Green-Gray
            'text_color': '#E8F5E9',          # Light Green-White
            'icon': '📦',
            'gradient': True,
            'card_style': 'bordered',
            'header_style': 'solid'
        },
        
        'sales': {
            'name': 'Sales',
            'primary_color': '#FF9800',      # Orange
            'secondary_color': '#F57C00',     # Darker Orange
            'accent_color': '#FFB74D',        # Light Orange
            'bg_color': '#231A12',            # Dark Orange-Gray
            'card_color': '#382A1D',          # Medium Orange-Gray
            'text_color': '#FFF3E0',          # Light Orange-White
            'icon': '💰',
            'gradient': True,
            'card_style': 'elevated',
            'header_style': 'gradient'
        },
        
        'invoices': {
            'name': 'Invoices',
            'primary_color': '#9C27B0',      # Purple
            'secondary_color': '#7B1FA2',     # Darker Purple
            'accent_color': '#BA68C8',        # Light Purple
            'bg_color': '#231A23',            # Dark Purple-Gray
            'card_color': '#382D38',          # Medium Purple-Gray
            'text_color': '#F3E5F5',          # Light Purple-White
            'icon': '📄',
            'gradient': False,
            'card_style': 'document',
            'header_style': 'solid'
        },
        
        'leases': {
            'name': 'Leases',
            'primary_color': '#00BCD4',      # Cyan
            'secondary_color': '#0097A7',     # Darker Cyan
            'accent_color': '#4DD0E1',        # Light Cyan
            'bg_color': '#1A2326',            # Dark Cyan-Gray
            'card_color': '#2D383A',          # Medium Cyan-Gray
            'text_color': '#E0F7FA',          # Light Cyan-White
            'icon': '🎯',
            'gradient': True,
            'card_style': 'elevated',
            'header_style': 'gradient'
        },
        
        'suppliers': {
            'name': 'Suppliers',
            'primary_color': '#795548',      # Brown
            'secondary_color': '#5D4037',     # Darker Brown
            'accent_color': '#A1887F',        # Light Brown
            'bg_color': '#231D1A',            # Dark Brown-Gray
            'card_color': '#38302A',          # Medium Brown-Gray
            'text_color': '#EFEBE9',          # Light Brown-White
            'icon': '🏭',
            'gradient': False,
            'card_style': 'bordered',
            'header_style': 'solid'
        },
        
        'reports': {
            'name': 'Reports',
            'primary_color': '#607D8B',      # Blue Gray
            'secondary_color': '#455A64',     # Darker Blue Gray
            'accent_color': '#90A4AE',        # Light Blue Gray
            'bg_color': '#1A2023',            # Dark Blue-Gray
            'card_color': '#2D3538',          # Medium Blue-Gray
            'text_color': '#ECEFF1',          # Light Blue-White
            'icon': '📊',
            'gradient': True,
            'card_style': 'chart',
            'header_style': 'gradient'
        },
        
        'settings': {
            'name': 'Settings',
            'primary_color': '#9E9E9E',      # Gray
            'secondary_color': '#757575',     # Darker Gray
            'accent_color': '#BDBDBD',        # Light Gray
            'bg_color': '#1A1A1A',            # Dark Gray
            'card_color': '#2C2C2C',          # Medium Gray
            'text_color': '#FAFAFA',          # White
            'icon': '⚙️',
            'gradient': False,
            'card_style': 'simple',
            'header_style': 'solid'
        }
    }
    
    @classmethod
    def get_theme(cls, tab_name: str) -> Dict:
        """Get theme configuration for specific tab."""
        return cls.THEMES.get(tab_name, cls.THEMES['dashboard'])
    
    @classmethod
    def apply_theme_to_frame(cls, frame, tab_name: str):
        """Apply theme to a frame."""
        theme = cls.get_theme(tab_name)
        
        if hasattr(frame, 'configure'):
            frame.configure(fg_color=theme['bg_color'])
    
    @classmethod
    def create_themed_card(cls, parent, tab_name: str, **kwargs) -> ctk.CTkFrame:
        """Create a themed card/frame."""
        theme = cls.get_theme(tab_name)
        
        if theme['card_style'] == 'elevated':
            # Elevated card with shadow effect
            card = ctk.CTkFrame(
                parent,
                fg_color=theme['card_color'],
                corner_radius=15,
                border_width=0,
                **kwargs
            )
        elif theme['card_style'] == 'bordered':
            # Bordered card
            card = ctk.CTkFrame(
                parent,
                fg_color=theme['card_color'],
                corner_radius=10,
                border_width=2,
                border_color=theme['primary_color'],
                **kwargs
            )
        elif theme['card_style'] == 'document':
            # Document-style card (like paper)
            card = ctk.CTkFrame(
                parent,
                fg_color='#FFFFFF',
                corner_radius=5,
                border_width=1,
                border_color='#CCCCCC',
                **kwargs
            )
        else:
            # Simple card
            card = ctk.CTkFrame(
                parent,
                fg_color=theme['card_color'],
                corner_radius=8,
                **kwargs
            )
        
        return card
    
    @classmethod
    def create_themed_button(cls, parent, tab_name: str, **kwargs) -> ctk.CTkButton:
        """Create a themed button."""
        theme = cls.get_theme(tab_name)
        
        button = ctk.CTkButton(
            parent,
            fg_color=theme['primary_color'],
            hover_color=theme['secondary_color'],
            corner_radius=8,
            **kwargs
        )
        
        return button
    
    @classmethod
    def create_themed_header(cls, parent, tab_name: str, title: str, 
                             subtitle: str = '') -> ctk.CTkFrame:
        """Create a themed header for tab."""
        theme = cls.get_theme(tab_name)
        
        header = ctk.CTkFrame(parent, fg_color=theme['card_color'], corner_radius=10)
        
        # Icon and title
        icon_label = ctk.CTkLabel(
            header,
            text=theme['icon'],
            font=ctk.CTkFont(size=36)
        )
        icon_label.pack(side='left', padx=15, pady=15)
        
        # Title text
        title_frame = ctk.CTkFrame(header, fg_color='transparent')
        title_frame.pack(side='left', fill='both', expand=True, padx=10, pady=15)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=theme['primary_color']
        )
        title_label.pack(anchor='w')
        
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                title_frame,
                text=subtitle,
                font=ctk.CTkFont(size=12),
                text_color=theme['accent_color']
            )
            subtitle_label.pack(anchor='w')
        
        return header
    
    @classmethod
    def create_stat_card(cls, parent, tab_name: str, 
                         title: str, value: str,
                         icon: str = '📊') -> ctk.CTkFrame:
        """Create a statistics card."""
        theme = cls.get_theme(tab_name)
        
        card = cls.create_themed_card(parent, tab_name, width=200, height=120)
        
        # Icon
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=32)
        )
        icon_label.pack(pady=(15, 5))
        
        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight='bold'),
            text_color=theme['primary_color']
        )
        value_label.pack()
        
        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=theme['text_color']
        )
        title_label.pack(pady=(0, 10))
        
        return card


# ============================================================================
# TAB-SPECIFIC CONTENT BUILDERS
# ============================================================================

class TabContentBuilder:
    """Builds tab-specific content with unique styling."""
    
    @staticmethod
    def build_dashboard_content(parent) -> ctk.CTkFrame:
        """Build dashboard-specific content."""
        theme = TabThemes.get_theme('dashboard')
        
        container = ctk.CTkFrame(parent, fg_color=theme['bg_color'])
        
        # Welcome header
        header = TabThemes.create_themed_header(
            container,
            'dashboard',
            'Dashboard',
            'Overview of your business'
        )
        header.pack(fill='x', padx=20, pady=20)
        
        # Stats grid
        stats_frame = ctk.CTkFrame(container, fg_color='transparent')
        stats_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create stat cards
        stats = [
            ('Total Products', '0', '📦'),
            ('Total Sales', '$0', '💰'),
            ('Low Stock', '0', '⚠️'),
            ('Pending Orders', '0', '📋')
        ]
        
        for i, (title, value, icon) in enumerate(stats):
            row = i // 2
            col = i % 2
            
            card = TabThemes.create_stat_card(
                stats_frame,
                'dashboard',
                title,
                value,
                icon
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_rowconfigure(0, weight=1)
        
        return container
    
    @staticmethod
    def build_inventory_content(parent) -> ctk.CTkFrame:
        """Build inventory-specific content."""
        theme = TabThemes.get_theme('inventory')
        
        container = ctk.CTkFrame(parent, fg_color=theme['bg_color'])
        
        # Header
        header = TabThemes.create_themed_header(
            container,
            'inventory',
            'Inventory Management',
            'Track and manage your products'
        )
        header.pack(fill='x', padx=20, pady=20)
        
        # Action buttons
        actions = ctk.CTkFrame(container, fg_color='transparent')
        actions.pack(fill='x', padx=20, pady=10)
        
        add_btn = TabThemes.create_themed_button(
            actions,
            'inventory',
            text='➕ Add Product',
            width=150,
            height=40
        )
        add_btn.pack(side='left', padx=5)
        
        scan_btn = TabThemes.create_themed_button(
            actions,
            'inventory',
            text='📷 Scan Barcode',
            width=150,
            height=40
        )
        scan_btn.pack(side='left', padx=5)
        
        export_btn = TabThemes.create_themed_button(
            actions,
            'inventory',
            text='📊 Export',
            width=150,
            height=40
        )
        export_btn.pack(side='left', padx=5)
        
        # Placeholder for product table
        table_placeholder = ctk.CTkLabel(
            container,
            text='📦 Product Table Will Appear Here\n\n(Connect to database to load products)',
            font=ctk.CTkFont(size=14),
            text_color=theme['accent_color']
        )
        table_placeholder.pack(fill='both', expand=True, padx=20, pady=20)
        
        return container
    
    @staticmethod
    def build_sales_content(parent) -> ctk.CTkFrame:
        """Build sales-specific content."""
        theme = TabThemes.get_theme('sales')
        
        container = ctk.CTkFrame(parent, fg_color=theme['bg_color'])
        
        # Header
        header = TabThemes.create_themed_header(
            container,
            'sales',
            'Sales & POS',
            'Process sales and transactions'
        )
        header.pack(fill='x', padx=20, pady=20)
        
        # Two-column layout
        content_frame = ctk.CTkFrame(container, fg_color='transparent')
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Left: Product search/cart
        left_frame = TabThemes.create_themed_card(content_frame, 'sales')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        search_label = ctk.CTkLabel(
            left_frame,
            text='🔍 Search Products',
            font=ctk.CTkFont(size=16, weight='bold'),
            text_color=theme['text_color']
        )
        search_label.pack(padx=15, pady=15, anchor='w')
        
        search_entry = ctk.CTkEntry(left_frame, placeholder_text='Enter product name or barcode...')
        search_entry.pack(fill='x', padx=15, pady=10)
        
        cart_label = ctk.CTkLabel(
            left_frame,
            text='🛒 Shopping Cart',
            font=ctk.CTkFont(size=14, weight='bold'),
            text_color=theme['text_color']
        )
        cart_label.pack(padx=15, pady=(20, 10), anchor='w')
        
        # Right: Payment
        right_frame = TabThemes.create_themed_card(content_frame, 'sales', width=300)
        right_frame.pack(side='right', fill='y', padx=(10, 0))
        
        payment_label = ctk.CTkLabel(
            right_frame,
            text='💳 Payment',
            font=ctk.CTkFont(size=18, weight='bold'),
            text_color=theme['text_color']
        )
        payment_label.pack(padx=15, pady=15, anchor='w')
        
        total_label = ctk.CTkLabel(
            right_frame,
            text='Total: $0.00',
            font=ctk.CTkFont(size=24, weight='bold'),
            text_color=theme['primary_color']
        )
        total_label.pack(padx=15, pady=20, anchor='w')
        
        checkout_btn = TabThemes.create_themed_button(
            right_frame,
            'sales',
            text='✅ Checkout',
            width=200,
            height=50,
            font=ctk.CTkFont(size=16, weight='bold')
        )
        checkout_btn.pack(pady=20)
        
        return container
    
    @staticmethod
    def build_invoices_content(parent) -> ctk.CTkFrame:
        """Build invoices-specific content."""
        theme = TabThemes.get_theme('invoices')
        
        container = ctk.CTkFrame(parent, fg_color=theme['bg_color'])
        
        # Header
        header = TabThemes.create_themed_header(
            container,
            'invoices',
            'Invoicing',
            'Create and manage invoices'
        )
        header.pack(fill='x', padx=20, pady=20)
        
        # Invoice list placeholder
        invoice_list = TabThemes.create_themed_card(container, 'invoices')
        invoice_list.pack(fill='both', expand=True, padx=20, pady=10)
        
        placeholder = ctk.CTkLabel(
            invoice_list,
            text='📄 Invoices\n\nNo invoices yet.\nClick "Create Invoice" to start.',
            font=ctk.CTkFont(size=14),
            text_color=theme['accent_color']
        )
        placeholder.pack(pady=50)
        
        return container
    
    @staticmethod
    def build_leases_content(parent) -> ctk.CTkFrame:
        """Build leases-specific content."""
        theme = TabThemes.get_theme('leases')
        
        container = ctk.CTkFrame(parent, fg_color=theme['bg_color'])
        
        # Header
        header = TabThemes.create_themed_header(
            container,
            'leases',
            'Lease & Rental',
            'Manage lease agreements and payments'
        )
        header.pack(fill='x', padx=20, pady=20)
        
        # Lease stats
        stats_frame = ctk.CTkFrame(container, fg_color='transparent')
        stats_frame.pack(fill='x', padx=20, pady=10)
        
        lease_stats = [
            ('Active Leases', '0', '📋'),
            ('Monthly Revenue', '$0', '💰'),
            ('Collections Due', '$0', '⏰')
        ]
        
        for i, (title, value, icon) in enumerate(lease_stats):
            card = TabThemes.create_stat_card(
                stats_frame,
                'leases',
                title,
                value,
                icon
            )
            card.grid(row=0, column=i, padx=10, sticky='nsew')
        
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_columnconfigure(1, weight=1)
        stats_frame.grid_columnconfigure(2, weight=1)
        
        return container


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_tab_theme(tab_name: str) -> Dict:
    """Get theme for specific tab."""
    return TabThemes.get_theme(tab_name)


def apply_theme_to_tab(tab_frame, tab_name: str):
    """Apply complete theme to tab."""
    theme = TabThemes.get_theme(tab_name)
    
    # Apply background
    if hasattr(tab_frame, 'configure'):
        tab_frame.configure(fg_color=theme['bg_color'])


def create_themed_tab_content(parent, tab_name: str) -> ctk.CTkFrame:
    """Create themed content for specific tab."""
    builders = {
        'dashboard': TabContentBuilder.build_dashboard_content,
        'inventory': TabContentBuilder.build_inventory_content,
        'sales': TabContentBuilder.build_sales_content,
        'invoices': TabContentBuilder.build_invoices_content,
        'leases': TabContentBuilder.build_leases_content,
    }
    
    builder = builders.get(tab_name)
    if builder:
        return builder(parent)
    else:
        # Default content
        theme = TabThemes.get_theme(tab_name)
        container = ctk.CTkFrame(parent, fg_color=theme['bg_color'])
        
        label = ctk.CTkLabel(
            container,
            text=f"{theme['icon']} {theme['name']}\n\nContent coming soon...",
            font=ctk.CTkFont(size=18),
            text_color=theme['text_color']
        )
        label.pack(pady=50)
        
        return container


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Tab Themes - Test/Demo")
    print("="*60)
    
    # Show all themes
    print("\n🎨 Available Tab Themes:")
    for tab_name, theme in TabThemes.THEMES.items():
        print(f"\n  {theme['icon']} {theme['name']}")
        print(f"     Primary: {theme['primary_color']}")
        print(f"     Background: {theme['bg_color']}")
        print(f"     Card Style: {theme['card_style']}")
    
    print("\n" + "="*60)
    print("To see visual demo, run from main application")
    print("="*60)
