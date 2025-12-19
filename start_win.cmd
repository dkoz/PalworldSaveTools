@echo off
rem Run the python bootstrapper
if "%1"=="--infologs" (
    python "%~dp0setup.py" --infologs
) else (
    python "%~dp0setup.py"
)
exit /b %errorlevel%
