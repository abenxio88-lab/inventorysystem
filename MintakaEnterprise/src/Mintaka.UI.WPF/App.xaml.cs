namespace Mintaka.UI.WPF;

using System.Windows;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Serilog;
using Mintaka.Infrastructure.Data;
using Mintaka.Application.Services;
using Mintaka.Core.Interfaces;
using Mintaka.UI.WPF.ViewModels;
using Mintaka.UI.WPF.Views;
using Microsoft.EntityFrameworkCore;

/// <summary>
/// Application entry point with dependency injection setup
/// </summary>
public partial class App : Application
{
    private readonly IHost _host;

    public App()
    {
        _host = Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                // Configure logging
                Log.Logger = new LoggerConfiguration()
                    .WriteTo.File("logs/mintaka-.log", rollingInterval: RollingInterval.Day)
                    .CreateLogger();

                services.AddLogging(builder => builder.AddSerilog());

                // Configure database
                var connectionString = context.Configuration.GetConnectionString("DefaultConnection") 
                    ?? "Server=(localdb)\\mssqllocaldb;Database=MintakaInventory;Trusted_Connection=true;";
                
                services.AddDbContext<ApplicationDbContext>(options =>
                    options.UseSqlServer(connectionString));

                // Register Unit of Work and Repositories
                services.AddScoped<IUnitOfWork, ApplicationDbContext>();

                // Register Services
                services.AddScoped<IProductService, ProductService>();
                services.AddScoped<IAuthenticationService, AuthenticationService>();

                // Register Views
                services.AddTransient<MainWindow>();
                services.AddTransient<LoginView>();
            })
            .Build();
    }

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();

        // Ensure database is created and seeded
        using (var scope = _host.Services.CreateScope())
        {
            var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
            await dbContext.Database.EnsureCreatedAsync();
        }

        // Show login window first - create with proper DI
        var serviceProvider = _host.Services;
        var authService = serviceProvider.GetRequiredService<IAuthenticationService>();
        var productService = serviceProvider.GetRequiredService<IProductService>();
        
        // Create login view model
        var loginViewModel = new LoginViewModel(authService, null);
        var loginView = new LoginView(loginViewModel);
        loginView.Show();

        // Setup logout action for main window
        Action showLoginWindow = () =>
        {
            Application.Current.Windows.OfType<MainWindow>().FirstOrDefault()?.Close();
            var newLoginView = new LoginView(new LoginViewModel(authService, null));
            newLoginView.Show();
        };

        // Store the logout action in app resources for MainWindow to access
        Resources["LogoutAction"] = showLoginWindow;

        // Hook up login success to open main window
        loginViewModel.PropertyChanged += (s, args) =>
        {
            if (args.PropertyName == nameof(LoginViewModel.CurrentUser) && loginViewModel.CurrentUser != null)
            {
                loginView.Close();
                
                var mainWindowViewModel = new MainWindowViewModel(
                    productService,
                    authService,
                    loginViewModel.CurrentUser,
                    showLoginWindow);
                
                var mainWindow = new MainWindow(mainWindowViewModel);
                mainWindow.Show();
            }
        };

        base.OnStartup(e);
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        await _host.StopAsync();
        _host.Dispose();
        Log.CloseAndFlush();
        base.OnExit(e);
    }
}
