# AI Hotel Assistant - Startup Script
# This script starts both backend and frontend servers

Write-Host "🚀 Starting AI Hotel Assistant..." -ForegroundColor Cyan
Write-Host ""

# Check if Python venv exists
if (-not (Test-Path "backend\venv\Scripts\python.exe")) {
    Write-Host "❌ Python virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: cd backend && python -m venv venv && .\venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "❌ Frontend dependencies not installed!" -ForegroundColor Red
    Write-Host "Run: cd frontend && npm install" -ForegroundColor Yellow
    exit 1
}

# Start Backend
Write-Host "🔧 Starting Backend Server (Port 8011)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; .\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --reload"

# Wait for backend to start
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test backend health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8011/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend is running!" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend health check failed, but continuing..." -ForegroundColor Yellow
}

# Start Frontend  
Write-Host "🎨 Starting Frontend Server (Port 5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

Write-Host ""
Write-Host "✨ Servers starting!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Backend:  http://localhost:8011" -ForegroundColor White
Write-Host "📍 Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "📍 Docs:     http://localhost:8011/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop servers" -ForegroundColor Gray
