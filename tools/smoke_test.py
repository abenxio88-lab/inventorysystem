import os
import sys
import logging

# Ensure inventory_app modules are importable
ROOT = os.getcwd()
INVENTORY_APP = os.path.join(ROOT, "inventory_app")
if INVENTORY_APP not in sys.path:
    sys.path.insert(0, INVENTORY_APP)

from logger_setup import setup_logger
setup_logger()
logging.info("Smoke test started")

import inventory_ui
import sales_ui
import profit_ui

# 1) Simulate login
logging.info("Login successful: smoke_test_user, role: admin")

# 2) Add inventory item
try:
    inv = inventory_ui.load_inventory()
except Exception:
    inv = []

new_item = {
    "model": "SMOKE-TEST-XYZ",
    "category": "Phone",
    "screen_type": "IPS",
    "supplier": "QA",
    "purchase_price": 50.0,
    "selling_price": 75.0,
    "stock": 10,
    "serial": "SMK123456",
    "notes": "Automated smoke test item"
}

# remove any existing test item
inv = [i for i in inv if i.get("model") != new_item["model"]]
inv.append(new_item)
inventory_ui.save_inventory(inv)
logging.info(f"Inventory Added: {new_item}")

# 3) Record a sale of 2 units
try:
    sales = sales_ui.load_sales()
except Exception:
    sales = []

qty = 2
# decrement stock in inventory
for it in inv:
    if it.get("model") == new_item["model"]:
        it["stock"] = int(it.get("stock", 0)) - qty
        selling_price = float(it.get("selling_price", 0))
        purchase_price = float(it.get("purchase_price", 0))
        break
else:
    logging.error("Smoke test item not found in inventory")
    selling_price = 0
    purchase_price = 0

inventory_ui.save_inventory(inv)

from datetime import datetime
now = datetime.now()
sale = {
    "date": now.strftime("%Y-%m-%d"),
    "month": now.strftime("%Y-%m"),
    "model": new_item["model"],
    "quantity": qty,
    "selling_price": selling_price,
    "purchase_price": purchase_price,
    "total": selling_price * qty
}

sales.append(sale)
sales_ui.save_sales(sales)
logging.info(f"Sale recorded: model={sale['model']}, qty={sale['quantity']}, total={sale['total']}")

# 4) Export profit (skip if openpyxl missing to avoid GUI prompts)
monthly = profit_ui.calculate_monthly_data()
logging.info(f"Monthly profit calculated for {len(monthly)} months")

if getattr(profit_ui, 'OPENPYXL_AVAILABLE', False):
    try:
        profit_ui.export_to_excel(monthly)
    except Exception:
        logging.error("Export failed during smoke test", exc_info=True)
else:
    logging.info("Export skipped: openpyxl not available")

# 5) Print log contents
log_file = os.path.join(INVENTORY_APP, 'logs', 'app.log')
print('\n--- app.log contents ---\n')
if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print('Log file not found:', log_file)
