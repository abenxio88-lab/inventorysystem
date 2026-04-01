"""
Premium Widgets Module
- Interactive Charts with hover effects
- Toast Notifications
- Skeleton Loading States
- Command Palette (Ctrl+K)
- Advanced Animations
"""

import tkinter as tk
from tkinter import ttk
import math
import time
from datetime import datetime, timedelta
from typing import Callable, List, Dict, Any, Optional
from ui_theme import ThemeManager

class ToastNotification:
    """Modern toast notification system"""
    
    def __init__(self, parent):
        self.parent = parent
        self.toasts = []
        self.toast_window = None
        self.max_toasts = 3
        
    def show(self, message: str, type: str = "info", duration: int = 4000):
        """Show a toast notification"""
        theme = ThemeManager()
        
        # Create toast window
        toast = tk.Toplevel(self.parent)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        toast.attributes('-alpha', 0.0)
        
        # Colors based on type
        colors = {
            "success": ("#10B981", "#065F46", "✓"),
            "error": ("#EF4444", "#991B1B", "✕"),
            "warning": ("#F59E0B", "#92400E", "⚠"),
            "info": ("#3B82F6", "#1E40AF", "ℹ")
        }
        
        bg_color, dark_color, icon = colors.get(type, colors["info"])
        
        # Calculate position
        x = self.parent.winfo_x() + self.parent.winfo_width() - 320
        y = self.parent.winfo_y() + 20 + (len(self.toasts) * 70)
        
        toast.geometry(f"300x60+{x}+{y}")
        
        # Create glassmorphic frame
        frame = tk.Frame(toast, bg=bg_color)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Icon label
        icon_label = tk.Label(frame, text=icon, font=("Segoe UI", 16, "bold"), 
                             bg=bg_color, fg="white", padx=15)
        icon_label.pack(side=tk.LEFT, fill=tk.Y)
        
        # Message label
        msg_label = tk.Label(frame, text=message, font=("Inter", 10), 
                            bg=bg_color, fg="white", wraplength=220, justify=tk.LEFT)
        msg_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15), pady=15)
        
        # Store toast info
        toast_info = {"window": toast, "y": y, "target_y": y}
        self.toasts.append(toast_info)
        
        # Fade in animation
        self._fade_in(toast)
        
        # Auto dismiss
        toast.after(duration, lambda: self._dismiss(toast))
        
        return toast
    
    def _fade_in(self, toast):
        """Fade in animation"""
        for i in range(1, 11):
            toast.after(i * 30, lambda alpha=i/10: toast.attributes('-alpha', alpha))
    
    def _dismiss(self, toast):
        """Dismiss toast with fade out"""
        for i in range(10, 0, -1):
            toast.after((10-i) * 30, lambda alpha=i/10: toast.attributes('-alpha', alpha))
        toast.after(300, toast.destroy)
        
        # Remove from list and reposition others
        self.toasts = [t for t in self.toasts if t["window"] != toast]
        self._reposition_toasts()
    
    def _reposition_toasts(self):
        """Reposition remaining toasts"""
        for i, toast_info in enumerate(self.toasts):
            new_y = self.parent.winfo_y() + 20 + (i * 70)
            toast_info["window"].geometry(f"300x60+{self.parent.winfo_x() + self.parent.winfo_width() - 320}+{new_y}")


