import traceback
try:
    import inventory_app.ui_theme as t
    print('loaded inventory_app.ui_theme')
    print(sorted([n for n in dir(t) if not n.startswith('_')]))
except Exception:
    traceback.print_exc()
