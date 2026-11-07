# Start Gemini Multi-Account Dashboard & Switcher
Set-Location -Path $PSScriptRoot
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting Gemini Multi-Account Quota Hub & Switcher..." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
python server.py
