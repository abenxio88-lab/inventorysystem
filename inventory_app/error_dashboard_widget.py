"""
Developer Error Dashboard Widget
=================================
Real-time error tracking widget for the main dashboard.
Shows error count, recent errors, and allows quick debugging.

Features:
- Live error counter
- Color-coded by severity
- Click to see error details
- Export errors button
- Clear resolved button
- Auto-refresh
"""

import os
import sys
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    import customtkinter as ctk
    CTk_AVAILABLE = True
except ImportError:
    CTk_AVAILABLE = False
    import tkinter as tk

from error_manager import get_error_manager, AppError, ErrorSeverity


# ============================================================================
# ERROR DASHBOARD WIDGET
# ============================================================================

class ErrorDashboardWidget(ctk.CTkFrame if CTk_AVAILABLE else object):
    """
    Real-time error tracking widget.
    Displays on main dashboard for developer visibility.
    """
    
    def __init__(self, parent, auto_refresh: bool = True,
                 refresh_interval: int = 5000):
        """
        Initialize error dashboard widget.
        
        Args:
            parent: Parent widget
            auto_refresh: Auto-refresh error count
            refresh_interval: Refresh interval in milliseconds
        """
        if CTk_AVAILABLE:
            super().__init__(parent)
        else:
            self._parent = parent
            self._frame = tk.Frame(parent)
        
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.error_manager = get_error_manager()
        
        # Store widget references
        self.count_label = None
        self.critical_label = None
        self.warning_label = None
        self.recent_list = None
        self.refresh_timer = None
        
        # Build UI
        self._create_widgets()
        
        # Register callback for real-time updates
        self.error_manager.register_callback(self._on_new_error)
        
        # Start auto-refresh
        if auto_refresh:
            self._start_auto_refresh()
        
        # Initial update
        self._update_display()
    
    def _create_widgets(self):
        """Create widget UI elements."""
        if not CTk_AVAILABLE:
            # Fallback for standard tkinter
            self._create_tkinter_widgets()
            return
        
        # Main container
        self.configure(fg_color='#2C2C2C', corner_radius=10)
        
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="🔴 Error Monitor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='#F44336'
        )
        title_label.grid(row=0, column=0, padx=15, pady=(15, 10), sticky='w')
        
        # Error counts frame
        counts_frame = ctk.CTkFrame(self, fg_color='transparent')
        counts_frame.grid(row=1, column=0, padx=15, pady=5, sticky='ew')
        
        # Total errors
        total_frame = ctk.CTkFrame(counts_frame, fg_color='#F44336', corner_radius=8)
        total_frame.grid(row=0, column=0, padx=5, sticky='ew')
        
        self.count_label = ctk.CTkLabel(
            total_frame,
            text="0 Errors",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='white'
        )
        self.count_label.pack(padx=15, pady=8)
        
        # Critical errors
        critical_frame = ctk.CTkFrame(counts_frame, fg_color='#9C27B0', corner_radius=8)
        critical_frame.grid(row=0, column=1, padx=5, sticky='ew')
        
        self.critical_label = ctk.CTkLabel(
            critical_frame,
            text="🔥 0 Critical",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='white'
        )
        self.critical_label.pack(padx=15, pady=8)
        
        # Warnings
        warning_frame = ctk.CTkFrame(counts_frame, fg_color='#FF9800', corner_radius=8)
        warning_frame.grid(row=0, column=2, padx=5, sticky='ew')
        
        self.warning_label = ctk.CTkLabel(
            warning_frame,
            text="⚠️ 0 Warnings",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='white'
        )
        self.warning_label.pack(padx=15, pady=8)
        
        # Configure grid weights
        counts_frame.grid_columnconfigure(0, weight=1)
        counts_frame.grid_columnconfigure(1, weight=1)
        counts_frame.grid_columnconfigure(2, weight=1)
        
        # Recent errors section
        recent_title = ctk.CTkLabel(
            self,
            text="Recent Errors:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#AAAAAA'
        )
        recent_title.grid(row=2, column=0, padx=15, pady=(15, 5), sticky='w')
        
        # Scrollable frame for recent errors
        self.recent_frame = ctk.CTkScrollableFrame(
            self,
            height=200,
            fg_color='#1A1A1A',
            corner_radius=8
        )
        self.recent_frame.grid(row=3, column=0, padx=15, pady=5, sticky='nsew')
        
        # Buttons frame
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.grid(row=4, column=0, padx=15, pady=10, sticky='ew')
        
        # Export button
        export_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Export Errors",
            command=self._export_errors,
            width=150,
            fg_color='#2196F3',
            hover_color='#1976D2'
        )
        export_btn.grid(row=0, column=0, padx=5)
        
        # Clear resolved button
        clear_btn = ctk.CTkButton(
            btn_frame,
            text="✅ Clear Resolved",
            command=self._clear_resolved,
            width=150,
            fg_color='#4CAF50',
            hover_color='#388E3C'
        )
        clear_btn.grid(row=0, column=1, padx=5)
        
        # View log button
        log_btn = ctk.CTkButton(
            btn_frame,
            text="📄 Open Log File",
            command=self._open_log_file,
            width=150,
            fg_color='#607D8B',
            hover_color='#455A64'
        )
        log_btn.grid(row=0, column=2, padx=5)
        
        # Configure grid weight
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def _create_tkinter_widgets(self):
        """Create widgets for standard tkinter (fallback)."""
        frame = self._frame
        
        # Title
        title_label = tk.Label(
            frame,
            text="🔴 Error Monitor",
            font=('Arial', 16, 'bold'),
            fg='#F44336',
            bg='#2C2C2C'
        )
        title_label.pack(padx=15, pady=(15, 10), anchor='w')
        
        # Count label
        self.count_label = tk.Label(
            frame,
            text="0 Errors",
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#F44336'
        )
        self.count_label.pack(padx=15, pady=5, fill='x')
        
        # Recent errors label
        recent_label = tk.Label(
            frame,
            text="Recent Errors:",
            font=('Arial', 12, 'bold'),
            fg='#AAAAAA',
            bg='#2C2C2C'
        )
        recent_label.pack(padx=15, pady=(15, 5), anchor='w')
        
        # Recent errors listbox
        self.recent_list = tk.Listbox(
            frame,
            height=10,
            bg='#1A1A1A',
            fg='#FFFFFF',
            selectbackground='#2196F3',
            font=('Consolas', 10)
        )
        self.recent_list.pack(padx=15, pady=5, fill='both', expand=True)
        
        # Bind double-click to show details
        self.recent_list.bind('<Double-Button-1>', self._show_error_details)
    
    def _update_display(self):
        """Update widget display with current error stats."""
        try:
            summary = self.error_manager.get_error_summary()
            
            if CTk_AVAILABLE and self.count_label:
                self.count_label.configure(text=f"{summary['total_errors']} Errors")
                self.critical_label.configure(text=f"🔥 {summary['critical']} Critical")
                self.warning_label.configure(text=f"⚠️ {summary['warning']} Warnings")
                
                # Update recent errors list
                self._update_recent_errors()
            elif not CTk_AVAILABLE and self.count_label:
                self.count_label.configure(text=f"{summary['total_errors']} Errors")
                
                # Update listbox
                if self.recent_list:
                    self.recent_list.delete(0, tk.END)
                    errors = self.error_manager.get_errors(limit=10)
                    for error in errors:
                        icon = ErrorSeverity.ICONS.get(error.severity, '❌')
                        self.recent_list.insert(
                            tk.END,
                            f"{icon} [{error.severity.upper()}] {error.message[:50]}..."
                        )
            
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def _update_recent_errors(self):
        """Update recent errors list in scrollable frame."""
        # Clear existing
        for widget in self.recent_frame.winfo_children():
            widget.destroy()
        
        # Get recent errors
        errors = self.error_manager.get_errors(limit=10)
        
        if not errors:
            no_errors = ctk.CTkLabel(
                self.recent_frame,
                text="✅ No errors yet!",
                font=ctk.CTkFont(size=12),
                text_color='#4CAF50'
            )
            no_errors.pack(padx=10, pady=20)
            return
        
        # Add error items
        for error in errors:
            error_item = self._create_error_item(error)
            error_item.pack(padx=10, pady=5, fill='x')
    
    def _create_error_item(self, error: AppError) -> ctk.CTkFrame:
        """Create a clickable error item widget."""
        item = ctk.CTkFrame(self.recent_frame, fg_color='#2A2A2A', corner_radius=5)
        
        # Icon and severity
        icon = ErrorSeverity.ICONS.get(error.severity, '❌')
        color = ErrorSeverity.COLORS.get(error.severity, '#F44336')
        
        header = ctk.CTkFrame(item, fg_color=color, height=30, corner_radius=3)
        header.pack(fill='x', padx=5, pady=5)
        
        severity_label = ctk.CTkLabel(
            header,
            text=f"{icon} {error.severity.upper()}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color='white'
        )
        severity_label.pack(side='left', padx=10)
        
        time_label = ctk.CTkLabel(
            header,
            text=error.timestamp.strftime('%H:%M:%S'),
            font=ctk.CTkFont(size=10),
            text_color='white'
        )
        time_label.pack(side='right', padx=10)
        
        # Message
        msg_label = ctk.CTkLabel(
            item,
            text=error.message[:100],
            font=ctk.CTkFont(size=11),
            text_color='#CCCCCC',
            wraplength=500,
            justify='left'
        )
        msg_label.pack(padx=10, pady=(0, 10), anchor='w')
        
        # Bind click to show details
        item.bind('<Button-1>', lambda e, err=error: self._show_error_details_popup(err))
        header.bind('<Button-1>', lambda e, err=error: self._show_error_details_popup(err))
        msg_label.bind('<Button-1>', lambda e, err=error: self._show_error_details_popup(err))
        
        return item
    
    def _on_new_error(self, error: AppError):
        """Callback when new error is detected."""
        # Schedule update on main thread
        if CTk_AVAILABLE:
            self.after(0, self._update_display)
        else:
            self._frame.after(0, self._update_display)
    
    def _start_auto_refresh(self):
        """Start auto-refresh timer."""
        def refresh():
            self._update_display()
            if self.auto_refresh:
                self.refresh_timer = self.after(self.refresh_interval, refresh)
        
        self.refresh_timer = self.after(self.refresh_interval, refresh)
    
    def _stop_auto_refresh(self):
        """Stop auto-refresh timer."""
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
            self.refresh_timer = None
    
    def _show_error_details_popup(self, error: AppError):
        """Show error details in popup window."""
        popup = ctk.CTkToplevel(self)
        popup.title(f"Error Details - {error.id}")
        popup.geometry("700x500")
        
        # Title
        title = ctk.CTkLabel(
            popup,
            text=f"{ErrorSeverity.ICONS.get(error.severity)} {error.severity.upper()}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ErrorSeverity.COLORS.get(error.severity, '#F44336')
        )
        title.pack(padx=20, pady=15)
        
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(popup, fg_color='#1A1A1A', corner_radius=10)
        scroll.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Error details
        details = [
            ("Message:", error.message),
            ("Module:", error.module),
            ("Function:", error.function),
            ("User Action:", error.user_action),
            ("Time:", error.timestamp.strftime('%Y-%m-%d %H:%M:%S')),
        ]
        
        if error.exception:
            details.append(("Exception:", f"{type(error.exception).__name__}: {error.exception}"))
        
        for label, value in details:
            lbl = ctk.CTkLabel(
                scroll,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color='#AAAAAA',
                justify='left'
            )
            lbl.pack(anchor='w', padx=15, pady=(10, 0))
            
            val = ctk.CTkLabel(
                scroll,
                text=str(value),
                font=ctk.CTkFont(size=11),
                text_color='#FFFFFF',
                justify='left',
                wraplength=600
            )
            val.pack(anchor='w', padx=15, pady=(0, 5))
        
        # Traceback
        if error.traceback:
            trace_lbl = ctk.CTkLabel(
                scroll,
                text="Stack Trace:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color='#F44336',
                justify='left'
            )
            trace_lbl.pack(anchor='w', padx=15, pady=(15, 5))
            
            trace_text = ctk.CTkTextbox(
                scroll,
                height=150,
                fg_color='#000000',
                text_color='#00FF00',
                font=ctk.CTkFont(family='Consolas', size=10)
            )
            trace_text.pack(fill='x', padx=15, pady=5)
            trace_text.insert('0.0', error.traceback)
            trace_text.configure(state='disabled')
        
        # Close button
        close_btn = ctk.CTkButton(
            popup,
            text="Close",
            command=popup.destroy,
            width=150
        )
        close_btn.pack(pady=15)
    
    def _export_errors(self):
        """Export errors to JSON file."""
        filepath = self.error_manager.export_errors()
        if filepath:
            print(f"✅ Errors exported to: {filepath}")
    
    def _clear_resolved(self):
        """Clear resolved errors."""
        self.error_manager.clear_resolved()
        self._update_display()
    
    def _open_log_file(self):
        """Open error log file."""
        import webbrowser
        log_file = self.error_manager.log_file
        if os.path.exists(log_file):
            webbrowser.open(log_file)
        else:
            print(f"Log file not found: {log_file}")
    
    def destroy(self):
        """Cleanup on destroy."""
        self._stop_auto_refresh()
        self.error_manager.unregister_callback(self._on_new_error)
        if CTk_AVAILABLE:
            super().destroy()
        else:
            self._frame.destroy()


