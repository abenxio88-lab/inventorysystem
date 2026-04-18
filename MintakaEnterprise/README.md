# Mintaka Enterprise Inventory System

## 🏆 Professional C# WPF Inventory Management Solution

A complete rewrite of the legacy Python/Tkinter system using modern .NET 8, WPF, and Clean Architecture principles.

---

## 📁 Project Structure

```
MintakaEnterprise/
├── src/
│   ├── Mintaka.Core/              # Domain entities & interfaces
│   │   ├── Entities/              # Product, User, Transaction, etc.
│   │   └── Interfaces/            # Repository & service contracts
│   ├── Mintaka.Application/       # Business logic layer
│   │   └── Services/              # ProductService, AuthenticationService
│   ├── Mintaka.Infrastructure/    # Data access & external services
│   │   ├── Data/
│   │   │   ├── ApplicationDbContext.cs
│   │   │   └── Repositories/      # EF Core repository implementations
│   │   └── Security/              # Encryption, hashing
│   └── Mintaka.UI.WPF/            # Presentation layer
│       ├── Views/                 # XAML windows & controls
│       ├── ViewModels/            # MVVM view models
│       └── Converters/            # Value converters
├── tests/
│   └── Mintaka.Tests/             # Unit & integration tests
├── docs/                          # Documentation
├── backup_python_legacy/          # Original Python code (archived)
└── Mintaka.sln                    # Visual Studio solution
```

---

## ✨ Key Features

### 🔐 Security First
- **PBKDF2-SHA256** password hashing with unique salts
- **Account lockout** after 5 failed attempts (30-minute cooldown)
- **Role-based access control** (Admin, Manager, User)
- **Complete audit trail** for all operations
- **Multi-tenancy** support for SaaS deployment

### 📊 Inventory Management
- **Product CRUD** with SKU validation
- **Stock adjustments** with transaction history
- **Low stock alerts** and expiry tracking
- **Bulk import/export** with merge capability
- **Category management** and advanced search

### 🛒 Sales & Purchases
- **Sales orders** with line items
- **Purchase orders** with receiving workflow
- **Customer & supplier** management
- **Credit limits** and outstanding balance tracking

### 📈 Reporting & Analytics
- **Real-time dashboard** with KPIs
- **Transaction history** with filtering
- **Sales reports** by date range
- **Inventory valuation** reports

### 🏢 Multi-Tenancy
- **Tenant isolation** at database level
- **Industry-specific** configurations
- **Subscription management** with expiration tracking
- **Plan types**: Starter, Professional, Enterprise

---

## 🚀 Getting Started

### Prerequisites
- .NET 8 SDK
- SQL Server 2019+ or LocalDB
- Visual Studio 2022 or VS Code

### Installation

1. **Clone the repository**
   ```bash
   cd MintakaEnterprise
   ```

2. **Restore packages**
   ```bash
   dotnet restore
   ```

3. **Configure connection string**
   
   Create `appsettings.json` in the UI project:
   ```json
   {
     "ConnectionStrings": {
       "DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=MintakaInventory;Trusted_Connection=true;"
     }
   }
   ```

4. **Run the application**
   ```bash
   dotnet run --project src/Mintaka.UI.WPF
   ```

### Default Credentials
- **Username:** `admin`
- **Password:** `Admin123!`

---

## 🧪 Running Tests

```bash
dotnet test tests/Mintaka.Tests
```

Test coverage includes:
- Product service operations
- Authentication flows
- Stock adjustments
- Validation rules

---

## 📐 Architecture Highlights

### Clean Architecture
```
UI Layer (WPF) 
    ↓
Application Layer (Services)
    ↓
Domain Layer (Entities & Interfaces)
    ↓
Infrastructure Layer (EF Core, SQL Server)
```

### Design Patterns
- **Repository Pattern** - Data access abstraction
- **Unit of Work** - Transaction management
- **MVVM** - Separation of UI concerns
- **Dependency Injection** - Loose coupling

### Database Schema
- **Products** - Inventory items with full lifecycle
- **Users** - Authentication & authorization
- **Transactions** - Audit trail for stock movements
- **SalesOrders** - Customer order management
- **PurchaseOrders** - Supplier order management
- **Tenants** - Multi-tenant isolation
- **AuditLogs** - Complete operation history

---

## 🔧 Configuration

### Environment Variables
```bash
MINTAKA_DB_HOST=localhost
MINTAKA_DB_NAME=MintakaInventory
MINTAKA_ENCRYPTION_KEY=your-secret-key
```

### App Settings
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=...;Database=...;..."
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "Security": {
    "MaxFailedLoginAttempts": 5,
    "LockoutDurationMinutes": 30
  }
}
```

---

## 📝 API Endpoints (Future REST API)

Planned endpoints for web/mobile integration:

```
POST   /api/auth/login
POST   /api/auth/register
GET    /api/products
POST   /api/products
PUT    /api/products/{id}
DELETE /api/products/{id}
POST   /api/inventory/adjust
GET    /api/reports/sales
GET    /api/reports/inventory
```

---

## 🛠️ Development

### Build Commands
```bash
# Build all projects
dotnet build

# Build release version
dotnet build -c Release

# Publish for deployment
dotnet publish -c Release -r win-x64 --self-contained
```

### Code Style
- Nullable reference types enabled
- Async/await throughout
- XML documentation comments
- xUnit testing framework

---

## 📄 License

Proprietary - All rights reserved to Mintaka Enterprises

---

## 🤝 Support

For issues and feature requests, contact: support@mintaka.com

---

*Built with .NET 8, WPF, Entity Framework Core, and CommunityToolkit.Mvvm*
