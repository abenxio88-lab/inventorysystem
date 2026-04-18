namespace Mintaka.UI.WPF.ViewModels;

using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using System.Windows;
using Mintaka.Application.Services;
using Mintaka.Core.Entities;

/// <summary>
/// Login View Model with authentication logic
/// </summary>
public partial class LoginViewModel : ObservableObject
{
    private readonly IAuthenticationService _authenticationService;
    private readonly MainWindow _mainWindow;

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

    public LoginViewModel(IAuthenticationService authenticationService, MainWindow mainWindow)
    {
        _authenticationService = authenticationService;
        _mainWindow = mainWindow;
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
                
                // Close login window and open main window
                Application.Current.Windows.OfType<LoginView>().FirstOrDefault()?.Close();
                _mainWindow.Show();
                _mainWindow.Activate();
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
