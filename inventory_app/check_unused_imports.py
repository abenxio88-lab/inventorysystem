"""
Script to find and remove unused imports from Python files.
This helps clean up the red line warnings in IDEs.
"""
import ast
import os
from pathlib import Path

def find_unused_imports(filepath):
    """Find unused imports in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        # Collect all imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((name, alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((name, f"{module}.{alias.name}", node.lineno))
        
        # Find all names used in the code (excluding import statements)
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # Get the root name (e.g., 'svc' from 'svc.inventory.get_all')
                root = node
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    used_names.add(root.id)
        
        # Find unused imports
        unused = []
        for name, full_name, line_no in imports:
            if name not in used_names:
                unused.append((name, full_name, line_no))
        
        return unused
    except Exception as e:
        return []

def main():
    """Check all Python files in inventory_app."""
    app_dir = Path(__file__).parent
    
    print("=== UNUSED IMPORTS REPORT ===\n")
    
    for py_file in sorted(app_dir.glob('*.py')):
        if py_file.name.startswith('_'):
            continue
            
        unused = find_unused_imports(py_file)
        
        if unused:
            print(f"\n{py_file.name}:")
            for name, full_name, line_no in unused:
                print(f"  Line {line_no}: {name} (from {full_name})")

if __name__ == '__main__':
    main()
