"""
Auto Issue Finder - Runs on Startup
=====================================
Automatically finds and displays ALL issues when app starts.
No more silent failures!
"""

import logging
from PySide6 import QtWidgets, QtCore, QtGui

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
            QtCore.QTimer.singleShot(1000, lambda: QtWidgets.QMessageBox.warning(root, "⚠️ System Health Alert", message))

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
            QtWidgets.QMessageBox.information(
                root,
                "🏥 System Health",
                "⚠️ Health check is not fully available.\n\n"
                "The error_detector module is missing.\n"
                "Basic system checks cannot be performed.\n\n"
                "Core application functionality is unaffected."
            )
            return

        issues = detector.check_all()

        if not issues:
            QtWidgets.QMessageBox.information(
                root,
                "🏥 System Health",
                "✅ All systems operational!\n\nNo issues detected.\nYour inventory system is healthy."
            )
            return

        # Create report window
        dlg = QtWidgets.QDialog(root)
        dlg.setWindowTitle("🏥 System Health Report")
        dlg.resize(800, 600)
        dlg.setModal(True)

        layout = QtWidgets.QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_frame = QtWidgets.QFrame()
        title_frame.setStyleSheet("background-color: #2563EB;")
        title_frame.setFixedHeight(60)
        title_label = QtWidgets.QLabel("🏥 System Health Report")
        title_label.setFont(QtGui.QFont("Segoe UI", 16, QtGui.QFont.Bold))
        title_label.setStyleSheet("color: white; background-color: transparent;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        title_layout = QtWidgets.QVBoxLayout(title_frame)
        title_layout.addWidget(title_label)
        layout.addWidget(title_frame)

        # Summary
        critical = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        summary_frame = QtWidgets.QFrame()
        summary_frame.setStyleSheet("background-color: #FEF2F2;")
        summary_layout = QtWidgets.QVBoxLayout(summary_frame)

        summary_text = f"📊 Found {len(issues)} issue(s): "
        summary_text += f"🔴 {critical} critical, " if critical else ""
        summary_text += f"🟠 {errors} errors, " if errors else ""
        summary_text += f"🟡 {warnings} warnings" if warnings else ""

        summary_label = QtWidgets.QLabel(summary_text)
        summary_label.setFont(QtGui.QFont("Segoe UI", 11, QtGui.QFont.Bold))
        summary_label.setStyleSheet("color: #DC2626; background-color: transparent;")
        summary_layout.addWidget(summary_label)
        layout.addWidget(summary_frame)

        # Issue list hint
        hint_label = QtWidgets.QLabel("Click each issue to see solution:")
        hint_label.setFont(QtGui.QFont("Segoe UI", 9))
        hint_label.setStyleSheet("color: #64748B;")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(hint_label)

        # Scrollable area with issues
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: white;")

        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 10, 20, 10)
        scroll_layout.setSpacing(5)

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

            card = QtWidgets.QFrame()
            card.setStyleSheet("background-color: white; border: 1px solid #ccc;")
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)

            # Header
            header = QtWidgets.QFrame()
            header.setStyleSheet(f"background-color: {severity_color[issue.severity]};")
            header.setFixedHeight(40)
            header_layout = QtWidgets.QVBoxLayout(header)
            header_layout.setContentsMargins(15, 8, 15, 8)

            header_label = QtWidgets.QLabel(f"{severity_icon[issue.severity]} [{issue.code}] {issue.title}")
            header_label.setFont(QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold))
            header_label.setStyleSheet("color: white; background-color: transparent;")
            header_layout.addWidget(header_label)
            card_layout.addWidget(header)

            # Details
            details = QtWidgets.QFrame()
            details.setStyleSheet("background-color: white;")
            details_layout = QtWidgets.QVBoxLayout(details)
            details_layout.setContentsMargins(15, 10, 15, 10)

            module_label = QtWidgets.QLabel(f"Module: {issue.affected_module}")
            module_label.setFont(QtGui.QFont("Segoe UI", 9))
            module_label.setStyleSheet("color: #64748B; background-color: transparent;")
            details_layout.addWidget(module_label)

            issue_label = QtWidgets.QLabel(f"Issue: {issue.description}")
            issue_label.setFont(QtGui.QFont("Segoe UI", 9))
            issue_label.setStyleSheet("color: #1E293B; background-color: transparent;")
            issue_label.setWordWrap(True)
            details_layout.addWidget(issue_label)

            # Solution box
            solution_box = QtWidgets.QFrame()
            solution_box.setStyleSheet("background-color: #F0FDF4; border: 1px solid #ccc;")
            solution_layout = QtWidgets.QVBoxLayout(solution_box)
            solution_layout.setContentsMargins(10, 8, 10, 8)

            solution_title = QtWidgets.QLabel("👉 Solution:")
            solution_title.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold))
            solution_title.setStyleSheet("color: #166534; background-color: transparent;")
            solution_layout.addWidget(solution_title)

            solution_text = QtWidgets.QLabel(issue.solution)
            solution_text.setFont(QtGui.QFont("Segoe UI", 9))
            solution_text.setStyleSheet("color: #166534; background-color: transparent;")
            solution_text.setWordWrap(True)
            solution_layout.addWidget(solution_text)

            details_layout.addWidget(solution_box)
            card_layout.addWidget(details)

            scroll_layout.addWidget(card)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)

        dlg.exec()

    return show_health_report
