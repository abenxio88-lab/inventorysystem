"""
Connection Status Widget Module
================================
Reusable PySide6 widget showing online/offline status.
"""

from PySide6 import QtWidgets, QtCore, QtGui

try:
    from .network import get_connectivity_monitor
    from .sync_engine import get_pending_sync_count
except (ImportError, ModuleNotFoundError):
    from network import get_connectivity_monitor
    from sync_engine import get_pending_sync_count


class ConnectionStatusWidget(QtWidgets.QWidget):
    """
    Status bar widget showing:
    - Online/Offline indicator (green/red)
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
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Online/Offline status
        self.status_label = QtWidgets.QLabel("\U0001f534 Offline")
        self.status_label.setStyleSheet("color: #dc3545; font-size: 9pt; font-family: 'Segoe UI';")
        layout.addWidget(self.status_label)

        # Pending sync counter
        self.pending_frame = QtWidgets.QWidget()
        pending_layout = QtWidgets.QHBoxLayout(self.pending_frame)
        pending_layout.setContentsMargins(10, 0, 10, 0)

        pending_title = QtWidgets.QLabel("\u23f3 Pending:")
        pending_title.setStyleSheet("color: #6c757d; font-size: 9pt; font-family: 'Segoe UI';")
        pending_layout.addWidget(pending_title)

        self.pending_label = QtWidgets.QLabel("0")
        self.pending_label.setStyleSheet("color: #007bff; font-size: 9pt; font-weight: bold; font-family: 'Segoe UI';")
        pending_layout.addWidget(self.pending_label)

        layout.addWidget(self.pending_frame)

        # Last sync time
        self.last_sync_label = QtWidgets.QLabel("")
        self.last_sync_label.setStyleSheet("color: #6c757d; font-size: 8pt; font-family: 'Segoe UI';")
        layout.addWidget(self.last_sync_label)

        layout.addStretch()

        # Manual sync button
        self.sync_button = QtWidgets.QPushButton("\U0001f504 Sync Now")
        self.sync_button.setFixedWidth(100)
        self.sync_button.clicked.connect(self._on_sync_click)
        layout.addWidget(self.sync_button)

        # Status info button
        self.info_button = QtWidgets.QPushButton("\u2139\ufe0f")
        self.info_button.setFixedWidth(30)
        self.info_button.clicked.connect(self._show_status_info)
        layout.addWidget(self.info_button)

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
            self.status_label.setText("\U0001f7e2 Online")
            self.status_label.setStyleSheet("color: #28a745; font-size: 9pt; font-family: 'Segoe UI';")
        else:
            self.status_label.setText("\U0001f534 Offline")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 9pt; font-family: 'Segoe UI';")

        # Update pending count
        self._update_pending_count()

    def _update_pending_count(self):
        """Update pending sync count display."""
        try:
            count = get_pending_sync_count()
            self.pending_label.setText(str(count))

            if count > 0:
                self.pending_label.setStyleSheet("color: #dc3545; font-size: 9pt; font-weight: bold; font-family: 'Segoe UI';")
            else:
                self.pending_label.setStyleSheet("color: #28a745; font-size: 9pt; font-weight: bold; font-family: 'Segoe UI';")
        except Exception:
            pass

        # Schedule next update in 5 seconds
        QtCore.QTimer.singleShot(5000, self._update_pending_count)

    def _on_sync_click(self):
        """Handle manual sync button click."""
        from .sync_engine import trigger_manual_sync

        self.sync_button.setEnabled(False)
        self.sync_button.setText("\u23f3 Syncing...")
        trigger_manual_sync()

        # Re-enable button after 3 seconds
        def reenable():
            self.sync_button.setEnabled(True)
            self.sync_button.setText("\U0001f504 Sync Now")
        QtCore.QTimer.singleShot(3000, reenable)

        if self.on_sync_callback:
            self.on_sync_callback()

    def _show_status_info(self):
        """Show detailed status information."""
        info_window = QtWidgets.QDialog(self)
        info_window.setWindowTitle("Connection Status")
        info_window.resize(400, 300)
        info_window.setModal(True)

        # Content frame
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QtWidgets.QLabel("System Status")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; font-family: 'Segoe UI';")
        title.setAlignment(QtCore.Qt.AlignLeft)
        content_layout.addWidget(title)
        content_layout.addSpacing(15)

        # Status details
        details = [
            ("Connection:", self.monitor.status_text),
            ("Last Check:", self.monitor.last_check.strftime("%Y-%m-%d %H:%M:%S") if self.monitor.last_check else "Never"),
            ("Pending Sync:", str(get_pending_sync_count())),
            ("Auto-Sync:", "Enabled" if self.monitor.is_online else "Disabled (Offline)"),
        ]

        for label_text, value in details:
            frame = QtWidgets.QWidget()
            frame_layout = QtWidgets.QHBoxLayout(frame)
            frame_layout.setContentsMargins(0, 0, 0, 0)

            label_widget = QtWidgets.QLabel(label_text)
            label_widget.setStyleSheet("font-size: 10pt; font-weight: bold; font-family: 'Segoe UI';")
            label_widget.setFixedWidth(120)
            frame_layout.addWidget(label_widget)

            value_widget = QtWidgets.QLabel(value)
            value_widget.setStyleSheet("font-size: 10pt; font-family: 'Segoe UI';")
            frame_layout.addWidget(value_widget)
            frame_layout.addStretch()

            content_layout.addWidget(frame)

        # Error message if offline
        if not self.monitor.is_online and self.monitor.last_error:
            error_group = QtWidgets.QGroupBox("Last Error")
            error_group_layout = QtWidgets.QVBoxLayout(error_group)

            error_label = QtWidgets.QLabel(self.monitor.last_error)
            error_label.setStyleSheet("color: #dc3545; font-size: 9pt; font-family: 'Segoe UI';")
            error_label.setWordWrap(True)
            error_group_layout.addWidget(error_label)

            content_layout.addWidget(error_group)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(info_window.close)
        content_layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)
        content_layout.addSpacing(20)

        info_window.setLayout(content_layout)
        info_window.exec()


class StatusBar(QtWidgets.QWidget):
    """
    Complete status bar with connection status and app info.
    """

    def __init__(self, parent, app_name="Inventory System"):
        super().__init__(parent)
        self.app_name = app_name
        self._setup_ui()

    def _setup_ui(self):
        """Create status bar UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Left side - App info
        self.app_label = QtWidgets.QLabel(f"{self.app_name} v2.0")
        self.app_label.setStyleSheet("color: #6c757d; font-size: 9pt; font-family: 'Segoe UI';")
        layout.addWidget(self.app_label)

        layout.addStretch()

        # Right side - Connection status widget
        self.connection_widget = ConnectionStatusWidget(self)
        layout.addWidget(self.connection_widget)

    def set_message(self, message: str):
        """Set a temporary status message."""
        self.app_label.setText(message)


def create_status_bar(parent, app_name="Inventory System"):
    """Create and return a status bar."""
    return StatusBar(parent, app_name)
