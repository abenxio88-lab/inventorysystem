Inventory App

This folder contains a simple Tkinter-based inventory management app.

Build & Run

1. Create and activate a virtual environment (optional but recommended):

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

2. Install dependencies:

   pip install -r requirements.txt

3. Run the app (development):

   python main.py

Executable

- A one-file, windowed executable was built with PyInstaller.
- The built executable and support files are in the `dist` folder.
- A distributable ZIP (`dist.zip`) was created at the project root.

Notes for distribution

- Test the executable on target machines. Some Windows systems may require the Microsoft Visual C++ Redistributable.
- To enable Excel export, ensure `openpyxl` is installed (already included in `requirements.txt`).

Contact

If you want a signed or installer-based distribution, tell me and I can help set that up.
