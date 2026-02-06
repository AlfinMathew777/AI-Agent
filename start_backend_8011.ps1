# Start Backend on Port 8011 (Alternate Port)
Write-Host "🚀 Starting Backend Server on Port 8011..." -ForegroundColor Cyan
cd "backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --reload
