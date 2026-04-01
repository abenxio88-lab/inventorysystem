import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
try:
    from .ui_theme import (
        make_button, make_card, styled_label, styled_entry, 
        FONT_REGULAR, FONT_BOLD, FONT_HEADING, SPACING_DEFAULT,
        COLOR_APP_BG, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_BORDER,
        COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
        COLOR_CARD_BG, get_palette
    )
except (ImportError, ModuleNotFoundError):
    from ui_theme import (
        make_button, make_card, styled_label, styled_entry, 
        FONT_REGULAR, FONT_BOLD, FONT_HEADING, SPACING_DEFAULT,
        COLOR_APP_BG, COLOR_TEXT_MUTED, COLOR_TEXT_MAIN, COLOR_BORDER,
        COLOR_PRIMARY, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING,
        COLOR_CARD_BG, get_palette
    )
import tkinter.font as tkfont
import json
import os
import copy

try:
    from .utils import get_data_dir, export_inventory_to_csv, import_inventory_from_csv, backup_data, audit_event, write_json_atomic, load_json_file
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir, export_inventory_to_csv, import_inventory_from_csv, backup_data, audit_event, write_json_atomic, load_json_file

try:
    from .barcode_system import scan_barcode_from_camera, generate_product_barcode
except (ImportError, ModuleNotFoundError):
    try: from barcode_system import scan_barcode_from_camera, generate_product_barcode
    except:
        scan_barcode_from_camera = lambda: None
        generate_product_barcode = lambda p: None

DATA_FILE = os.path.join(get_data_dir(), "inventory.json")

def load_inventory():
    return load_json_file(DATA_FILE, default=[])

def save_inventory(data):
    try:
        write_json_atomic(DATA_FILE, data)
    except Exception:
        logging.exception("Failed to save inventory")

