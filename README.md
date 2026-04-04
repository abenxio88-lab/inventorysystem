# Mintaka Sphere Inventory Management System

## Quick Start
```bash
cd inventory_app
python main.py
```

## Architecture
```
inventory_app/
├── database.py    ← ALL SQL (InventoryDB class)
├── services.py    ← Business logic (svc.inventory, svc.sales, etc.)
├── *_ui.py        ← UI ONLY — zero SQL, reads/writes through svc.*
└── main.py        ← Single entry point, all tabs wired
```

## Features (20 tabs)
Inventory, Sales, Locations, Suppliers, Purchase Orders, Sales Orders,
Stock Transfers, Invoicing, Returns/RMA, Reports, Profit Analysis,
Alerts, Smart Analytics, Industry Settings, Trade-ins, Service Tickets,
Dashboard, Pharmacy, Electronics, Lease/Rental

## Tech Stack
Python 3.14 | Tkinter/CustomTkinter | SQLite (WAL mode)
