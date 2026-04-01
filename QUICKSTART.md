# 🚀 QUICK START GUIDE - Minataka Sphere Inventory System v2.0

## 📦 INSTALLATION

### Step 1: Install Dependencies

Open Command Prompt or PowerShell in the project folder:

```bash
cd "c:\Users\Lenovo\Desktop\FINALs\MS VSCODE  TESTIMG\MINTAKAtest - Copy\inventory_app"
```

Install the required packages:

```bash
# Install core dependencies (REQUIRED)
pip install -r requirements.txt

# OR install just the essential new feature:
pip install qrcode[pil]
```

**That's it!** All other features use Python's built-in libraries.

---

### Step 2: Run the Application

```bash
python main.py
```

On first run:
1. Database will auto-initialize
2. You'll be prompted to create an admin account
3. Login with your credentials
4. Start using the system!

---

## 🎯 WHAT'S NEW IN v2.0

### Status Bar (Bottom of Window)
```
┌─────────────────────────────────────────────────────────────┐
│  Minataka Sphere IMS v2.0  │  🔴 Offline  │  🔄 Sync Now   │
└─────────────────────────────────────────────────────────────┘
```

- **🟢 Online / 🔴 Offline** - Real-time internet status
- **⏳ Pending: X** - Shows pending sync operations
- **💾 Quick Backup** - One-click backup button
- **ℹ️** - Detailed status information

---

### Alerts Tab (Admin Only)
```
🔔 Alerts & Notifications

┌────────────────────────────────────────────────────────────┐
│  Unread: 5  │  Critical: 2  │  Warnings: 3  │  Total: 15  │
├────────────────────────────────────────────────────────────┤
│  [🟢] Low Stock    │ "iPhone 16 Pro" has only 3 units     │
│  [🔴] Out of Stock │ "Samsung S24" is out of stock        │
└────────────────────────────────────────────────────────────┘
```

**Features:**
- Automatic low stock detection
- Warranty expiry warnings
- Filter by severity/type
- Mark as read/acknowledge/delete

---

### Enhanced Backup System
- **Automatic daily backups** (configurable time)
- **Manual backup** - Click "💾 Quick Backup"
- **Compressed ZIP** format
- **SHA256 integrity checks**
- **Auto-cleanup** of old backups (30-day retention)

---

### QR Code Generation
Generate QR codes for your products:

```python
# In Python console or script:
from qr_generator import save_product_qr

product = {
    'id': 1,
    'sku': 'IPHONE-16-PRO',
    'model': 'iPhone 16 Pro Max',
    'stock': 50,
    'selling_price': 2000
}

save_product_qr(product, 'iphone_qr.png')
```

This creates a scannable QR code with product information.

---

## 📁 FILE STRUCTURE

```
inventory_app/
├── main.py               # Main application entry point
├── database.py           # SQLite database (NEW)
├── network.py            # Connectivity monitoring (NEW)
├── sync_engine.py        # Cloud sync engine (NEW)
├── status_widget.py      # Status bar widgets (NEW)
├── backup_manager.py     # Enhanced backup (NEW)
├── qr_generator.py       # QR code generation (NEW)
├── alerts.py             # Alerts system (NEW)
├── alerts_ui.py          # Alerts UI tab (NEW)
│
├── data/
│   ├── inventory.db      # SQLite database (auto-created)
│   ├── inventory.json    # Legacy format (still supported)
│   ├── sales.json
│   ├── users.json
│   ├── settings.json
│   └── backups/          # Automatic backups
│
└── requirements.txt      # Dependencies
```

---

## 🧪 TESTING

Run the test suite to verify everything works:

```bash
python test_features.py
```

Expected output:
```
✅ DATABASE: PASSED
✅ NETWORK: PASSED
✅ ALERTS: PASSED
✅ BACKUP: PASSED
✅ QR GENERATOR: PASSED (if qrcode installed)
✅ SYNC ENGINE: PASSED
```

---

## 🎓 HOW TO USE NEW FEATURES

