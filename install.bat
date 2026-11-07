@echo off
title Gemini Account Hub Setup
cd /d "%~dp0"
echo ========================================================
echo         Gemini Multi-Account Hub - Setup
echo ========================================================
echo.

:: 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in your PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo (Make sure to check "Add Python to PATH" during installation)
    echo.
    pause
    exit /b 1
)

echo [1/3] Python detected:
python --version
echo.

:: 2. Create Desktop Shortcut
echo [2/3] Creating Windows Desktop Shortcut...
python setup_shortcut.py
echo.

:: 3. Launch App
echo [3/3] Starting Gemini Account Hub...
start "" pythonw app.py
echo.
echo ========================================================
echo  [SUCCESS] Gemini Account Hub is installed and running!
echo  Check your Windows System Tray (by the clock) or Desktop!
echo ========================================================
echo.
timeout /t 3 >nul
exit
