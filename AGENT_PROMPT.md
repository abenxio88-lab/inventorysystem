# 🚀 ENTERPRISE INVENTORY MANAGEMENT SYSTEM - AGENT BUILD PROMPT

## **PROJECT VISION**
Build a **$50,000+ enterprise-grade inventory management system** for mobile electronics & tech products businesses. Offline-first with Google Drive cloud sync. Professional, scalable, production-ready software.

---

## **🎯 CORE REQUIREMENTS**

### **1. SYSTEM ARCHITECTURE**
- **Offline-First**: Works 100% without internet
- **Cloud-Optional**: Google Drive backup for users who enable it
- **No Internet Dependency**: Never requires internet to function
- **Real-Time Sync**: Auto-sync when user is online
- **Encrypted**: All data encrypted locally and to cloud

### **2. TARGET BUSINESS**
Electronics/Mobile retailer with:
- Multiple warehouses/stores
- High SKU count (100s to 10,000s of products)
- Fast-moving inventory
- Multiple suppliers
- Team of 5-50 employees
- Need for compliance & audit trails

---

## **🗄️ DATABASE ARCHITECTURE (ENTERPRISE SCHEMA)**

### **Core Tables**
```
Users (Enhanced)
├── user_id (UUID)
├── username
├── email
├── role (ADMIN, MANAGER, STAFF, VIEWER)
├── encrypted_password
├── phone
├── created_at
├── last_login
├── is_active
└── department

CloudCredentials (NEW - PER USER)
├── cred_id (UUID)
├── user_id (FK)
├── google_refresh_token (encrypted)
├── google_drive_folder_id
├── is_enabled
├── last_sync_timestamp
├── sync_frequency (minutes)
├── encryption_key (encrypted)
└── created_at

SyncLog (NEW - AUDIT TRAIL)
├── sync_id (UUID)
├── user_id (FK)
├── timestamp
├── change_type (INSERT, UPDATE, DELETE, CONFLICT)
├── table_name
├── record_id
├── old_value (JSON)
├── new_value (JSON)
├── sync_status (LOCAL, PENDING, SYNCED, CONFLICT)
├── conflict_resolution_method
└── resolved_at

Locations (NEW - MULTI-WAREHOUSE)
├── location_id (UUID)
├── location_name
├── location_type (WAREHOUSE, RETAIL_STORE, SERVICE_CENTER)
├── address
├── city
├── state
├── country
├── manager_id (FK Users)
├── phone
├── email
├── capacity_sqft
├── is_active
└── created_at

Suppliers (NEW)
├── supplier_id (UUID)
├── supplier_name
├── contact_person
├── email
├── phone
├── address
├── payment_terms
├── lead_time_days
├── is_active
├── rating (1-5)
└── created_at

Products (ENHANCED)
├── product_id (UUID)
├── sku (UNIQUE)
├── product_name
├── category
├── subcategory
├── description
├── brand
├── model
├── specifications (JSON - for electronics)
├── cost_price
├── selling_price
├── markup_percentage
├── unit (UNIT, BOX, PACK, etc)
├── barcode (128/QR code)
├── image_path
├── supplier_id (FK)
├── warranty_months
├── expiry_date (for subscription/license)
├── is_serialized (for expensive electronics)
├── stock_reorder_point
├── stock_reorder_qty
├── created_by (FK Users)
├── created_at
├── version_number (for sync conflicts)
└── last_modified_at

Inventory (CORE - LOCATION-BASED)
├── inventory_id (UUID)
├── product_id (FK)
├── location_id (FK)
├── quantity_on_hand
├── quantity_reserved
├── quantity_damaged
├── quantity_in_transit
├── last_counted_date
├── last_counted_by (FK Users)
├── variance (for audits)
├── updated_at
└── sync_status

SerialNumbers (NEW - ELECTRONICS TRACKING)
├── serial_id (UUID)
├── product_id (FK)
├── serial_number (UNIQUE)
├── inventory_id (FK)
├── location_id (FK)
├── purchase_date
├── warranty_expiry
├── status (ACTIVE, SOLD, DAMAGED, LOST)
├── assigned_to_customer (optional)
└── created_at

Stock Movements (NEW - FULL AUDIT)
├── movement_id (UUID)
├── product_id (FK)
├── from_location_id (FK)
├── to_location_id (FK)
├── movement_type (RECEIVE, SALE, RETURN, DAMAGE, TRANSFER, COUNT_ADJUSTMENT)
├── quantity
├── reference_number (PO/SO/RMA)
├── initiated_by (FK Users)
├── created_at
├── reason (for adjustments)
└── notes

PurchaseOrders (NEW)
├── po_id (UUID)
├── po_number (UNIQUE)
├── supplier_id (FK)
├── location_id (FK)
├── order_date
├── expected_delivery_date
├── status (DRAFT, SENT, CONFIRMED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED)
├── total_amount
├── created_by (FK Users)
├── created_at
└── notes

SalesOrders (NEW)
├── so_id (UUID)
├── so_number (UNIQUE)
├── order_date
├── customer_name
├── customer_email
├── customer_phone
├── delivery_address
├── status (DRAFT, CONFIRMED, SHIPPED, DELIVERED, RETURNED, CANCELLED)
├── total_amount
├── discount_percentage
├── tax_amount
├── notes
├── created_by (FK Users)
├── created_at
└── payment_status

Returns & RMA (NEW)
├── rma_id (UUID)
├── rma_number (UNIQUE)
├── original_order_id (FK SalesOrders)
├── product_id (FK)
├── serial_number (for electronics)
├── reason (DEFECTIVE, DOA, WRONG_ITEM, CUSTOMER_RETURN)
├── status (OPEN, IN_INSPECTION, APPROVED, REJECTED, REPLACEMENT_ISSUED, REFUND_ISSUED)
├── return_date
├── resolved_date
├── resolution_notes
├── created_by (FK Users)
└── created_at

Alerts & Notifications (NEW)
├── alert_id (UUID)
├── user_id (FK)
├── alert_type (LOW_STOCK, OVERSTOCK, EXPIRY_WARNING, DAMAGED_DETECTED, SYNC_PENDING)
├── product_id (FK)
├── message
├── severity (INFO, WARNING, CRITICAL)
├── is_read
├── created_at
└── acknowledged_at

AuditLog (NEW - COMPLIANCE)
├── audit_id (UUID)
├── user_id (FK)
├── action (LOGIN, CREATE, UPDATE, DELETE, EXPORT, SYNC, REPORT)
├── table_name
├── record_id
├── timestamp
├── ip_address
├── changes (JSON)
└── notes
```