### 1. Check Connection Status
Look at the bottom status bar:
- 🟢 = Internet available
- 🔴 = Working offline (all features still work!)

### 2. View Alerts
1. Login as admin
2. Click "🔔 Alerts" tab
3. See low stock warnings
4. Click "✅ Mark All Read" to clear

### 3. Quick Backup
1. Click "💾 Quick Backup" button
2. Wait for confirmation dialog
3. Backup saved to `data/backups/`

### 4. Generate QR Codes
```python
from qr_generator import create_qr

# Simple QR
create_qr("https://minataka.com", "website_qr.png")

# Product QR
from qr_generator import save_product_qr
save_product_qr(product_data, "product_qr.png")
```

### 5. Restore from Backup
```python
from backup_manager import backup_manager

# List available backups
backups = backup_manager.list_backups()
for b in backups:
    print(f"{b['filename']} - {b['created_at']}")

# Restore
backup_manager.restore_backup("path/to/backup.zip")
```

---

## ⚙️ CONFIGURATION

### Backup Settings (Admin Only)
1. Go to Dashboard tab
2. Click "Backup Settings" button
3. Configure:
   - Backup time (hour:minute)
   - Retention period (days)

### Alert Settings
Configured in database `alert_settings` table:
- `low_stock` - Enable/disable
- `threshold_value` - Stock level trigger
- `email_enabled` - Email notifications (future)

---

## 🔧 TROUBLESHOOTING

### "Database init failed"
- Check if `data/` folder is writable
- Ensure no other process has the database open

### "Backup failed"
- Check disk space
- Verify `data/backups/` folder permissions

### "qrcode library not available"
```bash
pip install qrcode[pil]
```

### App won't start
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
del /s /q __pycache__
del /s /q *.pyc
```

---

## 📊 DATABASE SCHEMA

The new SQLite database includes:

**Core Tables:**
- `products` - Enhanced with SKU, barcode, serial numbers
- `locations` - Multiple warehouses/stores
- `suppliers` - Supplier contact & performance
- `customers` - Customer database
- `categories` - Product categorization

**Transaction Tables:**
- `purchase_orders` - PO management
- `sales_orders` - Sales tracking
- `stock_transfers` - Inter-location transfers
- `serial_numbers` - Device-level tracking

**System Tables:**
- `alerts` - Notifications
- `audit_log` - Activity trail
- `sync_queue` - Pending sync operations
- `settings` - Configuration

---

## 🎯 NEXT FEATURES TO IMPLEMENT

Ready for Phase 2-7? Here's what's next:

1. **Google Drive Sync** - Cloud backup (optional)
2. **Multi-Location UI** - Manage warehouses
3. **Supplier Management** - Supplier database & PO
4. **Serial Number Tracking** - Device-level inventory
5. **Purchase Orders** - Automated ordering
6. **Advanced Reports** - PDF/Excel with charts

---

## 📞 SUPPORT

**Contact:** usmansaeed.1988@gmail.com  
**Phone:** +92-344-4560738  

**Developed by:** Minataka Sphere  
**Copyright:** © 2026 Abenxio  
**Version:** 2.0 Enterprise

---

## 🎉 SUCCESS CHECKLIST

After installation, verify:

- [ ] Application starts without errors
- [ ] Can create admin account
- [ ] Can login successfully
- [ ] Status bar visible at bottom
- [ ] Connection status shows (🟢 or 🔴)
- [ ] Can add inventory items
- [ ] Can record sales
- [ ] Quick Backup button works
- [ ] Alerts tab visible (admin login)
- [ ] Test script passes (5/6 or 6/6)

**All checked? You're ready to go! 🚀**

---

## 💡 TIPS

1. **Always run as administrator** on first setup
2. **Backup regularly** - Use Quick Backup before major changes
3. **Check alerts daily** - Stay on top of low stock
4. **Use QR codes** - Faster inventory management
5. **Monitor sync status** - Ensure data is backed up

---

**Happy Inventory Managing! 📦✨**
