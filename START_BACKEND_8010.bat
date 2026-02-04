@echo off
echo Starting Backend Server on Port 8010...
cd /d "%~dp0backend"
call venv\Scripts\activate
call python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
pause
