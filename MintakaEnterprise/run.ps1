Write-Host "=== Mintaka Enterprise Setup ===" -ForegroundColor Green

# Check .NET
$dotnetVersion = dotnet --version
if ($LASTEXITCODE -ne 0) {
    Write-Host ".NET SDK not found! Please install from https://dotnet.microsoft.com/download" -ForegroundColor Red
    exit 1
}
Write-Host ".NET Version: $dotnetVersion" -ForegroundColor Green

# Restore packages
Write-Host "`nRestoring packages..." -ForegroundColor Yellow
dotnet restore
if ($LASTEXITCODE -ne 0) { exit 1 }

# Build
Write-Host "`nBuilding application..." -ForegroundColor Yellow
dotnet build --no-restore
if ($LASTEXITCODE -ne 0) { exit 1 }

# Run migrations
Write-Host "`nUpdating database..." -ForegroundColor Yellow
dotnet ef database update --project src/Mintaka.Infrastructure --startup-project src/Mintaka.UI.WPF
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Migration failed. You may need to configure your connection string first." -ForegroundColor Red
}

# Run app
Write-Host "`nStarting application..." -ForegroundColor Green
dotnet run --project src/Mintaka.UI.WPF
