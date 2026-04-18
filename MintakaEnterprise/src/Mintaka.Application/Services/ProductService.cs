namespace Mintaka.Application.Services;

using Mintaka.Core.Entities;
using Mintaka.Core.Interfaces;
using Microsoft.Extensions.Logging;

/// <summary>
/// Main product service implementing business logic for inventory management
/// </summary>
public class ProductService : IProductService
{
    private readonly IUnitOfWork _unitOfWork;
    private readonly ILogger<ProductService> _logger;

    public ProductService(IUnitOfWork unitOfWork, ILogger<ProductService> logger)
    {
        _unitOfWork = unitOfWork;
        _logger = logger;
    }

    /// <summary>
    /// Get all products for a tenant with optional filtering
    /// </summary>
    public async Task<IEnumerable<Product>> GetProductsAsync(int tenantId, string? category = null, bool activeOnly = true)
    {
        try
        {
            var products = await _unitOfWork.Products.GetAllAsync();
            var filtered = products.Where(p => p.TenantId == tenantId);
            
            if (activeOnly)
                filtered = filtered.Where(p => p.IsActive);
            
            if (!string.IsNullOrEmpty(category))
                filtered = filtered.Where(p => p.Category.Equals(category, StringComparison.OrdinalIgnoreCase));

            return filtered.OrderBy(p => p.Name).ToList();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving products for tenant {TenantId}", tenantId);
            throw;
        }
    }

    /// <summary>
    /// Get a single product by ID
    /// </summary>
    public async Task<Product?> GetProductByIdAsync(int id, int tenantId)
    {
        var product = await _unitOfWork.Products.GetByIdAsync(id);
        
        if (product == null || product.TenantId != tenantId || !product.IsActive)
            return null;

        return product;
    }

    /// <summary>
    /// Get product by SKU
    /// </summary>
    public async Task<Product?> GetProductBySkuAsync(string sku, int tenantId)
    {
        return await _unitOfWork.Products.GetBySkuAsync(sku, tenantId);
    }

    /// <summary>
    /// Create a new product with validation
    /// </summary>
    public async Task<Product> CreateProductAsync(Product product, int userId)
    {
        try
        {
            // Validate SKU uniqueness
            var existing = await _unitOfWork.Products.GetBySkuAsync(product.SKU, product.TenantId);
            if (existing != null)
                throw new InvalidOperationException($"Product with SKU '{product.SKU}' already exists.");

            // Set audit fields
            product.CreatedAt = DateTime.UtcNow;
            product.UpdatedAt = DateTime.UtcNow;
            product.CreatedBy = userId;
            product.IsActive = true;

            var created = await _unitOfWork.Products.AddAsync(product);
            await _unitOfWork.SaveChangesAsync();

            // Log creation
            await CreateAuditLogAsync(created.Id, "Products", "Create", userId, product.TenantId, null, product);

            _logger.LogInformation("Product created: {ProductId} - {ProductName}", created.Id, created.Name);
            return created;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating product");
            throw;
        }
    }

    /// <summary>
    /// Update an existing product
    /// </summary>
    public async Task<Product> UpdateProductAsync(Product product, int userId)
    {
        try
        {
            var existing = await _unitOfWork.Products.GetByIdAsync(product.Id);
            if (existing == null)
                throw new InvalidOperationException($"Product with ID {product.Id} not found.");

            // Check SKU uniqueness if changed
            if (existing.SKU != product.SKU)
            {
                var skuExists = await _unitOfWork.Products.GetBySkuAsync(product.SKU, product.TenantId);
                if (skuExists != null && skuExists.Id != product.Id)
                    throw new InvalidOperationException($"Product with SKU '{product.SKU}' already exists.");
            }

            // Preserve certain fields
            product.CreatedAt = existing.CreatedAt;
            product.CreatedBy = existing.CreatedBy;
            product.UpdatedAt = DateTime.UtcNow;
            product.UpdatedBy = userId;

            await _unitOfWork.Products.UpdateAsync(product);
            await _unitOfWork.SaveChangesAsync();

            // Log update
            await CreateAuditLogAsync(product.Id, "Products", "Update", userId, product.TenantId, existing, product);

            _logger.LogInformation("Product updated: {ProductId} - {ProductName}", product.Id, product.Name);
            return product;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating product {ProductId}", product.Id);
            throw;
        }
    }

