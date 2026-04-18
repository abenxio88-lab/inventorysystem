namespace Mintaka.Core.Entities;

/// <summary>
/// Represents a product in the inventory system.
/// Supports multi-tenancy, expiry tracking, and comprehensive audit trails.
/// </summary>
public class Product
{
    public int Id { get; set; }
    
    /// <summary>
    /// Unique product identifier (SKU)
    /// </summary>
    public string SKU { get; set; } = string.Empty;
    
    /// <summary>
    /// Product name
    /// </summary>
    public string Name { get; set; } = string.Empty;
    
    /// <summary>
    /// Detailed description
    /// </summary>
    public string? Description { get; set; }
    
    /// <summary>
    /// Category for grouping products
    /// </summary>
    public string Category { get; set; } = string.Empty;
    
    /// <summary>
    /// Current quantity in stock
    /// </summary>
    public decimal Quantity { get; set; }
    
    /// <summary>
    /// Unit price for selling
    /// </summary>
    public decimal UnitPrice { get; set; }
    
    /// <summary>
    /// Cost price for profit calculation
    /// </summary>
    public decimal CostPrice { get; set; }
    
    /// <summary>
    /// Minimum quantity threshold for alerts
    /// </summary>
    public decimal MinQuantity { get; set; } = 10;
    
    /// <summary>
    /// Maximum quantity capacity
    /// </summary>
    public decimal MaxQuantity { get; set; } = 10000;
    
    /// <summary>
    /// Expiration date (nullable for non-perishable items)
    /// </summary>
    public DateTime? ExpiryDate { get; set; }
    
    /// <summary>
    /// Manufacturing date
    /// </summary>
    public DateTime? ManufactureDate { get; set; }
    
    /// <summary>
    /// Supplier reference
    /// </summary>
    public int? SupplierId { get; set; }
    
    /// <summary>
    /// Location/Bin within warehouse
    /// </summary>
    public string? Location { get; set; }
    
    /// <summary>
    /// Barcode/QR code data
    /// </summary>
    public string? Barcode { get; set; }
    
    /// <summary>
    /// Tenant ID for multi-tenancy
    /// </summary>
    public int TenantId { get; set; }
    
    /// <summary>
    /// Whether the product is active
    /// </summary>
    public bool IsActive { get; set; } = true;
    
    /// <summary>
    /// Track when created
    /// </summary>
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    /// <summary>
    /// Track last update
    /// </summary>
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    
    /// <summary>
    /// User who created this record
    /// </summary>
    public int? CreatedBy { get; set; }
    
    /// <summary>
    /// User who last updated
    /// </summary>
    public int? UpdatedBy { get; set; }
}

