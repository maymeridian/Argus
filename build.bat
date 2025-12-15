@echo off
echo --- Building Argus 2.0 ---

:: 1. Clean previous builds
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

:: 2. Run PyInstaller
:: --icon: Sets the actual .exe file icon in Windows Explorer
:: --add-data: Bundles the file so the app can use it for the Taskbar/Window title

pyinstaller --noconfirm --onedir --windowed ^
    --name "Argus" ^
    --icon "icon.ico" ^
    --add-data "libraries;libraries" ^
    --add-data "settings.json;." ^
    --add-data "icon.ico;." ^
    --collect-all customtkinter ^
    --collect-all rapidocr_onnxruntime ^
    gui.py

echo.
echo --- Build Complete! ---
pause