namespace Mintaka.Infrastructure.Data;

using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using Mintaka.Core.Entities;
using Mintaka.Core.Interfaces;

/// <summary>
/// Entity Framework Core database context
/// </summary>
public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options)
    {
    }

    // DbSet properties for each entity (internal to avoid conflicts with repository pattern)
    internal DbSet<Product> ProductDbSet => Set<Product>();
    internal DbSet<User> UserDbSet => Set<User>();
    internal DbSet<InventoryTransaction> TransactionDbSet => Set<InventoryTransaction>();
    internal DbSet<Customer> CustomerDbSet => Set<Customer>();
    internal DbSet<Supplier> SupplierDbSet => Set<Supplier>();
    internal DbSet<SalesOrder> SalesOrderDbSet => Set<SalesOrder>();
    internal DbSet<SalesOrderItem> SalesOrderItemDbSet => Set<SalesOrderItem>();
    internal DbSet<PurchaseOrder> PurchaseOrderDbSet => Set<PurchaseOrder>();
    internal DbSet<PurchaseOrderItem> PurchaseOrderItemDbSet => Set<PurchaseOrderItem>();
    internal DbSet<Tenant> TenantDbSet => Set<Tenant>();
    internal DbSet<AuditLog> AuditLogDbSet => Set<AuditLog>();

    // Repository implementations (commented - not yet implemented)
    // private IProductRepository? _products;
    // private IUserRepository? _users;
    // private IInventoryTransactionRepository? _transactions;
    // private ICustomerRepository? _customers;
    // private ISupplierRepository? _suppliers;
    // private ISalesOrderRepository? _salesOrders;
    // private IPurchaseOrderRepository? _purchaseOrders;
    // private ITenantRepository? _tenants;
    // private IAuditLogRepository? _auditLogs;
    //
    // public IProductRepository Products => _products ??= new ProductRepository(this);
    // public IUserRepository Users => _users ??= new UserRepository(this);
    // public IInventoryTransactionRepository Transactions => _transactions ??= new InventoryTransactionRepository(this);
    // public ICustomerRepository Customers => _customers ??= new CustomerRepository(this);
    // public ISupplierRepository Suppliers => _suppliers ??= new SupplierRepository(this);
    // public ISalesOrderRepository SalesOrders => _salesOrders ??= new SalesOrderRepository(this);
    // public IPurchaseOrderRepository PurchaseOrders => _purchaseOrders ??= new PurchaseOrderRepository(this);
    // public ITenantRepository Tenants => _tenants ??= new TenantRepository(this);
    // public IAuditLogRepository AuditLogs => _auditLogs ??= new AuditLogRepository(this);

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Apply all configurations
        ConfigureProduct(modelBuilder);
        ConfigureUser(modelBuilder);
        ConfigureTenant(modelBuilder);
        ConfigureIndexes(modelBuilder);

        // Seed default tenant
        modelBuilder.Entity<Tenant>().HasData(
            new Tenant 
            { 
                Id = 1, 
                Name = "Default Organization", 
                Industry = "General",
                Currency = "USD",
                TimeZone = "UTC",
                IsActive = true,
                CreatedAt = DateTime.UtcNow,
                PlanType = "Starter"
            }
        );

        // Seed admin user (password: Admin123!)
        var salt = GenerateSalt();
        var passwordHash = HashPassword("Admin123!", salt);
        
        modelBuilder.Entity<User>().HasData(
            new User
            {
                Id = 1,
                Username = "admin",
                Email = "admin@mintaka.com",
                PasswordHash = passwordHash,
                Salt = salt,
                Role = "Admin",
                TenantId = 1,
                IsActive = true,
                CreatedAt = DateTime.UtcNow
            }
        );
    }

    #region Model Configuration

    private void ConfigureProduct(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => e.SKU).IsUnique();
            entity.HasIndex(e => e.TenantId);
            entity.HasIndex(e => e.Category);
            entity.HasIndex(e => e.SupplierId);
            
            entity.Property(e => e.SKU).HasMaxLength(50).IsRequired();
            entity.Property(e => e.Name).HasMaxLength(200).IsRequired();
            entity.Property(e => e.Description).HasMaxLength(2000);
            entity.Property(e => e.Category).HasMaxLength(100);
            entity.Property(e => e.Location).HasMaxLength(100);
            entity.Property(e => e.Barcode).HasMaxLength(100);
            entity.Property(e => e.UnitPrice).HasColumnType("decimal(18,4)");
            entity.Property(e => e.CostPrice).HasColumnType("decimal(18,4)");
            entity.Property(e => e.Quantity).HasColumnType("decimal(18,4)");
        });
    }

    private void ConfigureUser(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id);
            
            entity.HasIndex(e => e.Username).IsUnique();
            entity.HasIndex(e => e.Email).IsUnique();
            entity.HasIndex(e => e.TenantId);
            
            entity.Property(e => e.Username).HasMaxLength(50).IsRequired();
            entity.Property(e => e.Email).HasMaxLength(100).IsRequired();
            entity.Property(e => e.Role).HasMaxLength(20);
        });
    }

    private void ConfigureTenant(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Tenant>(entity =>
        {
            entity.HasKey(e => e.Id);
            
            entity.Property(e => e.Name).HasMaxLength(200).IsRequired();
            entity.Property(e => e.Industry).HasMaxLength(50);
            entity.Property(e => e.Currency).HasMaxLength(3);
            entity.Property(e => e.PlanType).HasMaxLength(20);
        });
    }

    private void ConfigureIndexes(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<InventoryTransaction>(entity =>
        {
            entity.HasIndex(e => e.ProductId);
            entity.HasIndex(e => e.UserId);
            entity.HasIndex(e => e.Timestamp);
            entity.HasIndex(e => e.TransactionType);
        });

        modelBuilder.Entity<SalesOrder>(entity =>
        {
            entity.HasIndex(e => e.OrderNumber).IsUnique();
            entity.HasIndex(e => e.CustomerId);
            entity.HasIndex(e => e.Status);
            entity.HasIndex(e => e.OrderDate);
        });

        modelBuilder.Entity<PurchaseOrder>(entity =>
        {
            entity.HasIndex(e => e.PONumber).IsUnique();
            entity.HasIndex(e => e.SupplierId);
            entity.HasIndex(e => e.Status);
        });

        modelBuilder.Entity<AuditLog>(entity =>
        {
            entity.HasIndex(e => e.TableName);
            entity.HasIndex(e => e.RecordId);
            entity.HasIndex(e => e.UserId);
            entity.HasIndex(e => e.Timestamp);
        });
    }

    #endregion

    #region Transaction Management

    private IDbContextTransaction? _currentTransaction;

    public async Task BeginTransactionAsync()
    {
        if (_currentTransaction != null) return;
        _currentTransaction = await Database.BeginTransactionAsync();
    }

    public async Task CommitTransactionAsync()
    {
        try
        {
            await SaveChangesAsync();
            if (_currentTransaction != null)
                await _currentTransaction.CommitAsync();
        }
        catch
        {
            await RollbackTransactionAsync();
            throw;
        }
        finally
        {
            _currentTransaction?.Dispose();
            _currentTransaction = null;
        }
    }

    public async Task RollbackTransactionAsync()
    {
        try
        {
            if (_currentTransaction != null)
                await _currentTransaction.RollbackAsync();
        }
        finally
        {
            _currentTransaction?.Dispose();
            _currentTransaction = null;
        }
    }

    public override void Dispose()
    {
        _currentTransaction?.Dispose();
        base.Dispose();
    }

    public override async Task<int> SaveChangesAsync(CancellationToken cancellationToken = default)
    {
        return await base.SaveChangesAsync(cancellationToken);
    }

    #endregion

    #region Helper Methods

    private static byte[] GenerateSalt()
    {
        var salt = new byte[32];
        using var rng = System.Security.Cryptography.RandomNumberGenerator.Create();
        rng.GetBytes(salt);
        return salt;
    }

    private static string HashPassword(string password, byte[] salt)
    {
        using var pbkdf2 = new System.Security.Cryptography.Rfc2898DeriveBytes(password, salt, 100000, System.Security.Cryptography.HashAlgorithmName.SHA256);
        var hash = pbkdf2.GetBytes(32);
        return Convert.ToBase64String(hash);
    }

    #endregion
}
