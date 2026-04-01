@echo off
REM Build script for MSInventory.exe
REM Usage: run from tools folder or double-click this file

SETROOT=%~dp0..\
cd /d "%SETROOT%"

echo Installing Python requirements...
python -m pip install -r inventory_app\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install requirements. Aborting.
    pause
    exit /b 1
)

echo Generating icon...
python tools\generate_icon.py
if %ERRORLEVEL% NEQ 0 (
    echo Icon generation failed. Aborting.
    pause
    exit /b 1
)

echo Building one-file executable with PyInstaller...
pyinstaller --noconfirm --clean --onefile --windowed --icon=tools\msinventory.ico --add-data "inventory_app/data;data" --name MSInventory inventory_app\main.py
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller build failed.
    pause
    exit /b 1
)

IF EXIST dist\MSInventory.exe (
    echo Moving MSInventory.exe to Desktop...
    move /Y dist\MSInventory.exe "%USERPROFILE%\Desktop\MSInventory.exe"
    echo Done. MSInventory.exe placed on your Desktop.
) ELSE (
    echo Built file missing in dist\
)
pause
