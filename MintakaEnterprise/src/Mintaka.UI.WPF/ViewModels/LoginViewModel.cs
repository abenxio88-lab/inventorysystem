namespace Mintaka.UI.WPF.ViewModels;

using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Windows;
using Mintaka.Application.Services;
using Mintaka.Core.Entities;
using Mintaka.UI.WPF.Views;

/// <summary>
/// Login View Model with authentication logic
/// </summary>
public partial class LoginViewModel : ObservableObject
{
    private readonly IAuthenticationService _authenticationService;
    private readonly Func<MainWindow>? _mainWindowFactory;

    [ObservableProperty]
    private string _username = string.Empty;

    [ObservableProperty]
    private string _password = string.Empty;

    [ObservableProperty]
    private string _errorMessage = string.Empty;

    [ObservableProperty]
    private bool _isLoading;

    [ObservableProperty]
    private User? _currentUser;

    public LoginViewModel(IAuthenticationService authenticationService, Func<MainWindow>? mainWindowFactory = null)
    {
        _authenticationService = authenticationService;
        _mainWindowFactory = mainWindowFactory;
    }

    [RelayCommand]
    private async Task LoginAsync()
    {
        if (string.IsNullOrWhiteSpace(Username))
        {
            ErrorMessage = "Please enter username";
            return;
        }

        if (string.IsNullOrWhiteSpace(Password))
        {
            ErrorMessage = "Please enter password";
            return;
        }

        IsLoading = true;
        ErrorMessage = string.Empty;

        try
        {
            var result = await _authenticationService.LoginAsync(Username, Password);
            
            if (result.Success && result.User != null)
            {
                CurrentUser = result.User;
                
                // Close login window
                var loginWindow = Application.Current.Windows.OfType<LoginView>().FirstOrDefault();
                loginWindow?.Close();

                // Open main window with the authenticated user
                if (_mainWindowFactory != null)
                {
                    var mainWindow = _mainWindowFactory();
                    mainWindow.Show();
                    mainWindow.Activate();
                }
            }
            else
            {
                ErrorMessage = result.Message ?? "Invalid credentials";
            }
        }
        catch (Exception ex)
        {
            ErrorMessage = "An error occurred. Please try again.";
            System.Diagnostics.Debug.WriteLine($"Login error: {ex.Message}");
        }
        finally
        {
            IsLoading = false;
        }
    }

    [RelayCommand]
    private void Exit()
    {
        Application.Current.Shutdown();
    }
}
