@echo off
setlocal enableextensions enabledelayedexpansion
title PalworldSaveTools

rem Resolve script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

rem Prefer venv Python if present
set "VENV_PY=%SCRIPT_DIR%venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    set "PYEXE=%VENV_PY%"
) else (
    rem Fallback to system Python
    set "PYEXE=python"
)

echo Using Python: "%PYEXE%"
"%PYEXE%" -c "import sys; print('Python', sys.version)" 2>nul

"%PYEXE%" "%SCRIPT_DIR%menu.py"