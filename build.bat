@echo off
echo --- Building Argus 2.0 ---

:: 1. Clean previous builds
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

:: 2. Run PyInstaller
:: --noconfirm: Don't ask to overwrite
:: --onedir: Keep it as a folder (Faster start)
:: --windowed: No black console window
:: --add-data: Includes necessary folders and files (Libraries, Config, Icons)
:: --collect-all: Ensures CustomTkinter and OCR themes/configs are included

pyinstaller --noconfirm --onedir --windowed ^
    --name "Argus" ^
    --add-data "libraries;libraries" ^
    --add-data "settings.json;." ^
    --add-data "icon.ico;." ^
    --collect-all customtkinter ^
    --collect-all rapidocr_onnxruntime ^
    gui.py

echo.
echo --- Build Complete! ---
pause