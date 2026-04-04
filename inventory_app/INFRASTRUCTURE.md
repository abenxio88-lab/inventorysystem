# Mintaka Sphere - Infrastructure Documentation

## 🏗️ Application Architecture Overview

### Core Components

#### 1. **app_core.py** - Central State Management
- **AppState**: Singleton pattern for global application state
  - Industry type management (Retail, Pharma, Electronics, Manufacturing, Healthcare)
  - Navigation history tracking
  - UI update callbacks system
  - Data link caching
  
- **PremiumPopup**: Universal dialog system
  - Scrollable content area (no hidden buttons)
  - Responsive layout with auto-sizing
  - Glassmorphism design support
  - Mouse wheel scrolling
  - Centered positioning
  
- **DataLinker**: Inter-module data synchronization
  - Sales → Inventory stock deduction
  - Purchase Orders → Inventory stock addition
  - Low Stock → Purchase Order suggestions
  - Supplier → Purchase Order linking

#### 2. **ui_theme.py** - Theme System
- Light/Dark mode toggle
- Dynamic color resolution
- Glassmorphism effects
- Consistent typography
- Premium component styling

#### 3. **Industry-Specific Configurations**

| Industry | Icon | Color | Key Features |
|----------|------|-------|--------------|
| Retail | 🛒 | #2563EB (Blue) | Barcode, POS, Loyalty Programs |
| Pharma | 💊 | #10B981 (Green) | Expiry Tracking, Batch Numbers, Prescription Management |
| Electronics | 📱 | #8B5CF6 (Purple) | Serial Numbers, Warranty Tracking, IMEI |
| Manufacturing | 🏭 | #F59E0B (Amber) | BOM, Work Orders, Raw Materials |
| Healthcare | 🏥 | #EF4444 (Red) | Patient Records, Equipment Tracking, Consumables |

---

## 🔗 Module Interlinking Matrix

### Sales Module Connections
```
Sales Recording
├── Deducts Inventory Stock (inventory_ui.py)
├── Creates Sales Record (sales.json)
├── Updates Profit Calculations (profit_ui.py)
├── Triggers Low Stock Alerts (alerts_ui.py)
└── Logs User Activity (audit_ui.py)
```

### Purchase Order Connections
```
Purchase Order Creation
├── Links to Suppliers (suppliers_ui.py)
├── Receives Stock → Updates Inventory (inventory_ui.py)
├── Updates Cost Prices (affects profit margins)
├── Creates Audit Log Entry
└── Can be auto-generated from Low Stock Alerts
```

### Inventory Module Connections
```
Inventory Management
├── Product Categories affect Sales filtering
├── Stock Levels trigger Alerts
├── Barcode/QR Generation (barcode_system.py, qr_generator.py)
├── Multi-location support (locations_ui.py)
└── Stock Transfer between locations (stock_transfer_ui.py)
```

### Alert System Connections
```
Alert Types
├── Low Stock → Suggests Purchase Orders
├── Expiry Tracking (Pharma) → Sales restrictions
├── Warranty Expiry (Electronics) → Customer notifications
└── Critical Stock → Dashboard warnings
```

---

## 🎨 UI Component Standards

### Dialog/Popup Specifications
- **Minimum Size**: 600x400px
- **Recommended Size**: 700x550px for forms
- **Maximum Size**: User resizable with constraints
- **Button Bar**: Always visible, right-aligned, never hidden
- **Content**: Scrollable if exceeds viewport
- **Positioning**: Centered on parent window

### Button Hierarchy
1. **Primary/Accent**: Main actions (Save, Confirm, Create)
2. **Success**: Positive actions (Complete Sale, Receive Order)
3. **Secondary**: Cancel, Back, Close
4. **Danger**: Delete, Remove, Void

### Card Design Pattern
```python
# Standard card structure
card = make_card(parent, padx=30, pady=20)
card.pack(fill="x", pady=(10, 15))

# Header section
title = label(card, "Section Title", kind="heading")
subtitle = label(card, "Description", foreground=COLOR_TEXT_MUTED)

# Content section
# ... form fields, tables, etc.
```

### Table/Treeview Styling
- Row height: 28px minimum
- Alternating row colors (even/odd tags)
- Special tags for status (low_stock, expired, warning)
- Hover effects where supported
- Column headers with clear labels

---

## 📊 Dashboard Integration Points

### Key Performance Indicators (KPIs)
Each KPI card should link to detailed views:

