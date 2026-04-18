namespace Mintaka.UI.WPF;

using System.Windows;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Serilog;
using Mintaka.Infrastructure.Data;
using Mintaka.Application.Services;
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
                var connectionString = "Server=(localdb)\\mssqllocaldb;Database=MintakaInventory;Trusted_Connection=true;";
                
                services.AddDbContext<ApplicationDbContext>(options =>
                    options.UseSqlServer(connectionString));

                // Register Services (minimal for now)
                services.AddScoped<IAuthenticationService, AuthenticationService>();

                // Register Views and ViewModels minimally
                services.AddTransient<MainWindow>();
            })
            .Build();
    }

    protected override async void OnStartup(StartupEventArgs e)
    {
        await _host.StartAsync();

        // Ensure database is created and seeded (wrapped in try-catch for cases where DB is unavailable)
        try
        {
            using (var scope = _host.Services.CreateScope())
            {
                var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
                await dbContext.Database.EnsureCreatedAsync();
            }
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Database initialization failed: {ex.Message}. App will continue without database.");
        }

        // Show login window first
        var loginView = _host.Services.GetRequiredService<LoginView>();
        loginView.Show();

        base.OnStartup(e);
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        await _host.StopAsync();
        _host.Dispose();
        base.OnExit(e);
    }
}
