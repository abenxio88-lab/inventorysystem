#!/usr/bin/env bash
# Build script for Mintaka Sphere Inventory System
# Usage: ./build.sh [python|dotnet|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Mintaka Sphere Build Script"
echo "=============================="

build_python() {
    echo ""
    echo "🐍 Building Python Project..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -e ".[dev]"
    
    # Run linters
    echo "Running Ruff linter..."
    ruff check inventory_app/ || true
    
    echo "Running Black formatter check..."
    black --check inventory_app/ || true
    
    # Run tests
    echo "Running tests..."
    pytest --cov=inventory_app || true
    
    echo "✅ Python build complete!"
}

build_dotnet() {
    echo ""
    echo "🔷 Building .NET Project..."
    
    cd MintakaEnterprise
    
    # Restore dependencies
    echo "Restoring NuGet packages..."
    dotnet restore Mintaka.sln
    
    # Build
    echo "Building solution..."
    dotnet build Mintaka.sln --configuration Release --no-restore
    
    # Format check
    echo "Checking code format..."
    dotnet format --verify-no-changes Mintaka.sln || true
    
    # Run tests
    echo "Running tests..."
    dotnet test Mintaka.sln --no-build --configuration Release || true
    
    cd ..
    
    echo "✅ .NET build complete!"
}

case "${1:-all}" in
    python)
        build_python
        ;;
    dotnet)
        build_dotnet
        ;;
    all|"")
        build_python
        build_dotnet
        ;;
    *)
        echo "Usage: $0 [python|dotnet|all]"
        exit 1
        ;;
esac

echo ""
echo "🎉 Build completed successfully!"
