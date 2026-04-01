import tkinter as tk
from tkinter import messagebox, ttk
import logging

try:
    # Attempt to import from the local package first
    from .ui_theme import (
        make_button, setup_theme, make_card, styled_label,
        styled_entry, center_window, FONT_HEADING, FONT_REGULAR,
        COLOR_TEXT_MUTED, FONT_BOLD, COLOR_APP_BG, COLOR_PRIMARY,
        SUBHEADING_FONT, FONT_SMALL, create_divider, COLOR_TEXT_MAIN,
        COLOR_BORDER, COLOR_PRIMARY_LIGHT
    )
except (ImportError, ModuleNotFoundError):
    # Fallback for running as a standalone script
    from ui_theme import (
        make_button, setup_theme, make_card, styled_label,
        styled_entry, center_window, FONT_HEADING, FONT_REGULAR,
        COLOR_TEXT_MUTED, FONT_BOLD, COLOR_APP_BG, COLOR_PRIMARY,
        SUBHEADING_FONT, FONT_SMALL, create_divider, COLOR_TEXT_MAIN,
        COLOR_BORDER, COLOR_PRIMARY_LIGHT
    )

try:
    from .utils import verify_user, list_users
except (ImportError, ModuleNotFoundError):
    from utils import verify_user, list_users

try:
    from .security import sanitize_for_display
except (ImportError, ModuleNotFoundError):
    try:
        from security import sanitize_for_display
    except (ImportError, ModuleNotFoundError):
        # Fallback for backwards compatibility
        sanitize_for_display = lambda x: str(x)[:50]

def open_login(on_success, master=None):
    """
    Creates and displays the premium login window with glassmorphism design.
    
    Args:
        on_success (function): The callback function to execute upon successful login.
                               It receives `username`, `role`, and `master`.
        master (tk.Tk, optional): The root window if this is part of a larger app.
                                  If None, a new Tk root is created.
    """
    if master is None:
        login_win = tk.Tk()
        is_root = True
    else:
        login_win = tk.Toplevel(master)
        is_root = False

    login_win.title("Minataka Sphere - Premium Access")
    login_win.geometry("480x620")
    login_win.resizable(False, False)
    
    # Configure window background
    try:
        login_win.configure(bg=COLOR_APP_BG)
    except Exception:
        pass

    # --- Main container with premium styling ---
    main_frame = ttk.Frame(login_win, padding=30)
    main_frame.pack(fill="both", expand=True)

    # --- Header section with logo/icon ---
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(pady=(20, 30))
    
    # Premium icon/emoji display
    icon_label = styled_label(header_frame, "🔐", font=("Segoe UI", 56))
    icon_label.pack(pady=(10, 10))
    
    # Company name with premium typography
    styled_label(header_frame, "Minataka Sphere", font=FONT_HEADING, foreground=COLOR_PRIMARY).pack(pady=(5, 5))
    styled_label(header_frame, "Inventory Management System", font=SUBHEADING_FONT, foreground=COLOR_TEXT_MUTED).pack()
    
    # Decorative line
    divider = create_divider(header_frame, orientation="horizontal", color=COLOR_BORDER, thickness=2)
    divider.pack(fill="x", pady=(20, 20))


    # --- Login Form Card with Glassmorphism ---
    card = make_card(main_frame, padx=30, pady=30)
    card.pack(fill="x", expand=False)

    # Username field with icon
    username_container = ttk.Frame(card)
    username_container.pack(fill="x", pady=(0, 20))
    
    styled_label(username_container, "Username", font=FONT_BOLD, foreground=COLOR_TEXT_MAIN).pack(anchor="w", pady=(0, 8))
    username_entry = styled_entry(username_container)
    username_entry.pack(fill="x", ipady=8)
    username_entry.insert(0, "")  # Placeholder behavior can be enhanced

    # Password field with icon
    password_container = ttk.Frame(card)
    password_container.pack(fill="x", pady=(0, 25))
    
    styled_label(password_container, "Password", font=FONT_BOLD, foreground=COLOR_TEXT_MAIN).pack(anchor="w", pady=(0, 8))
    password_entry = styled_entry(password_container, show="•")
    password_entry.pack(fill="x", ipady=8)

    def login(event=None):
        """Handles the login logic using stored users."""
        username = username_entry.get().strip()
        password = password_entry.get()
        
        # Basic input validation
        if not username or not password:
            messagebox.showerror("Input Error", "Username and password are required")
            password_entry.delete(0, tk.END)
            return

        ok, role = verify_user(username, password)
        if ok:
            logging.info(f"Login successful: {sanitize_for_display(username)}, role: {role}")
            login_win.destroy()
            on_success(username, role, master)
        else:
            logging.warning(f"Login failed for username: {sanitize_for_display(username)}")
            messagebox.showerror("Login Failed", "Invalid username or password")
            password_entry.delete(0, tk.END)

    # --- Premium Login Button ---
    login_btn = make_button(card, text="SIGN IN", command=login, kind="primary", icon="🚀")
    login_btn.pack(fill="x", ipady=12, pady=(10, 0))

    # --- Helper text ---
    helper_frame = ttk.Frame(card)
    helper_frame.pack(fill="x", pady=(15, 0))
    
    help_text = styled_label(helper_frame, "Need help? Contact your administrator", 
                            font=FONT_SMALL, foreground=COLOR_TEXT_MUTED)
    help_text.pack(anchor="center")

    # --- Bindings ---
    username_entry.bind('<Return>', lambda e: password_entry.focus())
    password_entry.bind('<Return>', login)
    
    # Add hover effects to button
    original_bg = COLOR_PRIMARY
    hover_bg = COLOR_PRIMARY_LIGHT
    
    def on_enter(e):
        try:
            login_btn.configure(style="Primary.TButton")
        except Exception:
            pass
    
    def on_leave(e):
        try:
            login_btn.configure(style="Primary.TButton")
        except Exception:
            pass

    # --- Finalize Window ---
    center_window(login_win)
    login_win.deiconify()
    login_win.lift()
    login_win.focus_force()
    username_entry.focus_set()

    if is_root:
        login_win.mainloop()

if __name__ == '__main__':
    # This allows the login UI to be tested standalone
    root = tk.Tk()
    root.withdraw()
    setup_theme(root, "superhero")
    open_login(lambda u, r, m: print(f"Login successful for {u} ({r})"))
    root.mainloop()

