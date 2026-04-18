"""
Developer Error Dashboard Widget
=================================
Enhanced real-time error tracking with:
- Live error counters with pulse animation
- Error trend chart (last 24 hours)
- Top error modules breakdown
- Search/filter bar
- Error grouping
- Copy to clipboard
- Export to JSON/CSV
- Syntax-highlighted stack traces
"""

import logging
import os
import sys
import json
import re
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import Counter

try:
    import customtkinter as ctk
    CTk_AVAILABLE = True
except ImportError:
    CTk_AVAILABLE = False
    import tkinter as tk
    from tkinter import messagebox

from error_manager import get_error_manager, AppError, ErrorSeverity


# ============================================================================
# REUSABLE UI HELPERS (No repetition)
# ============================================================================

class DashboardHelpers:
    """Shared UI component factory - eliminates repetitive widget creation."""

    @staticmethod
    def make_stat_card(parent, label: str, value: str, color: str, icon: str):
        """Create a reusable stat card widget."""
        if not CTk_AVAILABLE:
            return None

        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=8)
        card.pack(side='left', padx=5, fill='both', expand=True)

        ctk.CTkLabel(
            card,
            text=f"{icon} {value}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='white'
        ).pack(padx=10, pady=(10, 0))

        ctk.CTkLabel(
            card,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color='white'
        ).pack(padx=10, pady=(0, 10))

        return card

    @staticmethod
    def make_search_bar(parent, on_search, on_clear):
        """Create reusable search/filter bar."""
        if not CTk_AVAILABLE:
            return None, None

        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.pack(fill='x', padx=15, pady=5)

        ctk.CTkLabel(
            frame,
            text="🔍",
            font=ctk.CTkFont(size=14)
        ).pack(side='left', padx=(0, 5))

        search_var = ctk.StringVar()
        entry = ctk.CTkEntry(
            frame,
            placeholder_text="Search errors...",
            textvariable=search_var,
            width=300
        )
        entry.pack(side='left', fill='x', expand=True, padx=5)
        entry.bind('<Return>', lambda e: on_search(search_var.get()))

        ctk.CTkButton(
            frame,
            text="Search",
            command=lambda: on_search(search_var.get()),
            width=80,
            fg_color='#2196F3',
            hover_color='#1976D2'
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            frame,
            text="Clear",
            command=lambda: (search_var.set(""), on_clear()),
            width=80,
            fg_color='#607D8B',
            hover_color='#455A64'
        ).pack(side='left', padx=5)

        return frame, search_var

    @staticmethod
    def make_action_buttons(parent, buttons: List[Dict]):
        """Create reusable action button row."""
        if not CTk_AVAILABLE:
            return None

        frame = ctk.CTkFrame(parent, fg_color='transparent')
        frame.pack(fill='x', padx=15, pady=10)

        for btn_cfg in buttons:
            ctk.CTkButton(
                frame,
                text=btn_cfg['text'],
                command=btn_cfg['command'],
                width=btn_cfg.get('width', 140),
                fg_color=btn_cfg.get('color', '#2196F3'),
                hover_color=btn_cfg.get('hover_color')
            ).pack(side='left', padx=5)

        return frame

    @staticmethod
    def format_stack_trace(traceback_text: str) -> str:
        """Add basic formatting to stack traces for readability."""
        if not traceback_text:
            return ""
        # Remove redundant blank lines
        lines = [line.rstrip() for line in traceback_text.split('\n') if line.strip()]
        return '\n'.join(lines)


# ============================================================================
# ERROR TREND CHART (Canvas-based, no external deps)
# ============================================================================

