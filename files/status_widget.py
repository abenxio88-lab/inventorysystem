"""
Connection Status Widget Module
================================
Reusable Tkinter widget showing online/offline status.
"""

import tkinter as tk
from tkinter import ttk

try:
    from .network import get_connectivity_monitor
    from .sync_engine import get_pending_sync_count
except (ImportError, ModuleNotFoundError):
    from network import get_connectivity_monitor
    from sync_engine import get_pending_sync_count


class ConnectionStatusWidget(ttk.Frame):
    """
    Status bar widget showing:
    - Online/Offline indicator (🟢/🔴)
    - Pending sync count
    - Last sync time
    - Manual sync button
    """
    
    def __init__(self, parent, on_sync_callback=None):
        super().__init__(parent)
        self.on_sync_callback = on_sync_callback
        self.monitor = get_connectivity_monitor()
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self):
        """Create the UI components."""
        # Status indicator frame
        self.configure(padding=5)
        
        # Online/Offline status
        self.status_label = tk.Label(
            self,
            text="🔴 Offline",
            font=("Segoe UI", 9),
            foreground="#dc3545"
        )
        self.status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Pending sync counter
        self.pending_frame = ttk.Frame(self)
        self.pending_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            self.pending_frame,
            text="⏳ Pending:",
            font=("Segoe UI", 9),
            foreground="#6c757d"
        ).pack(side=tk.LEFT)
        
        self.pending_label = tk.Label(
            self.pending_frame,
            text="0",
            font=("Segoe UI", 9, "bold"),
            foreground="#007bff"
        )
        self.pending_label.pack(side=tk.LEFT, padx=5)
        
        # Last sync time
        self.last_sync_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 8),
            foreground="#6c757d"
        )
        self.last_sync_label.pack(side=tk.LEFT, padx=10)
        
        # Manual sync button
        self.sync_button = ttk.Button(
            self,
            text="🔄 Sync Now",
            command=self._on_sync_click,
            width=12
        )
        self.sync_button.pack(side=tk.RIGHT, padx=5)
        
        # Status info button
        self.info_button = ttk.Button(
            self,
            text="ℹ️",
            command=self._show_status_info,
            width=3
        )
        self.info_button.pack(side=tk.RIGHT)
    
    def _start_monitoring(self):
        """Start monitoring connectivity and sync status."""
        # Register callback for connectivity changes
        self.monitor.add_callback(self._on_connectivity_change)
        
        # Update pending sync count periodically
        self._update_pending_count()
    
    def _on_connectivity_change(self, is_online: bool):
        """Handle connectivity status change."""
        self._update_status_display()
    
    def _update_status_display(self):
        """Update the status display."""
        is_online = self.monitor.is_online
        
        if is_online:
            self.status_label.config(text="🟢 Online", foreground="#28a745")
        else:
            self.status_label.config(text="🔴 Offline", foreground="#dc3545")
        
        # Update pending count
        self._update_pending_count()
    
    def _update_pending_count(self):
        """Update pending sync count display."""
        try:
            count = get_pending_sync_count()
            self.pending_label.config(text=str(count))
            
            if count > 0:
                self.pending_label.config(foreground="#dc3545")
            else:
                self.pending_label.config(foreground="#28a745")
        except Exception:
            pass
        
        # Schedule next update in 5 seconds
        self.after(5000, self._update_pending_count)
    
    def _on_sync_click(self):
        """Handle manual sync button click."""
        from .sync_engine import trigger_manual_sync
        
        self.sync_button.config(state='disabled', text="⏳ Syncing...")
        trigger_manual_sync()
        
        # Re-enable button after 3 seconds
        def reenable():
            self.sync_button.config(state='normal', text="🔄 Sync Now")
        self.after(3000, reenable)
        
        if self.on_sync_callback:
            self.on_sync_callback()
    
    def _show_status_info(self):
        """Show detailed status information."""
        info_window = tk.Toplevel(self)
        info_window.title("Connection Status")
        info_window.geometry("400x300")
        info_window.resizable(False, False)
        info_window.transient(self.winfo_toplevel())
        
        # Make modal
        info_window.grab_set()
        
        # Content frame
        content = ttk.Frame(info_window, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = tk.Label(
            content,
            text="System Status",
            font=("Segoe UI", 14, "bold")
        )
        title.pack(anchor=tk.W, pady=(0, 15))
        
        # Status details
        details = [
            ("Connection:", self.monitor.status_text),
            ("Last Check:", self.monitor.last_check.strftime("%Y-%m-%d %H:%M:%S") if self.monitor.last_check else "Never"),
            ("Pending Sync:", str(get_pending_sync_count())),
            ("Auto-Sync:", "Enabled" if self.monitor.is_online else "Disabled (Offline)"),
        ]
        
        for label, value in details:
            frame = ttk.Frame(content)
            frame.pack(fill=tk.X, pady=5)
            
            tk.Label(
                frame,
                text=f"{label}",
                font=("Segoe UI", 10, "bold"),
                width=15,
                anchor=tk.W
            ).pack(side=tk.LEFT)
            
            tk.Label(
                frame,
                text=value,
                font=("Segoe UI", 10)
            ).pack(side=tk.LEFT)
        
        # Error message if offline
        if not self.monitor.is_online and self.monitor.last_error:
            error_frame = ttk.LabelFrame(content, text="Last Error", padding=10)
            error_frame.pack(fill=tk.X, pady=15)
            
            tk.Label(
                error_frame,
                text=self.monitor.last_error,
                font=("Segoe UI", 9),
                foreground="#dc3545",
                wraplength=350,
                justify=tk.LEFT
            ).pack(anchor=tk.W)
        
        # Close button
        ttk.Button(
            content,
            text="Close",
            command=info_window.destroy
        ).pack(pady=(20, 0))


class StatusBar(ttk.Frame):
    """
    Complete status bar with connection status and app info.
    """
    
    def __init__(self, parent, app_name="Inventory System"):
        super().__init__(parent)
        self.app_name = app_name
        self._setup_ui()
    
    def _setup_ui(self):
        """Create status bar UI."""
        self.configure(padding=5)
        
        # Left side - App info
        self.app_label = tk.Label(
            self,
            text=f"{self.app_name} v2.0",
            font=("Segoe UI", 9),
            foreground="#6c757d"
        )
        self.app_label.pack(side=tk.LEFT, padx=10)
        
        # Right side - Connection status widget
        self.connection_widget = ConnectionStatusWidget(self)
        self.connection_widget.pack(side=tk.RIGHT)
    
    def set_message(self, message: str):
        """Set a temporary status message."""
        self.app_label.config(text=message)


def create_status_bar(parent, app_name="Inventory System"):
    """Create and return a status bar."""
    return StatusBar(parent, app_name)
