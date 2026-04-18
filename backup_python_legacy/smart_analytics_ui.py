"""
Smart Analytics Dashboard
==========================
AI-powered analytics with interactive charts and insights.
"""

from PySide6 import QtWidgets, QtCore, QtGui
import logging
from datetime import datetime

from ui_theme import (
    make_button, make_card, styled_label,
    FONT_HEADING, FONT_BOLD, FONT_REGULAR,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING
)
from ai_intelligence import InventoryHealthAnalyzer, AIDemandForecaster

logger = logging.getLogger(__name__)


def create_smart_analytics_tab(parent, current_user=None):
    """
    Create smart analytics tab with AI insights.
    """
    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(window)
    layout.setContentsMargins(15, 15, 15, 15)

    # Header
    header_frame = QtWidgets.QHBoxLayout()

    header_label = styled_label(window, "\U0001f9e0 Smart Analytics", font=FONT_HEADING)
    header_frame.addWidget(header_label)

    # Refresh button
    def refresh_all():
        load_insights()
        QtWidgets.QMessageBox.information(window, "Refreshed", "Analytics updated")

    refresh_btn = make_button(window, "\U0001f504 Refresh", command=refresh_all, kind="primary")
    header_frame.addWidget(refresh_btn, alignment=QtCore.Qt.AlignRight)

    layout.addLayout(header_frame)
    layout.addSpacing(15)

    # KPI Cards
    kpi_frame = QtWidgets.QWidget()
    kpi_layout = QtWidgets.QGridLayout(kpi_frame)
    kpi_layout.setContentsMargins(0, 0, 0, 0)

    # Create KPI cards
    kpis = {
        'forecast_accuracy': ("\U0001f4ca Forecast Accuracy", "87%", COLOR_PRIMARY, 0),
        'predicted_demand': ("\U0001f4c8 Predicted Demand (30d)", "Rs. 125,000", COLOR_SUCCESS, 1),
        'reorder_items': ("\u26a0\ufe0f Items to Reorder", "8", COLOR_WARNING, 2),
        'anomalies': ("\U0001f514 Anomalies Detected", "3", COLOR_DANGER, 3)
    }

    kpi_labels = {}
    for key, (title, value, color, col) in kpis.items():
        card = make_card(kpi_frame, padding=15)
        card_layout = QtWidgets.QVBoxLayout(card)

        title_label = styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d")
        title_label.setAlignment(QtCore.Qt.AlignLeft)
        card_layout.addWidget(title_label)

        value_label = styled_label(card, text=value, font=("Segoe UI", 20, "bold"), foreground=color)
        value_label.setAlignment(QtCore.Qt.AlignLeft)
        card_layout.addWidget(value_label)

        kpi_layout.addWidget(card, 0, col)
        kpi_labels[key] = value_label

    layout.addWidget(kpi_frame)
    layout.addSpacing(15)

    # Main content area
    content_frame = QtWidgets.QWidget()
    content_layout = QtWidgets.QHBoxLayout(content_frame)
    content_layout.setContentsMargins(0, 0, 0, 0)

    # Left panel - Demand Forecast
    forecast_frame = make_card(content_frame, padding=15)
    forecast_layout = QtWidgets.QVBoxLayout(forecast_frame)

    styled_label(forecast_frame, "\U0001f4ca Demand Forecast", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    forecast_layout.addSpacing(10)

    # Forecast list
    forecast_list = QtWidgets.QTreeWidget()
    forecast_list.setHeaderLabels(["Product", "Stock", "30d Demand", "Action"])
    forecast_list.setColumnWidth(0, 150)
    forecast_list.setColumnWidth(1, 60)
    forecast_list.setColumnWidth(2, 80)
    forecast_list.setColumnWidth(3, 120)
    forecast_list.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
    forecast_list.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
    forecast_layout.addWidget(forecast_list)

    content_layout.addWidget(forecast_frame)

    # Right panel - Anomalies
    anomaly_frame = make_card(content_frame, padding=15)
    anomaly_layout = QtWidgets.QVBoxLayout(anomaly_frame)

    styled_label(anomaly_frame, "\U0001f514 Anomaly Alerts", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    anomaly_layout.addSpacing(10)

    anomaly_list = QtWidgets.QTreeWidget()
    anomaly_list.setHeaderLabels(["Type", "Severity", "Product"])
    anomaly_list.setColumnWidth(0, 100)
    anomaly_list.setColumnWidth(1, 70)
    anomaly_list.setColumnWidth(2, 150)
    anomaly_list.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
    anomaly_layout.addWidget(anomaly_list)

    content_layout.addWidget(anomaly_frame)

    layout.addWidget(content_frame, stretch=1)

    # Reorder Suggestions section
    reorder_frame = make_card(window, padding=15)
    reorder_layout = QtWidgets.QVBoxLayout(reorder_frame)

    styled_label(reorder_frame, "\U0001f6d2 Smart Reorder Suggestions", font=FONT_BOLD).setAlignment(QtCore.Qt.AlignLeft)
    reorder_layout.addSpacing(10)

    reorder_list = QtWidgets.QTreeWidget()
    reorder_list.setHeaderLabels(["Product", "Current Stock", "Suggested Order", "Urgency"])
    reorder_list.setColumnWidth(0, 200)
    reorder_list.setColumnWidth(1, 100)
    reorder_list.setColumnWidth(2, 100)
    reorder_list.setColumnWidth(3, 80)
    reorder_layout.addWidget(reorder_list)

    layout.addWidget(reorder_frame)

    # Store state
    window.forecast_list = forecast_list
    window.anomaly_list = anomaly_list
    window.reorder_list = reorder_list
    window.kpi_labels = kpi_labels

    def load_insights():
        """Load AI insights from the intelligence module."""
        try:
            from ai_intelligence import AIDemandForecaster, SmartReorderEngine
            forecaster = AIDemandForecaster()
            forecasts = forecaster.forecast_all_products(forecast_days=30)

            reorder_engine = SmartReorderEngine()
            reorders = reorder_engine.analyze_reorder_needs()

            anomalies = [f for f in forecasts if f.get("stockout_risk") == "critical"]

            kpi_labels['reorder_items'].setText(str(len(reorders)))
            kpi_labels['anomalies'].setText(str(len(anomalies)))

            # Update forecast list
            forecast_list.clear()
            for forecast in forecasts[:10]:
                action_text = f"Risk: {forecast.get('stockout_risk', 'Unknown').title()}"
                item = QtWidgets.QTreeWidgetItem([
                    str(forecast.get("product_name")),
                    str(forecast.get("current_stock")),
                    str(forecast.get("predicted_demand")),
                    action_text
                ])
                forecast_list.addTopLevelItem(item)

            # Update anomaly list
            anomaly_list.clear()
            for alert in anomalies:
                item = QtWidgets.QTreeWidgetItem([
                    "Critical Stockout",
                    "\U0001f534",
                    alert.get("product_name", "Unknown")
                ])
                anomaly_list.addTopLevelItem(item)

            # Update reorder list
            reorder_list.clear()
            for suggestion in reorders:
                urgency = suggestion.get('priority', 'normal')
                urgency_text = "\U0001f534 Urgent/High" if urgency in ['urgent', 'high'] else "\U0001f7e1 Normal/Low"
                item = QtWidgets.QTreeWidgetItem([
                    suggestion.get('product_name'),
                    str(suggestion.get('current_stock')),
                    str(suggestion.get('reorder_quantity')),
                    urgency_text
                ])
                reorder_list.addTopLevelItem(item)

            logger.info("Smart analytics loaded")
        except Exception as e:
            # Graceful degradation: show empty state when tables/features unavailable
            error_msg = str(e)
            if "no such table" in error_msg.lower():
                logger.info(f"AI analytics skipped - {error_msg}")
                # Show user-friendly empty state
                kpi_labels['reorder_items'].setText("0")
                kpi_labels['anomalies'].setText("0")
                forecast_list.clear()
                anomaly_list.clear()
                reorder_list.clear()
                forecast_list.addTopLevelItem(QtWidgets.QTreeWidgetItem(["Feature unavailable", "N/A", "N/A", "Table not found"]))
            else:
                logger.error(f"Failed to load insights: {e}")

    # Load initial data
    load_insights()

    return window


def open_forecast_details(parent, product_id):
    """Open detailed forecast view."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle("Demand Forecast Details")
    dlg.resize(600, 500)
    dlg.setModal(True)

    layout = QtWidgets.QVBoxLayout(dlg)
    layout.setContentsMargins(20, 20, 20, 20)

    styled_label(dlg, "\U0001f4ca Detailed Forecast", font=FONT_HEADING).setAlignment(QtCore.Qt.AlignLeft)
    layout.addSpacing(15)

    # Forecast details
    details_card = make_card(dlg, padding=20)
    details_layout = QtWidgets.QVBoxLayout(details_card)
    layout.addWidget(details_card, stretch=1)

    try:
        from ai_intelligence import AIDemandForecaster
        forecaster = AIDemandForecaster()
        forecast = forecaster.forecast_demand(product_id, forecast_days=30)
        if forecast:
            details = [
                ("Product ID:", str(product_id)),
                ("Predicted Demand (30 days):", str(forecast.get("predicted_demand"))),
                ("Daily Average:", str(forecast.get("daily_average"))),
                ("Confidence:", forecast.get("confidence", "Unknown").title()),
                ("Recommended Stock:", str(forecast.get("recommended_stock"))),
                ("Trend:", forecast.get("trend", "Unknown").title()),
            ]

            for label, value in details:
                frame = QtWidgets.QHBoxLayout()
                label_widget = styled_label(dlg, f"{label}", font=FONT_BOLD, width=25)
                frame.addWidget(label_widget)
                frame.addWidget(styled_label(dlg, str(value)))
                details_layout.addLayout(frame)
                details_layout.addSpacing(5)

    except Exception as e:
        logger.exception("Failed to load forecast details")
        styled_label(details_card, f"Error: {e}", foreground=COLOR_DANGER).setAlignment(QtCore.Qt.AlignCenter)

    close_btn = QtWidgets.QPushButton("Close")
    close_btn.clicked.connect(dlg.close)
    layout.addWidget(close_btn, alignment=QtCore.Qt.AlignCenter)
    layout.addSpacing(10)

    dlg.exec()
