# Start Backend on Port 8010
Write-Host "🚀 Starting Backend Server on Port 8010..." -ForegroundColor Cyan
cd "backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
