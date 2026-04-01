"""
FIXED Startup Wizard - Works without errors
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime

def create_startup_wizard(parent, on_complete_callback=None):
    """Create a simple, working setup wizard."""
    
    wizard = tk.Toplevel(parent) if parent else tk.Tk()
    wizard.title("Minataka Sphere - Setup Wizard")
    wizard.geometry("700x600")
    wizard.resizable(False, False)
    
    if parent:
        wizard.transient(parent)
        wizard.grab_set()
    
    # Main container
    main_frame = ttk.Frame(wizard, padding=30)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # State
    step = {'value': 1}
    company_type = {'value': 'general_retail'}
    company_name = {'value': ''}
    
    def next_step():
        step['value'] += 1
        show_step(step['value'])
    
    def prev_step():
        step['value'] -= 1
        show_step(step['value'])
    
    def show_step(step_num):
        # Clear frame
        for widget in main_frame.winfo_children():
            widget.destroy()
        
        if step_num == 1:
            show_welcome()
        elif step_num == 2:
            show_business_type()
        elif step_num == 3:
            show_company_info()
        elif step_num == 4:
            show_create_admin()
        elif step_num == 5:
            finish_setup()
    
    def show_welcome():
        # Title
        title = ttk.Label(main_frame, text="🎉 Welcome to Minataka Sphere!", 
                         font=("Segoe UI", 20, "bold"))
        title.pack(pady=(20, 20))
        
        subtitle = ttk.Label(main_frame, 
                            text="Inventory Management System v2.0\n\n"
                                 "This wizard will help you set up your business.",
                            font=("Segoe UI", 11),
                            justify="center")
        subtitle.pack(pady=20)
        
        features = ttk.Label(main_frame,
                            text="✨ Features:\n\n"
                                 "• Multi-location inventory\n"
                                 "• Complete invoicing system\n"
                                 "• Barcode scanning\n"
                                 "• Lease & rental management\n"
                                 "• Advanced reporting\n"
                                 "• User hierarchy with device locking",
                            font=("Segoe UI", 10),
                            justify="left")
        features.pack(pady=20, anchor="w")
        
        # Button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Button(btn_frame, text="Get Started →", command=next_step).pack()
    
    def show_business_type():
        # Title
        title = ttk.Label(main_frame, text="🏢 Select Your Business Type",
                         font=("Segoe UI", 16, "bold"))
        title.pack(pady=(10, 20))
        
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        businesses = [
            ('lease_rental', '🎯 Lease & Rental', 'Equipment rental, lease management'),
            ('electronics', '📱 Electronics', 'Mobile phones, computers'),
            ('pharmacy', '💊 Pharmacy', 'Medical supplies, healthcare'),
            ('retail', '🏪 General Retail', 'Retail store, general merchandise'),
            ('wholesale', '📦 Wholesale', 'Wholesale trading, distribution'),
        ]
        
        selected_var = tk.StringVar(value='electronics')
        
        for i, (key, name, desc) in enumerate(businesses):
            frame = ttk.Frame(options_frame)
            frame.pack(fill=tk.X, pady=5)
            
            radio = ttk.Radiobutton(frame, variable=selected_var, value=key)
            radio.pack(side=tk.LEFT)
            
            info = ttk.Frame(frame)
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
            
            ttk.Label(info, text=name, font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
            ttk.Label(info, text=desc, font=("Segoe UI", 9), foreground="#666").pack(anchor=tk.W)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Button(btn_frame, text="← Back", command=prev_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Next →", 
                  command=lambda: (company_type.__setitem__('value', selected_var.get()), next_step())).pack(side=tk.LEFT, padx=5)
    
    def show_company_info():
        # Title
        title = ttk.Label(main_frame, text="📋 Company Information",
                         font=("Segoe UI", 16, "bold"))
        title.pack(pady=(10, 20))
        
        # Form
        form_frame = ttk.LabelFrame(main_frame, text="Your Company Details", padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        company_var = tk.StringVar(value="Minataka Sphere")
        ttk.Entry(form_frame, textvariable=company_var, width=40).grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form_frame, text="Your Name:").grid(row=2, column=0, sticky=tk.W, pady=5)
        name_var = tk.StringVar(value="Amy")
        ttk.Entry(form_frame, textvariable=name_var, width=40).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form_frame, text="Your Email:").grid(row=4, column=0, sticky=tk.W, pady=5)
        email_var = tk.StringVar(value="amy@mintaka.com")
        ttk.Entry(form_frame, textvariable=email_var, width=40).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form_frame, text="Currency:").grid(row=6, column=0, sticky=tk.W, pady=5)
        currency_var = tk.StringVar(value="PKR")
        ttk.Combobox(form_frame, textvariable=currency_var, values=["PKR", "USD", "EUR", "GBP"], width=38).grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=20)
        
        ttk.Button(btn_frame, text="← Back", command=prev_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Next →", 
                  command=lambda: (company_name.__setitem__('value', company_var.get()), next_step())).pack(side=tk.LEFT, padx=5)
    
    def show_create_admin():
        # Title
        title = ttk.Label(main_frame, text="👑 Create Owner Admin Account",
                         font=("Segoe UI", 16, "bold"))
        title.pack(pady=(10, 20))
        
        # Warning
        warning = ttk.Label(main_frame,
                           text="⚠️ IMPORTANT: This will be the HIGHEST level admin account.\n"
                                "Write down your password - you'll need it to login!",
                           font=("Segoe UI", 10),
                           foreground="#cc0000",
                           justify="center")
        warning.pack(pady=10)
        
        # Form
        form_frame = ttk.LabelFrame(main_frame, text="Admin Credentials", padding=20)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(form_frame, text="Admin Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        admin_name_var = tk.StringVar(value="Amy")
        ttk.Entry(form_frame, textvariable=admin_name_var, width=40).grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form_frame, text="Admin Email:").grid(row=2, column=0, sticky=tk.W, pady=5)
        admin_email_var = tk.StringVar(value="amy@mintaka.com")
        ttk.Entry(form_frame, textvariable=admin_email_var, width=40).grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=4, column=0, sticky=tk.W, pady=5)
        password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=password_var, show="*", width=40).grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        ttk.Label(form_frame, text="Confirm Password:").grid(row=6, column=0, sticky=tk.W, pady=5)
        confirm_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=confirm_var, show="*", width=40).grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=20)
        
        def create_account():
            password = password_var.get()
            confirm = confirm_var.get()
            
            if not password or len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
            
            # Create the admin user
            try:
                from utils import create_user
                email = admin_email_var.get()
                create_user(email, password, role='admin')
                
                # Save company info
                with open('data/settings.json', 'w') as f:
                    json.dump({
                        'company_name': company_name['value'],
                        'company_type': company_type['value'],
                        'currency': 'PKR'
                    }, f, indent=2)
                
                messagebox.showinfo("Success", "Owner Admin account created!")
                next_step()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create account: {e}")
        
        ttk.Button(btn_frame, text="← Back", command=prev_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Create Account ✓", command=create_account).pack(side=tk.LEFT, padx=5)
    
    def finish_setup():
        # Success screen
        title = ttk.Label(main_frame, text="✅ Setup Complete!",
                         font=("Segoe UI", 20, "bold"),
                         foreground="#00aa00")
        title.pack(pady=(40, 20))
        
        message = ttk.Label(main_frame,
                           text=f"Welcome to Minataka Sphere!\n\n"
                                f"Company: {company_name['value']}\n"
                                f"Business Type: {company_type['value']}\n\n"
                                f"You can now login with your Owner Admin account.",
                           font=("Segoe UI", 11),
                           justify="center")
        message.pack(pady=20)
        
        # Button
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, pady=40)
        
        def finish():
            wizard.destroy()
            if on_complete_callback:
                on_complete_callback(company_type['value'], company_name['value'])
        
        ttk.Button(btn_frame, text="Continue to Login →", command=finish).pack()
    
    # Show first step
    show_step(1)
    
    # Handle window close
    def on_close():
        if messagebox.askyesno("Exit", "Quit setup?"):
            wizard.destroy()
            if parent:
                parent.quit()
                parent.destroy()
    
    wizard.protocol("WM_DELETE_WINDOW", on_close)
