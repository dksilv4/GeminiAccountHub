# Gemini Multi-Account Hub - 1-Click PowerShell Setup
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       Gemini Multi-Account Hub - Setup" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "[ERROR] Python was not found in your PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/3] Python detected: $(python --version)" -ForegroundColor Green

# 2. Desktop Shortcut
Write-Host "[2/3] Creating Windows Desktop Shortcut..." -ForegroundColor White
python setup_shortcut.py

# 3. Launch App
Write-Host "[3/3] Starting Gemini Account Hub in background..." -ForegroundColor White
Start-Process "pythonw" -ArgumentList "app.py" -WorkingDirectory $PSScriptRoot

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Gemini Account Hub is installed and running!" -ForegroundColor Green
Write-Host " Check your Windows System Tray (by the clock) or Desktop!" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
Start-Sleep -Seconds 2