---

## **🎨 USER INTERFACE - WINDOWS/TAB STRUCTURE**

### **Main Dashboard (Enhanced)**
- **Connection Status Widget** (Top-Right)
  - 🟢 Online & Synced
  - 🟡 Online & Syncing
  - 🔴 Offline
  - Pending items count
  - Last sync time

- **Quick Stats Cards**
  - Total Inventory Value
  - Low Stock Items
  - Pending Sync Items
  - Monthly Sales
  - Top 5 Moving Products

- **Real-Time Alerts Panel**
  - Low stock notifications
  - Expiry warnings
  - System notifications

### **Tab 1: Quick Scan (NEW)**
- QR/Barcode scanner
- Quick add/receive
- Real-time stock update
- Bulk operations
- Camera feed

### **Tab 2: Inventory Management (ENHANCED)**
- **Products Grid** with columns:
  - SKU | Name | Category | Location | On-Hand | Reserved | Damaged | In-Transit | Cost | Selling Price | Margin% | Action
- **Filters**: Category, Location, Supplier, Stock Status
- **Quick Actions**:
  - Add Product with all details
  - Edit Product details & specifications
  - Bulk Upload from CSV/Excel
  - Set Serial Numbers for electronics
  - Generate Barcodes/QR codes
  - Search & Advanced Filter
  - Multi-select & batch operations

- **Stock Transfer Module**
  - From Location → To Location
  - Quantity
  - Reference
  - Auto-updates all locations

### **Tab 3: Locations (NEW)**
- **Warehouse/Store Management**
  - List all locations with capacity
  - Stock distribution map
  - Manager assignments
  - Add/Edit locations
  - Stock distribution chart

