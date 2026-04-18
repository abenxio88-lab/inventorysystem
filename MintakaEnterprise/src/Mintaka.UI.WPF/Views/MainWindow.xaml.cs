using System.Windows;
using Mintaka.UI.WPF.ViewModels;

namespace Mintaka.UI.WPF.Views;

/// <summary>
/// Main application window after successful login
/// </summary>
public partial class MainWindow : Window
{
    private readonly MainWindowViewModel _viewModel;

    public MainWindow(MainWindowViewModel viewModel)
    {
        InitializeComponent();
        _viewModel = viewModel;
        DataContext = _viewModel;
    }
}
