namespace Mintaka.Infrastructure.Data.Repositories;

using Microsoft.EntityFrameworkCore;
using Mintaka.Core.Entities;
using Mintaka.Core.Interfaces;

/// <summary>
/// Generic repository implementation
/// </summary>
public class Repository<T> : IRepository<T> where T : class
{
    protected readonly ApplicationDbContext _context;
    protected readonly DbSet<T> _dbSet;

    public Repository(ApplicationDbContext context)
    {
        _context = context;
        _dbSet = context.Set<T>();
    }

    public virtual async Task<T?> GetByIdAsync(int id)
    {
        return await _dbSet.FindAsync(id);
    }

    public virtual async Task<IEnumerable<T>> GetAllAsync()
    {
        return await _dbSet.ToListAsync();
    }

    public virtual async Task<T> AddAsync(T entity)
    {
        await _dbSet.AddAsync(entity);
        return entity;
    }

    public virtual Task UpdateAsync(T entity)
    {
        _dbSet.Update(entity);
        return Task.CompletedTask;
    }

    public virtual Task DeleteAsync(T entity)
    {
        _dbSet.Remove(entity);
        return Task.CompletedTask;
    }

    public virtual async Task<IEnumerable<T>> FindAsync(Func<T, bool> predicate)
    {
        return await Task.FromResult(_dbSet.Where(predicate).ToList());
    }
}

/// <summary>
/// Product repository implementation
/// </summary>
public class ProductRepository : Repository<Product>, IProductRepository
{
    public ProductRepository(ApplicationDbContext context) : base(context) { }

    public async Task<Product?> GetBySkuAsync(string sku, int tenantId)
    {
        return await _dbSet.FirstOrDefaultAsync(p => p.SKU == sku && p.TenantId == tenantId);
    }

    public async Task<IEnumerable<Product>> GetByCategoryAsync(string category, int tenantId)
    {
        return await _dbSet.Where(p => p.Category == category && p.TenantId == tenantId && p.IsActive).ToListAsync();
    }

    public async Task<IEnumerable<Product>> SearchAsync(string searchTerm, int tenantId)
    {
        var term = searchTerm.ToLower();
        return await _dbSet.Where(p => 
            p.TenantId == tenantId && 
            p.IsActive &&
            (p.Name.ToLower().Contains(term) || 
             p.SKU.ToLower().Contains(term) || 
             (p.Description != null && p.Description.ToLower().Contains(term)))).ToListAsync();
    }

    public async Task<IEnumerable<Product>> GetLowStockAsync(int tenantId)
    {
        return await _dbSet.Where(p => 
            p.TenantId == tenantId && 
            p.IsActive && 
            p.Quantity <= p.MinQuantity).ToListAsync();
    }

    public async Task<IEnumerable<Product>> GetExpiringSoonAsync(int daysUntilExpiry, int tenantId)
    {
        var expiryDate = DateTime.UtcNow.AddDays(daysUntilExpiry);
        return await _dbSet.Where(p => 
            p.TenantId == tenantId && 
            p.IsActive && 
            p.ExpiryDate.HasValue && 
            p.ExpiryDate.Value <= expiryDate).ToListAsync();
    }

    public async Task<bool> UpdateStockAsync(int productId, decimal quantityChange)
    {
        var product = await _dbSet.FindAsync(productId);
        if (product == null) return false;

        product.Quantity += quantityChange;
        product.UpdatedAt = DateTime.UtcNow;
        return true;
    }
}

/// <summary>
/// User repository implementation
/// </summary>
public class UserRepository : Repository<User>, IUserRepository
{
    public UserRepository(ApplicationDbContext context) : base(context) { }

    public async Task<User?> GetByUsernameAsync(string username)
    {
        return await _dbSet.FirstOrDefaultAsync(u => u.Username == username);
    }

    public async Task<User?> GetByEmailAsync(string email)
    {
        return await _dbSet.FirstOrDefaultAsync(u => u.Email == email);
    }

    public async Task<bool> ValidateCredentialsAsync(string username, string password)
    {
        var user = await GetByUsernameAsync(username);
        if (user == null) return false;

        using var pbkdf2 = new System.Security.Cryptography.Rfc2898DeriveBytes(password, user.Salt, 100000, System.Security.Cryptography.HashAlgorithmName.SHA256);
        var computedHash = Convert.ToBase64String(pbkdf2.GetBytes(32));
        
        return computedHash == user.PasswordHash;
    }

    public async Task<bool> IsUsernameTakenAsync(string username, int tenantId)
    {
        return await _dbSet.AnyAsync(u => u.Username == username && u.TenantId == tenantId);
    }

    public async Task<bool> IsEmailTakenAsync(string email, int tenantId)
    {
        return await _dbSet.AnyAsync(u => u.Email == email && u.TenantId == tenantId);
    }

    public async Task<int> GetFailedLoginAttemptsAsync(string username)
    {
        var user = await GetByUsernameAsync(username);
        return user?.FailedLoginAttempts ?? 0;
    }

