import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from collections import defaultdict
import logging

try:
    from openpyxl import Workbook, load_workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from .utils import get_data_dir
    from .ui_theme import make_button, make_card, frame, label, treeview, COLOR_SUCCESS, COLOR_DANGER, COLOR_PRIMARY, COLOR_TEXT_MUTED, styled_label
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir
    from ui_theme import make_button, make_card, frame, label, treeview, COLOR_SUCCESS, COLOR_DANGER, COLOR_PRIMARY, COLOR_TEXT_MUTED, styled_label

try:
    from .utils import load_json_file
except Exception:
    from utils import load_json_file

SALES_FILE = os.path.join(get_data_dir(), "sales.json")

def load_sales():
    return load_json_file(SALES_FILE, default=[])

def calculate_monthly_data():
    sales = load_sales()
    monthly = defaultdict(lambda: {"revenue": 0, "cost": 0, "profit": 0})
    for sale in sales:
        month = sale.get("month", "Unknown")
        revenue = sale.get("selling_price", 0) * sale.get("quantity", 0)
        cost = sale.get("purchase_price", 0) * sale.get("quantity", 0)
        monthly[month]["revenue"] += revenue
        monthly[month]["cost"] += cost
        monthly[month]["profit"] += (revenue - cost)
    return monthly

def export_to_excel(monthly_data):
    if not monthly_data:
        messagebox.showerror("Error", "No data to export")
        return
    if not OPENPYXL_AVAILABLE:
        messagebox.showerror("Missing Dependency", "The 'openpyxl' package is required for Excel export.\nInstall it with: pip install openpyxl")
        return
    # ... (rest of export function remains the same)
    try:
        template_name = "monthly_profit_report.xlsx"
        template_path = template_name
        if not os.path.exists(template_path):
            template_path = os.path.join(os.path.dirname(__file__), template_name)

        if os.path.exists(template_path):
            wb = load_workbook(template_path)
            ws = wb.active
            if ws.max_row > 1: ws.delete_rows(2, ws.max_row)
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = "Monthly Profit Report"
            ws.append(["Month", "Revenue", "Cost", "Profit"])

        for month, data in sorted(monthly_data.items()):
            ws.append([month, round(data["revenue"], 2), round(data["cost"], 2), round(data["profit"], 2)])

        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        file_name = "monthly_profit_report_exported.xlsx"
        save_path = os.path.join(desktop, file_name)
        
        wb.save(save_path)
        logging.info(f"Profit report exported to Desktop: {save_path}")
        messagebox.showinfo("Success", f"Report exported to Desktop:\n {file_name}")
    except Exception:
        logging.error("Failed to export profit report", exc_info=True)
        messagebox.showerror("Error", "Failed to export report")