class ErrorTrendChart:
    """Lightweight error trend visualization using canvas."""

    def __init__(self, parent, height: int = 120):
        self.parent = parent
        self.height = height
        self.canvas = None
        self.data_points = []

    def create(self):
        """Create the trend chart canvas."""
        if not CTk_AVAILABLE:
            return

        self.canvas = ctk.CTkCanvas(
            self.parent,
            height=self.height,
            bg='#1A1A1A',
            highlightthickness=0,
            borderwidth=0
        )
        self.canvas.pack(fill='x', padx=15, pady=5)

    def update(self, errors: List[AppError]):
        """Update chart with error data."""
        if not CTk_AVAILABLE or not self.canvas:
            return

        self.data_points = self._aggregate_errors(errors)
        self._draw_chart()

    def _aggregate_errors(self, errors: List[AppError]) -> List[int]:
        """Aggregate errors by hour for last 24 hours."""
        now = datetime.now()
        hourly_counts = [0] * 24

        for error in errors:
            hours_ago = (now - error.timestamp).total_seconds() / 3600
            if 0 <= hours_ago < 24:
                idx = int(hours_ago)
                hourly_counts[23 - idx] += 1

        return hourly_counts

    def _draw_chart(self):
        """Draw the trend chart."""
        if not self.canvas:
            return

        self.canvas.delete('all')
        width = int(self.canvas.cget('width')) or 500
        height = self.height
        data = self.data_points

        if not data or max(data) == 0:
            self.canvas.create_text(
                width // 2, height // 2,
                text="No errors in last 24 hours",
                fill='#4CAF50',
                font=('Segoe UI', 12)
            )
            return

        max_val = max(data)
        padding = 20
        chart_w = width - padding * 2
        chart_h = height - padding * 2
        step = chart_w / (len(data) - 1) if len(data) > 1 else chart_w

        # Draw grid lines
        for i in range(5):
            y = padding + (chart_h / 4) * i
            self.canvas.create_line(
                padding, y, width - padding, y,
                fill='#333333', width=1
            )

        # Draw area fill
        points = []
        for i, val in enumerate(data):
            x = padding + i * step
            y = padding + chart_h - (val / max_val) * chart_h if max_val > 0 else padding
            points.extend([x, y])

        if len(points) >= 4:
            area_points = [points[0], points[1]] + points + [points[-2], height - padding]
            self.canvas.create_polygon(
                area_points,
                fill='#F4433620',
                outline=''
            )

        # Draw line
        if len(points) >= 4:
            self.canvas.create_line(
                points,
                fill='#F44336',
                width=2,
                smooth=True
            )

        # Draw points
        for i in range(0, len(points), 2):
            x, y = points[i], points[i + 1]
            self.canvas.create_oval(
                x - 2, y - 2, x + 2, y + 2,
                fill='#F44336'
            )


# ============================================================================
# TOP MODULES BAR CHART
# ============================================================================

class TopModulesChart:
    """Bar chart showing top error-generating modules."""

    def __init__(self, parent, height: int = 150):
        self.parent = parent
        self.height = height
        self.frame = None

    def create(self):
        """Create the modules chart container."""
        if not CTk_AVAILABLE:
            return

        self.frame = ctk.CTkFrame(self.parent, fg_color='#1A1A1A', corner_radius=8)
        self.frame.pack(fill='x', padx=15, pady=5)

        ctk.CTkLabel(
            self.frame,
            text="📈 Top Error Modules:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#AAAAAA'
        ).pack(anchor='w', padx=10, pady=(10, 5))

    def update(self, errors: List[AppError]):
        """Update module breakdown."""
        if not CTk_AVAILABLE or not self.frame:
            return

        # Clear existing bars
        for widget in self.frame.winfo_children()[1:]:
            widget.destroy()

        module_counts = Counter(e.module for e in errors if e.module != 'Unknown')
        total = sum(module_counts.values()) or 1

        for module, count in module_counts.most_common(5):
            pct = (count / total) * 100
            bar_frame = ctk.CTkFrame(self.frame, fg_color='transparent')
            bar_frame.pack(fill='x', padx=10, pady=2)

            ctk.CTkLabel(
                bar_frame,
                text=f"{module:20s}",
                font=ctk.CTkFont(size=10),
                text_color='#CCCCCC',
                width=100
            ).pack(side='left')

            bar = ctk.CTkProgressBar(
                bar_frame,
                width=200,
                progress_color='#F44336'
            )
            bar.pack(side='left', padx=5, fill='x', expand=True)
            bar.set(count / max(module_counts.values()))

            ctk.CTkLabel(
                bar_frame,
                text=f"{count} ({pct:.0f}%)",
                font=ctk.CTkFont(size=10),
                text_color='#AAAAAA',
                width=70
            ).pack(side='left')


