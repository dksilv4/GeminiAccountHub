@echo off
cd /d "%~dp0"
start "" wscript.exe "launch_silent.vbs"
timeout /t 1 /nobreak >nul
start "" "http://localhost:54321"
