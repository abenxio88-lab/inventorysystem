"""
CLEAN MAIN.PY - Setup Wizard FIRST, then Login
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

try:
    from logger_setup import setup_logger
    setup_logger()
except:
    pass

print("🚀 Minataka Sphere v2.0 - Starting...")

# Create main window
root = tk.Tk()
root.title("Minataka Sphere - Setup")
root.geometry("600x500")
root.attributes('-topmost', True)

# Welcome screen
welcome_frame = ttk.Frame(root, padding=30)
welcome_frame.pack(fill=tk.BOTH, expand=True)

title = ttk.Label(welcome_frame, text="🎉 Welcome to Minataka Sphere!", 
                  font=("Segoe UI", 20, "bold"),
                  foreground="#0066cc")
title.pack(pady=30)

info = ttk.Label(welcome_frame,
                 text="Inventory Management System v2.0\n\n"
                      "First-time setup will guide you through:\n"
                      "• Selecting your business type\n"
                      "• Company information\n"
                      "• Creating your Owner Admin account\n\n"
                      "This takes about 2 minutes.",
                 font=("Segoe UI", 11),
                 justify="center")
info.pack(pady=20)

def start_wizard():
    """Start the setup wizard."""
    welcome_frame.pack_forget()
    
    try:
        from startup_wizard_fixed import create_startup_wizard
        
        def on_setup_complete(company_type, company_name):
            print(f"✅ Setup complete: {company_type} - {company_name}")
            show_login()
        
        create_startup_wizard(root, on_setup_complete)
    except Exception as e:
        messagebox.showerror("Wizard Error", f"Setup wizard failed: {e}\n\nGoing to login instead.")
        show_login()

def show_login():
    """Show login screen."""
    # Clear window
    for widget in root.winfo_children():
        widget.destroy()
    
    # Login frame
    login_frame = ttk.Frame(root, padding=30)
    login_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(login_frame, text="🔐 Login", font=("Segoe UI", 18, "bold")).pack(pady=20)
    
    # Username
    user_frame = ttk.Frame(login_frame)
    user_frame.pack(fill=tk.X, pady=10)
    ttk.Label(user_frame, text="Username:", width=12).pack(side=tk.LEFT)
    user_var = tk.StringVar(value="amy@mintaka.com")
    ttk.Entry(user_frame, textvariable=user_var, width=30).pack(side=tk.LEFT)
    
    # Password
    pass_frame = ttk.Frame(login_frame)
    pass_frame.pack(fill=tk.X, pady=10)
    ttk.Label(pass_frame, text="Password:", width=12).pack(side=tk.LEFT)
    pass_var = tk.StringVar()
    ttk.Entry(pass_frame, textvariable=pass_var, show="*", width=30).pack(side=tk.LEFT)
    
    def do_login():
        try:
            from utils import verify_user
            ok, role = verify_user(user_var.get(), pass_var.get())
            
            if ok:
                messagebox.showinfo("Success", f"✅ Login successful!\n\nRole: {role}")
                root.destroy()
                open_dashboard(user_var.get(), role)
            else:
                messagebox.showerror("Failed", "❌ Invalid username or password")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    ttk.Button(login_frame, text="🚀 LOGIN", command=do_login).pack(pady=20)
    
    # Bind Enter
    def on_enter(event):
        do_login()
    root.bind('<Return>', on_enter)

def open_dashboard(username, role):
    """Open main dashboard."""
    dash = tk.Tk()
    dash.title(f"Minataka Sphere - {username}")
    dash.geometry("1280x800")
    
    # Welcome
    welcome = ttk.Label(dash, 
                       text=f"✅ WELCOME!\n\nUser: {username}\nRole: {role}\n\n"
                            f"🎉 System Ready!",
                       font=("Segoe UI", 24, "bold"),
                       foreground="#00aa00")
    welcome.pack(pady=50)
    
    # Tabs
    notebook = ttk.Notebook(dash)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Dashboard
    dash_tab = ttk.Frame(notebook)
    notebook.add(dash_tab, text="🏠 Dashboard")
    ttk.Label(dash_tab, text="Dashboard", font=("Segoe UI", 16)).pack(pady=50)
    
    # Inventory
    try:
        from inventory_ui import create_inventory_tab
        inv = create_inventory_tab(notebook, current_user=username)
        notebook.add(inv, text="📦 Inventory")
        print("✅ Inventory tab loaded")
    except Exception as e:
        print(f"❌ Inventory error: {e}")
    
    # Sales
    try:
        from sales_ui import create_sales_tab
        sales = create_sales_tab(notebook)
        notebook.add(sales, text="💰 Sales")
        print("✅ Sales tab loaded")
    except Exception as e:
        print(f"❌ Sales error: {e}")
    
    print(f"🎉 Dashboard ready for {username}!")
    dash.mainloop()

# Start button
start_btn = ttk.Button(welcome_frame, text="Start Setup →", command=start_wizard)
start_btn.pack(pady=30, ipadx=20, ipady=10)

# Skip button
skip_btn = ttk.Button(welcome_frame, text="Skip to Login", command=show_login, style="secondary.TButton")
skip_btn.pack(pady=10)

print("✅ Window created - should be visible!")
print("💡 Check your screen for the Minataka Sphere window")

root.mainloop()
