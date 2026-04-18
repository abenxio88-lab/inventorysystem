# Mintaka Sphere Inventory Management System

[![Python CI](https://github.com/your-org/mintaka-sphere/actions/workflows/python-ci.yml/badge.svg)](https://github.com/your-org/mintaka-sphere/actions/workflows/python-ci.yml)
[![.NET CI](https://github.com/your-org/mintaka-sphere/actions/workflows/dotnet-ci.yml/badge.svg)](https://github.com/your-org/mintaka-sphere/actions/workflows/dotnet-ci.yml)

A professional inventory management system available in both Python (desktop) and .NET 8 WPF (enterprise) versions.

---

## 📁 Projects

### 🐍 Python Desktop Application (`inventory_app/`)
Modern Tkinter-based desktop application with SQLite database.

**Quick Start:**
```bash
cd inventory_app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 🔷 .NET 8 Enterprise Application (`MintakaEnterprise/`)
Professional WPF application built on .NET 8 with Clean Architecture.

**Quick Start:**
```bash
cd MintakaEnterprise
dotnet restore
dotnet run
```

---

## 🛠️ Development

### Build Script (Both Projects)
```bash
# Linux/macOS
./build.sh

# Windows PowerShell
.\build.ps1
```

### Code Quality Tools

**Python:**
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Lint
ruff check .
black --check .

# Type check
mypy inventory_app/

# Test
pytest --cov=inventory_app
```

**.NET:**
```bash
# Format check
dotnet format --verify-no-changes

# Test
dotnet test
```

---

## 📋 Requirements

- **Python**: 3.10+ (tested on 3.10, 3.11, 3.12)
- **.NET SDK**: 8.0+ (see `MintakaEnterprise/global.json` for exact version)

---

## 📄 License

MIT License

