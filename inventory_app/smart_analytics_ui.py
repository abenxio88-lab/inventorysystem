"""
Smart Analytics Dashboard
==========================
AI-powered analytics with interactive charts and insights.
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
    window = ttk.Frame(parent, padding=15)

    # Header
    header_frame = ttk.Frame(window)
    header_frame.pack(fill="x", pady=(0, 15))

    styled_label(header_frame, "\U0001f9e0 Smart Analytics", font=FONT_HEADING).pack(side=tk.LEFT)

    # Refresh button
    def refresh_all():
        load_insights()
        messagebox.showinfo("Refreshed", "Analytics updated")

    make_button(header_frame, "\U0001f504 Refresh", command=refresh_all, kind="primary").pack(side=tk.RIGHT)

    # KPI Cards
    kpi_frame = ttk.Frame(window)
    kpi_frame.pack(fill="x", pady=(0, 15))
    kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

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
        card.grid(row=0, column=col, padx=8, sticky="nsew")

        styled_label(card, text=title, font=("Segoe UI", 9), foreground="#6c757d").pack(anchor="w")
        value_label = styled_label(card, text=value, font=("Segoe UI", 20, "bold"), foreground=color)
        value_label.pack(anchor="w", pady=(5, 0))

        kpi_labels[key] = value_label

    # Main content area
    content_frame = ttk.Frame(window)
    content_frame.pack(fill="both", expand=True)

    # Left panel - Demand Forecast
    forecast_frame = make_card(content_frame, padding=15)
    forecast_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 8))

    styled_label(forecast_frame, "\U0001f4ca Demand Forecast", font=FONT_BOLD).pack(anchor="w", pady=(0, 10))

    # Forecast list
    forecast_list = ttk.Treeview(forecast_frame, columns=("product", "stock", "demand", "action"), show="headings", height=8)
    forecast_list.heading("product", text="Product")
    forecast_list.heading("stock", text="Stock")
    forecast_list.heading("demand", text="30d Demand")
    forecast_list.heading("action", text="Action")

    forecast_list.column("product", width=150)
    forecast_list.column("stock", width=60, anchor="center")
    forecast_list.column("demand", width=80, anchor="e")
    forecast_list.column("action", width=120)

    forecast_list.pack(fill="both", expand=True)

    # Right panel - Anomalies
    anomaly_frame = make_card(content_frame, padding=15)
    anomaly_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(8, 0))

    styled_label(anomaly_frame, "\U0001f514 Anomaly Alerts", font=FONT_BOLD).pack(anchor="w", pady=(0, 10))

    anomaly_list = ttk.Treeview(anomaly_frame, columns=("type", "severity", "product"), show="headings", height=8)
    anomaly_list.heading("type", text="Type")
    anomaly_list.heading("severity", text="Severity")
    anomaly_list.heading("product", text="Product")

    anomaly_list.column("type", width=100)
    anomaly_list.column("severity", width=70, anchor="center")
    anomaly_list.column("product", width=150)

    anomaly_list.pack(fill="both", expand=True)

    # Reorder Suggestions section
    reorder_frame = make_card(window, padding=15)
    reorder_frame.pack(fill="x", pady=(15, 0))

    styled_label(reorder_frame, "\U0001f6d2 Smart Reorder Suggestions", font=FONT_BOLD).pack(anchor="w", pady=(0, 10))

    reorder_list = ttk.Treeview(reorder_frame, columns=("product", "current", "suggest", "urgency"), show="headings", height=5)
    reorder_list.heading("product", text="Product")
    reorder_list.heading("current", text="Current Stock")
    reorder_list.heading("suggest", text="Suggested Order")
    reorder_list.heading("urgency", text="Urgency")

    reorder_list.column("product", width=200)
    reorder_list.column("current", width=100, anchor="e")
    reorder_list.column("suggest", width=100, anchor="e")
    reorder_list.column("urgency", width=80, anchor="center")

    reorder_list.pack(fill="both", expand=True)

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

            kpi_labels['reorder_items'].config(text=str(len(reorders)))
            kpi_labels['anomalies'].config(text=str(len(anomalies)))

            # Update forecast list
            forecast_list.delete(*forecast_list.get_children())
            for forecast in forecasts[:10]:
                action_text = f"Risk: {forecast.get('stockout_risk', 'Unknown').title()}"
                forecast_list.insert("", "end", values=(
                    forecast.get("product_name"),
                    forecast.get("current_stock"),
                    forecast.get("predicted_demand"),
                    action_text
                ))

            # Update anomaly list
            anomaly_list.delete(*anomaly_list.get_children())
            for alert in anomalies:
                anomaly_list.insert("", "end", values=(
                    "Critical Stockout",
                    "\U0001f534",
                    alert.get("product_name", "Unknown")
                ))

            # Update reorder list
            reorder_list.delete(*reorder_list.get_children())
            for suggestion in reorders:
                urgency = suggestion.get('priority', 'normal')
                urgency_text = "\U0001f534 Urgent/High" if urgency in ['urgent', 'high'] else "\U0001f7e1 Normal/Low"
                reorder_list.insert("", "end", values=(
                    suggestion.get('product_name'),
                    suggestion.get('current_stock'),
                    suggestion.get('reorder_quantity'),
                    urgency_text
                ))

            logger.info("Smart analytics loaded")

        except Exception as e:
            logger.exception(f"Failed to load insights: {e}")
            messagebox.showerror("Error", f"Failed to load analytics: {e}")

    # Load initial data
    load_insights()

    return window


def open_forecast_details(parent, product_id):
    """Open detailed forecast view."""
    dlg = tk.Toplevel(parent)
    dlg.title("Demand Forecast Details")
    dlg.geometry("600x500")
    dlg.transient(parent)
    dlg.grab_set()

    content = ttk.Frame(dlg, padding=20)
    content.pack(fill="both", expand=True)

    styled_label(content, "\U0001f4ca Detailed Forecast", font=FONT_HEADING).pack(anchor="w", pady=(0, 15))

    # Forecast details
    details_card = make_card(content, padding=20)
    details_card.pack(fill="both", expand=True)

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
                frame = ttk.Frame(details_card)
                frame.pack(fill="x", pady=5)
                styled_label(frame, f"{label}", font=FONT_BOLD, width=25).pack(side=tk.LEFT)
                styled_label(frame, str(value)).pack(side=tk.LEFT)

    except Exception as e:
        logger.exception("Failed to load forecast details")
        styled_label(details_card, f"Error: {e}", foreground=COLOR_DANGER).pack(pady=20)

    ttk.Button(dlg, text="Close", command=dlg.destroy).pack(pady=10)
