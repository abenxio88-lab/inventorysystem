"""
Auto Issue Finder - Runs on Startup
=====================================
Automatically finds and displays ALL issues when app starts.
No more silent failures!
"""

import logging
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)


def check_and_show_issues(root):
    """
    Check for issues on startup and show them.
    Call this right after main window loads.
    """
    try:
        # Try to import error detector - if not available, skip health check
        try:
            from src.error_detector import detector, IssueSeverity
        except ImportError:
            logger.info("Health check skipped - error_detector module not available")
            return True

        issues = detector.check_all()

        if not issues:
            logger.info("✅ System health check passed - no issues")
            return True
        
        # Count by severity
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        
        # Log all issues
        logger.warning(f"🏥 System Health Check: {len(issues)} issues found")
        logger.warning(f"  Critical: {critical}, Errors: {errors}, Warnings: {warnings}")
        
        for issue in issues:
            logger.warning(f"  [{issue.code}] {issue.title}")
        
        # Show critical/error issues immediately
        blocking_issues = [i for i in issues if i.severity in [IssueSeverity.CRITICAL, IssueSeverity.ERROR]]
        
        if blocking_issues:
            # Show first blocking issue
            issue = blocking_issues[0]
            
            message = (
                f"⚠️ SYSTEM ISSUE DETECTED ⚠️\n\n"
                f"❌ {issue.title}\n\n"
                f"{issue.description}\n\n"
                f"👉 SOLUTION:\n{issue.solution}\n\n"
                f"{'='*60}\n"
                f"Total Issues: {len(issues)} ({critical} critical, {errors} errors, {warnings} warnings)\n"
                f"{'='*60}\n\n"
                f"Click 🏥 Health button (top bar) to see all issues."
            )
            
            # Schedule message box to show after main window loads
            root.after(1000, lambda: messagebox.showwarning("⚠️ System Health Alert", message))
        
        return len(blocking_issues) == 0
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return True  # Don't block app if health check itself fails


def add_health_check_to_button(root, notebook):
    """
    Add health check functionality to existing health button.
    Shows issues in a nice formatted way.
    """
    # Try to import error detector - if not available, show simple message
    try:
        from src.error_detector import detector, IssueSeverity
        error_detector_available = True
    except ImportError:
        error_detector_available = False
        logger.info("Health report disabled - error_detector module not available")

    def show_health_report():
        """Show health report in scrollable window."""
        # If error detector not available, show simple message
        if not error_detector_available:
            messagebox.showinfo(
                "🏥 System Health",
                "⚠️ Health check is not fully available.\n\n"
                "The error_detector module is missing.\n"
                "Basic system checks cannot be performed.\n\n"
                "Core application functionality is unaffected."
            )
            return

        issues = detector.check_all()
        
        if not issues:
            messagebox.showinfo(
                "🏥 System Health",
                "✅ All systems operational!\n\nNo issues detected.\nYour inventory system is healthy."
            )
            return
        
        # Create report window
        dlg = tk.Toplevel(root)
        dlg.title("🏥 System Health Report")
        dlg.geometry("800x600")
        dlg.transient(root)
        
        # Title
        title_frame = tk.Frame(dlg, bg="#2563EB", height=60)
        title_frame.pack(fill="x")
        
        tk.Label(
            title_frame,
            text="🏥 System Health Report",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#2563EB"
        ).pack(pady=15)
        
        # Summary
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        
        summary_frame = tk.Frame(dlg, bg="#FEF2F2", padx=20, pady=15)
        summary_frame.pack(fill="x", padx=20, pady=10)
        
        summary_text = f"📊 Found {len(issues)} issue(s): "
        summary_text += f"🔴 {critical} critical, " if critical else ""
        summary_text += f"🟠 {errors} errors, " if errors else ""
        summary_text += f"🟡 {warnings} warnings" if warnings else ""
        
        tk.Label(
            summary_frame,
            text=summary_text,
            font=("Segoe UI", 11, "bold"),
            bg="#FEF2F2",
            fg="#DC2626"
        ).pack()
        
        # Issue list
        tk.Label(
            dlg,
            text="Click each issue to see solution:",
            font=("Segoe UI", 9),
            fg="#64748B"
        ).pack(pady=(10, 5))
        
        # Scrollable frame with issues
        import tkinter.ttk as ttk
        
        container = ttk.Frame(dlg, padding=10)
        container.pack(fill="both", expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add issue cards
        for i, issue in enumerate(issues, 1):
            severity_color = {
                IssueSeverity.CRITICAL: "#DC2626",
                IssueSeverity.ERROR: "#EA580C",
                IssueSeverity.WARNING: "#CA8A04",
                IssueSeverity.INFO: "#2563EB"
            }
            
            severity_icon = {
                IssueSeverity.CRITICAL: "🔴",
                IssueSeverity.ERROR: "🟠",
                IssueSeverity.WARNING: "🟡",
                IssueSeverity.INFO: "🔵"
            }
            
            card = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
            card.pack(fill="x", pady=5)
            
            # Header
            header = tk.Frame(card, bg=severity_color[issue.severity], height=40)
            header.pack(fill="x")
            
            tk.Label(
                header,
                text=f"{severity_icon[issue.severity]} [{issue.code}] {issue.title}",
                font=("Segoe UI", 10, "bold"),
                fg="white",
                bg=severity_color[issue.severity],
                anchor="w",
                padx=15,
                pady=8
            ).pack()
            
            # Details
            details = tk.Frame(card, bg="white", padx=15, pady=10)
            details.pack(fill="x")
            
            tk.Label(
                details,
                text=f"Module: {issue.affected_module}",
                font=("Segoe UI", 9),
                fg="#64748B",
                bg="white",
                anchor="w"
            ).pack(anchor="w")
            
            tk.Label(
                details,
                text=f"Issue: {issue.description}",
                font=("Segoe UI", 9),
                fg="#1E293B",
                bg="white",
                anchor="w",
                wraplength=700,
                justify="left"
            ).pack(anchor="w", pady=(5, 10))
            
            # Solution box
            solution_box = tk.Frame(details, bg="#F0FDF4", relief="solid", bd=1)
            solution_box.pack(fill="x", pady=5)
            
            tk.Label(
                solution_box,
                text="👉 Solution:",
                font=("Segoe UI", 9, "bold"),
                fg="#166534",
                bg="#F0FDF4",
                anchor="w"
            ).pack(anchor="w", padx=10, pady=(8, 0))
            
            tk.Label(
                solution_box,
                text=issue.solution,
                font=("Segoe UI", 9),
                fg="#166534",
                bg="#F0FDF4",
                anchor="w",
                justify="left",
                wraplength=680
            ).pack(anchor="w", padx=10, pady=(0, 8))
        
        # Close button
        ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=10)
    
    return show_health_report