def create_inventory_tab(parent, current_user=None):
    """
    Creates the inventory management tab.

    Args:
        parent (ttk.Notebook): The notebook widget to attach this tab to.
        
    Returns:
        ttk.Frame: The frame containing the inventory management content.
    """
    window = ttk.Frame(parent, padding=15)
    
    # Use centralized fonts from ui_theme
    body_font = FONT_REGULAR
    label_font = FONT_BOLD
    section_font = FONT_HEADING
    table_font = FONT_REGULAR
    
    # Use a PanedWindow for resizable side-by-side layout
    paned_window = ttk.PanedWindow(window, orient='horizontal')
    paned_window.pack(fill='both', expand=True)

    # LEFT FRAME: Form and Actions
    left_frame = ttk.Frame(paned_window, padding=10)
    paned_window.add(left_frame, weight=1)

    # RIGHT FRAME: Table and Search
    right_frame = ttk.Frame(paned_window, padding=10)
    paned_window.add(right_frame, weight=3)

    # Undo stack
    undo_stack = []

    # Helper functions (add, update, etc.)
    def refresh_model_list():
        inv = load_inventory()
        models = sorted(list({i.get("model") for i in inv if i.get("model")}))
        model_cb['values'] = models

    def _is_admin():
        try:
            from .utils import load_users
        except (ImportError, ModuleNotFoundError):
            from utils import load_users
        if not current_user:
            return False
        users = load_users()
        return users.get(current_user, {}).get('role') == 'admin'

    def build_item():
        return {
            "model": model_var.get().strip(),
            "category": category_var.get().strip(),
            "screen_type": screen_var.get().strip(),
            "supplier": supplier_entry.get().strip(),
            "purchase_price": int(purchase_var.get()),
            "selling_price": int(selling_var.get()),
            "stock": int(stock_var.get()),
            "notes": notes_entry.get().strip()
        }

    def add_item():
        data = load_inventory()
        model = model_var.get().strip()
        if not model:
            messagebox.showerror("Error", "Model name required")
            return
        if any(i.get("model") == model for i in data):
            messagebox.showerror("Error", "Model already exists — use Update")
            return
        
        undo_stack.append(copy.deepcopy(data))
        if len(undo_stack) > 10: undo_stack.pop(0)

        data.append(build_item())
        try:
            save_inventory(data)
            logging.info(f"Inventory Added: {model}")
            try:
                audit_event(current_user, "add", target=model, details={"model": model})
            except Exception:
                logging.exception("Failed to audit add_item")
            refresh()
            clear_form()
        except Exception:
            logging.error("Failed to save inventory", exc_info=True)
            messagebox.showerror("Error", "Failed to save inventory")

    def update_item():
        data = load_inventory()
        model = model_var.get().strip()
        if not model:
            messagebox.showerror("Error", "Model name required")
            return
        for i, it in enumerate(data):
            if it.get("model") == model:
                undo_stack.append(copy.deepcopy(data))
                if len(undo_stack) > 10: undo_stack.pop(0)
                data[i] = build_item()
                try:
                    save_inventory(data)
                    logging.info(f"Inventory Updated: {model}")
                    try:
                        audit_event(current_user, "update", target=model, details={"model": model})
                    except Exception:
                        logging.exception("Failed to audit update_item")
                    refresh()
                    clear_form()
                    return
                except Exception:
                    logging.error("Failed to save inventory", exc_info=True)
                    messagebox.showerror("Error", "Failed to save inventory")
                    return
        messagebox.showerror("Error", "Model not found — use Add to create new model")

    def delete_item():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select item to delete")
            return

        if not _is_admin():
            messagebox.showerror("Permission Denied", "Only admins can delete items")
            return

        selected = sel[0]
        model = tree.item(selected, "values")[0]
        if not messagebox.askyesno("Confirm", f"Delete {model}?"):
            return

        old = load_inventory()
        undo_stack.append(copy.deepcopy(old))
        if len(undo_stack) > 10: undo_stack.pop(0)

        data = [i for i in old if i.get("model") != model]
        try:
            save_inventory(data)
            logging.info(f"Inventory Deleted: {model}")
            try:
                audit_event(current_user, "delete", target=model, details={"model": model})
            except Exception:
                logging.exception("Failed to audit delete_item")
            refresh()
            clear_form()
        except Exception:
            logging.error("Failed to delete inventory", exc_info=True)
            messagebox.showerror("Error", "Failed to delete inventory")

    def undo_action():
        if not undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo")
            return
        prev = undo_stack.pop()
        try:
            save_inventory(prev)
            refresh()
            clear_form()
            logging.info("Undo applied")
            try:
                audit_event(current_user, "undo", details={"note": "undo applied"})
            except Exception:
                logging.exception("Failed to audit undo")
        except Exception:
            logging.error("Failed to undo", exc_info=True)
            messagebox.showerror("Error", "Failed to undo")

    def clear_form():
        model_var.set("")
        category_var.set("")
        screen_var.set("")
        supplier_entry.delete(0, tk.END)
        purchase_var.set(0)
        selling_var.set(0)
        stock_var.set(0)
        notes_entry.delete(0, tk.END)
        
    def quick_scan():
        """Use camera to scan barcode and auto-fill form."""
        result = scan_barcode_from_camera()
        if result:
            data = result.get('raw_data', '')
            if data:
                # If it's a known product format, we could parse it
                # For now, just put the raw data in the model/notes
                model_var.set(data)
                notes_entry.delete(0, tk.END)
                notes_entry.insert(0, f"Scanned: {data}")
                messagebox.showinfo("Scanned", f"Barcode detected: {data}")
        else:
            messagebox.showwarning("Scanner", "No barcode detected or scanner closed.")

    def on_tree_click(event):
        row = tree.identify_row(event.y)
        if row == "":
            try:
                sel = tree.selection()
                if sel:
                    tree.selection_remove(sel)
            except Exception: pass
            clear_form()
            return "break"

    def refresh(data=None):
        tree.delete(*tree.get_children())
        items = data if data is not None else load_inventory()
        total = 0
        for i, item in enumerate(items):
            stock_val = int(item.get("stock", 0))
            total += stock_val
            tags = ("even",) if i % 2 else ("odd",)
            if stock_val <= 5:
                tags = ("low",)
            
            tree.insert("", "end", values=(
                item.get("model"),
                item.get("category", ""),
                item.get("screen_type", ""),
                item.get("supplier", ""),
                f'{item.get("purchase_price", 0):,}',
                f'{item.get("selling_price", 0):,}',
                stock_val
            ), tags=tags)
        refresh_model_list()
        total_var.set(f"Total Stock Items: {total:,}")

    def on_select(event):
        sel = tree.selection()
        if not sel:
            clear_form()
            return
        v = tree.item(sel[0], "values")
        model_var.set(v[0])
        category_var.set(v[1])
        screen_var.set(v[2])
        supplier_entry.delete(0, tk.END); supplier_entry.insert(0, v[3])
        # Convert formatted string back to int for spinboxes
        purchase_var.set(int(v[4].replace(",", "")))
        selling_var.set(int(v[5].replace(",", "")))
        stock_var.set(v[6])

    # ===== FORM SECTION (now in left_frame) =====
    form_label = styled_label(left_frame, text="PRODUCT INFORMATION", kind="heading")
    form_label.pack(anchor="w", pady=(0, 10))

    form_card = make_card(left_frame, padx=20, pady=20)
    form_card.pack(fill="x", pady=(0, 15))

    entries = {}

    # Grid config for form
    form_card.grid_columnconfigure(0, weight=1)
    form_card.grid_columnconfigure(1, weight=1)

    # Helper for labels
    def get_bg(w):
        try: return w.cget("background")
        except:
            try: return w.cget("bg")
            except: return None

    card_bg = get_bg(form_card)

    def form_lbl(text, r, c, **kwargs):
        l = styled_label(form_card, text=text, kind="bold", foreground=COLOR_TEXT_MUTED)
        l.grid(row=r, column=c, sticky="w", padx=5, pady=(8, 2))
        return l

    form_lbl("Model", 0, 0)
    model_frame = ttk.Frame(form_card)
    model_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)
    
    model_var = tk.StringVar()
    model_cb = ttk.Combobox(model_frame, textvariable=model_var)
    model_cb.pack(side="left", expand=True, fill="x")
    
    scan_btn = make_button(model_frame, "🔍 Scan", command=quick_scan, kind="primary", width=8)
    scan_btn.pack(side="right", padx=(5, 0))
    
    entries["Model"] = model_cb
    try: model_cb.configure(font=body_font)
    except: pass
    form_lbl("Category", 2, 0)
    category_var = tk.StringVar()
    category_cb = ttk.Combobox(form_card, textvariable=category_var, values=["Phone", "Tablet", "Accessory"])
    category_cb.grid(row=3, column=0, sticky="ew", padx=5)
    entries["Category"] = category_cb
    try: category_cb.configure(font=body_font)
    except: pass

    form_lbl("Screen Type", 2, 1)
    screen_var = tk.StringVar()
    screen_cb = ttk.Combobox(form_card, textvariable=screen_var, values=["LCD", "IPS", "OLED", "AMOLED", "TFT"])
    screen_cb.grid(row=3, column=1, sticky="ew", padx=5)
    entries["Screen Type"] = screen_cb
    try: screen_cb.configure(font=body_font)
    except: pass

    form_lbl("Supplier", 4, 0)
    supplier_entry = styled_entry(form_card)
    supplier_entry.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5)
    entries["Supplier"] = supplier_entry
    try: supplier_entry.configure(font=body_font)
    except: pass
    
    form_lbl("Purchase Price", 6, 0)
    purchase_var = tk.IntVar(value=0)
    purchase_spin = ttk.Spinbox(form_card, from_=0, to=1000000, textvariable=purchase_var)
    purchase_spin.grid(row=7, column=0, sticky="ew", padx=5)
    try: purchase_spin.configure(font=body_font)
    except: pass

    form_lbl("Selling Price", 6, 1)
    selling_var = tk.IntVar(value=0)
    selling_spin = ttk.Spinbox(form_card, from_=0, to=1000000, textvariable=selling_var)
    selling_spin.grid(row=7, column=1, sticky="ew", padx=5)
    try: selling_spin.configure(font=body_font)
    except: pass

    form_lbl("Stock Quantity", 8, 0)
    stock_var = tk.IntVar(value=0)
    stock_spin = ttk.Spinbox(form_card, from_=0, to=100000, textvariable=stock_var)
    stock_spin.grid(row=9, column=0, columnspan=2, sticky="ew", padx=5)
    try: stock_spin.configure(font=body_font)
    except: pass

    form_lbl("Notes", 10, 0)
    notes_entry = styled_entry(form_card)
    notes_entry.grid(row=11, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10))
    try: notes_entry.configure(font=body_font)
    except: pass

    # ===== ACTIONS BUTTON BAR (now in left_frame) =====
    btn_frame = ttk.Frame(left_frame)
    btn_frame.pack(fill="x", pady=10)

    # Use consistent button sizing and font for clarity
    make_button(btn_frame, "Add Item", command=lambda: add_item(), kind="success").pack(side="left", expand=True, fill="x", padx=(0, 5))
    make_button(btn_frame, "Update Item", command=lambda: update_item(), kind="primary").pack(side="left", expand=True, fill="x", padx=(0, 5))
    make_button(btn_frame, "Delete Item", command=lambda: delete_item(), kind="danger").pack(side="left", expand=True, fill="x")
    
    # Second row of buttons
    btn_frame_2 = ttk.Frame(left_frame)
    btn_frame_2.pack(fill="x", pady=(5, 10))
    make_button(btn_frame_2, "Undo", command=lambda: undo_action(), kind="warning").pack(side="left", expand=True, fill="x", padx=(0, 5))
    make_button(btn_frame_2, "Clear Form", command=lambda: clear_form(), kind="secondary").pack(side="left", expand=True, fill="x")

    # ===== TOOLBAR SECTION (now in right_frame) =====
    toolbar = ttk.Frame(right_frame, padding=(0, 6))
    toolbar.pack(fill="x", pady=(0, 12))

    styled_label(toolbar, "Search:").pack(side="left", padx=(0, 10))
    search_var = tk.StringVar()
    search_entry = styled_entry(toolbar, textvariable=search_var)
    search_entry.pack(side="left", expand=True, fill="x")

    def apply_search(event=None):
        q = search_var.get().strip().lower()
        if not q:
            refresh()
            return
        results = []
        for it in load_inventory():
            combined = " ".join([str(v) for v in it.values()]).lower()
            if q in combined:
                results.append(it)
        refresh(results)

    make_button(toolbar, "Search", command=apply_search, kind="primary").pack(side="left", padx=10)
    make_button(toolbar, "Clear", command=lambda: (search_var.set(""), refresh()), kind="secondary").pack(side="left")

    def on_export_csv():
        fname = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile=f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if not fname:
            return
        try:
            export_inventory_to_csv(fname)
            messagebox.showinfo("Export", f"Exported inventory to: {fname}")
        except Exception:
            logging.exception("Export failed")
            messagebox.showerror("Export Failed", "Failed to export inventory to CSV")

    def on_import_csv():
        fname = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not fname:
            return
        if not _is_admin():
            messagebox.showerror("Permission Denied", "Only admins can import inventory")
            return
        # Parse CSV for preview and validation
        import csv
        parsed = []
        invalid = []
        with open(fname, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, r in enumerate(reader, start=1):
                try:
                    item = {
                        "model": str(r.get("model", "")).strip(),
                        "category": str(r.get("category", "")).strip(),
                        "screen_type": str(r.get("screen_type", r.get("screen", ""))).strip(),
                        "supplier": str(r.get("supplier", "")).strip(),
                        "purchase_price": int(float(r.get("purchase_price", 0) or 0)),
                        "selling_price": int(float(r.get("selling_price", 0) or 0)),
                        "stock": int(float(r.get("stock", 0) or 0)),
                        "notes": str(r.get("notes", "")).strip()
                    }
                except Exception:
                    invalid.append((i, r))
                    continue
                # Basic validation
                if not item.get("model"):
                    invalid.append((i, r))
                else:
                    parsed.append(item)

        def show_preview():
            pv = tk.Toplevel(window)
            pv.title("Import Preview")
            pv.geometry("900x500")
            pv.transient(window)
            pv.grab_set()

            lbl = styled_label(pv, f"Previewing {os.path.basename(fname)} — {len(parsed)} valid rows, {len(invalid)} invalid rows", kind="heading")
            lbl.pack(anchor="w", pady=(6, 6), padx=6)

            treef = make_card(pv, padx=6, pady=6)
            treef.pack(fill="both", expand=True, padx=6, pady=(0,6))

            cols = ("model", "category", "screen_type", "supplier", "purchase_price", "selling_price", "stock")
            t = ttk.Treeview(treef, columns=cols, show="headings")
            for c in cols:
                t.heading(c, text=c)
                t.column(c, width=120)
            for it in parsed[:200]:
                t.insert("", "end", values=(it.get("model"), it.get("category"), it.get("screen_type"), it.get("supplier"), it.get("purchase_price"), it.get("selling_price"), it.get("stock")))
            t.pack(fill="both", expand=True)

            info = ttk.Frame(pv)
            info.pack(fill="x", pady=6)
            if invalid:
                styled_label(info, f"{len(invalid)} invalid rows — first invalid row shown below", foreground=COLOR_DANGER).pack(anchor="w")
            btn_frame = ttk.Frame(pv)
            btn_frame.pack(fill="x", pady=(6,12))

            def proceed():
                merge = messagebox.askyesno("Import", "Merge with existing inventory?\nYes = merge, No = replace", parent=pv)
                try:
                    import_inventory_from_csv(fname, merge=merge)
                    refresh()
                    messagebox.showinfo("Import", "Inventory imported successfully", parent=pv)
                    try:
                        audit_event(current_user, "import_csv", target=os.path.basename(fname), details={"merge": merge})
                    except Exception:
                        logging.exception("Failed to audit import")
                except Exception:
                    logging.exception("Import failed")
                    messagebox.showerror("Import Failed", "Failed to import inventory from CSV", parent=pv)
                pv.destroy()

            def cancel():
                pv.destroy()

            make_button(btn_frame, "Proceed with Import", command=proceed, kind="primary").pack(side="left", padx=6)
            make_button(btn_frame, "Cancel", command=cancel, kind="secondary").pack(side="left")

        show_preview()

    def on_backup():
        if not _is_admin():
            messagebox.showerror("Permission Denied", "Only admins can run backups")
            return

        try:
            dest = backup_data()
            messagebox.showinfo("Backup", f"Data backed up to: {dest}")
        except Exception:
            logging.exception("Backup failed")
            messagebox.showerror("Backup Failed", "Failed to backup data")

    def on_generate_qr():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Select item to generate QR")
            return
        
        model = tree.item(sel[0], "values")[0]
        # Find item in inventory
        items = load_inventory()
        item = next((i for i in items if i.get("model") == model), None)
        
        if item:
            try:
                # Add a dummy ID for the barcode generator if missing
                if 'id' not in item:
                    item['id'] = abs(hash(model)) % 1000000
                
                path = generate_product_barcode(item)
                if path:
                    messagebox.showinfo("Success", f"QR/Barcode generated at:\n{path}")
                    # Open the folder
                    os.startfile(os.path.dirname(path))
            except Exception as e:
                logging.exception("QR generation failed")
                messagebox.showerror("Error", f"Failed to generate QR: {e}")

    make_button(toolbar, "Export CSV", command=on_export_csv, kind="secondary").pack(side="left", padx=(10,0))
    make_button(toolbar, "Import CSV", command=on_import_csv, kind="secondary").pack(side="left", padx=(5,0))
    make_button(toolbar, "Backup", command=on_backup, kind="secondary").pack(side="left", padx=(5,0))
    make_button(toolbar, "Generate QR", command=on_generate_qr, kind="success").pack(side="left", padx=(5,0))

    state = {"full": False}
    def toggle_fullscreen():
        state["full"] = not state["full"]
        top_level = window.winfo_toplevel()
        top_level.attributes("-fullscreen", state["full"])

    btn_full = make_button(toolbar, "⛶", command=toggle_fullscreen, kind="secondary")
    btn_full.pack(side="right")
    
    total_var = tk.StringVar(value="Total Items: 0")
    styled_label(right_frame, text="", textvariable=total_var, kind="bold").pack(anchor="e", pady=(0, 5))

    # ===== TABLE SECTION (now in right_frame) =====
    table_frame = make_card(right_frame, padx=10, pady=10)
    table_frame.pack(fill="both", expand=True)

    columns = ("model", "category", "screen", "supplier", "purchase", "selling", "stock")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")

    column_map = {
        "model": ("Model Name", 150),
        "category": ("Category", 80),
        "screen": ("Screen Type", 80),
        "supplier": ("Supplier", 100),
        "purchase": ("Purchase Price", 100),
        "selling": ("Selling Price", 100),
        "stock": ("Stock Level", 60)
    }

    for col, (label_text, width) in column_map.items():
        anchor = "center" # Changed to center
        tree.heading(col, text=label_text.upper(), anchor=anchor)
        tree.column(col, width=width, anchor=anchor)

    # Scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)

    # Row tag styles
    palette = get_palette()
    # Futuristic Row Tagging
    tree.tag_configure("low", background="#3D0000", foreground=COLOR_DANGER) # Deep dark red bg
    tree.tag_configure("odd", background=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN)
    tree.tag_configure("even", background=COLOR_APP_BG, foreground=COLOR_TEXT_MAIN)

    tree.bind("<Button-1>", on_tree_click)
    tree.bind("<<TreeviewSelect>>", on_select)
    
    # Set Treeview font to FONT_REGULAR (which is 12) and row height
    try:
        style = ttk.Style()
        style.configure("Treeview", font=FONT_REGULAR, rowheight=28)
        style.configure("Treeview.Heading", font=FONT_BOLD)
    except Exception:
        pass

    refresh()

    # Key bindings
    def focus_next(event):
        event.widget.tk_focusNext().focus()
        return "break"

    search_entry.bind('<Return>', lambda e: apply_search())
    for w in [model_cb, category_cb, screen_cb, supplier_entry, purchase_spin, selling_spin, stock_spin, notes_entry]:
        w.bind('<Return>', focus_next)

    window.focus_set()
    return window