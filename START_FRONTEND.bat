@echo off
echo Starting Frontend Development Server...
cd /d "%~dp0frontend"
call npm run dev
pause
