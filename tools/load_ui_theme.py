import importlib.util, traceback, os
p = os.path.join(os.path.dirname(__file__), '..', 'inventory_app', 'ui_theme.py')
try:
    spec = importlib.util.spec_from_file_location('ui_theme_local', os.path.abspath(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print('Loaded ui_theme_local')
    print(sorted([n for n in dir(m) if not n.startswith('_')]))
except Exception:
    traceback.print_exc()
