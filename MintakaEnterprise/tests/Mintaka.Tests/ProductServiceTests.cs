using Xunit;
using FluentAssertions;
using Moq;
using Mintaka.Core.Entities;
using Mintaka.Application.Services;
using Mintaka.Core.Interfaces;
using Microsoft.Extensions.Logging;

namespace Mintaka.Tests.Unit.Application;

/// <summary>
/// Unit tests for ProductService
/// </summary>
public class ProductServiceTests
{
    private readonly Mock<IUnitOfWork> _mockUnitOfWork;
    private readonly Mock<ILogger<ProductService>> _mockLogger;
    private readonly ProductService _productService;

    public ProductServiceTests()
    {
        _mockUnitOfWork = new Mock<IUnitOfWork>();
        _mockLogger = new Mock<ILogger<ProductService>>();
        _productService = new ProductService(_mockUnitOfWork.Object, _mockLogger.Object);
    }

    [Fact]
    public async Task GetProductByIdAsync_WhenProductExists_ReturnsProduct()
    {
        // Arrange
        var productId = 1;
        var tenantId = 1;
        var product = new Product 
        { 
            Id = productId, 
            Name = "Test Product", 
            SKU = "TEST001",
            TenantId = tenantId,
            IsActive = true 
        };

        _mockUnitOfWork.Setup(u => u.Products.GetByIdAsync(productId))
            .ReturnsAsync(product);

        // Act
        var result = await _productService.GetProductByIdAsync(productId, tenantId);

        // Assert
        result.Should().NotBeNull();
        result!.Id.Should().Be(productId);
        result.Name.Should().Be("Test Product");
    }

    [Fact]
    public async Task GetProductByIdAsync_WhenProductDoesNotExist_ReturnsNull()
    {
        // Arrange
        _mockUnitOfWork.Setup(u => u.Products.GetByIdAsync(It.IsAny<int>()))
            .ReturnsAsync((Product?)null);

        // Act
        var result = await _productService.GetProductByIdAsync(999, 1);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task CreateProductAsync_WithValidData_CreatesProduct()
    {
        // Arrange
        var newProduct = new Product
        {
            Name = "New Product",
            SKU = "NEW001",
            Quantity = 100,
            UnitPrice = 29.99m,
            TenantId = 1
        };

        _mockUnitOfWork.Setup(u => u.Products.GetBySkuAsync(It.IsAny<string>(), It.IsAny<int>()))
            .ReturnsAsync((Product?)null);

        _mockUnitOfWork.Setup(u => u.Products.AddAsync(It.IsAny<Product>()))
            .ReturnsAsync(newProduct);

        _mockUnitOfWork.Setup(u => u.SaveChangesAsync()).ReturnsAsync(1);

        // Act
        var result = await _productService.CreateProductAsync(newProduct, 1);

        // Assert
        result.Should().NotBeNull();
        result.SKU.Should().Be("NEW001");
        _mockUnitOfWork.Verify(u => u.Products.AddAsync(It.IsAny<Product>()), Times.Once);
        _mockUnitOfWork.Verify(u => u.SaveChangesAsync(), Times.Once);
    }

    [Fact]
    public async Task CreateProductAsync_WithDuplicateSKU_ThrowsException()
    {
        // Arrange
        var existingProduct = new Product { Id = 1, SKU = "DUP001", TenantId = 1 };
        
        _mockUnitOfWork.Setup(u => u.Products.GetBySkuAsync("DUP001", 1))
            .ReturnsAsync(existingProduct);

        var newProduct = new Product { SKU = "DUP001", TenantId = 1 };

        // Act & Assert
        await FluentActions.Invoking(() => 
            _productService.CreateProductAsync(newProduct, 1))
            .Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*already exists*");
    }

    [Fact]
    public async Task AdjustStockAsync_WithPositiveQuantity_IncreasesStock()
    {
        // Arrange
        var product = new Product { Id = 1, Quantity = 50, MinQuantity = 10, MaxQuantity = 1000, TenantId = 1 };
        
        _mockUnitOfWork.Setup(u => u.Products.GetByIdAsync(1)).ReturnsAsync(product);
        _mockUnitOfWork.Setup(u => u.Products.UpdateAsync(It.IsAny<Product>())).Returns(Task.CompletedTask);
        _mockUnitOfWork.Setup(u => u.Transactions.AddAsync(It.IsAny<InventoryTransaction>())).ReturnsAsync((InventoryTransaction t) => t);
        _mockUnitOfWork.Setup(u => u.SaveChangesAsync()).ReturnsAsync(1);

        // Act
        var result = await _productService.AdjustStockAsync(1, 25, "Stock received", 1, 1);

        // Assert
        result.Should().BeTrue();
        product.Quantity.Should().Be(75);
    }

    [Fact]
    public async Task AdjustStockAsync_WithNegativeQuantity_DecreasesStock()
    {
        // Arrange
        var product = new Product { Id = 1, Quantity = 50, MinQuantity = 10, MaxQuantity = 1000, TenantId = 1 };
        
        _mockUnitOfWork.Setup(u => u.Products.GetByIdAsync(1)).ReturnsAsync(product);
        _mockUnitOfWork.Setup(u => u.Products.UpdateAsync(It.IsAny<Product>())).Returns(Task.CompletedTask);
        _mockUnitOfWork.Setup(u => u.Transactions.AddAsync(It.IsAny<InventoryTransaction>())).ReturnsAsync((InventoryTransaction t) => t);
        _mockUnitOfWork.Setup(u => u.SaveChangesAsync()).ReturnsAsync(1);

        // Act
        var result = await _productService.AdjustStockAsync(1, -20, "Damaged goods", 1, 1);

        // Assert
        result.Should().BeTrue();
        product.Quantity.Should().Be(30);
    }

    [Fact]
    public async Task AdjustStockAsync_WhenQuantityGoesBelowZero_ThrowsException()
    {
        // Arrange
        var product = new Product { Id = 1, Quantity = 10, TenantId = 1 };
        
        _mockUnitOfWork.Setup(u => u.Products.GetByIdAsync(1)).ReturnsAsync(product);

        // Act & Assert
        await FluentActions.Invoking(() => 
            _productService.AdjustStockAsync(1, -15, "Invalid adjustment", 1, 1))
            .Should().ThrowAsync<InvalidOperationException>()
            .WithMessage("*below zero*");
    }
}
