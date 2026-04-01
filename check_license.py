import os
import sys
import logging

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from inventory_app.license_manager import verify_software_activation
    from inventory_app.utils import get_data_dir
    
    print(f"Data directory: {get_data_dir()}")
    license_file = os.path.join(get_data_dir(), 'license.json')
    print(f"License file path: {license_file}")
    print(f"License file exists: {os.path.exists(license_file)}")
    
    print("Calling verify_software_activation()...")
    is_licensed, status = verify_software_activation()
    print(f"Result: is_licensed={is_licensed}, status={status}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
