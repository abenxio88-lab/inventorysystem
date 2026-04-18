"""
Diagnostic script to test tab function imports
"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import TAB_REGISTRY, get_industry_config

print("=" * 80)
print("TAB FUNCTION IMPORT TEST")
print("=" * 80)

industry = get_industry_config("electronics")
visible_tabs = industry.get_visible_tabs()

print(f"\nIndustry: {industry.industry_name}")
print(f"Visible tabs: {visible_tabs}\n")

print("-" * 80)
print(f"{'Tab Name':<25} {'Module':<30} {'Function':<35} {'Status'}")
print("-" * 80)

for tab_name in visible_tabs:
    if tab_name not in TAB_REGISTRY:
        print(f"{tab_name:<25} {'N/A':<30} {'N/A':<35} ❌ NOT IN REGISTRY")
        continue
    
    tab_info = TAB_REGISTRY[tab_name]
    module_name = tab_info["module"]
    func_name = tab_info["function"]
    
    try:
        import importlib
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        print(f"{tab_name:<25} {module_name:<30} {func_name:<35} ✅ OK")
    except ImportError as e:
        print(f"{tab_name:<25} {module_name:<30} {func_name:<35} ❌ IMPORT ERROR: {e}")
    except AttributeError as e:
        print(f"{tab_name:<25} {module_name:<30} {func_name:<35} ❌ FUNCTION NOT FOUND: {e}")
    except Exception as e:
        print(f"{tab_name:<25} {module_name:<30} {func_name:<35} ❌ ERROR: {e}")

print("=" * 80)
