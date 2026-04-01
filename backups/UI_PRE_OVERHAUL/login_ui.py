import tkinter as tk
from tkinter import messagebox, ttk
import logging

try:
    # Attempt to import from the local package first
    from .ui_theme import (
        make_button, setup_theme, make_card, styled_label,
        styled_entry, center_window, FONT_HEADING, FONT_REGULAR,
        COLOR_TEXT_MUTED, FONT_BOLD
    )
except (ImportError, ModuleNotFoundError):
    # Fallback for running as a standalone script
    from ui_theme import (
        make_button, setup_theme, make_card, styled_label,
        styled_entry, center_window, FONT_HEADING, FONT_REGULAR,
        COLOR_TEXT_MUTED, FONT_BOLD
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
    Creates and displays the login window.
    
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

    login_win.title("Login - Inventory System")
    login_win.geometry("400x550")
    login_win.resizable(False, False)

    # --- Main container ---
    main_frame = ttk.Frame(login_win, padding=20)
    main_frame.pack(fill="both", expand=True)

    # --- Header section ---
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(pady=(10, 20))
    
    styled_label(header_frame, "🔐", font=("Segoe UI", 40)).pack()
    styled_label(header_frame, "Minataka Sphere", font=FONT_HEADING).pack(pady=5)
    styled_label(header_frame, "Inventory Management Access", foreground=COLOR_TEXT_MUTED).pack()

    # --- Login Form Card ---
    card = make_card(main_frame, padx=25, pady=25)
    card.pack(fill="x", expand=False)

    # Username
    styled_label(card, "Username", font=FONT_BOLD).pack(anchor="w", pady=(10, 5))
    username_entry = styled_entry(card)
    username_entry.pack(fill="x", pady=(0, 15))

    # Password
    styled_label(card, "Password", font=FONT_BOLD).pack(anchor="w", pady=(10, 5))
    password_entry = styled_entry(card, show="*")
    password_entry.pack(fill="x", pady=(0, 20))

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

    # --- Login Button ---
    login_btn = make_button(card, text="LOGIN", command=login, kind="primary")
    login_btn.pack(fill="x", ipady=8, pady=(15, 0))

    # --- Bindings ---
    username_entry.bind('<Return>', lambda e: password_entry.focus())
    password_entry.bind('<Return>', login)

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