    public async Task LockUserAsync(string username, TimeSpan lockDuration)
    {
        var user = await GetByUsernameAsync(username);
        if (user != null)
        {
            user.IsLocked = true;
            user.LockedUntil = DateTime.UtcNow + lockDuration;
            user.FailedLoginAttempts++;
        }
    }

    public async Task ResetFailedLoginAttemptsAsync(string username)
    {
        var user = await GetByUsernameAsync(username);
        if (user != null)
        {
            user.FailedLoginAttempts = 0;
            user.IsLocked = false;
            user.LockedUntil = null;
        }
    }

    public async Task UpdateLastLoginAsync(int userId)
    {
        var user = await _dbSet.FindAsync(userId);
        if (user != null)
        {
            user.LastLoginAt = DateTime.UtcNow;
            user.FailedLoginAttempts = 0;
            user.IsLocked = false;
            user.LockedUntil = null;
        }
    }
}

/// <summary>
/// Inventory transaction repository implementation
/// </summary>
public class InventoryTransactionRepository : Repository<InventoryTransaction>, IInventoryTransactionRepository
{
    public InventoryTransactionRepository(ApplicationDbContext context) : base(context) { }

    public async Task<IEnumerable<InventoryTransaction>> GetByProductIdAsync(int productId)
    {
        return await _dbSet.Where(t => t.ProductId == productId).OrderByDescending(t => t.Timestamp).ToListAsync();
    }

    public async Task<IEnumerable<InventoryTransaction>> GetByUserIdAsync(int userId)
    {
        return await _dbSet.Where(t => t.UserId == userId).OrderByDescending(t => t.Timestamp).ToListAsync();
    }

    public async Task<IEnumerable<InventoryTransaction>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, int tenantId)
    {
        return await _dbSet.Where(t => 
            t.TenantId == tenantId && 
            t.Timestamp >= startDate && 
            t.Timestamp <= endDate).OrderByDescending(t => t.Timestamp).ToListAsync();
    }

    public async Task<IEnumerable<InventoryTransaction>> GetByTypeAsync(string transactionType, int tenantId)
    {
        return await _dbSet.Where(t => 
            t.TenantId == tenantId && 
            t.TransactionType == transactionType).OrderByDescending(t => t.Timestamp).ToListAsync();
    }

    public async Task<decimal> GetTotalStockInAsync(int productId)
    {
        return await _dbSet.Where(t => t.ProductId == productId && (t.TransactionType == "In" || t.TransactionType == "Adjustment In"))
            .SumAsync(t => t.Quantity);
    }

    public async Task<decimal> GetTotalStockOutAsync(int productId)
    {
        return await _dbSet.Where(t => t.ProductId == productId && (t.TransactionType == "Out" || t.TransactionType == "Adjustment Out"))
            .SumAsync(t => t.Quantity);
    }
}

/// <summary>
/// Customer repository implementation
/// </summary>
public class CustomerRepository : Repository<Customer>, ICustomerRepository
{
    public CustomerRepository(ApplicationDbContext context) : base(context) { }

    public async Task<Customer?> GetByEmailAsync(string email)
    {
        return await _dbSet.FirstOrDefaultAsync(c => c.Email == email);
    }

    public async Task<IEnumerable<Customer>> SearchAsync(string searchTerm, int tenantId)
    {
        var term = searchTerm.ToLower();
        return await _dbSet.Where(c => 
            c.TenantId == tenantId && 
            c.IsActive &&
            (c.Name.ToLower().Contains(term) || 
             c.Email.ToLower().Contains(term) || 
             c.Phone.Contains(term))).ToListAsync();
    }

    public async Task<IEnumerable<Customer>> GetWithOutstandingBalanceAsync(int tenantId)
    {
        return await _dbSet.Where(c => 
            c.TenantId == tenantId && 
            c.IsActive && 
            c.OutstandingBalance > 0).ToListAsync();
    }
}

/// <summary>
/// Supplier repository implementation
/// </summary>
public class SupplierRepository : Repository<Supplier>, ISupplierRepository
{
    public SupplierRepository(ApplicationDbContext context) : base(context) { }

    public async Task<IEnumerable<Supplier>> GetByCountryAsync(string country, int tenantId)
    {
        return await _dbSet.Where(s => s.Country == country && s.TenantId == tenantId && s.IsActive).ToListAsync();
    }

    public async Task<IEnumerable<Supplier>> SearchAsync(string searchTerm, int tenantId)
    {
        var term = searchTerm.ToLower();
        return await _dbSet.Where(s => 
            s.TenantId == tenantId && 
            s.IsActive &&
            (s.Name.ToLower().Contains(term) || 
             s.ContactPerson.ToLower().Contains(term) || 
             s.Email.ToLower().Contains(term))).ToListAsync();
    }
}

/// <summary>
/// Sales order repository implementation
/// </summary>
public class SalesOrderRepository : Repository<SalesOrder>, ISalesOrderRepository
{
    public SalesOrderRepository(ApplicationDbContext context) : base(context) { }

