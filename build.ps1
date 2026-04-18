# Build script for Mintaka Sphere Inventory System (PowerShell)
# Usage: .\build.ps1 [python|dotnet|all]

param(
    [ValidateSet("python", "dotnet", "all")]
    [string]$Target = "all"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "🔨 Mintaka Sphere Build Script" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

function Build-Python {
    Write-Host ""
    Write-Host "🐍 Building Python Project..." -ForegroundColor Green
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        Write-Host "Creating virtual environment..."
        python -m venv .venv
    }
    
    # Activate virtual environment
    & ".\.venv\Scripts\Activate.ps1"
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install dependencies
    Write-Host "Installing dependencies..."
    pip install -e ".[dev]"
    
    # Run linters
    Write-Host "Running Ruff linter..."
    ruff check inventory_app/
    
    Write-Host "Running Black formatter check..."
    black --check inventory_app/
    
    # Run tests
    Write-Host "Running tests..."
    pytest --cov=inventory_app
    
    Write-Host "✅ Python build complete!" -ForegroundColor Green
}

function Build-DotNet {
    Write-Host ""
    Write-Host "🔷 Building .NET Project..." -ForegroundColor Green
    
    Set-Location MintakaEnterprise
    
    # Restore dependencies
    Write-Host "Restoring NuGet packages..."
    dotnet restore Mintaka.sln
    
    # Build
    Write-Host "Building solution..."
    dotnet build Mintaka.sln --configuration Release --no-restore
    
    # Format check
    Write-Host "Checking code format..."
    dotnet format --verify-no-changes Mintaka.sln
    
    # Run tests
    Write-Host "Running tests..."
    dotnet test Mintaka.sln --no-build --configuration Release
    
    Set-Location ..
    
    Write-Host "✅ .NET build complete!" -ForegroundColor Green
}

switch ($Target) {
    "python" { Build-Python }
    "dotnet" { Build-DotNet }
    "all" { 
        Build-Python
        Build-DotNet
    }
}

Write-Host ""
Write-Host "🎉 Build completed successfully!" -ForegroundColor Green