class SkeletonLoader:
    """Skeleton loading state for better UX"""
    
    def __init__(self, parent, width=300, height=20, skeleton_type="rect"):
        self.parent = parent
        self.skeleton_type = skeleton_type
        self.canvas = tk.Canvas(parent, width=width, height=height, 
                               highlightthickness=0, bg='transparent')
        self.shimmer_rect = None
        self.animating = False
        
    def start(self):
        """Start skeleton animation"""
        self.canvas.delete("all")
        width = int(self.canvas['width'])
        height = int(self.canvas['height'])
        
        # Base skeleton shape
        if self.skeleton_type == "circle":
            self.canvas.create_oval(5, 5, height-5, height-5, 
                                   fill='#E5E7EB', outline='')
        elif self.skeleton_type == "text":
            # Multiple text lines
            for i in range(3):
                y = i * (height // 3) + 2
                line_width = width - (i * 20)
                self.canvas.create_rectangle(0, y, line_width, y + height//3 - 4,
                                            fill='#E5E7EB', outline='')
        else:  # rect
            self.canvas.create_rectangle(5, 5, width-5, height-5,
                                        fill='#E5E7EB', outline='', radius=8)
        
        # Shimmer effect
        self.shimmer_rect = self.canvas.create_rectangle(-width//2, 0, width//2, height,
                                                         fill='rgba(255,255,255,0.4)', outline='')
        
        self.animating = True
        self._animate_shimmer(0)
        
        return self.canvas
    
    def _animate_shimmer(self, x):
        """Animate shimmer effect"""
        if not self.animating:
            return
            
        width = int(self.canvas['width'])
        self.canvas.move(self.shimmer_rect, 3, 0)
        
        if x > width:
            self.canvas.coords(self.shimmer_rect, -width//2, 0, width//2, int(self.canvas['height']))
        else:
            self.parent.after(16, lambda: self._animate_shimmer(x + 3))
    
    def stop(self):
        """Stop animation"""
        self.animating = False
        self.canvas.delete("all")


class InteractiveChart:
    """Interactive data visualization with hover effects"""
    
    def __init__(self, parent, chart_type="bar", width=400, height=250):
        self.parent = parent
        self.chart_type = chart_type
        self.width = width
        self.height = height
        self.data = []
        self.colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
        self.hover_tooltip = None
        
        self.canvas = tk.Canvas(parent, width=width, height=height,
                               highlightthickness=0, bg='transparent')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._hide_tooltip)
        
    def set_data(self, data: List[Dict[str, Any]]):
        """Set chart data: [{'label': 'Jan', 'value': 100}, ...]"""
        self.data = data
        self._draw()
        
    def _draw(self):
        """Draw the chart"""
        self.canvas.delete("all")
        
        if not self.data:
            return
            
        max_value = max(item['value'] for item in self.data) or 1
        
        if self.chart_type == "bar":
            self._draw_bar_chart(max_value)
        elif self.chart_type == "line":
            self._draw_line_chart(max_value)
        elif self.chart_type == "pie":
            self._draw_pie_chart()
            
    def _draw_bar_chart(self, max_value):
        """Draw bar chart"""
        bar_width = (self.width - 60) // len(self.data)
        spacing = 5
        
        for i, item in enumerate(self.data):
            x = 40 + i * bar_width
            bar_height = (item['value'] / max_value) * (self.height - 40)
            y = self.height - 20 - bar_height
            
            # Draw bar with gradient effect
            color = self.colors[i % len(self.colors)]
            self.canvas.create_rectangle(x + spacing, y, x + bar_width - spacing, 
                                        self.height - 20, fill=color, outline='',
                                        tags=f"bar_{i}", stipple='gray50')
            
            # Label
            self.canvas.create_text(x + bar_width//2, self.height - 10, 
                                   text=item['label'], font=("Inter", 8),
                                   fill='#6B7280')
                                   
    def _draw_line_chart(self, max_value):
        """Draw line chart"""
        points = []
        step_x = (self.width - 60) / (len(self.data) - 1) if len(self.data) > 1 else 0
        
        for i, item in enumerate(self.data):
            x = 40 + i * step_x
            y = self.height - 20 - (item['value'] / max_value) * (self.height - 40)
            points.extend([x, y])
            
            # Draw point
            self.canvas.create_oval(x-4, y-4, x+4, y+4, 
                                   fill=self.colors[i % len(self.colors)], outline='')
                                   
        # Draw line
        if len(points) >= 4:
            self.canvas.create_line(points, width=2, smooth=True, 
                                   fill=self.colors[0])
                                   
    def _draw_pie_chart(self):
        """Draw pie chart"""
        total = sum(item['value'] for item in self.data)
        start_angle = 0
        
        for i, item in enumerate(self.data):
            extent = (item['value'] / total) * 360 if total > 0 else 0
            color = self.colors[i % len(self.colors)]
            
            self.canvas.create_arc(20, 20, self.width-20, self.height-20,
                                  start=start_angle, extent=extent,
                                  fill=color, outline='',
                                  tags=f"slice_{i}")
            start_angle += extent
            
    def _on_mouse_move(self, event):
        """Handle mouse hover"""
        items = self.canvas.find_withtag(tk.CURRENT)
        if items:
            item_id = items[0]
            tags = self.canvas.gettags(item_id)
            for tag in tags:
                if tag.startswith("bar_") or tag.startswith("slice_"):
                    idx = int(tag.split("_")[1])
                    if idx < len(self.data):
                        self._show_tooltip(event.x_root, event.y_root, self.data[idx])
                    break
                    
    def _show_tooltip(self, x, y, data_item):
        """Show hover tooltip"""
        if self.hover_tooltip:
            self.hover_tooltip.destroy()
            
        self.hover_tooltip = tk.Toplevel(self.parent)
        self.hover_tooltip.overrideredirect(True)
        self.hover_tooltip.attributes('-topmost', True)
        
        tooltip_frame = tk.Frame(self.hover_tooltip, bg='#1F2937', relief=tk.FLAT)
        tooltip_frame.pack()
        
        tk.Label(tooltip_frame, text=data_item['label'], 
                font=("Inter", 10, "bold"), bg='#1F2937', fg='white').pack(padx=10, pady=5)
        tk.Label(tooltip_frame, text=f"{data_item['value']:,}", 
                font=("Inter", 12), bg='#1F2937', fg='#3B82F6').pack(padx=10, pady=(0, 5))
                
        self.hover_tooltip.geometry(f"+{x+10}+{y-10}")
        
    def _hide_tooltip(self, event=None):
        """Hide tooltip"""
        if self.hover_tooltip:
            self.hover_tooltip.destroy()
            self.hover_tooltip = None


class CommandPalette:
    """Global command palette (Ctrl+K style search)"""
    
    def __init__(self, parent, commands: List[Dict[str, Any]]):
        self.parent = parent
        self.commands = commands
        self.filtered_commands = commands.copy()
        self.palette_window = None
        self.search_var = tk.StringVar()
        self.selected_index = 0
        self.result_listbox = None
        
    def show(self):
        """Show command palette"""
        if self.palette_window and self.palette_window.winfo_exists():
            self.palette_window.destroy()
            
        self.palette_window = tk.Toplevel(self.parent)
        self.palette_window.title("Command Palette")
        self.palette_window.overrideredirect(True)
        self.palette_window.attributes('-topmost', True)
        
        # Center on parent
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 250
        y = self.parent.winfo_y() + 100
        self.palette_window.geometry(f"500x400+{x}+{y}")
        
        # Glassmorphic container
        container = tk.Frame(self.palette_window, bg='#FFFFFF', relief=tk.FLAT)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Search box
        search_frame = tk.Frame(container, bg='#F3F4F6', height=50)
        search_frame.pack(fill=tk.X, padx=20, pady=20)
        search_frame.pack_propagate(False)
        
        search_icon = tk.Label(search_frame, text="🔍", font=("Segoe UI", 16),
                              bg='#F3F4F6', fg='#6B7280')
        search_icon.pack(side=tk.LEFT, padx=15, pady=15)
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=("Inter", 14), bg='#F3F4F6', fg='#1F2937',
                               relief=tk.FLAT, insertbackground='#3B82F6')
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=15)
        search_entry.focus_set()
        
        self.search_var.trace_add("write", self._filter_commands)
        search_entry.bind("<Down>", self._navigate_results)
        search_entry.bind("<Return>", self._execute_selected)
        search_entry.bind("<Escape>", self._close)
        
        # Results list
        list_frame = tk.Frame(container, bg='#FFFFFF')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.result_listbox = tk.Listbox(list_frame, font=("Inter", 11),
                                        bg='#FFFFFF', fg='#1F2937',
                                        selectbackground='#3B82F6',
                                        selectforeground='white',
                                        relief=tk.FLAT, highlightthickness=1,
                                        highlightbackground='#E5E7EB')
        self.result_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                 command=self.result_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_listbox.config(yscrollcommand=scrollbar.set)
        
        self.result_listbox.bind("<Double-Button-1>", lambda e: self._execute_selected())
        
        self._update_results()
        
    def _filter_commands(self, *args):
        """Filter commands based on search"""
        query = self.search_var.get().lower()
        if query:
            self.filtered_commands = [
                cmd for cmd in self.commands 
                if query in cmd['name'].lower() or query in cmd.get('category', '').lower()
            ]
        else:
            self.filtered_commands = self.commands.copy()
        self._update_results()
        
    def _update_results(self):
        """Update results listbox"""
        self.result_listbox.delete(0, tk.END)
        for cmd in self.filtered_commands[:20]:  # Limit to 20 results
            category = cmd.get('category', '')
            display = f"{cmd['name']}  ({category})" if category else cmd['name']
            self.result_listbox.insert(tk.END, display)
            
    def _navigate_results(self, event):
        """Navigate results with keyboard"""
        self.result_listbox.selection_clear(0, tk.END)
        self.result_listbox.selection_set(self.selected_index)
        self.result_listbox.see(self.selected_index)
        
    def _execute_selected(self, event=None):
        """Execute selected command"""
        selection = self.result_listbox.curselection()
        if selection and selection[0] < len(self.filtered_commands):
            cmd = self.filtered_commands[selection[0]]
            callback = cmd.get('callback')
            if callback:
                self._close()
                callback()
                
    def _close(self, event=None):
        """Close palette"""
        if self.palette_window:
            self.palette_window.destroy()
            self.palette_window = None


