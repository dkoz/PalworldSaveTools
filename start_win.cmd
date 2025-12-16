@echo off
rem Run the python bootstrapper
python "%~dp0start.py"
exit /b %errorlevel%