def create_profit_tab(parent):
    """
    Creates the profit analysis tab, including a table of monthly data and a visual chart.
    """
    window = ttk.Frame(parent, padding=20)
    
    label(window, "PROFITABILITY ANALYSIS", kind="heading").pack(anchor="w", pady=(0, 20))

    monthly_data = calculate_monthly_data()

    # --- Summary Data ---
    total_rev = sum(d["revenue"] for d in monthly_data.values())
    total_cost = sum(d["cost"] for d in monthly_data.values())
    total_prof = sum(d["profit"] for d in monthly_data.values())
    window = ttk.Frame(parent, padding=20)

    label(window, "PROFITABILITY ANALYSIS", kind="heading").pack(anchor="w", pady=(0, 20))

    # --- Summary Cards Frame ---
    summary_frame = ttk.Frame(window)
    summary_frame.pack(fill="x", expand=True, pady=(10, 20))
    summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def stats_card(parent, title, value, color, col):
        card = make_card(parent, padding=20)
        card.grid(row=0, column=col, padx=15, sticky="nsew")
        styled_label(card, title, font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))
        lbl = styled_label(card, f"Rs. {value:,.2f}", font=("Segoe UI", 24, "bold"), foreground=color)
        lbl.pack(pady=5)
        return lbl

    # placeholders, will be updated by populate_summary()
    rev_lbl = stats_card(summary_frame, "TOTAL REVENUE", 0, COLOR_PRIMARY, 0)
    cost_lbl = stats_card(summary_frame, "TOTAL COST OF GOODS", 0, COLOR_TEXT_MUTED, 1)
    prof_lbl = stats_card(summary_frame, "NET PROFIT", 0, COLOR_SUCCESS, 2)

    # Controls: month selector / view mode
    ctrl_frame = ttk.Frame(window)
    ctrl_frame.pack(fill="x", pady=(0, 10))

    months_all = sorted(list({s.get('month') for s in load_sales() if s.get('month')}), reverse=True)
    month_var = tk.StringVar()
    month_cb = ttk.Combobox(ctrl_frame, textvariable=month_var, values=months_all)
    try: month_cb.configure(width=16)
    except: pass
    month_cb.pack(side='left', padx=(0, 10))

    def set_month_list():
        vals = sorted(list({s.get('month') for s in load_sales() if s.get('month')}), reverse=True)
        month_cb['values'] = vals

    def show_month():
        m = month_var.get().strip()
        if not m:
            messagebox.showinfo('Select month', 'Please select a month (YYYY-MM)')
            return
        populate_month(m)

    make_button(ctrl_frame, 'Show Month', command=show_month, kind='primary').pack(side='left', padx=5)
    make_button(ctrl_frame, 'Summary', command=lambda: populate_summary(), kind='secondary').pack(side='left', padx=5)

    # Chart area
    chart_objs = {}
    if MATPLOTLIB_AVAILABLE:
        chart_frame = make_card(window, padding=20)
        chart_frame.pack(fill='x', expand=False, pady=(0, 20))
        fig = Figure(figsize=(10, 4), dpi=100)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.get_tk_widget().pack(fill='both', expand=True)
        chart_objs = {'fig': fig, 'ax': ax, 'canvas': canvas}

    # Table
    label(window, "MONTHLY PERFORMANCE DATA", kind="heading").pack(anchor="w", pady=(20, 10))
    table_frame = make_card(window, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("month", "revenue", "cost", "profit")
    tree = treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "month": ("Month", 250),
        "revenue": ("Revenue", 200),
        "cost": ("Cost", 200),
        "profit": ("Profit", 200)
    }

    for col, (label_text, width) in column_map.items():
        tree.heading(col, text=label_text.upper(), anchor="w")
        tree.column(col, width=width, anchor="w")

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    def populate_summary():
        md = calculate_monthly_data()
        # update summary cards
        total_rev = sum(d["revenue"] for d in md.values())
        total_cost = sum(d["cost"] for d in md.values())
        total_prof = sum(d["profit"] for d in md.values())
        rev_lbl.config(text=f"Rs. {total_rev:,.2f}")
        cost_lbl.config(text=f"Rs. {total_cost:,.2f}")
        prof_lbl.config(text=f"Rs. {total_prof:,.2f}")

        # populate table
        tree.delete(*tree.get_children())
        set_month_list()
        for month, data in sorted(md.items(), reverse=True):
            tree.insert("", "end", values=(
                month,
                f"{data['revenue']:,.2f}",
                f"{data['cost']:,.2f}",
                f"{data['profit']:,.2f}"
            ))

        # update chart
        try:
            if chart_objs:
                ax = chart_objs['ax']
                canvas = chart_objs['canvas']
                ax.clear()
                months = sorted(md.keys())
                profits = [md[m]['profit'] for m in months]
                colors = [COLOR_SUCCESS if p >= 0 else COLOR_DANGER for p in profits]
                # Use numeric x positions to draw bars (avoids categorical warnings)
                x = list(range(len(months)))
                ax.bar(x, profits, color=colors, edgecolor='black', alpha=0.9)
                ax.set_xticks(x)
                ax.set_xticklabels(months, rotation=45, ha='right')
                ax.set_title('Monthly Net Profit', fontsize=16)
                ax.set_ylabel('Profit (Rs.)', fontsize=12)
                ax.grid(axis='y', linestyle='--', alpha=0.4)
                chart_objs['fig'].tight_layout()
                canvas.draw()
        except Exception:
            logging.exception('Failed to draw summary chart')

    def populate_month(month):
        sales = load_sales()
        rows = [s for s in sales if s.get('month') == month]
        revenue = sum(s.get('selling_price', 0) * s.get('quantity', 0) for s in rows)
        cost = sum(s.get('purchase_price', 0) * s.get('quantity', 0) for s in rows)
        profit = revenue - cost

        # update summary cards for this month
        rev_lbl.config(text=f"Rs. {revenue:,.2f}")
        cost_lbl.config(text=f"Rs. {cost:,.2f}")
        prof_lbl.config(text=f"Rs. {profit:,.2f}")

        # reconfigure table for detail view
        tree.delete(*tree.get_children())
        tree.config(columns=("date", "model", "qty", "selling_price", "purchase_price", "profit"))
        tree['show'] = 'headings'
        detail_map = {
            "date": ("Date", 140),
            "model": ("Model", 300),
            "qty": ("Qty", 80),
            "selling_price": ("Unit Price", 120),
            "purchase_price": ("Cost", 120),
            "profit": ("Profit", 120)
        }
        for col, (label_text, width) in detail_map.items():
            tree.heading(col, text=label_text.upper(), anchor="w")
            tree.column(col, width=width, anchor="w")

        for s in rows:
            p = (s.get('selling_price', 0) - s.get('purchase_price', 0)) * s.get('quantity', 0)
            tree.insert("", "end", values=(
                s.get('date'),
                s.get('model'),
                s.get('quantity'),
                f"{s.get('selling_price',0):,.2f}",
                f"{s.get('purchase_price',0):,.2f}",
                f"{p:,.2f}"
            ))

        # update chart to show per-sale profit
        try:
            if chart_objs:
                ax = chart_objs['ax']
                canvas = chart_objs['canvas']
                ax.clear()
                labels = [f"{r.get('date')}\n{r.get('model')}" for r in rows]
                profits = [ (r.get('selling_price',0)-r.get('purchase_price',0))*r.get('quantity',0) for r in rows]
                colors = [COLOR_SUCCESS if p >= 0 else COLOR_DANGER for p in profits]
                x = list(range(len(labels)))
                ax.bar(x, profits, color=colors, edgecolor='black', alpha=0.9)
                ax.set_xticks(x)
                ax.set_xticklabels(labels, rotation=45, ha='right')
                ax.set_title(f'Profits for {month}', fontsize=14)
                ax.grid(axis='y', linestyle='--', alpha=0.4)
                chart_objs['fig'].tight_layout()
                canvas.draw()
        except Exception:
            logging.exception('Failed to draw month chart')

    # initial populate
    populate_summary()

    def refresh_data(event=None):
        try:
            populate_summary()
        except Exception:
            logging.exception("Failed to refresh profit data")

    # Refresh when the notebook tab is selected
    try:
        nb = parent
        def on_tab_changed(ev):
            try:
                sel = nb.select()
                if sel == str(window):
                    refresh_data()
            except Exception:
                pass
        nb.bind('<<NotebookTabChanged>>', on_tab_changed)
    except Exception:
        pass

    # FOOTER
    footer = ttk.Frame(window)
    footer.pack(fill="x", pady=(20, 0))

    make_button(footer, "Export to Excel", command=lambda: export_to_excel(calculate_monthly_data()), kind="primary").pack(side="right")

    return window