### **Tab 4: Suppliers (NEW)**
- Supplier database
- Contact info
- Performance metrics
- Lead time tracking
- Payment terms

### **Tab 5: Purchase Orders (NEW)**
- Create PO from low stock alerts
- Track deliveries
- GRN (Goods Receipt Notes)
- Supplier comparison
- Cost tracking

### **Tab 6: Sales & Orders (NEW)**
- Sales order management
- Customer history
- Order tracking
- Delivery status
- Return processing

### **Tab 7: Reports (ENHANCED)**
- **Stock Reports**
  - Current inventory by location
  - Stock aging
  - Slow/Fast movers
  - Variance reports
  - Physical count sheets

- **Sales Reports**
  - Daily/Weekly/Monthly sales
  - Top products
  - Revenue by category
  - Customer analysis

- **Financial Reports**
  - Inventory valuation (FIFO/LIFO)
  - Profit by product/category
  - Margin analysis
  - Cost vs Selling price

- **Compliance Reports**
  - Audit logs
  - User activity
  - Change history
  - Data integrity check

- **Export**: PDF, Excel, CSV, PowerPoint

### **Tab 8: Cloud Backup (NEW)**
- **Google Drive Setup**
  - OAuth login button
  - Status: Connected/Not Connected
  - Show Google account
  - Disconnect option

- **Sync Settings**
  - Auto-sync frequency (every 5/10/15 mins)
  - Manual sync button
  - Full backup button
  - Restore from backup
  - Backup history

- **Sync Details**
  - Last sync time
  - Next sync time
  - Items pending sync
  - Sync history log
  - Conflict resolution history

- **Data Encryption**
  - Encryption status
  - View encryption key (masked)
  - Change encryption password

### **Tab 9: Settings (ENHANCED)**
- **User Management**
  - Add/Edit/Deactivate users
  - Assign roles & permissions
  - Change passwords
  - Activity history

- **System Settings**
  - Company name, logo, address
  - Backup frequency
  - Alert thresholds
  - Currency, tax rates
  - Report templates

- **Database Operations**
  - Manual backup
  - Database integrity check
  - Clear cache
  - Reset demo data

### **Tab 10: Audit & Compliance (NEW)**
- Complete audit trail
- User activity log
- Change history with versions
- Data integrity reports
- Export compliance reports

---

## **🌟 KEY FEATURES TO IMPLEMENT**

### **PHASE 1: OFFLINE-FIRST FOUNDATION**
- [ ] Enhanced SQLite database with all tables
- [ ] SQLCipher encryption for local storage
- [ ] Offline detection & status indicator
- [ ] Data validation & integrity checks
- [ ] Local backup mechanism

### **PHASE 2: GOOGLE DRIVE SYNC**
- [ ] Google OAuth integration
- [ ] Per-user cloud credentials storage (encrypted)
- [ ] Sync engine with queue-based operations
- [ ] Conflict detection & resolution
- [ ] Automatic sync when online
- [ ] Manual sync button
- [ ] Sync status UI widget
- [ ] Backup history & restore

### **PHASE 3: QR/BARCODE**
- [ ] Barcode/QR code generation (Code128, EAN13, QR)
- [ ] Camera-based scanning (OpenCV)
- [ ] Quick add/receive from scan
- [ ] Bulk import from file

### **PHASE 4: MULTI-LOCATION**
- [ ] Location management module
- [ ] Stock distribution tracking
- [ ] Inventory transfers between locations
- [ ] Location-specific reports

### **PHASE 5: ELECTRONICS-SPECIFIC**
- [ ] Serial number tracking
- [ ] Warranty management
- [ ] Expiry/subscription tracking
- [ ] Device specifications storage
- [ ] Brand & model organization
- [ ] RMA (Return Material Authorization)

### **PHASE 6: PURCHASE ORDERS**
- [ ] PO creation & management
- [ ] Supplier tracking
- [ ] Goods Receipt Notes (GRN)
- [ ] Delivery tracking
- [ ] Cost comparison

### **PHASE 7: SALES & ORDERS**
- [ ] Sales order management
- [ ] Customer database
- [ ] Order tracking
- [ ] Delivery status
- [ ] Return processing

