@echo off
echo Starting Backend Server...
cd /d "%~dp0backend"
call venv\Scripts\activate
call uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
pause