    /// <summary>
    /// Soft delete a product
    /// </summary>
    public async Task<bool> DeleteProductAsync(int id, int userId, int tenantId)
    {
        try
        {
            var product = await _unitOfWork.Products.GetByIdAsync(id);
            if (product == null || product.TenantId != tenantId)
                return false;

            // Soft delete
            product.IsActive = false;
            product.UpdatedAt = DateTime.UtcNow;
            product.UpdatedBy = userId;

            await _unitOfWork.Products.UpdateAsync(product);
            await _unitOfWork.SaveChangesAsync();

            await CreateAuditLogAsync(id, "Products", "Delete", userId, tenantId, product, null);

            _logger.LogInformation("Product deleted: {ProductId}", id);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting product {ProductId}", id);
            throw;
        }
    }

    /// <summary>
    /// Search products by name, SKU, or description
    /// </summary>
    public async Task<IEnumerable<Product>> SearchProductsAsync(string searchTerm, int tenantId)
    {
        if (string.IsNullOrWhiteSpace(searchTerm))
            return await GetProductsAsync(tenantId);

        var products = await _unitOfWork.Products.SearchAsync(searchTerm, tenantId);
        return products.Where(p => p.IsActive).ToList();
    }

    /// <summary>
    /// Get products with low stock
    /// </summary>
    public async Task<IEnumerable<Product>> GetLowStockProductsAsync(int tenantId)
    {
        var products = await _unitOfWork.Products.GetLowStockAsync(tenantId);
        return products.Where(p => p.IsActive && p.Quantity <= p.MinQuantity).ToList();
    }

    /// <summary>
    /// Get products expiring soon
    /// </summary>
    public async Task<IEnumerable<Product>> GetExpiringProductsAsync(int tenantId, int daysUntilExpiry = 30)
    {
        var expiryDate = DateTime.UtcNow.AddDays(daysUntilExpiry);
        var products = await _unitOfWork.Products.GetExpiringSoonAsync(daysUntilExpiry, tenantId);
        return products.Where(p => p.IsActive && p.ExpiryDate.HasValue && p.ExpiryDate.Value <= expiryDate).ToList();
    }

    /// <summary>
    /// Adjust stock quantity (add or remove)
    /// </summary>
    public async Task<bool> AdjustStockAsync(int productId, decimal quantityChange, string reason, int userId, int tenantId)
    {
        try
        {
            var product = await _unitOfWork.Products.GetByIdAsync(productId);
            if (product == null || product.TenantId != tenantId)
                return false;

            var newQuantity = product.Quantity + quantityChange;
            if (newQuantity < 0)
                throw new InvalidOperationException("Cannot reduce stock below zero.");

            if (newQuantity > product.MaxQuantity)
                throw new InvalidOperationException($"Cannot exceed maximum quantity of {product.MaxQuantity}.");

            // Update product stock
            product.Quantity = newQuantity;
            product.UpdatedAt = DateTime.UtcNow;
            product.UpdatedBy = userId;

            await _unitOfWork.Products.UpdateAsync(product);

            // Create transaction record
            var transaction = new InventoryTransaction
            {
                ProductId = productId,
                TransactionType = quantityChange >= 0 ? "Adjustment In" : "Adjustment Out",
                Quantity = Math.Abs(quantityChange),
                UnitPrice = product.UnitPrice,
                Notes = reason,
                UserId = userId,
                TenantId = tenantId,
                Timestamp = DateTime.UtcNow
            };

            await _unitOfWork.Transactions.AddAsync(transaction);
            await _unitOfWork.SaveChangesAsync();

            await CreateAuditLogAsync(productId, "Products", "StockAdjustment", userId, tenantId, 
                new { OldQuantity = product.Quantity - quantityChange }, 
                new { NewQuantity = newQuantity, Reason = reason });

            _logger.LogInformation("Stock adjusted for product {ProductId}: {Change} ({Reason})", 
                productId, quantityChange, reason);

            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adjusting stock for product {ProductId}", productId);
            throw;
        }
    }