# ============================================================================
# ERROR NOTIFICATION TOAST
# ============================================================================

class ErrorNotificationToast:
    """Popup toast notification for errors."""
    
    def __init__(self, parent, error: AppError, duration: int = 5000):
        """
        Show error toast notification.
        
        Args:
            parent: Parent window
            error: Error to display
            duration: How long to show (ms), 0 = until closed
        """
        self.parent = parent
        self.error = error
        self.duration = duration
        
        self._show()
    
    def _show(self):
        """Show toast notification."""
        if not CTk_AVAILABLE:
            # Fallback to messagebox
            from tkinter import messagebox
            messagebox.showerror(
                f"❌ {self.error.severity.upper()}",
                f"{self.error.message}\n\nModule: {self.error.module}"
            )
            return
        
        # Create toast window
        self.toast = ctk.CTkToplevel(self.parent)
        self.toast.title("Error Detected")
        self.toast.geometry("500x150+100+100")
        self.toast.attributes('-topmost', True)
        
        # Color based on severity
        color = ErrorSeverity.COLORS.get(self.error.severity, '#F44336')
        self.toast.configure(fg_color=color)
        
        # Icon and message
        icon = ErrorSeverity.ICONS.get(self.error.severity, '❌')
        
        msg_label = ctk.CTkLabel(
            self.toast,
            text=f"{icon} {self.error.message[:80]}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color='white'
        )
        msg_label.pack(padx=20, pady=15)
        
        # Details button
        details_btn = ctk.CTkButton(
            self.toast,
            text="View Details",
            command=lambda: self._show_details(),
            width=120,
            fg_color='white',
            text_color=color
        )
        details_btn.pack(pady=10)
        
        # Auto-close if duration set
        if self.duration > 0:
            self.toast.after(self.duration, self._close)
    
    def _show_details(self):
        """Show full error details."""
        # Would need reference to dashboard widget
        pass
    
    def _close(self):
        """Close toast."""
        if hasattr(self, 'toast') and self.toast.winfo_exists():
            self.toast.destroy()


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def create_error_dashboard(parent, auto_refresh: bool = True) -> ErrorDashboardWidget:
    """Create and return error dashboard widget."""
    return ErrorDashboardWidget(parent, auto_refresh=auto_refresh)


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    # Test the error dashboard
    print("="*60)
    print("Error Dashboard Widget - Test")
    print("="*60)
    
    # Create test window
    if CTk_AVAILABLE:
        root = ctk.CTk()
        root.title("Error Dashboard Test")
        root.geometry("600x500")
        
        # Create widget
        dashboard = ErrorDashboardWidget(root, auto_refresh=True)
        dashboard.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Generate test errors
        from error_manager import report_error, report_warning, report_critical
        
        def generate_test_errors():
            report_info("Test info message", module='Test')
            report_warning("Test warning message", module='Test')
            
            try:
                1 / 0
            except:
                report_error("Test division by zero", module='Test')
            
            try:
                raise ValueError("Test critical error")
            except:
                report_critical("Test critical failure", module='Test')
        
        # Button to generate test errors
        test_btn = ctk.CTkButton(
            root,
            text="🧪 Generate Test Errors",
            command=generate_test_errors
        )
        test_btn.pack(pady=10)
        
        print("\n✅ Click 'Generate Test Errors' to test the dashboard")
        
        root.mainloop()
    else:
        print("❌ CustomTkinter not available - cannot run GUI test")
        print("Run this test from the main application instead")