/// <summary>
/// Represents a user in the system with role-based access
/// </summary>
public class User
{
    public int Id { get; set; }
    public string Username { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    public byte[] Salt { get; set; } = Array.Empty<byte>();
    public string Role { get; set; } = "User"; // Admin, Manager, User
    public int TenantId { get; set; }
    public bool IsLocked { get; set; } = false;
    public DateTime? LastLoginAt { get; set; }
    public int FailedLoginAttempts { get; set; } = 0;
    public DateTime? LockedUntil { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public bool IsActive { get; set; } = true;
}

/// <summary>
/// Inventory transaction record (stock in/out)
/// </summary>
public class InventoryTransaction
{
    public int Id { get; set; }
    public int ProductId { get; set; }
    public string TransactionType { get; set; } = string.Empty; // In, Out, Adjustment, Transfer
    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal TotalValue => Quantity * UnitPrice;
    public string? Notes { get; set; }
    public string? ReferenceNumber { get; set; } // PO#, SO#, etc.
    public int UserId { get; set; }
    public int TenantId { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    
    // Navigation properties
    public Product? Product { get; set; }
    public User? User { get; set; }
}

/// <summary>
/// Customer entity
/// </summary>
public class Customer
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? Country { get; set; }
    public string? TaxNumber { get; set; }
    public decimal CreditLimit { get; set; }
    public decimal OutstandingBalance { get; set; }
    public int TenantId { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Supplier entity
/// </summary>
public class Supplier
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string ContactPerson { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? Country { get; set; }
    public string? TaxNumber { get; set; }
    public decimal LeadTimeDays { get; set; }
    public int TenantId { get; set; }
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Sales order entity
/// </summary>
public class SalesOrder
{
    public int Id { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public int CustomerId { get; set; }
    public DateTime OrderDate { get; set; } = DateTime.UtcNow;
    public DateTime? ShipDate { get; set; }
    public string Status { get; set; } = "Pending"; // Pending, Processing, Shipped, Completed, Cancelled
    public decimal SubTotal { get; set; }
    public decimal TaxAmount { get; set; }
    public decimal DiscountAmount { get; set; }
    public decimal TotalAmount => SubTotal + TaxAmount - DiscountAmount;
    public string? Notes { get; set; }
    public int TenantId { get; set; }
    public int CreatedBy { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation
    public Customer? Customer { get; set; }
    public ICollection<SalesOrderItem> Items { get; set; } = new List<SalesOrderItem>();
}

/// <summary>
/// Sales order line item
/// </summary>
public class SalesOrderItem
{
    public int Id { get; set; }
    public int SalesOrderId { get; set; }
    public int ProductId { get; set; }
    public decimal Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal Discount { get; set; }
    public decimal Total => (Quantity * UnitPrice) - Discount;
    
    // Navigation
    public SalesOrder? Order { get; set; }
    public Product? Product { get; set; }
}

/// <summary>
/// Purchase order entity
/// </summary>
public class PurchaseOrder
{
    public int Id { get; set; }
    public string PONumber { get; set; } = string.Empty;
    public int SupplierId { get; set; }
    public DateTime OrderDate { get; set; } = DateTime.UtcNow;
    public DateTime? ExpectedDeliveryDate { get; set; }
    public DateTime? ReceivedDate { get; set; }
    public string Status { get; set; } = "Pending"; // Pending, Ordered, PartiallyReceived, Completed, Cancelled
    public decimal SubTotal { get; set; }
    public decimal TaxAmount { get; set; }
    public decimal TotalAmount => SubTotal + TaxAmount;
    public string? Notes { get; set; }
    public int TenantId { get; set; }
    public int CreatedBy { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    // Navigation
    public Supplier? Supplier { get; set; }
    public ICollection<PurchaseOrderItem> Items { get; set; } = new List<PurchaseOrderItem>();
}

/// <summary>
/// Purchase order line item
/// </summary>
public class PurchaseOrderItem
{
    public int Id { get; set; }
    public int PurchaseOrderId { get; set; }
    public int ProductId { get; set; }
    public decimal Quantity { get; set; }
    public decimal UnitCost { get; set; }
    public decimal Total => Quantity * UnitCost;
    public decimal QuantityReceived { get; set; } = 0;
    
    // Navigation
    public PurchaseOrder? Order { get; set; }
    public Product? Product { get; set; }
}

/// <summary>
/// Tenant for multi-tenancy support
/// </summary>
public class Tenant
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Industry { get; set; } = "General"; // Retail, Manufacturing, Food, Pharma, etc.
    public string? LogoPath { get; set; }
    public string Currency { get; set; } = "USD";
    public string TimeZone { get; set; } = "UTC";
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? SubscriptionExpiresAt { get; set; }
    public string PlanType { get; set; } = "Starter"; // Starter, Professional, Enterprise
}

/// <summary>
/// Audit log for compliance and tracking
/// </summary>
public class AuditLog
{
    public int Id { get; set; }
    public string TableName { get; set; } = string.Empty;
    public int RecordId { get; set; }
    public string Action { get; set; } = string.Empty; // Create, Update, Delete
    public string OldValues { get; set; } = string.Empty; // JSON
    public string NewValues { get; set; } = string.Empty; // JSON
    public int UserId { get; set; }
    public int TenantId { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public string? IpAddress { get; set; }
}
