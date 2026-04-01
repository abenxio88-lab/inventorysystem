"""
SIMPLE LOGIN - Just login, no wizard
"""
import tkinter as tk
from tkinter import ttk, messagebox

root = tk.Tk()
root.title("Minataka Sphere - Login")
root.geometry("450x350")
root.attributes('-topmost', True)
root.lift()

# Title
title = ttk.Label(root, text="🔐 Minataka Sphere Login", 
                  font=("Segoe UI", 18, "bold"),
                  foreground="#0066cc")
title.pack(pady=30)

# Username
user_frame = ttk.Frame(root)
user_frame.pack(fill=tk.X, padx=40, pady=5)

ttk.Label(user_frame, text="Username:", width=12).pack(side=tk.LEFT)
user_var = tk.StringVar(value="amy@mintaka.com")
user_entry = ttk.Entry(user_frame, textvariable=user_var, width=30)
user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Password
pass_frame = ttk.Frame(root)
pass_frame.pack(fill=tk.X, padx=40, pady=15)

ttk.Label(pass_frame, text="Password:", width=12).pack(side=tk.LEFT)
pass_var = tk.StringVar()
pass_entry = ttk.Entry(pass_frame, textvariable=pass_var, show="*", width=30)
pass_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

def do_login(event=None):
    """Login."""
    username = user_var.get()
    password = pass_var.get()
    
    if not username or not password:
        messagebox.showerror("Error", "Please enter both username and password")
        return
    
    try:
        from utils import verify_user
        ok, role = verify_user(username, password)
        
        if ok:
            messagebox.showinfo("Success!", f"✅ Login successful!\n\nUsername: {username}\nRole: {role}\n\nOpening dashboard...")
            root.destroy()
            open_dashboard(username, role)
        else:
            messagebox.showerror("Login Failed", "❌ Invalid username or password\n\nPlease check your credentials and try again.")
            pass_var.set("")
    except Exception as e:
        messagebox.showerror("Error", f"Login error: {e}")

# Login button
login_btn = ttk.Button(root, text="🚀 LOGIN", command=do_login)
login_btn.pack(pady=20, ipadx=20, ipady=5)

# Bind Enter key
pass_entry.bind('<Return>', do_login)
user_entry.bind('<Return>', lambda e: pass_entry.focus())

# Info label
info = ttk.Label(root, 
                 text="💡 Default: amy@mintaka.com / [your password]\n"
                      "Or use: admin / Admin123!",
                 font=("Segoe UI", 8),
                 foreground="#666")
info.pack(side=tk.BOTTOM, pady=10)

def open_dashboard(username, role):
    """Open main dashboard."""
    dash = tk.Tk()
    dash.title(f"Minataka Sphere - {username}")
    dash.geometry("1280x800")
    
    # Welcome message
    welcome = ttk.Label(dash, 
                       text=f"✅ WELCOME {username}!\n\n"
                            f"Role: {role}\n\n"
                            f"🎉 Your Minataka Sphere system is ready!\n\n"
                            f"Dashboard tabs will appear here.",
                       font=("Segoe UI", 20, "bold"),
                       foreground="#00aa00",
                       justify="center")
    welcome.pack(expand=True)
    
    # Add tabs
    notebook = ttk.Notebook(dash)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Dashboard tab
    dash_tab = ttk.Frame(notebook)
    notebook.add(dash_tab, text="🏠 Dashboard")
    ttk.Label(dash_tab, text="Dashboard Content", font=("Segoe UI", 16)).pack(pady=50)
    
    # Inventory tab
    try:
        from inventory_ui import create_inventory_tab
        inv_tab = create_inventory_tab(notebook, current_user=username)
        notebook.add(inv_tab, text="📦 Inventory")
    except Exception as e:
        print(f"Inventory tab error: {e}")
    
    # Sales tab
    try:
        from sales_ui import create_sales_tab
        sales_tab = create_sales_tab(notebook)
        notebook.add(sales_tab, text="💰 Sales")
    except Exception as e:
        print(f"Sales tab error: {e}")
    
    print(f"✅ Dashboard opened for {username} ({role})")
    dash.mainloop()

print("🚀 Login window is ready! Check your screen!")
root.mainloop()