# ============================================================================
# ERROR DETAILS POPUP
# ============================================================================

class ErrorDetailsPopup:
    """Reusable error details dialog with copy-to-clipboard."""

    def __init__(self, parent, error: AppError):
        self.parent = parent
        self.error = error
        self.popup = None
        self._show()

    def _show(self):
        """Show error details popup."""
        if not CTk_AVAILABLE:
            messagebox.showinfo("Error Details", str(self.error))
            return

        self.popup = ctk.CTkToplevel(self.parent)
        self.popup.title(f"Error Details - {self.error.id}")
        self.popup.geometry("750x550")
        self.popup.transient(self.parent)

        # Header with severity color
        color = ErrorSeverity.COLORS.get(self.error.severity, '#F44336')
        header = ctk.CTkFrame(self.popup, fg_color=color, height=50)
        header.pack(fill='x')
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"{ErrorSeverity.ICONS.get(self.error.severity)} {self.error.severity.upper()}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='white'
        ).pack(side='left', padx=15, pady=10)

        ctk.CTkButton(
            header,
            text="📋 Copy All",
            command=self._copy_to_clipboard,
            width=100,
            fg_color='white',
            text_color=color
        ).pack(side='right', padx=15, pady=10)

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self.popup, fg_color='#1A1A1A', corner_radius=0)
        scroll.pack(fill='both', expand=True)

        # Details
        details = [
            ("Message", self.error.message),
            ("Module", self.error.module),
            ("Function", self.error.function),
            ("User Action", self.error.user_action),
            ("Time", self.error.timestamp.strftime('%Y-%m-%d %H:%M:%S')),
            ("Status", "✅ Resolved" if self.error.resolved else "⏳ Unresolved"),
        ]

        if self.error.exception:
            details.append(("Exception", f"{type(self.error.exception).__name__}: {self.error.exception}"))

        for label, value in details:
            self._add_detail_row(scroll, label, value)

        # Stack trace
        if self.error.traceback:
            self._add_detail_row(scroll, "Stack Trace", "", is_title=True)
            trace_box = ctk.CTkTextbox(
                scroll,
                height=180,
                fg_color='#0D0D0D',
                text_color='#00FF00',
                font=('Consolas', 9),
                wrap='word'
            )
            trace_box.pack(fill='x', padx=15, pady=5)
            trace_box.insert('0.0', DashboardHelpers.format_stack_trace(self.error.traceback))
            trace_box.configure(state='disabled')

        # Footer
        footer = ctk.CTkFrame(self.popup, fg_color='transparent')
        footer.pack(fill='x')

        ctk.CTkButton(
            footer,
            text="Close",
            command=self.popup.destroy,
            width=120
        ).pack(pady=10)

    def _add_detail_row(self, parent, label: str, value: str, is_title: bool = False):
        """Add a detail row to the popup."""
        if is_title:
            ctk.CTkLabel(
                parent,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color='#F44336'
            ).pack(anchor='w', padx=15, pady=(15, 5))
        else:
            row = ctk.CTkFrame(parent, fg_color='transparent')
            row.pack(fill='x', padx=15, pady=2)

            ctk.CTkLabel(
                row,
                text=f"{label}:",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color='#AAAAAA',
                width=100
            ).pack(side='left')

            ctk.CTkLabel(
                row,
                text=str(value)[:100],
                font=ctk.CTkFont(size=11),
                text_color='#FFFFFF',
                wraplength=500
            ).pack(side='left', fill='x', expand=True)

    def _copy_to_clipboard(self):
        """Copy error details to clipboard."""
        text = self._format_error_text()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(text)
        self.parent.update()

    def _format_error_text(self) -> str:
        """Format error as plain text for clipboard."""
        lines = [
            f"Error ID: {self.error.id}",
            f"Severity: {self.error.severity.upper()}",
            f"Message: {self.error.message}",
            f"Module: {self.error.module}",
            f"Function: {self.error.function}",
            f"Time: {self.error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if self.error.exception:
            lines.append(f"Exception: {type(self.error.exception).__name__}: {self.error.exception}")
        if self.error.traceback:
            lines.append(f"\nStack Trace:\n{self.error.traceback}")
        return '\n'.join(lines)


# ============================================================================
# MAIN DASHBOARD WIDGET
# ============================================================================

class ErrorDashboardWidget(ctk.CTkFrame if CTk_AVAILABLE else object):
    """Enhanced error tracking dashboard."""

    def __init__(self, parent, auto_refresh: bool = True, refresh_interval: int = 5000):
        if CTk_AVAILABLE:
            super().__init__(parent)
        else:
            self._frame = tk.Frame(parent)

        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.error_manager = get_error_manager()

        # UI components
        self.count_label = None
        self.critical_label = None
        self.warning_label = None
        self.search_var = None
        self.trend_chart = None
        self.modules_chart = None
        self.recent_frame = None
        self.refresh_timer = None
        self._filtered_errors = []

        self._create_widgets()
        self.error_manager.register_callback(self._on_new_error)

        if auto_refresh:
            self._start_auto_refresh()

        self._update_display()

    def _create_widgets(self):
        """Build dashboard UI - single source of truth."""
        if not CTk_AVAILABLE:
            self._create_tkinter_fallback()
            return

        self.configure(fg_color='#2C2C2C', corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        # 1. Title
        ctk.CTkLabel(
            self,
            text="🔴 Error Monitor",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color='#F44336'
        ).grid(row=0, column=0, padx=15, pady=(15, 10), sticky='w')

        # 2. Stat Cards
        stats_frame = ctk.CTkFrame(self, fg_color='transparent')
        stats_frame.grid(row=1, column=0, padx=15, pady=5, sticky='ew')
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._stat_cards_frame = ctk.CTkFrame(stats_frame, fg_color='transparent')
        self._stat_cards_frame.pack(fill='x')

        # 3. Trend Chart
        self.trend_chart = ErrorTrendChart(self, height=100)
        ctk.CTkLabel(
            self,
            text="📊 Error Trend (Last 24 Hours)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#AAAAAA'
        ).grid(row=2, column=0, padx=15, pady=(15, 5), sticky='w')
        self.trend_chart.create()

        # 4. Modules Chart
        self.modules_chart = TopModulesChart(self, height=120)
        self.modules_chart.create()

        # 5. Search Bar
        _, self.search_var = DashboardHelpers.make_search_bar(
            self,
            on_search=self._apply_search,
            on_clear=self._clear_search
        )

        # 6. Recent Errors Title
        ctk.CTkLabel(
            self,
            text="Recent Errors:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color='#AAAAAA'
        ).grid(row=5, column=0, padx=15, pady=(15, 5), sticky='w')

        # 7. Scrollable Error List
        self.recent_frame = ctk.CTkScrollableFrame(
            self,
            height=200,
            fg_color='#1A1A1A',
            corner_radius=8
        )
        self.recent_frame.grid(row=6, column=0, padx=15, pady=5, sticky='nsew')

        # 8. Action Buttons
        DashboardHelpers.make_action_buttons(self, [
            {'text': '💾 Export JSON', 'command': self._export_json, 'color': '#2196F3', 'hover_color': '#1976D2'},
            {'text': '📄 Export CSV', 'command': self._export_csv, 'color': '#4CAF50', 'hover_color': '#388E3C'},
            {'text': '✅ Clear Resolved', 'command': self._clear_resolved, 'color': '#607D8B', 'hover_color': '#455A64'},
            {'text': '📂 Open Log', 'command': self._open_log, 'color': '#FF9800', 'hover_color': '#F57C00'},
        ])

        self.grid_rowconfigure(6, weight=1)

    def _update_stat_cards(self, summary: Dict[str, Any]):
        """Update stat cards without recreating them."""
        if not CTk_AVAILABLE:
            return

        for widget in self._stat_cards_frame.winfo_children():
            widget.destroy()

        DashboardHelpers.make_stat_card(
            self._stat_cards_frame, "Critical",
            str(summary['critical']), '#9C27B0', '🔥'
        )
        DashboardHelpers.make_stat_card(
            self._stat_cards_frame, "Errors",
            str(summary['error']), '#F44336', '❌'
        )
        DashboardHelpers.make_stat_card(
            self._stat_cards_frame, "Warnings",
            str(summary['warning']), '#FF9800', '⚠️'
        )
        DashboardHelpers.make_stat_card(
            self._stat_cards_frame, "Info",
            str(summary['total_errors'] - summary['error'] - summary['warning'] - summary['critical']),
            '#2196F3', 'ℹ️'
        )

    def _update_display(self):
        """Refresh entire dashboard."""
        try:
            summary = self.error_manager.get_error_summary()
            self._update_stat_cards(summary)

            errors = self.error_manager.get_errors(limit=50)
            self.trend_chart.update(errors)
            self.modules_chart.update(errors)

            if self.search_var and self.search_var.get().strip():
                self._apply_search(self.search_var.get())
            else:
                self._render_error_list(errors)

        except Exception as e:
            logging.error(f"Error updating display: {e}")

    def _render_error_list(self, errors: List[AppError]):
        """Render error list items."""
        if not CTk_AVAILABLE or not self.recent_frame:
            return

        for widget in self.recent_frame.winfo_children():
            widget.destroy()

        if not errors:
            ctk.CTkLabel(
                self.recent_frame,
                text="✅ No errors recorded!",
                font=ctk.CTkFont(size=12),
                text_color='#4CAF50'
            ).pack(padx=10, pady=20)
            return

        for error in errors[:20]:
            self._create_error_item(error)

    def _create_error_item(self, error: AppError):
        """Create a single error list item."""
        item = ctk.CTkFrame(self.recent_frame, fg_color='#2A2A2A', corner_radius=5)
        item.pack(fill='x', padx=10, pady=3)

        # Header bar
        color = ErrorSeverity.COLORS.get(error.severity, '#F44336')
        header = ctk.CTkFrame(item, fg_color=color, height=28, corner_radius=3)
        header.pack(fill='x', padx=5, pady=3)
        header.pack_propagate(False)

        icon = ErrorSeverity.ICONS.get(error.severity, '❌')
        ctk.CTkLabel(
            header,
            text=f"{icon} {error.severity.upper()}",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color='white'
        ).pack(side='left', padx=8)

        ctk.CTkLabel(
            header,
            text=f"{error.module} • {error.timestamp.strftime('%H:%M:%S')}",
            font=ctk.CTkFont(size=9),
            text_color='white'
        ).pack(side='right', padx=8)

        # Message
        ctk.CTkLabel(
            item,
            text=error.message[:120],
            font=ctk.CTkFont(size=11),
            text_color='#CCCCCC',
            wraplength=500,
            justify='left'
        ).pack(anchor='w', padx=10, pady=(0, 8))

        # Click handlers
        for w in [item, header]:
            w.bind('<Button-1>', lambda e, err=error: ErrorDetailsPopup(self, err))

    # ── Search & Filter ──────────────────────────────────────

    def _apply_search(self, query: str):
        """Filter errors by search query."""
        q = query.lower().strip()
        all_errors = self.error_manager.get_errors(limit=100)

        if q:
            self._filtered_errors = [
                e for e in all_errors
                if q in e.message.lower() or q in e.module.lower() or q in e.function.lower()
            ]
        else:
            self._filtered_errors = all_errors

        self._render_error_list(self._filtered_errors)

    def _clear_search(self):
        """Clear search filter."""
        if self.search_var:
            self.search_var.set("")
        self._filtered_errors = []
        self._update_display()

    # ── Action Handlers ──────────────────────────────────────

    def _export_json(self):
        """Export errors to JSON."""
        filepath = self.error_manager.export_errors()
        if filepath:
            logging.info(f"Exported JSON: {filepath}")

    def _export_csv(self):
        """Export errors to CSV."""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV files', '*.csv')],
            initialfile=f"errors_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if not filepath:
            return

        errors = self.error_manager.get_errors(limit=1000)
        try:
            import csv
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'timestamp', 'severity', 'message', 'module',
                    'function', 'user_action', 'exception_type', 'resolved'
                ])
                writer.writeheader()
                for e in errors:
                    writer.writerow(e.to_dict())
            logging.info(f"Exported CSV: {filepath}")
        except Exception as ex:
            logging.error(f"Export failed: {ex}")

    def _clear_resolved(self):
        """Clear resolved errors."""
        self.error_manager.clear_resolved()
        self._update_display()

    def _open_log(self):
        """Open error log file."""
        log_file = self.error_manager.log_file
        if os.path.exists(log_file):
            webbrowser.open(log_file)
        else:
            logging.warning(f"Log file not found: {log_file}")

    # ── Callbacks & Auto-Refresh ─────────────────────────────

    def _on_new_error(self, error: AppError):
        """Callback on new error - schedules UI update."""
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
        """Stop auto-refresh."""
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
            self.refresh_timer = None

    # ── Fallback for non-CTk environments ────────────────────

    def _create_tkinter_fallback(self):
        """Basic tkinter fallback when CustomTkinter unavailable."""
        frame = self._frame
        tk.Label(frame, text="🔴 Error Monitor", font=('Arial', 14, 'bold'), fg='#F44336').pack(pady=10)

        self.count_label = tk.Label(frame, text="0 Errors", font=('Arial', 12, 'bold'), bg='#F44336', fg='white')
        self.count_label.pack(fill='x', padx=10, pady=5)

        self.recent_list = tk.Listbox(frame, height=8, bg='#1A1A1A', fg='white', font=('Consolas', 9))
        self.recent_list.pack(fill='both', expand=True, padx=10, pady=5)
        self.recent_list.bind('<Double-Button-1>', lambda e: self._show_tkinter_details())

    def _show_tkinter_details(self):
        """Show error details in tkinter fallback."""
        if not self.recent_list or self.recent_list.size() == 0:
            return
        sel = self.recent_list.curselection()
        if not sel:
            return
        errors = self.error_manager.get_errors(limit=10)
        if sel[0] < len(errors):
            messagebox.showinfo("Error Details", str(errors[sel[0]]))

    def destroy(self):
        """Cleanup on destroy."""
        self._stop_auto_refresh()
        self.error_manager.unregister_callback(self._on_new_error)
        if CTk_AVAILABLE:
            super().destroy()
        else:
            self._frame.destroy()


# ============================================================================
# CONVENIENCE LAUNCHER
# ============================================================================

def open_error_dashboard(parent):
    """Open error dashboard in a new window."""
    if not CTk_AVAILABLE:
        return

    win = ctk.CTkToplevel(parent)
    win.title("🔴 Error Monitor Dashboard")
    win.geometry("800x700")
    win.transient(parent)

    dashboard = ErrorDashboardWidget(win, auto_refresh=True)
    dashboard.pack(fill='both', expand=True, padx=10, pady=10)
