import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging

try:
    from .utils import list_users, create_user, delete_user, set_password
except (ImportError, ModuleNotFoundError):
    from utils import list_users, create_user, delete_user, set_password

try:
    from .ui_theme import make_card, styled_label, make_button
except (ImportError, ModuleNotFoundError):
    from ui_theme import make_card, styled_label, make_button

try:
    from .security import (
        validate_username, validate_password_strength, 
        sanitize_for_display, sanitize_html
    )
except (ImportError, ModuleNotFoundError):
    from security import (
        validate_username, validate_password_strength, 
        sanitize_for_display, sanitize_html
    )


def open_user_manager(master=None, current_user=None):
    # Require admin role to open user manager
    try:
        from .utils import load_users
    except (ImportError, ModuleNotFoundError):
        from utils import load_users

    users = load_users()
    if not current_user or users.get(current_user, {}).get("role") != "admin":
        try:
            messagebox.showerror("Permission Denied", "Only admins can manage users")
        except Exception:
            pass
        return None

    win = tk.Toplevel(master) if master is not None else tk.Tk()
    win.title("User Management")
    win.geometry("500x400")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    styled_label(frame, "Users", kind="heading").pack(anchor="w")

    tree = ttk.Treeview(frame, columns=("role",), show="headings")
    tree.heading("role", text="Role")
    tree.pack(fill="both", expand=True, pady=(10, 10))

    def refresh():
        for r in tree.get_children():
            tree.delete(r)
        for u in list_users():
            # Sanitize username and role for safe display (XSS prevention)
            safe_username = sanitize_for_display(u["username"])
            safe_role = sanitize_for_display(u["role"])
            tree.insert("", "end", values=(safe_username, safe_role))

    def add_user():
        username = simpledialog.askstring("New User", "Username:", parent=win)
        if not username:
            return
        
        # Validate username format
        if not validate_username(username):
            messagebox.showerror("Invalid Username", 
                               "Username must be 3-50 characters, start with a letter, "
                               "and contain only letters, numbers, and underscores.")
            return
        
        password = simpledialog.askstring("Password", f"Password for {username}:", parent=win, show="*")
        if not password:
            return
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            messagebox.showerror("Weak Password", error_msg)
            return
        
        role = simpledialog.askstring("Role", f"Role for {username} (admin/staff):", parent=win)
        if not role:
            role = "staff"
        
        # Validate and sanitize role
        role = role.lower().strip()
        if role not in ["admin", "staff", "manager", "viewer"]:
            role = "staff"
        
        try:
            create_user(username, password, role)
            messagebox.showinfo("User Created", f"User '{sanitize_for_display(username)}' created successfully")
            refresh()
        except ValueError as e:
            messagebox.showerror("Error", f"User creation failed: {str(e)}")
            logging.warning(f"Failed to create user {username}: {e}")
        except Exception as e:
            logging.exception("Failed to create user")
            messagebox.showerror("Error", str(e))

    def remove_user():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Select", "Select a user to delete")
            return
        item = tree.item(sel[0], "values")
        username = item[0]
        if messagebox.askyesno("Confirm", f"Delete user '{username}'?"):
            try:
                delete_user(username)
                refresh()
            except Exception:
                logging.exception("Failed to delete user")
                messagebox.showerror("Error", "Failed to delete user")

    def change_password():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Select", "Select a user")
            return
        username = tree.item(sel[0], "values")[0]
        new_pw = simpledialog.askstring("New Password", f"New password for {username}:", parent=win, show="*")
        if not new_pw:
            return
        
        # Validate new password strength
        is_valid, error_msg = validate_password_strength(new_pw)
        if not is_valid:
            messagebox.showerror("Weak Password", error_msg)
            return
        
        # Confirm password
        confirm_pw = simpledialog.askstring("Confirm Password", f"Confirm new password:", parent=win, show="*")
        if not confirm_pw or confirm_pw != new_pw:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        try:
            set_password(username, new_pw)
            messagebox.showinfo("Password", f"Password for '{sanitize_for_display(username)}' updated successfully")
        except Exception as e:
            logging.exception("Failed to set password")
            messagebox.showerror("Error", f"Failed to set password: {str(e)}")

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x")

    make_button(btn_frame, "Add", command=add_user, kind="success").pack(side="left", padx=4)
    make_button(btn_frame, "Delete", command=remove_user, kind="danger").pack(side="left", padx=4)
    make_button(btn_frame, "Change Password", command=change_password, kind="primary").pack(side="left", padx=4)

    refresh()

    return win
