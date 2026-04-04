import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import logging

from utils import AUDIT_LOG, load_users
from ui_theme import make_card, styled_label, make_button, frame


def open_audit_viewer(master=None, current_user=None):
    # Only admins allowed
    users = load_users()
    user_role = users.get(current_user, {}).get("role", "")
    if not current_user or user_role not in ["admin", "OWNER_ADMIN"]:
        try:
            messagebox.showerror("Permission Denied", f"Audit logs restricted to administrators. Your role: {user_role}")
        except Exception:
            pass
        return None

    win = tk.Toplevel(master) if master is not None else tk.Tk()
    win.title("Audit Log Viewer")
    win.geometry("900x500")

    top = frame(win, padding=12)
    top.pack(fill="both", expand=True)

    styled_label(top, "Audit Events", kind="heading").pack(anchor="w")

    toolbar = ttk.Frame(top)
    toolbar.pack(fill="x", pady=(6, 10))

    tk.Label(toolbar, text="Search:").pack(side="left", padx=(0, 8))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(toolbar, textvariable=search_var)
    search_entry.pack(side="left", fill="x", expand=True)

    def load_entries():
        rows = []
        if not os.path.exists(AUDIT_LOG):
            return rows
        try:
            with open(AUDIT_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    rows.append(obj)
        except Exception:
            logging.exception("Failed to read audit log")
        return rows

    cols = ("timestamp", "user", "action", "target", "details")
    tree = ttk.Treeview(top, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=150, anchor="w")
    tree.pack(fill="both", expand=True)

    def refresh(filter_text=None):
        tree.delete(*tree.get_children())
        entries = load_entries()
        q = (filter_text or "").lower()
        for e in entries:
            details = e.get("details")
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False)
            vals = (e.get("timestamp"), e.get("user"), e.get("action"), e.get("target"), details)
            if not q or q in " ".join([str(v).lower() for v in vals]):
                tree.insert("", "end", values=vals)

    def on_search(event=None):
        refresh(search_var.get())

    make_button(toolbar, "Search", command=on_search, kind="primary").pack(side="left", padx=6)
    make_button(toolbar, "Refresh", command=lambda: refresh(search_entry.get()), kind="secondary").pack(side="left")

    refresh()
    return win

def create_audit_tab(parent, current_user=None):
    """Embeddable version for notebook tabs."""
    tab = ttk.Frame(parent, padding=12)
    
    styled_label(tab, "Audit Events", kind="heading").pack(anchor="w")

    toolbar = ttk.Frame(tab)
    toolbar.pack(fill="x", pady=(6, 10))

    tk.Label(toolbar, text="Search:").pack(side="left", padx=(0, 8))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(toolbar, textvariable=search_var)
    search_entry.pack(side="left", fill="x", expand=True)

    def load_entries():
        rows = []
        if not os.path.exists(AUDIT_LOG):
            return rows
        try:
            with open(AUDIT_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    rows.append(obj)
        except Exception:
            logging.exception("Failed to read audit log")
        return rows

    cols = ("timestamp", "user", "action", "target", "details")
    tree = ttk.Treeview(tab, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c.capitalize())
        tree.column(c, width=150, anchor="w")
    tree.pack(fill="both", expand=True)

    def refresh(filter_text=None):
        tree.delete(*tree.get_children())
        entries = load_entries()
        q = (filter_text or "").lower()
        for e in entries:
            details = e.get("details")
            if isinstance(details, dict):
                details = json.dumps(details, ensure_ascii=False)
            vals = (e.get("timestamp"), e.get("user"), e.get("action"), e.get("target"), details)
            if not q or q in " ".join([str(v).lower() for v in vals]):
                tree.insert("", "end", values=vals)

    def on_search(event=None):
        refresh(search_var.get())

    make_button(toolbar, "Search", command=on_search, kind="primary").pack(side="left", padx=6)
    make_button(toolbar, "Refresh", command=lambda: refresh(search_var.get()), kind="secondary").pack(side="left")

    refresh()
    return tab
