"""
Setup Licensing UI Module
==========================
Professional admin setup wizard and user authorization interface.

Features:
- First-time admin setup wizard (OWNER ADMIN creation)
- User authorization request interface
- Admin approval dashboard
- Device binding information display
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import logging

try:
    from .license_manager import AdminHierarchyManager, LicenseManager, get_device_info
    from .ui_theme import (
        setup_theme,
        COLOR_APP_BG, COLOR_CARD_BG, COLOR_PRIMARY, COLOR_SUCCESS,
        COLOR_DANGER, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_BORDER,
        FONT_REGULAR, FONT_BOLD, FONT_HEADING
    )
    from .security import hash_password, validate_password_strength, validate_email, validate_security_pin
except (ImportError, ModuleNotFoundError):
    from license_manager import AdminHierarchyManager, LicenseManager, get_device_info
    from ui_theme import (
        setup_theme,
        COLOR_APP_BG, COLOR_CARD_BG, COLOR_PRIMARY, COLOR_SUCCESS,
        COLOR_DANGER, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_BORDER,
        FONT_REGULAR, FONT_BOLD, FONT_HEADING
    )
    from security import hash_password, validate_password_strength, validate_email, validate_security_pin

# Theme colors (from ui_theme.py for consistency with main application)
BG_COLOR = COLOR_APP_BG
CARD_BG = COLOR_CARD_BG
PRIMARY_COLOR = COLOR_PRIMARY
TEXT_COLOR = COLOR_TEXT_MAIN


# ============================================================================
# ADMIN SETUP WIZARD
# ============================================================================

def create_admin_setup_wizard(parent=None) -> bool:
    """Create OWNER ADMIN account on first launch."""

    # MASTER CREDENTIALS - Only these can activate the software
    MASTER_USERNAME = "abenxio88"
    MASTER_PASSWORD = "M@trixR3lo@ded327922"
    MASTER_EMAIL = "abenxio88@gmail.com"

    # Create hidden root if no parent provided
    if parent is None:
        parent = tk.Tk()
        parent.withdraw()
        _cleanup_root = True
    else:
        _cleanup_root = False

    # First: Show master credential verification
    verify_window = tk.Toplevel(parent)
    verify_window.title("Minataka Sphere - Admin Verification")
    verify_window.geometry("550x500")
    verify_window.resizable(False, False)
    verify_window.config(bg=BG_COLOR)

    # Center the window
    verify_window.update_idletasks()
    ws = verify_window.winfo_screenwidth()
    hs = verify_window.winfo_screenheight()
    x = (ws // 2) - (550 // 2)
    y = (hs // 2) - (500 // 2)
    verify_window.geometry(f"550x500+{x}+{y}")

    # Header
    tk.Label(verify_window, text="🔐 Admin Verification Required",
            font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(padx=30, pady=(25, 15), anchor='w')

    tk.Label(verify_window,
            text="Enter the master admin credentials to activate this software.\nContact Minataka Sphere support if you don't have these.",
            font=FONT_REGULAR, bg=BG_COLOR, fg=TEXT_COLOR, wraplength=490).pack(anchor='w', pady=(0, 20), padx=30)

    # Verification Form
    verify_frame = tk.Frame(verify_window, bg=BG_COLOR)
    verify_frame.pack(fill='both', expand=True, padx=30, pady=(0, 10))

    # Username
    tk.Label(verify_frame, text="Username:", font=FONT_BOLD,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky='w', pady=10)
    verify_username_var = tk.StringVar()
    verify_username_entry = ttk.Entry(verify_frame, textvariable=verify_username_var, width=35)
    verify_username_entry.grid(row=0, column=1, sticky='ew', pady=10)

    # Password
    tk.Label(verify_frame, text="Password:", font=FONT_BOLD,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, sticky='w', pady=10)
    verify_password_var = tk.StringVar()
    verify_password_entry = ttk.Entry(verify_frame, textvariable=verify_password_var, width=35, show='*')
    verify_password_entry.grid(row=1, column=1, sticky='ew', pady=10)

    # Email
    tk.Label(verify_frame, text="Email:", font=FONT_BOLD,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, sticky='w', pady=10)
    verify_email_var = tk.StringVar()
    verify_email_entry = ttk.Entry(verify_frame, textvariable=verify_email_var, width=35)
    verify_email_entry.grid(row=2, column=1, sticky='ew', pady=10)

    verify_frame.columnconfigure(1, weight=1)

    # Buttons - at the bottom
    button_frame = tk.Frame(verify_window, bg=BG_COLOR)
    button_frame.pack(fill='x', padx=30, pady=(15, 25))

    verification_result = {'success': False}

    def on_verify():
        username = verify_username_var.get().strip()
        password = verify_password_var.get()
        email = verify_email_var.get().strip()

        # Check against master credentials
        if username == MASTER_USERNAME and password == MASTER_PASSWORD and email == MASTER_EMAIL:
            verification_result['success'] = True
            verify_window.destroy()
        else:
            messagebox.showerror("Access Denied",
                               "❌ Invalid credentials!\n\n"
                               "These credentials do not match the Minataka Sphere master admin.\n"
                               "Contact support at: " + MASTER_EMAIL)

    verify_btn = tk.Button(button_frame, text="Verify & Activate", command=on_verify,
                          bg=PRIMARY_COLOR, fg='white', font=FONT_BOLD,
                          padx=25, pady=12, cursor='hand2', relief='flat')
    verify_btn.pack(side='left', padx=5)

    cancel_btn = tk.Button(button_frame, text="Cancel", command=lambda: verify_window.destroy(),
                          bg=COLOR_TEXT_MUTED, fg='white', font=FONT_REGULAR,
                          padx=20, pady=12, cursor='hand2', relief='flat')
    cancel_btn.pack(side='left', padx=5)

    verify_window.transient(parent)
    verify_window.grab_set()
    parent.wait_window(verify_window)

    if not verification_result['success']:
        if _cleanup_root:
            parent.destroy()
        return False

    # Verification passed - now show the account creation wizard
    wizard_window = tk.Toplevel(parent)
    wizard_window.title("Minataka Sphere - Create Administrator Account")
    wizard_window.geometry("650x750")
    wizard_window.resizable(False, False)
    wizard_window.config(bg=BG_COLOR)

    # Header
    tk.Label(wizard_window, text="👤 Create Your Administrator Account",
            font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(padx=30, pady=(30, 10), anchor='w')

    tk.Label(wizard_window,
            text="Master verification successful. Now, set up your personal administrator account and a secure PIN.",
            font=FONT_REGULAR, bg=BG_COLOR, fg=TEXT_COLOR, wraplength=590).pack(anchor='w', pady=(0, 20), padx=30)

    # Admin Creation Form
    form_frame = tk.Frame(wizard_window, bg=BG_COLOR)
    form_frame.pack(fill='both', expand=True, padx=30, pady=10)

    # Username
    tk.Label(form_frame, text="Admin Username:", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky='w', pady=10)
    admin_user_var = tk.StringVar(value=MASTER_USERNAME)
    ttk.Entry(form_frame, textvariable=admin_user_var, width=35).grid(row=0, column=1, sticky='ew', pady=10, padx=(10, 0))

    # Full Name
    tk.Label(form_frame, text="Full Name:", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, sticky='w', pady=10)
    admin_name_var = tk.StringVar(value="System Administrator")
    ttk.Entry(form_frame, textvariable=admin_name_var, width=35).grid(row=1, column=1, sticky='ew', pady=10, padx=(10, 0))

    # Email
    tk.Label(form_frame, text="Admin Email:", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, sticky='w', pady=10)
    admin_email_var = tk.StringVar(value=MASTER_EMAIL)
    ttk.Entry(form_frame, textvariable=admin_email_var, width=35).grid(row=2, column=1, sticky='ew', pady=10, padx=(10, 0))

    # Password
    tk.Label(form_frame, text="Admin Password:", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=3, column=0, sticky='w', pady=10)
    admin_pass_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=admin_pass_var, width=35, show='*').grid(row=3, column=1, sticky='ew', pady=10, padx=(10, 0))

    # Confirm Password
    tk.Label(form_frame, text="Confirm Password:", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=4, column=0, sticky='w', pady=10)
    admin_confirm_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=admin_confirm_var, width=35, show='*').grid(row=4, column=1, sticky='ew', pady=10, padx=(10, 0))

    # Security PIN
    tk.Label(form_frame, text="Security PIN (4-8 digits):", font=FONT_BOLD, bg=BG_COLOR, fg=TEXT_COLOR).grid(row=5, column=0, sticky='w', pady=10)
    admin_pin_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=admin_pin_var, width=35, show='*').grid(row=5, column=1, sticky='ew', pady=10, padx=(10, 0))

    form_frame.columnconfigure(1, weight=1)

    # Info box for PIN
    pin_info = tk.Label(wizard_window, text="💡 The Security PIN is required for critical admin operations.",
                        font=("Segoe UI", 9, "italic"), bg=BG_COLOR, fg=COLOR_TEXT_MUTED)
    pin_info.pack(padx=30, pady=(0, 10), anchor='w')

    # Buttons
    button_frame = tk.Frame(wizard_window, bg=BG_COLOR)
    button_frame.pack(fill='x', padx=30, pady=25, side='bottom')

    def on_activate():
        admin_username = admin_user_var.get().strip()
        admin_name = admin_name_var.get().strip()
        admin_email = admin_email_var.get().strip()
        password = admin_pass_var.get()
        confirm_pass = admin_confirm_var.get()
        security_pin = admin_pin_var.get().strip()

        # Validations
        if not all([admin_username, admin_name, admin_email, password, security_pin]):
            messagebox.showerror("Error", "All fields are required!")
            return

        if password != confirm_pass:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        is_valid_pass, pass_err = validate_password_strength(password)
        if not is_valid_pass:
            messagebox.showerror("Weak Password", pass_err)
            return

        if not validate_email(admin_email):
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return

        if not validate_security_pin(security_pin):
            messagebox.showerror("Invalid PIN", "Security PIN must be 4 to 8 digits.")
            return

        try:
            # Use secure hash_password from security module
            password_hash = hash_password(password)
            pin_hash = hash_password(security_pin)

            AdminHierarchyManager.create_owner_admin(admin_username, admin_name, admin_email, password_hash, pin_hash)
            LicenseManager.initialize_license(admin_email)

            # Show success
            messagebox.showinfo("Success",
                              f"✅ Software Activated Successfully!\n\n"
                              f"Welcome {admin_name} to Minataka Sphere!\n\n"
                              f"═══════════════════════════════════\n"
                              f"ADMIN ACCOUNT CREATED:\n"
                              f"═══════════════════════════════════\n"
                              f"Username: {admin_username}\n"
                              f"Role: OWNER_ADMIN\n"
                              f"═══════════════════════════════════\n\n"
                              f"You can now log in and manage the system.")
            wizard_window.destroy()

        except Exception as e:
            logging.error(f"Error creating Owner Admin: {e}")
            messagebox.showerror("Error", f"Failed to create account: {str(e)}")

    activate_btn = tk.Button(button_frame, text="Activate Software", command=on_activate,
                          bg=COLOR_SUCCESS, fg='white', font=FONT_BOLD,
                          padx=25, pady=12, cursor='hand2', relief='flat')
    activate_btn.pack(side='left', padx=5)

    cancel_btn = tk.Button(button_frame, text="Cancel", command=lambda: wizard_window.destroy(),
                          bg=COLOR_TEXT_MUTED, fg='white', font=FONT_REGULAR,
                          padx=20, pady=12, cursor='hand2', relief='flat')
    cancel_btn.pack(side='left', padx=5)

    # Make window modal
    wizard_window.transient(parent)
    wizard_window.grab_set()
    wizard_window.focus()

    # Center window on screen
    wizard_window.update_idletasks()
    ws = wizard_window.winfo_screenwidth()
    hs = wizard_window.winfo_screenheight()
    x = (ws // 2) - (650 // 2)
    y = (hs // 2) - (750 // 2)
    wizard_window.geometry(f"650x750+{x}+{y}")
    wizard_window.update()

    # Wait for window to close
    parent.wait_window(wizard_window)

    # Cleanup if we created our own root
    if _cleanup_root:
        parent.destroy()

    return True


# ============================================================================
# USER AUTHORIZATION REQUEST DIALOG
# ============================================================================

def create_user_request_dialog(parent_window) -> dict:
    """Staff member requests authorization to use the software."""

    request_window = tk.Toplevel(parent_window)
    request_window.title("Request Software Access")
    request_window.geometry("500x400")
    request_window.resizable(False, False)
    request_window.config(bg=BG_COLOR)

    # Apply theme
    setup_theme(request_window, theme_name="cosmo")

    result = {'submitted': False, 'data': {}}

    # Header
    tk.Label(request_window, text="Request Software Access",
            font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(padx=20, pady=15, anchor='w')

    tk.Label(request_window,
            text="Please provide your information. Your administrator will review and approve your request.",
            font=FONT_REGULAR, bg=BG_COLOR, fg=TEXT_COLOR, wraplength=460).pack(padx=20, pady=5, anchor='w')

    # Form Frame
    form_frame = tk.Frame(request_window, bg=BG_COLOR)
    form_frame.pack(fill='both', expand=True, padx=20, pady=15)

    # Name
    tk.Label(form_frame, text="Full Name:", font=FONT_REGULAR,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=0, column=0, sticky='w', pady=10)
    name_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=name_var, width=35).grid(row=0, column=1, sticky='ew', pady=10)

    # Email
    tk.Label(form_frame, text="Email:", font=FONT_REGULAR,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=1, column=0, sticky='w', pady=10)
    email_var = tk.StringVar()
    ttk.Entry(form_frame, textvariable=email_var, width=35).grid(row=1, column=1, sticky='ew', pady=10)

    # Department
    tk.Label(form_frame, text="Department:", font=FONT_REGULAR,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=2, column=0, sticky='w', pady=10)
    dept_var = tk.StringVar()
    dept_combo = ttk.Combobox(form_frame, textvariable=dept_var, width=32,
                             values=['Sales', 'Inventory', 'Management', 'Admin', 'Other'])
    dept_combo.grid(row=2, column=1, sticky='ew', pady=10)

    # Reason
    tk.Label(form_frame, text="Reason for Access:", font=FONT_REGULAR,
             bg=BG_COLOR, fg=TEXT_COLOR).grid(row=3, column=0, sticky='nw', pady=(10, 0))
    reason_var = tk.StringVar()
    reason_text = scrolledtext.ScrolledText(form_frame, height=4, width=35, wrap=tk.WORD,
                                            bg=CARD_BG, fg=TEXT_COLOR, font=FONT_REGULAR)
    reason_text.grid(row=3, column=1, sticky='ew', pady=10)

    form_frame.columnconfigure(1, weight=1)

    # Buttons
    button_frame = tk.Frame(request_window, bg=BG_COLOR)
    button_frame.pack(fill='x', padx=20, pady=15)

    def on_submit():
        name = name_var.get().strip()
        email = email_var.get().strip()
        dept = dept_var.get().strip()
        reason = reason_text.get('1.0', tk.END).strip()

        if not all([name, email, dept, reason]):
            messagebox.showerror("Validation Error", "All fields are required.")
            return

        if '@' not in email:
            messagebox.showerror("Validation Error", "Please enter a valid email address.")
            return

        result['submitted'] = True
        result['data'] = {
            'name': name,
            'email': email,
            'department': dept,
            'reason': reason,
            'requested_date': datetime.now().isoformat()
        }

        messagebox.showinfo("Success",
                          "Your request has been submitted.\nYour administrator will review it shortly.")
        request_window.destroy()

    def on_cancel():
        request_window.destroy()

    submit_btn = tk.Button(button_frame, text="Submit Request", command=on_submit,
                          bg=PRIMARY_COLOR, fg='white', font=FONT_BOLD,
                          padx=20, pady=10, cursor='hand2', relief='flat')
    submit_btn.pack(side='left', padx=5)

    cancel_btn = tk.Button(button_frame, text="Cancel", command=on_cancel,
                          bg=COLOR_TEXT_MUTED, fg='white', font=FONT_REGULAR,
                          padx=20, pady=10, cursor='hand2', relief='flat')
    cancel_btn.pack(side='left', padx=5)

    request_window.transient(parent_window)
    request_window.grab_set()
    request_window.focus()

    parent_window.wait_window(request_window)

    return result


# ============================================================================
# ADMIN APPROVAL PANEL
# ============================================================================

def create_admin_approval_panel(master=None) -> tk.Frame:
    """Create a panel for admins to approve pending user requests."""

    approval_frame = tk.Frame(master, bg=BG_COLOR)

    # Header
    tk.Label(approval_frame, text="Approve User Requests",
             font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(fill='x', padx=10, pady=10)

    # Users Treeview
    columns = ('Name', 'Email', 'Role', 'Requested', 'Status')
    users_tree = ttk.Treeview(approval_frame, columns=columns, height=12)
    users_tree.pack(fill='both', expand=True, padx=10, pady=10)

    users_tree.column('#0', width=0, stretch=tk.NO)
    users_tree.column('Name', anchor=tk.W, width=150)
    users_tree.column('Email', anchor=tk.W, width=200)
    users_tree.column('Role', anchor=tk.W, width=100)
    users_tree.column('Requested', anchor=tk.W, width=120)
    users_tree.column('Status', anchor=tk.W, width=80)

    users_tree.heading('#0', text='', anchor=tk.W)
    users_tree.heading('Name', text='Name', anchor=tk.W)
    users_tree.heading('Email', text='Email', anchor=tk.W)
    users_tree.heading('Role', text='Role', anchor=tk.W)
    users_tree.heading('Requested', text='Requested', anchor=tk.W)
    users_tree.heading('Status', text='Status', anchor=tk.W)

    # Scrollbar
    scrollbar = ttk.Scrollbar(approval_frame, orient=tk.VERTICAL, command=users_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
    users_tree.config(yscrollcommand=scrollbar.set)

    # Buttons Frame
    button_frame = tk.Frame(approval_frame, bg=BG_COLOR)
    button_frame.pack(fill='x', padx=10, pady=10)

    def on_approve():
        selected = users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to approve.")
            return

        messagebox.showinfo("Approved", "User has been approved and can now access the software.")
        refresh_pending_users()

    def on_reject():
        selected = users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to reject.")
            return

        messagebox.showinfo("Rejected", "User request has been rejected.")
        refresh_pending_users()

    def refresh_pending_users():
        try:
            users_tree.delete(*users_tree.get_children())
            pending_users = AdminHierarchyManager.get_pending_user_requests()
            for user in pending_users:
                users_tree.insert('', tk.END, values=(
                    user['username'],
                    user['email'],
                    user['role'],
                    user['authorized_date'][:10] if user['authorized_date'] else 'Unknown',
                    'PENDING'
                ))
        except Exception as e:
            logging.error(f"Error refreshing pending users: {e}")

    approve_btn = tk.Button(button_frame, text="Approve", command=on_approve,
                           bg=COLOR_SUCCESS, fg='white', font=FONT_BOLD,
                           padx=20, pady=10, cursor='hand2', relief='flat')
    approve_btn.pack(side='left', padx=5)

    reject_btn = tk.Button(button_frame, text="Reject", command=on_reject,
                          bg=COLOR_DANGER, fg='white', font=FONT_BOLD,
                          padx=20, pady=10, cursor='hand2', relief='flat')
    reject_btn.pack(side='left', padx=5)

    refresh_btn = tk.Button(button_frame, text="Refresh", command=refresh_pending_users,
                           bg=COLOR_PRIMARY, fg='white', font=FONT_BOLD,
                           padx=20, pady=10, cursor='hand2', relief='flat')
    refresh_btn.pack(side='left', padx=5)

    approval_frame.refresh_pending_users = refresh_pending_users

    return approval_frame


# ============================================================================
# OWNER ADMIN DASHBOARD
# ============================================================================

def create_owner_admin_dashboard(master=None) -> tk.Frame:
    """Create the Owner Admin dashboard for managing users and system."""

    dashboard_frame = tk.Frame(master, bg=BG_COLOR)

    # Create notebook for tabs
    notebook = ttk.Notebook(dashboard_frame)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    # ========== USERS TAB ==========
    users_frame = tk.Frame(notebook, bg=BG_COLOR)
    notebook.add(users_frame, text='Manage Users')

    # Header
    tk.Label(users_frame, text="Authorized Users",
             font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(fill='x', padx=10, pady=10)

    # Users Treeview
    users_columns = ('Username', 'Email', 'Role', 'Status', 'Authorized Date')
    users_tree = ttk.Treeview(users_frame, columns=users_columns, height=15)
    users_tree.pack(fill='both', expand=True, padx=10, pady=10)

    users_tree.column('#0', width=0, stretch=tk.NO)
    users_tree.column('Username', anchor=tk.W, width=120)
    users_tree.column('Email', anchor=tk.W, width=200)
    users_tree.column('Role', anchor=tk.W, width=100)
    users_tree.column('Status', anchor=tk.W, width=80)
    users_tree.column('Authorized Date', anchor=tk.W, width=120)

    users_tree.heading('#0', text='', anchor=tk.W)
    users_tree.heading('Username', text='Username', anchor=tk.W)
    users_tree.heading('Email', text='Email', anchor=tk.W)
    users_tree.heading('Role', text='Role', anchor=tk.W)
    users_tree.heading('Status', text='Status', anchor=tk.W)
    users_tree.heading('Authorized Date', text='Authorized Date', anchor=tk.W)

    scrollbar = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=users_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
    users_tree.config(yscrollcommand=scrollbar.set)

    # Actions
    action_frame = tk.Frame(users_frame, bg=BG_COLOR)
    action_frame.pack(fill='x', padx=10, pady=10)

    def refresh_users():
        try:
            users_tree.delete(*users_tree.get_children())
            all_users = AdminHierarchyManager.get_all_users()
            for user in all_users:
                users_tree.insert('', tk.END, values=(
                    user['username'],
                    user['email'],
                    user['role'],
                    user['status'],
                    user['authorized_date'][:10] if user['authorized_date'] else 'Unknown'
                ))
        except Exception as e:
            logging.error(f"Error refreshing users: {e}")

    def on_deactivate():
        selected = users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to deactivate.")
            return

        values = users_tree.item(selected[0], 'values')
        username = values[0]

        if messagebox.askyesno("Confirm", f"Deactivate user '{username}'?"):
            messagebox.showinfo("Success", f"User '{username}' has been deactivated.")
            refresh_users()

    refresh_btn = tk.Button(action_frame, text="Refresh", command=refresh_users,
                           bg=COLOR_PRIMARY, fg='white', font=FONT_BOLD,
                           padx=20, pady=10, cursor='hand2', relief='flat')
    refresh_btn.pack(side='left', padx=5)

    deactivate_btn = tk.Button(action_frame, text="Deactivate User", command=on_deactivate,
                              bg=COLOR_DANGER, fg='white', font=FONT_BOLD,
                              padx=20, pady=10, cursor='hand2', relief='flat')
    deactivate_btn.pack(side='left', padx=5)

    # ========== AUTHORIZATION LOG TAB ==========
    log_frame = tk.Frame(notebook, bg=BG_COLOR)
    notebook.add(log_frame, text='Authorization Log')

    tk.Label(log_frame, text="Authorization History",
             font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(fill='x', padx=10, pady=10)

    # Log Treeview
    log_columns = ('Authorized By', 'User', 'Action', 'Timestamp')
    log_tree = ttk.Treeview(log_frame, columns=log_columns, height=15)
    log_tree.pack(fill='both', expand=True, padx=10, pady=10)

    log_tree.column('#0', width=0, stretch=tk.NO)
    log_tree.column('Authorized By', anchor=tk.W, width=150)
    log_tree.column('User', anchor=tk.W, width=150)
    log_tree.column('Action', anchor=tk.W, width=100)
    log_tree.column('Timestamp', anchor=tk.W, width=150)

    log_tree.heading('#0', text='', anchor=tk.W)
    log_tree.heading('Authorized By', text='Authorized By', anchor=tk.W)
    log_tree.heading('User', text='User', anchor=tk.W)
    log_tree.heading('Action', text='Action', anchor=tk.W)
    log_tree.heading('Timestamp', text='Timestamp', anchor=tk.W)

    log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_tree.yview)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
    log_tree.config(yscrollcommand=log_scrollbar.set)

    def refresh_log():
        try:
            log_tree.delete(*log_tree.get_children())
            logs = AdminHierarchyManager.get_authorization_log()
            for log_entry in logs:
                log_tree.insert('', tk.END, values=(
                    log_entry['authorized_by'][:30],
                    log_entry['authorized_user'][:30],
                    log_entry['action'],
                    log_entry['timestamp']
                ))
        except Exception as e:
            logging.error(f"Error refreshing log: {e}")

    log_action_frame = tk.Frame(log_frame, bg=BG_COLOR)
    log_action_frame.pack(fill='x', padx=10, pady=10)

    log_refresh_btn = tk.Button(log_action_frame, text="Refresh", command=refresh_log,
                               bg=COLOR_PRIMARY, fg='white', font=FONT_BOLD,
                               padx=20, pady=10, cursor='hand2', relief='flat')
    log_refresh_btn.pack(side='left', padx=5)

    # ========== DEVICE INFO TAB ==========
    device_frame = tk.Frame(notebook, bg=BG_COLOR)
    notebook.add(device_frame, text='Device Info')

    tk.Label(device_frame, text="Device Binding Information",
             font=FONT_HEADING, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(fill='x', padx=10, pady=10)

    device_info = get_device_info()
    info_frame = tk.Frame(device_frame, bg=BG_COLOR)
    info_frame.pack(fill='both', expand=True, padx=20, pady=15)

    info_text = scrolledtext.ScrolledText(info_frame, height=20, wrap=tk.WORD,
                                          bg=CARD_BG, fg=TEXT_COLOR, font=FONT_REGULAR)
    info_text.pack(fill='both', expand=True)

    info_content = f"""
Device Binding Information
==========================

Hostname:         {device_info['hostname']}
OS:               {device_info['os']}
OS Version:       {device_info['os_version']}
Processor:        {device_info['processor']}
MAC Address:      {device_info['mac_address']}
IP Address:       {device_info['ip_address']}
Fingerprint:      {device_info['fingerprint'][:32]}...

License:
=========
Check the license information to see device binding status.
If you need to transfer this license to another device,
contact the licensing administrator.

Security Notes:
==============
- This device is bound to the software license
- Attempting to run on a different device will require authorization
- All user activities are logged for security audit
"""

    info_text.insert('1.0', info_content)
    info_text.config(state='disabled')

    # Initial refresh
    refresh_users()
    refresh_log()

    return dashboard_frame