    public async Task<SalesOrder?> GetByOrderNumberAsync(string orderNumber)
    {
        return await _dbSet.Include(o => o.Items).ThenInclude(i => i.Product)
            .FirstOrDefaultAsync(o => o.OrderNumber == orderNumber);
    }

    public async Task<IEnumerable<SalesOrder>> GetByCustomerIdAsync(int customerId)
    {
        return await _dbSet.Where(o => o.CustomerId == customerId).OrderByDescending(o => o.OrderDate).ToListAsync();
    }

    public async Task<IEnumerable<SalesOrder>> GetByStatusAsync(string status, int tenantId)
    {
        return await _dbSet.Where(o => o.Status == status && o.TenantId == tenantId).OrderByDescending(o => o.OrderDate).ToListAsync();
    }

    public async Task<IEnumerable<SalesOrder>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, int tenantId)
    {
        return await _dbSet.Where(o => 
            o.TenantId == tenantId && 
            o.OrderDate >= startDate && 
            o.OrderDate <= endDate).OrderByDescending(o => o.OrderDate).ToListAsync();
    }

    public async Task<decimal> GetTotalSalesAsync(DateTime startDate, DateTime endDate, int tenantId)
    {
        return await _dbSet.Where(o => 
            o.TenantId == tenantId && 
            o.OrderDate >= startDate && 
            o.OrderDate <= endDate &&
            o.Status != "Cancelled")
            .SumAsync(o => o.TotalAmount);
    }
}

/// <summary>
/// Purchase order repository implementation
/// </summary>
public class PurchaseOrderRepository : Repository<PurchaseOrder>, IPurchaseOrderRepository
{
    public PurchaseOrderRepository(ApplicationDbContext context) : base(context) { }

    public async Task<PurchaseOrder?> GetByPONumberAsync(string poNumber)
    {
        return await _dbSet.Include(o => o.Items).ThenInclude(i => i.Product)
            .FirstOrDefaultAsync(o => o.PONumber == poNumber);
    }

    public async Task<IEnumerable<PurchaseOrder>> GetBySupplierIdAsync(int supplierId)
    {
        return await _dbSet.Where(o => o.SupplierId == supplierId).OrderByDescending(o => o.OrderDate).ToListAsync();
    }

    public async Task<IEnumerable<PurchaseOrder>> GetByStatusAsync(string status, int tenantId)
    {
        return await _dbSet.Where(o => o.Status == status && o.TenantId == tenantId).OrderByDescending(o => o.OrderDate).ToListAsync();
    }

    public async Task<IEnumerable<PurchaseOrder>> GetPendingDeliveryAsync(int tenantId)
    {
        return await _dbSet.Where(o => 
            o.TenantId == tenantId && 
            (o.Status == "Ordered" || o.Status == "PartiallyReceived")).OrderBy(o => o.ExpectedDeliveryDate).ToListAsync();
    }
}

/// <summary>
/// Tenant repository implementation
/// </summary>
public class TenantRepository : Repository<Tenant>, ITenantRepository
{
    public TenantRepository(ApplicationDbContext context) : base(context) { }

    public async Task<Tenant?> GetByIndustryAsync(string industry)
    {
        return await _dbSet.FirstOrDefaultAsync(t => t.Industry == industry && t.IsActive);
    }

    public async Task<IEnumerable<Tenant>> GetActiveTenantsAsync()
    {
        return await _dbSet.Where(t => t.IsActive).ToListAsync();
    }

    public async Task<bool> IsSubscriptionActiveAsync(int tenantId)
    {
        var tenant = await _dbSet.FindAsync(tenantId);
        return tenant != null && 
               tenant.IsActive && 
               (!tenant.SubscriptionExpiresAt.HasValue || tenant.SubscriptionExpiresAt.Value > DateTime.UtcNow);
    }
}

/// <summary>
/// Audit log repository implementation
/// </summary>
public class AuditLogRepository : Repository<AuditLog>, IAuditLogRepository
{
    public AuditLogRepository(ApplicationDbContext context) : base(context) { }

    public async Task<IEnumerable<AuditLog>> GetByTableNameAsync(string tableName, int recordId)
    {
        return await _dbSet.Where(a => a.TableName == tableName && a.RecordId == recordId)
            .OrderByDescending(a => a.Timestamp).ToListAsync();
    }

    public async Task<IEnumerable<AuditLog>> GetByUserIdAsync(int userId)
    {
        return await _dbSet.Where(a => a.UserId == userId).OrderByDescending(a => a.Timestamp).ToListAsync();
    }

    public async Task<IEnumerable<AuditLog>> GetByDateRangeAsync(DateTime startDate, DateTime endDate, int tenantId)
    {
        return await _dbSet.Where(a => 
            a.TenantId == tenantId && 
            a.Timestamp >= startDate && 
            a.Timestamp <= endDate).OrderByDescending(a => a.Timestamp).ToListAsync();
    }

    public async Task<IEnumerable<AuditLog>> GetRecentAsync(int tenantId, int count = 100)
    {
        return await _dbSet.Where(a => a.TenantId == tenantId)
            .OrderByDescending(a => a.Timestamp)
            .Take(count).ToListAsync();
    }
}