1. **Total Products** → Inventory Module
2. **Total Items in Stock** → Inventory with filters
3. **Low Stock Alerts** → Alerts Module + Quick PO creation
4. **Today's Sales** → Sales Module with today's filter
5. **Monthly Profit** → Profit Reports
6. **Pending Orders** → Purchase Orders Module

### Quick Actions Panel
Direct links to frequently used features:
- Add New Product
- Record Sale
- Create Purchase Order
- View Reports
- Stock Transfer

### Industry-Specific Widgets
Dynamic content based on selected industry:
- Retail: Top-selling products, Loyalty members
- Pharma: Expiring soon, Prescription tracking
- Electronics: Warranty claims, IMEI lookup
- Manufacturing: Production orders, Material consumption
- Healthcare: Equipment status, Patient billing

---

## 🔄 Data Flow Patterns

### Sale Transaction Flow
```
1. User clicks "Record Sale" button
2. PremiumPopup opens with product selection
3. User selects product → Stock info displays
4. User enters quantity → Total calculates
5. Click "Confirm Sale":
   a. Validate stock availability
   b. If low stock → Show warning dialog
   c. Deduct from inventory
   d. Create sales record
   e. Update profit calculations
   f. Check if stock now below threshold → Create alert
   g. Log audit event
   h. Refresh parent table
   i. Show success message
   j. Close dialog
```

### Purchase Order Receipt Flow
```
1. User receives purchase order
2. System validates items against PO
3. For each item:
   a. Update stock quantity (+)
   b. Update average cost if needed
   c. Link batch/expiry if applicable
4. Mark PO as "Received"
5. Clear related low-stock alerts
6. Update inventory valuation
7. Log audit event
```

---

## 🎯 Best Practices Implemented

### 1. No Hidden Buttons
- All dialogs use PremiumPopup with scrollable content
- Button bars always visible at bottom
- Proper minimum sizes enforced
- Responsive layout with packing

### 2. Industry Awareness
- Every module checks `app_state.get_industry_config()`
- Industry-specific fields shown/hidden dynamically
- Feature badges display relevant capabilities
- Color coding matches industry theme

### 3. Data Integrity
- Atomic JSON writes (write_json_atomic)
- Undo stack for critical operations
- Validation before data modification
- Confirmation dialogs for destructive actions

### 4. User Experience
- Real-time updates (stock info, totals)
- Visual feedback (alerts, warnings, success messages)
- Keyboard shortcuts where applicable
- Consistent navigation patterns

### 5. Audit & Compliance
- Every action logged with user, timestamp, details
- Undo capability tracked
- Export capabilities for reporting
- Backup integration

---

## 🚀 Future Enhancement Roadmap

### Phase 1: Complete Module Updates
- [x] Sales UI - Premium dialogs
- [ ] Inventory UI - Enhanced forms
- [ ] Purchase Orders - Auto-suggestions
- [ ] Suppliers - Relationship mapping
- [ ] Reports - Interactive charts

### Phase 2: Advanced Features
- [ ] Real-time dashboard updates
- [ ] Predictive analytics (ML-based)
- [ ] Mobile companion app
- [ ] Cloud sync improvements
- [ ] Multi-user collaboration

### Phase 3: Enterprise Features
- [ ] Role-based access control refinement
- [ ] API for third-party integrations
- [ ] Advanced reporting engine
- [ ] Automated backup scheduling
- [ ] Performance optimization

---

## 📝 Code Style Guidelines

### Import Organization
```python
# 1. Standard library
import tkinter as tk
from tkinter import ttk, messagebox

# 2. Third-party
import logging

# 3. Local imports (with fallback)
try:
    from .ui_theme import ...
except ImportError:
    from ui_theme import ...

# 4. Local modules
from app_core import AppState, PremiumPopup
```

### Function Documentation
```python
def function_name(param1: type, param2: type) -> ReturnType:
    """
    Brief description of function purpose.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception occurs
    """
```

### Error Handling Pattern
```python
try:
    # Operation
except SpecificException as e:
    logging.error("Descriptive message", exc_info=True)
    messagebox.showerror("User-friendly title", "What happened + what to do")
finally:
    # Cleanup if needed
```

---

## 🔐 Security Considerations

1. **Authentication**: Login required for all modules
2. **Authorization**: Role-based permissions (Admin/User)
3. **Audit Trail**: All actions logged with user context
4. **Data Backup**: Automatic backups before bulk operations
5. **Input Validation**: Sanitize all user inputs
6. **Session Management**: Current user tracked in app_state

---

*Last Updated: 2025*
*Version: 2.0 Premium Edition*
