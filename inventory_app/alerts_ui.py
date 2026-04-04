"""
Alerts UI Module
================
User interface for viewing and managing alerts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_PRIMARY
from alerts import alert_manager, get_unread_alerts


def create_alerts_tab(parent, current_user=None):
    """
    Creates the alerts management tab.
    """
    window = ttk.Frame(parent, padding=15)
    
    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))
    
    styled_label(header_frame, "🔔 Alerts & Notifications", font=FONT_BOLD).pack(side=tk.LEFT)
    
    # Actions
    actions_frame = ttk.Frame(header_frame)
    actions_frame.pack(side=tk.RIGHT)
    
    def refresh_alerts():
        window.refresh_alerts()
    
    make_button(actions_frame, "🔄 Refresh", command=refresh_alerts, kind="secondary").pack(side=tk.LEFT, padx=5)
    make_button(actions_frame, "✅ Mark All Read", command=lambda: mark_all_read(window), kind="success").pack(side=tk.LEFT, padx=5)
    
    # Summary cards
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", pady=(0, 15))
    summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
    
    def create_summary_card(parent, title, value, color, col):
        card = make_card(parent, padding=15)
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        
        title_label = styled_label(card, text=title, font=("Segoe UI", 10), foreground="#6c757d")
        title_label.pack(anchor="w")
        
        value_label = styled_label(card, text=str(value), font=("Segoe UI", 24, "bold"), foreground=color)
        value_label.pack(anchor="w", pady=(5, 0))
        
        return value_label
    
    # Create summary cards (will be updated by update_summary)
    unread_lbl = create_summary_card(summary_frame, "Unread", 0, COLOR_DANGER, 0)
    critical_lbl = create_summary_card(summary_frame, "Critical", 0, COLOR_DANGER, 1)
    warning_lbl = create_summary_card(summary_frame, "Warnings", 0, COLOR_WARNING, 2)
    total_lbl = create_summary_card(summary_frame, "Total", 0, COLOR_PRIMARY, 3)
    
    # Store labels for updates
    window.summary_labels = {
        'unread': unread_lbl,
        'critical': critical_lbl,
        'warning': warning_lbl,
        'total': total_lbl
    }
    
    # Filter toolbar
    filter_frame = ttk.Frame(window)
    filter_frame.pack(fill="x", pady=(0, 10))
    
    styled_label(filter_frame, "Filter:").pack(side=tk.LEFT, padx=(0, 10))
    
    filter_var = tk.StringVar(value="all")
    filter_combo = ttk.Combobox(
        filter_frame,
        textvariable=filter_var,
        values=["all", "unread", "critical", "high", "medium", "low"],
        state="readonly",
        width=15
    )
    filter_combo.pack(side=tk.LEFT, padx=5)
    
    type_filter_var = tk.StringVar(value="all")
    type_combo = ttk.Combobox(
        filter_frame,
        textvariable=type_filter_var,
        values=["all", "low_stock", "warranty_expiry", "out_of_stock", "system"],
        state="readonly",
        width=20
    )
    type_combo.pack(side=tk.LEFT, padx=5)
    
    def apply_filter():
        window.refresh_alerts()
    
    make_button(filter_frame, "Apply", command=apply_filter, kind="primary").pack(side=tk.LEFT, padx=10)
    
    # Alerts table
    table_frame = make_card(window, padding=10)
    table_frame.pack(fill="both", expand=True)
    
    columns = ("severity", "type", "title", "message", "date", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    
    column_map = {
        "severity": ("!", 50),
        "type": ("Type", 120),
        "title": ("Title", 200),
        "message": ("Message", 400),
        "date": ("Date", 150),
        "status": ("Status", 100)
    }
    
    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text, anchor="w")
        tree.column(col, width=width, anchor="w" if col != "severity" else "center", minwidth=80)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.pack(side=tk.LEFT, fill="both", expand=True)
    
    # Action buttons
    action_bar = ttk.Frame(window)
    action_bar.pack(fill="x", pady=(10, 0))
    
    def on_mark_read():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an alert to mark as read")
            return
        
        if alert_manager:
            for item in sel:
                alert_id = tree.item(item, "tags")[0] if tree.item(item, "tags") else None
                if alert_id:
                    alert_manager.mark_as_read(int(alert_id))
            
            window.refresh_alerts()
            messagebox.showinfo("Success", "Alert(s) marked as read")
    
    def on_acknowledge():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an alert to acknowledge")
            return
        
        if alert_manager and current_user:
            for item in sel:
                alert_id = tree.item(item, "tags")[0] if tree.item(item, "tags") else None
                if alert_id:
                    alert_manager.acknowledge_alert(int(alert_id), current_user)
            
            window.refresh_alerts()
            messagebox.showinfo("Success", "Alert(s) acknowledged")
    
    def on_delete():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Please select an alert to delete")
            return
        
        if messagebox.askyesno("Confirm", "Delete selected alert(s)?"):
            if alert_manager:
                for item in sel:
                    alert_id = tree.item(item, "tags")[0] if tree.item(item, "tags") else None
                    if alert_id:
                        alert_manager.delete_alert(int(alert_id))
                
                window.refresh_alerts()
                messagebox.showinfo("Success", "Alert(s) deleted")
    
    make_button(action_bar, "📖 Mark Read", command=on_mark_read, kind="secondary").pack(side=tk.LEFT, padx=5)
    make_button(action_bar, "✓ Acknowledge", command=on_acknowledge, kind="primary").pack(side=tk.LEFT, padx=5)
    make_button(action_bar, "🗑️ Delete", command=on_delete, kind="danger").pack(side=tk.LEFT, padx=5)
    
    # Store state
    window.filter_var = filter_var
    window.type_filter_var = type_filter_var
    window.tree = tree
    
    def refresh():
        """Refresh alerts display."""
        if not alert_manager:
            return
        
        # Get alerts
        filter_type = filter_var.get()
        type_filter = type_filter_var.get()
        
        if filter_type == "unread":
            alerts = alert_manager.get_unread_alerts()
        else:
            alerts = alert_manager.get_all_alerts()
        
        # Apply filters
        filtered = []
        for alert in alerts:
            if type_filter != "all" and alert.get('alert_type') != type_filter:
                continue
            if filter_type != "unread" and filter_type != "all":
                if alert.get('severity') != filter_type:
                    continue
            filtered.append(alert)
        
        # Update table
        tree.delete(*tree.get_children())
        
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵'
        }
        
        for alert in filtered:
            severity_icon = severity_icons.get(alert.get('severity', 'low'), '⚪')
            
            status = "Read" if alert.get('is_read') else "Unread"
            if alert.get('is_acknowledged'):
                status = "Acknowledged"
            
            tags = (str(alert.get('id', '')),)
            
            tree.insert("", "end", values=(
                severity_icon,
                alert.get('alert_type', '').replace('_', ' ').title(),
                alert.get('title', ''),
                alert.get('message', '')[:100] + ('...' if len(alert.get('message', '')) > 100 else ''),
                alert.get('created_at', '')[:16] if alert.get('created_at') else '',
                status
            ), tags=tags)
        
        # Update summary
        update_summary(window)
    
    window.refresh_alerts = refresh
    window.refresh_alerts()
    
    return window


def update_summary(window):
    """Update summary cards."""
    if not alert_manager or not hasattr(window, 'summary_labels'):
        return
    
    try:
        unread = alert_manager.get_alert_count(unread_only=True)
        all_alerts = alert_manager.get_all_alerts()
        
        critical = sum(1 for a in all_alerts if a.get('severity') == 'critical' and not a.get('is_read'))
        warning = sum(1 for a in all_alerts if a.get('severity') in ['high', 'medium'] and not a.get('is_read'))
        total = len(all_alerts)
        
        window.summary_labels['unread'].config(text=str(unread))
        window.summary_labels['critical'].config(text=str(critical))
        window.summary_labels['warning'].config(text=str(warning))
        window.summary_labels['total'].config(text=str(total))
    except Exception as e:
        logging.error(f"Failed to update alert summary: {e}")


def mark_all_read(window):
    """Mark all alerts as read."""
    if not alert_manager:
        return
    
    count = alert_manager.mark_all_as_read()
    window.refresh_alerts()
    messagebox.showinfo("Success", f"Marked {count} alert(s) as read")
