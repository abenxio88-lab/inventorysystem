"""
Alerts UI Module
================
User interface for viewing and managing alerts.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging

from ui_theme import make_card, styled_label, make_button, FONT_REGULAR, FONT_BOLD, COLOR_DANGER, COLOR_WARNING, COLOR_SUCCESS, COLOR_PRIMARY
from alerts import alert_manager, get_unread_alerts


def create_alerts_tab(parent, current_user=None):
    """
    Creates the alerts management tab.
    """
    window = QtWidgets.QWidget()
    window.setContentsMargins(15, 15, 15, 15)

    main_layout = QtWidgets.QVBoxLayout(window)
    main_layout.setContentsMargins(0, 0, 0, 0)

    # Header
    header_frame = QtWidgets.QWidget()
    header_layout = QtWidgets.QHBoxLayout(header_frame)
    header_layout.setContentsMargins(0, 0, 0, 0)

    header_label = QtWidgets.QLabel("Alerts & Notifications")
    header_label.setFont(FONT_BOLD)
    header_layout.addWidget(header_label)
    header_layout.addStretch()

    # Actions
    refresh_btn = QtWidgets.QPushButton("Refresh")
    refresh_btn.clicked.connect(lambda: window.refresh_alerts())
    refresh_btn.setStyleSheet("padding: 5px 15px; border-radius: 3px;")
    header_layout.addWidget(refresh_btn)

    mark_all_btn = QtWidgets.QPushButton("Mark All Read")
    mark_all_btn.clicked.connect(lambda: mark_all_read(window))
    mark_all_btn.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px; border-radius: 3px;")
    header_layout.addWidget(mark_all_btn)

    main_layout.addWidget(header_frame)

    # Summary cards
    summary_frame = QtWidgets.QWidget()
    summary_layout = QtWidgets.QHBoxLayout(summary_frame)
    summary_layout.setContentsMargins(0, 0, 0, 0)
    summary_layout.setSpacing(10)

    def create_summary_card(parent, title, value, color):
        card = QtWidgets.QGroupBox(title)
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)

        value_label = QtWidgets.QLabel(str(value))
        value_label.setFont(QtGui.QFont("Segoe UI", 24, QtGui.QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(value_label)

        parent.layout().addWidget(card)
        return value_label

    # Create summary cards (will be updated by update_summary)
    unread_lbl = create_summary_card(summary_frame, "Unread", 0, COLOR_DANGER)
    critical_lbl = create_summary_card(summary_frame, "Critical", 0, COLOR_DANGER)
    warning_lbl = create_summary_card(summary_frame, "Warnings", 0, COLOR_WARNING)
    total_lbl = create_summary_card(summary_frame, "Total", 0, COLOR_PRIMARY)

    main_layout.addWidget(summary_frame)

    # Store labels for updates
    window.summary_labels = {
        'unread': unread_lbl,
        'critical': critical_lbl,
        'warning': warning_lbl,
        'total': total_lbl
    }

    # Filter toolbar
    filter_frame = QtWidgets.QWidget()
    filter_layout = QtWidgets.QHBoxLayout(filter_frame)
    filter_layout.setContentsMargins(0, 0, 0, 0)

    filter_label = QtWidgets.QLabel("Filter:")
    filter_layout.addWidget(filter_label)

    filter_combo = QtWidgets.QComboBox()
    filter_combo.addItems(["all", "unread", "critical", "high", "medium", "low"])
    filter_layout.addWidget(filter_combo)

    type_filter_combo = QtWidgets.QComboBox()
    type_filter_combo.addItems(["all", "low_stock", "warranty_expiry", "out_of_stock", "system"])
    filter_layout.addWidget(type_filter_combo)

    def apply_filter():
        window.refresh_alerts()

    apply_btn = QtWidgets.QPushButton("Apply")
    apply_btn.clicked.connect(apply_filter)
    apply_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    filter_layout.addWidget(apply_btn)

    main_layout.addWidget(filter_frame)

    # Alerts table
    table_frame = QtWidgets.QWidget()
    table_layout = QtWidgets.QVBoxLayout(table_frame)
    table_layout.setContentsMargins(0, 0, 0, 0)

    tree = QtWidgets.QTableWidget()
    columns = ("severity", "type", "title", "message", "date", "status")
    column_map = {
        "severity": ("!", 50),
        "type": ("Type", 120),
        "title": ("Title", 200),
        "message": ("Message", 400),
        "date": ("Date", 150),
        "status": ("Status", 100)
    }

    tree.setColumnCount(len(columns))
    tree.setHorizontalHeaderLabels([column_map[c][0] for c in columns])
    for i, col in enumerate(columns):
        tree.horizontalHeader().resizeSection(i, column_map[col][1])
    tree.horizontalHeader().setStretchLastSection(True)
    table_layout.addWidget(tree)
    main_layout.addWidget(table_frame, stretch=1)

    # Action buttons
    action_bar = QtWidgets.QWidget()
    action_layout = QtWidgets.QHBoxLayout(action_bar)
    action_layout.setContentsMargins(0, 0, 0, 0)

    def on_mark_read():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select an alert to mark as read")
            return

        if alert_manager:
            for index in selected_rows:
                row = index.row()
                alert_id = tree.item(row, 0).data(QtCore.Qt.UserRole) if tree.item(row, 0) else None
                if alert_id:
                    alert_manager.mark_as_read(int(alert_id))

            window.refresh_alerts()
            QtWidgets.QMessageBox.information(window, "Success", "Alert(s) marked as read")

    def on_acknowledge():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select an alert to acknowledge")
            return

        if alert_manager and current_user:
            for index in selected_rows:
                row = index.row()
                alert_id = tree.item(row, 0).data(QtCore.Qt.UserRole) if tree.item(row, 0) else None
                if alert_id:
                    alert_manager.acknowledge_alert(int(alert_id), current_user)

            window.refresh_alerts()
            QtWidgets.QMessageBox.information(window, "Success", "Alert(s) acknowledged")

    def on_delete():
        selected_rows = tree.selectionModel().selectedRows()
        if not selected_rows:
            QtWidgets.QMessageBox.information(window, "Select", "Please select an alert to delete")
            return

        reply = QtWidgets.QMessageBox.question(window, "Confirm", "Delete selected alert(s)?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            if alert_manager:
                for index in selected_rows:
                    row = index.row()
                    alert_id = tree.item(row, 0).data(QtCore.Qt.UserRole) if tree.item(row, 0) else None
                    if alert_id:
                        alert_manager.delete_alert(int(alert_id))

                window.refresh_alerts()
                QtWidgets.QMessageBox.information(window, "Success", "Alert(s) deleted")

    mark_read_btn = QtWidgets.QPushButton("Mark Read")
    mark_read_btn.clicked.connect(on_mark_read)
    mark_read_btn.setStyleSheet("padding: 5px 15px; border-radius: 3px;")
    action_layout.addWidget(mark_read_btn)

    ack_btn = QtWidgets.QPushButton("Acknowledge")
    ack_btn.clicked.connect(on_acknowledge)
    ack_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px; border-radius: 3px;")
    action_layout.addWidget(ack_btn)

    delete_btn = QtWidgets.QPushButton("Delete")
    delete_btn.clicked.connect(on_delete)
    delete_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 5px 15px; border-radius: 3px;")
    action_layout.addWidget(delete_btn)

    main_layout.addWidget(action_bar)

    # Store state
    window.filter_combo = filter_combo
    window.type_filter_combo = type_filter_combo
    window.tree = tree

    def refresh():
        """Refresh alerts display."""
        if not alert_manager:
            return

        # Get alerts
        filter_type = filter_combo.currentText()
        type_filter = type_filter_combo.currentText()

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
        tree.setRowCount(0)

        severity_icons = {
            'critical': '\U0001f534',
            'high': '\U0001f7e0',
            'medium': '\U0001f7e1',
            'low': '\U0001f535'
        }

        for alert in filtered:
            severity_icon = severity_icons.get(alert.get('severity', 'low'), '\u26aa')

            status = "Read" if alert.get('is_read') else "Unread"
            if alert.get('is_acknowledged'):
                status = "Acknowledged"

            alert_id = alert.get('id', '')
            row = tree.rowCount()
            tree.insertRow(row)

            for col, val in enumerate([
                severity_icon,
                alert.get('alert_type', '').replace('_', ' ').title(),
                alert.get('title', ''),
                alert.get('message', '')[:100] + ('...' if len(alert.get('message', '')) > 100 else ''),
                alert.get('created_at', '')[:16] if alert.get('created_at') else '',
                status
            ]):
                item = QtWidgets.QTableWidgetItem(str(val))
                if alert_id:
                    item.setData(QtCore.Qt.UserRole, alert_id)
                tree.setItem(row, col, item)

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

        window.summary_labels['unread'].setText(str(unread))
        window.summary_labels['critical'].setText(str(critical))
        window.summary_labels['warning'].setText(str(warning))
        window.summary_labels['total'].setText(str(total))
    except Exception as e:
        logging.error(f"Failed to update alert summary: {e}")


def mark_all_read(window):
    """Mark all alerts as read."""
    if not alert_manager:
        return

    count = alert_manager.mark_all_as_read()
    window.refresh_alerts()
    QtWidgets.QMessageBox.information(window, "Success", f"Marked {count} alert(s) as read")
