"""
FINAL SIMPLE MAIN - GUARANTEED TO SHOW WINDOW
"""
import tkinter as tk
from tkinter import ttk, messagebox

# Force window to front
root = tk.Tk()
root.title("Minataka Sphere - Setup")
root.geometry("500x400")
root.attributes('-topmost', True)  # Force to front
root.lift()  # Bring to front
root.focus_force()  # Force focus

print("✅ Window created - should be visible NOW!")

# Big visible label
label = ttk.Label(root, 
                  text="🎉 MINATAKA SPHERE\n\nSetup is starting...\n\n"
                       "If you see this window, the app is working!",
                  font=("Segoe UI", 16, "bold"),
                  justify="center",
                  foreground="#0066cc")
label.pack(expand=True, pady=50)

def start_wizard():
    """Start the setup wizard."""
    try:
        from startup_wizard_fixed import create_startup_wizard
        
        def on_done(company_type, company_name):
            print(f"✅ Setup complete: {company_type}")
            # Don't destroy root - keep it for login
            # show_login() will be called
        
        create_startup_wizard(root, on_done)
    except Exception as e:
        messagebox.showerror("Wizard Error", str(e))
        show_login()

def show_login():
    """Show simple login."""
    login_win = tk.Toplevel(root)
    login_win.title("Login")
    login_win.geometry("400x300")
    login_win.attributes('-topmost', True)
    
    ttk.Label(login_win, text="🔐 Login", font=("Segoe UI", 16, "bold")).pack(pady=20)
    
    ttk.Label(login_win, text="Username:").pack(anchor=tk.W, padx=20)
    user_var = tk.StringVar(value="amy@mintaka.com")
    ttk.Entry(login_win, textvariable=user_var, width=40).pack(padx=20, pady=5)
    
    ttk.Label(login_win, text="Password:").pack(anchor=tk.W, padx=20)
    pass_var = tk.StringVar()
    ttk.Entry(login_win, textvariable=pass_var, show="*", width=40).pack(padx=20, pady=5)
    
    def do_login():
        try:
            from utils import verify_user
            ok, role = verify_user(user_var.get(), pass_var.get())
            if ok:
                messagebox.showinfo("Success", f"Login successful as {role}!")
                login_win.destroy()
                root.destroy()
                # Open main dashboard
                open_dashboard(user_var.get(), role)
            else:
                messagebox.showerror("Error", "Invalid username or password")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    ttk.Button(login_win, text="LOGIN", command=do_login).pack(pady=20)

def open_dashboard(username, role):
    """Open main dashboard."""
    dash = tk.Tk()
    dash.title(f"Minataka Sphere - {username}")
    dash.geometry("1280x800")
    dash.attributes('-topmost', True)
    
    ttk.Label(dash, text=f"✅ WELCOME {username}!\n\nRole: {role}\n\nDashboard loaded successfully!",
              font=("Segoe UI", 20, "bold"),
              foreground="#00aa00").pack(expand=True)
    
    dash.mainloop()

# Button to start
btn = ttk.Button(root, text="Start Setup Wizard →", command=start_wizard)
btn.pack(pady=20)

# Info label
info = ttk.Label(root, text="💡 Tip: Check your taskbar if window is hidden",
                 font=("Segoe UI", 9),
                 foreground="#666")
info.pack(side=tk.BOTTOM, pady=10)

print("🚀 App is running! Check your screen for the window.")
print("💡 If you don't see it, check the Windows taskbar!")

root.mainloop()
