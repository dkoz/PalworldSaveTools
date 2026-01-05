@echo off
title PalworldSaveTools Auto Translation
echo ========================================
echo 🌐 PalworldSaveTools Auto Translation
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python and make sure it's in your PATH.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Run the translation script
python auto_translate_standalone.py

echo.
echo ========================================
echo Press any key to exit...
pause >nul
