@echo off
rem Run the python bootstrapper
if "%1"=="--infologs" (
    python "%~dp0setup_pst.py" --infologs
) else (
    python "%~dp0setup_pst.py"
)
exit /b %errorlevel%