    /// <summary>
    /// Get product categories for a tenant
    /// </summary>
    public async Task<IEnumerable<string>> GetCategoriesAsync(int tenantId)
    {
        var products = await GetProductsAsync(tenantId);
        return products.Select(p => p.Category).Distinct().OrderBy(c => c).ToList();
    }

    /// <summary>
    /// Bulk import products
    /// </summary>
    public async Task<int> BulkImportAsync(IEnumerable<Product> products, int tenantId, int userId, bool mergeExisting = false)
    {
        var importedCount = 0;
        var errors = new List<string>();

        await _unitOfWork.BeginTransactionAsync();
        try
        {
            foreach (var product in products)
            {
                try
                {
                    product.TenantId = tenantId;
                    
                    if (mergeExisting && !string.IsNullOrEmpty(product.SKU))
                    {
                        var existing = await _unitOfWork.Products.GetBySkuAsync(product.SKU, tenantId);
                        if (existing != null)
                        {
                            // Merge: update quantity and price
                            existing.Quantity += product.Quantity;
                            existing.UnitPrice = product.UnitPrice;
                            existing.UpdatedAt = DateTime.UtcNow;
                            existing.UpdatedBy = userId;
                            await _unitOfWork.Products.UpdateAsync(existing);
                            importedCount++;
                            continue;
                        }
                    }

                    // Create new product
                    await CreateProductAsync(product, userId);
                    importedCount++;
                }
                catch (Exception ex)
                {
                    errors.Add($"Failed to import product {product.SKU}: {ex.Message}");
                }
            }

            if (errors.Any())
                _logger.LogWarning("Bulk import completed with errors: {Errors}", string.Join("; ", errors));

            await _unitOfWork.CommitTransactionAsync();
        }
        catch (Exception ex)
        {
            await _unitOfWork.RollbackTransactionAsync();
            _logger.LogError(ex, "Bulk import failed");
            throw;
        }

        return importedCount;
    }

    /// <summary>
    /// Create audit log entry
    /// </summary>
    private async Task CreateAuditLogAsync(int recordId, string tableName, string action, int userId, int tenantId, object? oldValue, object? newValue)
    {
        var auditLog = new AuditLog
        {
            TableName = tableName,
            RecordId = recordId,
            Action = action,
            OldValues = oldValue != null ? System.Text.Json.JsonSerializer.Serialize(oldValue) : string.Empty,
            NewValues = newValue != null ? System.Text.Json.JsonSerializer.Serialize(newValue) : string.Empty,
            UserId = userId,
            TenantId = tenantId,
            Timestamp = DateTime.UtcNow
        };

        await _unitOfWork.AuditLogs.AddAsync(auditLog);
    }
}

/// <summary>
/// Product service interface
/// </summary>
public interface IProductService
{
    Task<IEnumerable<Product>> GetProductsAsync(int tenantId, string? category = null, bool activeOnly = true);
    Task<Product?> GetProductByIdAsync(int id, int tenantId);
    Task<Product?> GetProductBySkuAsync(string sku, int tenantId);
    Task<Product> CreateProductAsync(Product product, int userId);
    Task<Product> UpdateProductAsync(Product product, int userId);
    Task<bool> DeleteProductAsync(int id, int userId, int tenantId);
    Task<IEnumerable<Product>> SearchProductsAsync(string searchTerm, int tenantId);
    Task<IEnumerable<Product>> GetLowStockProductsAsync(int tenantId);
    Task<IEnumerable<Product>> GetExpiringProductsAsync(int tenantId, int daysUntilExpiry = 30);
    Task<bool> AdjustStockAsync(int productId, decimal quantityChange, string reason, int userId, int tenantId);
    Task<IEnumerable<string>> GetCategoriesAsync(int tenantId);
    Task<int> BulkImportAsync(IEnumerable<Product> products, int tenantId, int userId, bool mergeExisting = false);
}
