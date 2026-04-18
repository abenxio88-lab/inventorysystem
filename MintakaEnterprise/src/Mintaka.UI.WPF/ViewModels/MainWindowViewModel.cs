namespace Mintaka.UI.WPF.ViewModels;

using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Windows;
using Mintaka.Application.Services;
using Mintaka.Core.Interfaces;
using Mintaka.Core.Entities;
using Mintaka.UI.WPF.Views;

/// <summary>
/// Main Window ViewModel with dashboard and navigation logic
/// </summary>
public partial class MainWindowViewModel : ObservableObject
{
    private readonly IProductService _productService;
    private readonly IAuthenticationService _authenticationService;
    private readonly int _tenantId;
    private readonly Action? _logoutAction;

    [ObservableProperty]
    private string _currentUserName = string.Empty;

    [ObservableProperty]
    private int _totalProducts;

    [ObservableProperty]
    private int _lowStockCount;

    [ObservableProperty]
    private int _expiringSoonCount;

    [ObservableProperty]
    private decimal _totalInventoryValue;

    public MainWindowViewModel(
        IProductService productService,
        IAuthenticationService authenticationService,
        User? currentUser = null,
        Action? logoutAction = null)
    {
        _productService = productService;
        _authenticationService = authenticationService;
        _logoutAction = logoutAction;
        _tenantId = currentUser?.TenantId ?? 1; // Default to tenant 1 if not provided

        if (currentUser != null)
        {
            CurrentUserName = $"{currentUser.Username} ({currentUser.Role})";
        }

        _ = LoadDashboardDataAsync();
    }

    /// <summary>
    /// Load dashboard KPI data
    /// </summary>
    private async Task LoadDashboardDataAsync()
    {
        try
        {
            // Load total products
            var products = await _productService.GetProductsAsync(_tenantId);
            TotalProducts = products.Count();

            // Load low stock count
            var lowStockProducts = await _productService.GetLowStockProductsAsync(_tenantId);
            LowStockCount = lowStockProducts.Count();

            // Load expiring soon count
            var expiringProducts = await _productService.GetExpiringProductsAsync(_tenantId, 30);
            ExpiringSoonCount = expiringProducts.Count();

            // Calculate total inventory value
            TotalInventoryValue = products.Sum(p => p.Quantity * p.CostPrice);
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Error loading dashboard: {ex.Message}");
            // Set default values on error
            TotalProducts = 0;
            LowStockCount = 0;
            ExpiringSoonCount = 0;
            TotalInventoryValue = 0;
        }
    }

    /// <summary>
    /// Logout command - closes main window and shows login
    /// </summary>
    [RelayCommand]
    private void Logout()
    {
        _logoutAction?.Invoke();
    }

    /// <summary>
    /// Refresh dashboard data
    /// </summary>
    [RelayCommand]
    private async Task RefreshDataAsync()
    {
        await LoadDashboardDataAsync();
    }
}