class PremiumButton(ttk.Button):
    """Enhanced button with hover effects and animations"""
    
    def __init__(self, parent, text="", command=None, variant="primary", **kwargs):
        self.variant = variant
        self.original_command = command
        self.hover_state = False
        
        # Variant styles
        styles = {
            "primary": {"bg": "#3B82F6", "fg": "white", "hover_bg": "#2563EB"},
            "success": {"bg": "#10B981", "fg": "white", "hover_bg": "#059669"},
            "danger": {"bg": "#EF4444", "fg": "white", "hover_bg": "#DC2626"},
            "secondary": {"bg": "#F3F4F6", "fg": "#1F2937", "hover_bg": "#E5E7EB"},
            "ghost": {"bg": "transparent", "fg": "#3B82F6", "hover_bg": "#EFF6FF"}
        }
        
        style = styles.get(variant, styles["primary"])
        
        super().__init__(parent, text=text, command=command,
                        style="TButton", **kwargs)
        
        self.configure(bg=style["bg"], fg=style["fg"])
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, event):
        """Hover enter effect"""
        styles = {
            "primary": {"bg": "#2563EB"},
            "success": {"bg": "#059669"},
            "danger": {"bg": "#DC2626"},
            "secondary": {"bg": "#E5E7EB"},
            "ghost": {"bg": "#EFF6FF"}
        }
        style = styles.get(self.variant, {})
        self.configure(bg=style.get("bg", self.cget("bg")))
        
    def _on_leave(self, event):
        """Hover leave effect"""
        styles = {
            "primary": {"bg": "#3B82F6"},
            "success": {"bg": "#10B981"},
            "danger": {"bg": "#EF4444"},
            "secondary": {"bg": "#F3F4F6"},
            "ghost": {"bg": "transparent"}
        }
        style = styles.get(self.variant, {})
        self.configure(bg=style.get("bg", self.cget("bg")))


class AnimatedFrame(tk.Frame):
    """Frame with smooth entrance animations"""
    
    def __init__(self, parent, anim_type="fade", duration=300, **kwargs):
        super().__init__(parent, **kwargs)
        self.anim_type = anim_type
        self.duration = duration
        self.alpha = 0.0
        
    def animate_in(self):
        """Animate frame entrance"""
        if self.anim_type == "fade":
            self._fade_animation(0)
        elif self.anim_type == "slide":
            self._slide_animation()
            
    def _fade_animation(self, step):
        """Fade in animation"""
        if step <= 10:
            self.after(step * (self.duration // 10), 
                      lambda: self._fade_animation(step + 1))
                      
    def _slide_animation(self):
        """Slide in animation"""
        pass
