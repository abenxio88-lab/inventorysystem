"""
Mintaka Sphere - Development Status Dashboard
==============================================
Shows development progress, issues, and system status.

Access: Admin only -> Dashboard tab or separate menu
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

try:
    from .dev_logging import get_status, get_dev_logger, save_report
    from .ui_theme import (
        make_card, make_glass_card, make_button, styled_label,
        create_divider, get_color, FONT_HEADING, SUBHEADING_FONT,
        FONT_SMALL, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY,
        COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    )
except (ImportError, ModuleNotFoundError):
    from dev_logging import get_status, get_dev_logger, save_report
    from ui_theme import (
        make_card, make_glass_card, make_button, styled_label,
        create_divider, get_color, FONT_HEADING, SUBHEADING_FONT,
        FONT_SMALL, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_PRIMARY,
        COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
    )


def create_dev_status_dashboard(parent, current_user: str = None):
    """
    Create development status dashboard
    
    Args:
        parent: Parent widget
        current_user: Current username (for admin check)
    
    Returns:
        Dashboard frame
    """
    # Check admin permission
    try:
        from .utils import load_users
    except (ImportError, ModuleNotFoundError):
        from utils import load_users
    
    users = load_users()
    if current_user and users.get(current_user, {}).get("role") not in ["admin", "OWNER_ADMIN"]:
        warning_label = styled_label(
            parent,
            "⛔ Access Denied: Admin privileges required",
            font=FONT_HEADING,
            foreground=COLOR_DANGER
        )
        warning_label.pack(pady=50)
        return parent
    
    # Main container
    dashboard_frame = make_glass_card(parent, padx=30, pady=30)
    
    # Header
    header_frame = ttk.Frame(dashboard_frame)
    header_frame.pack(fill="x", pady=(0, 20))
    
    title_label = styled_label(
        header_frame,
        "🔧 Development Status Dashboard",
        font=FONT_HEADING,
        foreground=get_color('text_main')
    )
    title_label.pack(anchor="w")
    
    subtitle_label = styled_label(
        header_frame,
        "Track development progress, issues, and system health",
        font=FONT_SMALL,
        foreground=get_color('text_muted')
    )
    subtitle_label.pack(anchor="w", pady=(8, 0))
    
    create_divider(header_frame, orientation="horizontal").pack(fill="x", pady=(15, 25))
    
    # Get status
    status = get_status()
    
    # Status cards
    cards_frame = ttk.Frame(dashboard_frame)
    cards_frame.pack(fill="x", pady=(0, 30))
    
    # Card configurations
    card_configs = [
        {
            "title": "📝 Total Logs",
            "value": str(status.get("log_count", 0)),
            "color": COLOR_PRIMARY,
            "icon": "📝"
        },
        {
            "title": "⚠️ Total Issues",
            "value": str(status.get("total_issues", 0)),
            "color": COLOR_WARNING if status.get("total_issues", 0) > 0 else COLOR_SUCCESS,
            "icon": "⚠️"
        },
        {
            "title": "🔴 Critical",
            "value": str(status.get("critical_issues", 0)),
            "color": COLOR_DANGER if status.get("critical_issues", 0) > 0 else COLOR_SUCCESS,
            "icon": "🔴"
        },
        {
            "title": "✅ Open Issues",
            "value": str(status.get("open_issues", 0)),
            "color": COLOR_WARNING if status.get("open_issues", 0) > 0 else COLOR_SUCCESS,
            "icon": "✅"
        }
    ]
    
    # Create cards
    for config in card_configs:
        card_container = ttk.Frame(cards_frame)
        card_container.pack(side="left", expand=True, fill="both", padx=(0, 15))
        
        card = make_card(card_container, padx=20, pady=20)
        card.pack(fill="both", expand=True)
        
        # Icon
        icon_label = styled_label(card, config["icon"], font=("Segoe UI", 28))
        icon_label.pack(pady=(0, 8))
        
        # Value
        value_label = styled_label(
            card,
            config["value"],
            font=FONT_HEADING,
            foreground=config["color"]
        )
        value_label.pack()
        
        # Title
        styled_label(
            card,
            config["title"],
            font=FONT_SMALL,
            foreground=get_color('text_muted')
        ).pack(pady=(4, 0))
    
    # Issues section
    issues_frame = make_card(dashboard_frame, padx=25, pady=20)
    issues_frame.pack(fill="x", pady=(0, 20))
    
    issues_title = styled_label(
        issues_frame,
        f"📋 Recent Issues ({status.get('total_issues', 0)} total)",
        font=SUBHEADING_FONT,
        foreground=get_color('text_main')
    )
    issues_title.pack(anchor="w", pady=(0, 15))
    
    # Show recent issues
    recent_issues = status.get("recent_issues", [])
    
    if recent_issues:
        for issue in reversed(recent_issues[-5:]):  # Last 5 issues
            issue_frame = ttk.Frame(issues_frame)
            issue_frame.pack(fill="x", pady=4)
            
            # Severity indicator
            severity_colors = {
                "low": COLOR_SUCCESS,
                "medium": COLOR_WARNING,
                "high": COLOR_DANGER,
                "critical": "#991B1B"
            }
            severity_color = severity_colors.get(issue.get("severity", "medium"), COLOR_WARNING)
            
            severity_dot = styled_label(
                issue_frame,
                "●",
                font=("Segoe UI", 8),
                foreground=severity_color
            )
            severity_dot.pack(side="left", padx=(0, 8))
            
            # Issue info
            issue_info = ttk.Frame(issue_frame)
            issue_info.pack(side="left", fill="x", expand=True)
            
            issue_title_lbl = styled_label(
                issue_info,
                issue.get("title", "Unknown Issue"),
                font=FONT_SMALL,
                foreground=get_color('text_main')
            )
            issue_title_lbl.pack(anchor="w")
            
            issue_meta = styled_label(
                issue_info,
                f"Module: {issue.get('module', 'app')} | Status: {issue.get('status', 'open')}",
                font=("Segoe UI", 8),
                foreground=get_color('text_muted')
            )
            issue_meta.pack(anchor="w")
    else:
        no_issues = styled_label(
            issues_frame,
            "✅ No issues reported - System is healthy!",
            font=FONT_SMALL,
            foreground=COLOR_SUCCESS
        )
        no_issues.pack(anchor="w", pady=10)
    
    # Action buttons
    buttons_frame = ttk.Frame(dashboard_frame)
    buttons_frame.pack(fill="x", pady=(20, 0))
    
    def on_refresh():
        """Refresh status"""
        for widget in dashboard_frame.winfo_children():
            widget.destroy()
        create_dev_status_dashboard(dashboard_frame, current_user)
    
    def on_save_report():
        """Save report"""
        try:
            filename = save_report()
            from tkinter import messagebox
            messagebox.showinfo("Report Saved", f"Development report saved:\n{filename}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to save report:\n{e}")
    
    def on_log_test():
        """Test logging"""
        try:
            from .dev_logging import info, report_issue
        except (ImportError, ModuleNotFoundError):
            from dev_logging import info, report_issue
        
        info("Test log entry from dashboard", "test")
        report_issue(
            "Test Issue",
            "This is a test issue created from the dashboard",
            "low",
            "test"
        )
        
        # Refresh
        on_refresh()
    
    refresh_btn = make_button(buttons_frame, "🔄 Refresh", on_refresh, kind="secondary")
    refresh_btn.pack(side="left", padx=(0, 10))
    
    save_btn = make_button(buttons_frame, "💾 Save Report", on_save_report, kind="primary")
    save_btn.pack(side="left", padx=(0, 10))
    
    test_btn = make_button(buttons_frame, "🧪 Test Log", on_log_test, kind="secondary")
    test_btn.pack(side="left")
    
    return dashboard_frame


def open_dev_dashboard(parent, current_user: str = None):
    """
    Open development dashboard in new window
    
    Args:
        parent: Parent window
        current_user: Current username
    """
    win = tk.Toplevel(parent) if parent else tk.Toplevel()
    win.title("🔧 Development Status")
    win.geometry("900x700")
    win.minsize(800, 600)
    win.resizable(True, True)
    
    if parent:
        win.transient(parent)
        win.grab_set()
    
    # Create dashboard
    dashboard = create_dev_status_dashboard(win, current_user)
    dashboard.pack(fill="both", expand=True, padx=20, pady=20)
    
    win.wait_window()


__all__ = [
    "create_dev_status_dashboard",
    "open_dev_dashboard"
]
