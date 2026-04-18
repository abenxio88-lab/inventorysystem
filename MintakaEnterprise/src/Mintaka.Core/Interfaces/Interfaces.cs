namespace Mintaka.Core.Interfaces;

using Mintaka.Core.Entities;

/// <summary>
/// Repository pattern interface for data access abstraction
/// </summary>
public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(int id);
    Task<IEnumerable<T>> GetAllAsync();
    Task<T> AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(T entity);
    Task<IEnumerable<T>> FindAsync(Func<T, bool> predicate);
}

/// <summary>
/// Product repository interface
/// </summary>
public interface IProductRepository : IRepository<Product>
{
    Task<Product?> GetBySkuAsync(string sku, int tenantId);
    Task<IEnumerable<Product>> GetByCategoryAsync(string category, int tenantId);
    Task<IEnumerable<Product>> SearchAsync(string searchTerm, int tenantId);
    Task<IEnumerable<Product>> GetLowStockAsync(int tenantId);
    Task<IEnumerable<Product>> GetExpiringSoonAsync(int daysUntilExpiry, int tenantId);
    Task<bool> UpdateStockAsync(int productId, decimal quantityChange);
}

/// <summary>
/// User repository interface
/// </summary>
public interface IUserRepository : IRepository<User>
{
    Task<User?> GetByUsernameAsync(string username);
    Task<User?> GetByEmailAsync(string email);
    Task<bool> ValidateCredentialsAsync(string username, string password);
    Task<bool> IsUsernameTakenAsync(string username, int tenantId);
    Task<bool> IsEmailTakenAsync(string email, int tenantId);
    Task<int> GetFailedLoginAttemptsAsync(string username);
    Task LockUserAsync(string username, TimeSpan lockDuration);
    Task ResetFailedLoginAttemptsAsync(string username);
    Task UpdateLastLoginAsync(int userId);
}

/// <summary>
/// Inventory transaction repository
/// </summary>
public interface IInventoryTransactionRepository : IRepository<InventoryTransaction>
{
    Task<IEnumerable<InventoryTransaction>> GetByProductIdAsync(int productId);
    Task<IEnumerable<InventoryTransaction>> GetByUserIdAsync(int userId);
    Task<IEnumerable<InventoryTransaction>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, int tenantId);
    Task<IEnumerable<InventoryTransaction>> GetByTypeAsync(string transactionType, int tenantId);
    Task<decimal> GetTotalStockInAsync(int productId);
    Task<decimal> GetTotalStockOutAsync(int productId);
}

/// <summary>
/// Customer repository
/// </summary>
public interface ICustomerRepository : IRepository<Customer>
{
    Task<Customer?> GetByEmailAsync(string email);
    Task<IEnumerable<Customer>> SearchAsync(string searchTerm, int tenantId);
    Task<IEnumerable<Customer>> GetWithOutstandingBalanceAsync(int tenantId);
}

/// <summary>
/// Supplier repository
/// </summary>
public interface ISupplierRepository : IRepository<Supplier>
{
    Task<IEnumerable<Supplier>> GetByCountryAsync(string country, int tenantId);
    Task<IEnumerable<Supplier>> SearchAsync(string searchTerm, int tenantId);
}

/// <summary>
/// Sales order repository
/// </summary>
public interface ISalesOrderRepository : IRepository<SalesOrder>
{
    Task<SalesOrder?> GetByOrderNumberAsync(string orderNumber);
    Task<IEnumerable<SalesOrder>> GetByCustomerIdAsync(int customerId);
    Task<IEnumerable<SalesOrder>> GetByStatusAsync(string status, int tenantId);
    Task<IEnumerable<SalesOrder>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, int tenantId);
    Task<decimal> GetTotalSalesAsync(DateTime startDate, DateTime endDate, int tenantId);
}

/// <summary>
/// Purchase order repository
/// </summary>
public interface IPurchaseOrderRepository : IRepository<PurchaseOrder>
{
    Task<PurchaseOrder?> GetByPONumberAsync(string poNumber);
    Task<IEnumerable<PurchaseOrder>> GetBySupplierIdAsync(int supplierId);
    Task<IEnumerable<PurchaseOrder>> GetByStatusAsync(string status, int tenantId);
    Task<IEnumerable<PurchaseOrder>> GetPendingDeliveryAsync(int tenantId);
}

/// <summary>
/// Tenant repository
/// </summary>
public interface ITenantRepository : IRepository<Tenant>
{
    Task<Tenant?> GetByIndustryAsync(string industry);
    Task<IEnumerable<Tenant>> GetActiveTenantsAsync();
    Task<bool> IsSubscriptionActiveAsync(int tenantId);
}

/// <summary>
/// Audit log repository
/// </summary>
public interface IAuditLogRepository : IRepository<AuditLog>
{
    Task<IEnumerable<AuditLog>> GetByTableNameAsync(string tableName, int recordId);
    Task<IEnumerable<AuditLog>> GetByUserIdAsync(int userId);
    Task<IEnumerable<AuditLog>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, int tenantId);
    Task<IEnumerable<AuditLog>> GetRecentAsync(int tenantId, int count = 100);
}

/// <summary>
/// Unit of Work pattern for transaction management
/// </summary>
public interface IUnitOfWork : IDisposable
{
    IProductRepository Products { get; }
    IUserRepository Users { get; }
    IInventoryTransactionRepository Transactions { get; }
    ICustomerRepository Customers { get; }
    ISupplierRepository Suppliers { get; }
    ISalesOrderRepository SalesOrders { get; }
    IPurchaseOrderRepository PurchaseOrders { get; }
    ITenantRepository Tenants { get; }
    IAuditLogRepository AuditLogs { get; }
    
    Task<int> SaveChangesAsync();
    Task BeginTransactionAsync();
    Task CommitTransactionAsync();
    Task RollbackTransactionAsync();
}
