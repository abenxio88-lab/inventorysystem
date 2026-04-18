
# How to Run Mintaka Enterprise on Windows

## Prerequisites

### 1. Install .NET SDK (Required)
**Download:** https://dotnet.microsoft.com/download/dotnet/8.0

- Download **.NET 8.0 SDK** (not just Runtime)
- Run the installer
- Verify installation by opening **Command Prompt** or **PowerShell** and typing:
  ```bash
  dotnet --version
  ```
  You should see something like `8.0.xxx`

### 2. Install SQL Server (Choose One Option)

#### Option A: SQL Server Express (Recommended for Development)
**Download:** https://www.microsoft.com/en-us/sql-server/sql-server-downloads
- Select **SQL Server Express** (Free)
- During installation:
  - Choose **Windows Authentication** or **Mixed Mode**
  - If Mixed Mode, remember your `sa` password
  - Note the **Server Name** (usually `localhost\SQLEXPRESS` or just `localhost`)

#### Option B: SQL Server LocalDB (Lightweight)
- Comes with Visual Studio
- Or install separately from Microsoft website
- Server name will be `(localdb)\MSSQLLocalDB`

#### Option C: Docker (Advanced)
```bash
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Passw0rd" -p 1433:1433 --name sqlserver -d mcr.microsoft.com/mssql/server:2022-latest
```

### 3. (Optional) Install Visual Studio 2022
**Download:** https://visualstudio.microsoft.com/downloads/
- Select **Community Edition** (Free)
- During installation, check:
  - ✅ **.NET desktop development**
  - ✅ **ASP.NET and web development** (optional)

---

## Step-by-Step Setup

### Step 1: Navigate to Project Folder
Open **PowerShell** or **Command Prompt**:
```bash
cd C:\path\to\MintakaEnterprise
```
Or if in workspace:
```bash
cd \workspace\MintakaEnterprise
```

### Step 2: Configure Database Connection

Open `src/Mintaka.Infrastructure/appsettings.json` (or create it) and update the connection string:

**For SQL Server Express:**
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost\\SQLEXPRESS;Database=MintakaDB;Trusted_Connection=True;TrustServerCertificate=True;"
  }
}
```

**For LocalDB:**
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=(localdb)\\MSSQLLocalDB;Database=MintakaDB;Trusted_Connection=True;"
  }
}
```

**For SQL Server with Username/Password:**
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=MintakaDB;User Id=sa;Password=YourStrong@Passw0rd;TrustServerCertificate=True;"
  }
}
```

### Step 3: Restore NuGet Packages
```bash
dotnet restore
```

### Step 4: Create Database and Run Migrations

```bash
# Navigate to Infrastructure project
cd src/Mintaka.Infrastructure

# Add migration (if not already present)
dotnet ef migrations add InitialCreate --project ../Mintaka.Infrastructure --startup-project ../Mintaka.UI.WPF

# Update database
dotnet ef database update --project ../Mintaka.Infrastructure --startup-project ../Mintaka.UI.WPF
```

**If EF Core CLI is not installed:**
```bash
dotnet tool install --global dotnet-ef
```
Then close and reopen your terminal, and try again.

### Step 5: Build the Application
Go back to solution root:
```bash
cd ../../..
dotnet build
```

### Step 6: Run the Application

#### Option A: Using Command Line
```bash
dotnet run --project src/Mintaka.UI.WPF
```

#### Option B: Using Visual Studio
1. Open `Mintaka.sln` in Visual Studio
2. Right-click on **Mintaka.UI.WPF** → **Set as Startup Project**
3. Press **F5** or click **Run**

#### Option C: Publish and Run Executable
```bash
dotnet publish src/Mintaka.UI.WPF -c Release -o ./publish
cd publish
Mintaka.UI.WPF.exe
```

---

## Default Login Credentials

After first run, use these credentials:
- **Username:** `admin`
- **Password:** `Admin@123`

*(Or check the database seed data in the code)*

---

## Troubleshooting

### Error: "A valid SQL Server instance could not be found"
- Verify SQL Server is running: Open **Services.msc** → Look for **SQL Server (SQLEXPRESS)**
- Check connection string matches your SQL Server instance name
- Try using `.` or `(local)` instead of `localhost`

### Error: "Login failed for user..."
- If using SQL Authentication, verify username/password in connection string
- If using Windows Authentication, ensure your Windows user has access
- Try enabling **SQL Server Management Studio (SSMS)** to test connection

### Error: "The .NET SDK can't be found"
- Reinstall .NET 8 SDK from https://dotnet.microsoft.com/download
- Restart your terminal/IDE after installation
- Check PATH environment variable

### Error: "Migration assembly mismatch"
```bash
dotnet ef database drop --force
dotnet ef database update
```

### Error: "Cannot access file because it's being used by another process"
- Close any running instances of the app
- Check Task Manager for lingering processes
- Restart Visual Studio

### WPF App Doesn't Show UI
- Ensure you're running on Windows (WPF doesn't work on Linux/Mac natively)
- Check Windows Event Viewer for errors
- Try running as Administrator

---

## Quick Start Script (PowerShell)

Save this as `run.ps1` and execute in PowerShell:

```powershell
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
```

Run with:
```powershell
.\run.ps1
```

---

## Next Steps After Running

1. **Login** with admin credentials
2. **Navigate Dashboard** - View KPIs
3. **Add Products** - Go to Products tab
4. **Manage Inventory** - Stock adjustments
5. **Add Customers/Suppliers** - Partner management

---

## Need Help?

- Check logs in: `bin/Debug/net8.0/logs/`
- Review `appsettings.json` for configuration
- Ensure SQL Server is accessible
- Check Windows Firewall isn't blocking the app

**Good luck! 🚀**