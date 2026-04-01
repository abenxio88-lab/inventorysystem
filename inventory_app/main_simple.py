"""
SIMPLIFIED MAIN.PY - Goes directly to Setup Wizard
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

try:
    from logger_setup import setup_logger
    setup_logger()
except:
    pass

print("🚀 Starting Minataka Sphere Setup...")

# Create root window
app_root = tk.Tk()
app_root.title("Minataka Sphere - Setup")
app_root.geometry("400x300")

# Show loading message
label = ttk.Label(app_root, text="🎉 Welcome to Minataka Sphere!\n\nStarting Setup Wizard...", 
                  font=("Segoe UI", 14), justify="center")
label.pack(expand=True)

def start_wizard():
    """Start the setup wizard after a short delay."""
    app_root.after(1000, show_wizard)

def show_wizard():
    """Show the actual setup wizard."""
    app_root.destroy()
    
    # Import and show FIXED wizard
    try:
        from startup_wizard_fixed import create_startup_wizard
        
        def on_setup_complete(company_type, company_name):
            print(f"✅ Setup complete: {company_type}")
            # Now show login
            show_login()
        
        create_startup_wizard(None, on_setup_complete)
    except Exception as e:
        messagebox.showerror("Error", f"Setup Wizard failed: {e}\n\nUsing simple setup instead.")
        show_login()

def show_login():
    """Show login screen."""
    from login_ui import open_login
    from dashboard_ui import create_dashboard_tab
    
    def on_login_success(username, role, master):
        print(f"✅ Login successful: {username} ({role})")
        # Create main window
        root = tk.Tk()
        root.title(f"Minataka Sphere - {username}")
        root.geometry("1280x800")
        
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add dashboard
        dashboard = create_dashboard_tab(notebook, username, role)
        notebook.add(dashboard, text="🏠 Dashboard")
        
        # Add inventory
        try:
            from inventory_ui import create_inventory_tab
            inventory = create_inventory_tab(notebook, current_user=username)
            notebook.add(inventory, text="📦 Inventory")
        except:
            pass
        
        # Add sales
        try:
            from sales_ui import create_sales_tab
            sales = create_sales_tab(notebook)
            notebook.add(sales, text="💰 Sales")
        except:
            pass
        
        print("🎉 Dashboard loaded successfully!")
        root.mainloop()
    
    open_login(on_login_success)

# Start the wizard after delay
start_wizard()
app_root.mainloop()

print("🎉 Minataka Sphere closed.")
