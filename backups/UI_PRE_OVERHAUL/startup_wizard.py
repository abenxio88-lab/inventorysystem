"""
Startup Wizard Module
======================
First-run company setup with industry selection and smart configuration.
Adapts the entire application based on business type.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import logging

try:
    from .database import init_database, get_db_cursor
    from .ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, FONT_HEADING, COLOR_PRIMARY, COLOR_SUCCESS
except (ImportError, ModuleNotFoundError):
    from database import init_database, get_db_cursor
    from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, FONT_HEADING, COLOR_PRIMARY, COLOR_SUCCESS


# Company type configurations with workflow adaptations
COMPANY_TYPES = {
    'lease_rental': {
        'name': 'Lease & Rental Business',
        'icon': '🎯',
        'description': 'Equipment rental, lease management, collections',
        'priority_tabs': ['dashboard', 'lease', 'collections', 'reports'],
        'hidden_tabs': ['suppliers', 'purchase_orders'],
        'features': {
            'leasing': True,
            'collections': True,
            'invoicing': True,
            'purchase_orders': False,
            'multi_location': False,
            'barcode_scanning': True,
        },
        'dashboard_widgets': ['items_leased', 'due_collections', 'revenue', 'collection_rate'],
        'quick_actions': ['create_lease', 'record_payment', 'scan_barcode', 'view_due'],
    },
    
    'electronics_retail': {
        'name': 'Electronics & Mobile Retail',
        'icon': '📱',
        'description': 'Mobile phones, computers, electronics store',
        'priority_tabs': ['dashboard', 'inventory', 'sales', 'electronics'],
        'hidden_tabs': ['lease'],
        'features': {
            'leasing': False,
            'collections': False,
            'invoicing': False,
            'purchase_orders': True,
            'multi_location': True,
            'barcode_scanning': True,
            'serial_tracking': True,
        },
        'dashboard_widgets': ['low_stock', 'today_sales', 'top_products', 'warranty_alerts'],
        'quick_actions': ['add_product', 'record_sale', 'scan_barcode', 'view_low_stock'],
    },
    
    'pharmacy': {
        'name': 'Pharmacy & Medical',
        'icon': '💊',
        'description': 'Pharmacy, medical supplies, healthcare',
        'priority_tabs': ['dashboard', 'inventory', 'sales', 'reports'],
        'hidden_tabs': ['lease', 'electronics'],
        'features': {
            'leasing': False,
            'collections': False,
            'invoicing': False,
            'purchase_orders': True,
            'multi_location': False,
            'barcode_scanning': True,
            'expiry_tracking': True,
            'batch_tracking': True,
        },
        'dashboard_widgets': ['expiring_soon', 'low_stock', 'today_sales', 'prescription_alerts'],
        'quick_actions': ['add_product', 'record_sale', 'view_expiry', 'check_stock'],
    },
    
    'general_retail': {
        'name': 'General Retail / Shop',
        'icon': '🏪',
        'description': 'Retail store, general merchandise',
        'priority_tabs': ['dashboard', 'inventory', 'sales', 'reports'],
        'hidden_tabs': ['lease', 'electronics'],
        'features': {
            'leasing': False,
            'collections': False,
            'invoicing': False,
            'purchase_orders': True,
            'multi_location': False,
            'barcode_scanning': True,
        },
        'dashboard_widgets': ['today_sales', 'low_stock', 'top_products', 'revenue'],
        'quick_actions': ['add_product', 'record_sale', 'view_stock', 'create_po'],
    },
    
    'wholesale': {
        'name': 'Wholesale & Distribution',
        'icon': '📦',
        'description': 'Wholesale trading, bulk distribution',
        'priority_tabs': ['dashboard', 'inventory', 'purchase_orders', 'sales_orders'],
        'hidden_tabs': ['lease', 'electronics'],
        'features': {
            'leasing': False,
            'collections': True,
            'invoicing': True,
            'purchase_orders': True,
            'multi_location': True,
            'barcode_scanning': True,
        },
        'dashboard_widgets': ['pending_orders', 'low_stock', 'receivables', 'shipments'],
        'quick_actions': ['create_po', 'create_sales_order', 'view_inventory', 'check_orders'],
    },
}


def create_startup_wizard(parent, on_complete_callback=None):
    """
    Create first-run startup wizard.
    Guides user through company type selection and initial setup.
    """
    wizard = tk.Toplevel(parent)
    wizard.title("Welcome - Company Setup")
    wizard.geometry("900x700")
    wizard.resizable(False, False)
    wizard.transient(parent)
    wizard.grab_set()
    
    # Center window
    wizard.update_idletasks()
    x = (wizard.winfo_screenwidth() // 2) - (900 // 2)
    y = (wizard.winfo_screenheight() // 2) - (700 // 2)
    wizard.geometry(f'900x700+{x}+{y}')
    wizard.deiconify()
    wizard.lift()
    wizard.focus_set()
    
    state = {
        'step': 1,
        'company_type': None,
        'company_name': '',
    }
    
    # Main container
    main_frame = ttk.Frame(wizard, padding=30)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Progress bar
    progress_var = tk.StringVar(value="Step 1 of 3")
    progress_label = tk.Label(main_frame, textvariable=progress_var, font=FONT_BOLD, bg=BG_COLOR if 'BG_COLOR' in globals() else '#F8F9FA', fg=COLOR_TEXT_MAIN if 'COLOR_TEXT_MAIN' in globals() else '#212529')
    progress_label.pack(anchor=tk.W, pady=(0, 10))
    
    progress_bar = ttk.Progressbar(main_frame, mode='determinate', maximum=3)
    progress_bar.pack(fill=tk.X, pady=(0, 20))
    progress_bar['value'] = 1
    
    # Step container
    step_frame = ttk.Frame(main_frame)
    step_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_step(step_num):
        """Show specific step."""
        # Clear step frame
        for widget in step_frame.winfo_children():
            widget.destroy()
        
        progress_var.set(f"Step {step_num} of 3")
        progress_bar['value'] = step_num
        
        if step_num == 1:
            show_welcome()
        elif step_num == 2:
            show_company_type()
        elif step_num == 3:
            show_features()
    
    def show_welcome():
        """Step 1: Welcome screen."""
        # Header
        header_frame = ttk.Frame(step_frame)
        header_frame.pack(fill=tk.X, pady=(20, 40))
        
        styled_label(header_frame, text="🎉 Welcome!", font=FONT_HEADING).pack(anchor=tk.W)
        styled_label(header_frame, 
                    text="Let's set up your inventory management system",
                    foreground="#6c757d").pack(anchor=tk.W, pady=(5, 0))
        
        # Info cards
        info_frame = ttk.Frame(step_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        features = [
            ("📦", "Inventory Management", "Track products across locations"),
            ("💰", "Sales & Orders", "Manage sales and customer orders"),
            ("📊", "Reports & Analytics", "Business insights and exports"),
            ("🎯", "Lease & Rental", "Complete lease management"),
            ("🔔", "Smart Alerts", "Low stock and expiry warnings"),
            ("☁️", "Cloud Backup", "Google Drive integration"),
        ]
        
        for i in range(0, len(features), 2):
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, pady=5)
            
            for j in range(2):
                if i + j < len(features):
                    icon, title, desc = features[i + j]
                    card = make_card(row_frame, padding=15)
                    card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
                    
                    styled_label(card, text=icon, font=("Segoe UI", 24)).pack(anchor=tk.W)
                    styled_label(card, text=title, font=FONT_BOLD).pack(anchor=tk.W, pady=(5, 0))
                    styled_label(card, text=desc, font=("Segoe UI", 9), 
                                foreground="#6c757d").pack(anchor=tk.W)
        
        # Next button
        button_frame = ttk.Frame(step_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def next_step():
            state['step'] = 2
            show_step(2)
        
        make_button(button_frame, "Get Started →", command=next_step, 
                   kind="success").pack(side=tk.RIGHT)
    
    def show_company_type():
        """Step 2: Select company type."""
        # Header
        header_frame = ttk.Frame(step_frame)
        header_frame.pack(fill=tk.X, pady=(20, 20))
        
        styled_label(header_frame, text="🏢 Select Your Business Type", font=FONT_HEADING).pack(anchor=tk.W)
        styled_label(header_frame, 
                    text="Choose the option that best describes your business",
                    foreground="#6c757d").pack(anchor=tk.W, pady=(5, 0))
        
        # Company type cards
        cards_frame = ttk.Frame(step_frame)
        cards_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Shared variable for radio buttons
        type_var = tk.StringVar(value=state.get('company_type') or 'general_retail')
        state['company_type'] = type_var.get()
        
        def select_type(type_id):
            type_var.set(type_id)
            state['company_type'] = type_id
            print(f"DEBUG: Selected company type: {type_id}")
        
        # Create cards
        for type_id, config in COMPANY_TYPES.items():
            card = make_card(cards_frame, padding=20)
            card.pack(fill=tk.X, pady=5)
            
            # Icon and name
            header = ttk.Frame(card)
            header.pack(fill=tk.X)
            
            styled_label(header, text=config['icon'], font=("Segoe UI", 32)).pack(side=tk.LEFT, padx=(0, 15))
            
            info = ttk.Frame(header)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            styled_label(info, text=config['name'], font=FONT_BOLD).pack(anchor=tk.W)
            styled_label(info, text=config['description'], font=("Segoe UI", 9), 
                        foreground="#6c757d").pack(anchor=tk.W)
            
            # Features
            features = [k.replace('_', ' ').title() for k, v in config['features'].items() if v][:4]
            features_text = " • ".join(features)
            
            f_lbl = styled_label(card, text=features_text, font=("Segoe UI", 8), 
                                foreground=COLOR_PRIMARY)
            f_lbl.pack(anchor=tk.W, pady=(10, 0))
            
            # Radio button (now using shared type_var)
            radio = ttk.Radiobutton(card, variable=type_var, value=type_id,
                                   command=lambda tid=type_id: select_type(tid))
            radio.pack(side=tk.RIGHT)

            # Make the entire card and its children clickable
            for widget in [card, header, info, f_lbl]:
                widget.bind("<Button-1>", lambda e, tid=type_id: select_type(tid))
            
            # Recursively bind children of header/info
            for widget in header.winfo_children():
                widget.bind("<Button-1>", lambda e, tid=type_id: select_type(tid))
            for widget in info.winfo_children():
                widget.bind("<Button-1>", lambda e, tid=type_id: select_type(tid))
        
        # Navigation
        button_frame = ttk.Frame(step_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def back():
            state['step'] = 1
            show_step(1)
        
        def next_step():
            if state.get('company_type'):
                state['step'] = 3
                show_step(3)
            else:
                messagebox.showinfo("Select", "Please select a business type")
        
        make_button(button_frame, "← Back", command=back, kind="secondary").pack(side=tk.LEFT)
        make_button(button_frame, "Next →", command=next_step, kind="primary").pack(side=tk.RIGHT)
    
    def show_features():
        """Step 3: Feature confirmation."""
        # Header
        header_frame = ttk.Frame(step_frame)
        header_frame.pack(fill=tk.X, pady=(20, 20))
        
        config = COMPANY_TYPES.get(state['company_type'], {})
        
        styled_label(header_frame, text="✅ Setup Summary", font=FONT_HEADING).pack(anchor=tk.W)
        styled_label(header_frame, 
                    text=f"You selected: {config['icon']} {config['name']}",
                    foreground="#6c757d").pack(anchor=tk.W, pady=(5, 0))
        
        # Features list
        features_frame = make_card(step_frame, padding=20)
        features_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        styled_label(features_frame, text="Enabled Features:", font=FONT_BOLD).pack(anchor=tk.W, pady=(0, 15))
        
        enabled = [k.replace('_', ' ').title() for k, v in config['features'].items() if v]
        
        for feature in enabled:
            feature_frame = ttk.Frame(features_frame)
            feature_frame.pack(fill=tk.X, pady=5)
            
            styled_label(feature_frame, text="✓", foreground=COLOR_SUCCESS, 
                        font=FONT_BOLD).pack(side=tk.LEFT, padx=(0, 10))
            styled_label(feature_frame, text=feature).pack(side=tk.LEFT)
        
        # Company name input
        name_frame = ttk.LabelFrame(step_frame, text="Company Name (Optional)", padding=15)
        name_frame.pack(fill=tk.X, pady=(20, 10))
        
        company_name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=company_name_var, width=50)
        name_entry.pack(fill=tk.X)
        
        # Navigation
        button_frame = ttk.Frame(step_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def back():
            state['step'] = 2
            show_step(2)
        
        def finish():
            # Save company type
            company_name = company_name_var.get().strip()
            save_company_config(state['company_type'], company_name)
            
            # Initialize database
            init_database()
            
            messagebox.showinfo("Complete", "Setup complete! Starting application...")
            wizard.destroy()
            
            # Call completion callback
            if on_complete_callback:
                on_complete_callback(state['company_type'], company_name)
        
        make_button(button_frame, "← Back", command=back, kind="secondary").pack(side=tk.LEFT)
        make_button(button_frame, "✓ Complete Setup", command=finish, kind="success").pack(side=tk.RIGHT)
    
    # Show first step
    show_step(1)
    
    # Handle window close
    def on_close():
        if messagebox.askyesno("Exit", "Quit setup?"):
            wizard.destroy()
            parent.quit()
            parent.destroy()
    
    wizard.protocol("WM_DELETE_WINDOW", on_close)


def save_company_config(company_type: str, company_name: str = ''):
    """Save company configuration to database."""
    with get_db_cursor() as cur:
        # Save company type
        cur.execute("""
            INSERT OR REPLACE INTO settings (key, value, category, description)
            VALUES ('company_type', ?, 'general', 'Selected business type')
        """, (company_type,))
        
        # Save company name
        if company_name:
            cur.execute("""
                INSERT OR REPLACE INTO settings (key, value, category, description)
                VALUES ('company_name', ?, 'general', 'Company name')
            """, (company_name,))
        
        # Save feature flags
        config = COMPANY_TYPES.get(company_type, {})
        for feature, enabled in config.get('features', {}).items():
            cur.execute("""
                INSERT OR REPLACE INTO settings (key, value, category)
                VALUES (?, ?, 'features')
            """, (f'feature_{feature}', '1' if enabled else '0'))


def get_company_type() -> str:
    """Get current company type."""
    with get_db_cursor() as cur:
        cur.execute("SELECT value FROM settings WHERE key = 'company_type'")
        row = cur.fetchone()
        return row['value'] if row else 'not_set'


def get_company_config() -> dict:
    """Get configuration for current company type."""
    company_type = get_company_type()
    return COMPANY_TYPES.get(company_type, COMPANY_TYPES['general_retail'])


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled for current company type."""
    config = get_company_config()
    return config['features'].get(feature, False)


def get_priority_tabs() -> list:
    """Get ordered list of priority tabs for current company type."""
    config = get_company_config()
    return config.get('priority_tabs', [])


def get_hidden_tabs() -> list:
    """Get list of tabs to hide for current company type."""
    config = get_company_config()
    return config.get('hidden_tabs', [])


def get_dashboard_widgets() -> list:
    """Get list of dashboard widgets for current company type."""
    config = get_company_config()
    return config.get('dashboard_widgets', [])


def get_quick_actions() -> list:
    """Get list of quick actions for current company type."""
    config = get_company_config()
    return config.get('quick_actions', [])