### **PHASE 8: ADVANCED REPORTS**
- [ ] Stock valuation reports
- [ ] Financial analysis (FIFO/LIFO)
- [ ] Sales analytics
- [ ] Profit by product/category
- [ ] Custom report builder
- [ ] PDF/Excel exports with charts

### **PHASE 9: COMPLIANCE & AUDIT**
- [ ] Complete audit trail
- [ ] User activity logging
- [ ] Change history with rollback
- [ ] Data integrity checks
- [ ] Compliance reporting

### **PHASE 10: USER & ROLES**
- [ ] Role-based access control (ADMIN, MANAGER, STAFF, VIEWER)
- [ ] Granular permissions
- [ ] Team management
- [ ] Activity tracking per user

---

## **🔒 SECURITY REQUIREMENTS**

- ✅ SQLCipher for local database encryption
- ✅ AES-256 encryption for data before cloud upload
- ✅ Google OAuth (never store passwords)
- ✅ User credentials encrypted locally only
- ✅ API tokens with expiration
- ✅ Activity logging for compliance
- ✅ Data integrity verification
- ✅ Secure password hashing (Argon2)
- ✅ TLS/SSL for cloud communication
- ✅ Session management

---

## **🎯 UI/UX STANDARDS**

- **Modern Professional Look**: Use PyQt6 or migrate to web (React)
- **Dark & Light Themes**: Professional color scheme
- **Responsive**: Works on laptops, desktops, tablets
- **Fast**: Snappy UI even with large datasets
- **Offline Indicator**: Always visible connection status
- **Keyboard Shortcuts**: Power users need efficiency
- **Undo/Redo**: For all operations
- **Search & Filter**: Quick access to data
- **Bulk Operations**: Select multiple items & act
- **Batch Import/Export**: Handle thousands of items
- **Real-Time Updates**: Changes reflect immediately
- **Notifications**: In-app alerts for important events

---

## **📱 MOBILE ELECTRONICS SPECIFIC FEATURES**

For electronics/mobile business:
- **Device Specifications**: Screen size, RAM, Storage, Battery, Camera specs
- **Brand & Model**: Organized by brand → model → variants
- **Serial Number Tracking**: Each device has unique serial
- **Warranty Management**: Warranty expiry dates & status
- **Damage Classification**: Screen damage, battery health, software issues
- **Subscription Tracking**: For software/cloud services bundled with devices
- **Trade-In Value**: Track trade-in inventory
- **Refurbished Stock**: Separate tracking for refurbished vs new
- **Service/Repair Tracking**: Which devices sent for service
- **Compliance**: Security updates, warranty claims

---

## **🚀 BUILD STANDARDS**

- **Code Quality**: PEP 8, type hints, docstrings
- **Error Handling**: Graceful degradation when offline
- **Logging**: Comprehensive logging for debugging
- **Testing**: Unit tests, integration tests
- **Documentation**: Code comments & README
- **Performance**: Handle 100K+ products smoothly
- **Scalability**: Designed for future growth
- **Maintainability**: Clean, modular code
- **Deployment**: Packagable as .exe, .dmg, .deb

---

## **🎓 DELIVERABLES**

Each module should include:
1. ✅ Database migrations
2. ✅ Core business logic
3. ✅ UI components
4. ✅ Error handling
5. ✅ Logging
6. ✅ Tests
7. ✅ Documentation

---

## **💡 EXECUTION APPROACH**

1. **Don't break existing code** - enhance incrementally
2. **Add new modules** - keep modular architecture
3. **Database migration** - version the schema
4. **Backward compatible** - old data must work
5. **Professional quality** - $50K grade code
6. **Production ready** - deployable day 1

---

## **🎬 ACTION REQUIRED**

Build this as a **production-grade enterprise software**. Each feature should be:
- ✅ Complete (no half-done features)
- ✅ Tested (works reliably)
- ✅ Documented (users & developers understand)
- ✅ Performant (handles scale)
- ✅ Secure (enterprise encrypted)
- ✅ Professional (looks $50K+ quality)

**This is enterprise software. Act like it.**

---

## **📞 NOTES**
- Backend API setup comes LATER
- Frontend first to see the "crazy software"
- Offline-first always
- Google Drive integration optional per user
- Ready to build at scale
