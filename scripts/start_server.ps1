# Start ACP Server on Port 8010 (avoiding Splunk on 8000)

Write-Host "🚀 Starting ACP Server" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "backend")) {
    Write-Host "❌ ERROR: backend/ directory not found" -ForegroundColor Red
    Write-Host "   Run this script from the project root" -ForegroundColor Yellow
    exit 1
}

# Check if uvicorn is installed
try {
    python -m uvicorn --version | Out-Null
} catch {
    Write-Host "❌ ERROR: uvicorn not installed" -ForegroundColor Red
    Write-Host "   Run: pip install uvicorn fastapi aiohttp" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "⚠️  PORT NOTICE:" -ForegroundColor Yellow
Write-Host "   Port 8000 is occupied by Splunk" -ForegroundColor Gray
Write-Host "   Starting ACP on port 8010 instead" -ForegroundColor Gray
Write-Host ""

# Start server
Write-Host "Starting server on http://localhost:8010..." -ForegroundColor Green
Write-Host ""
Write-Host "📖 API Documentation: http://localhost:8010/docs" -ForegroundColor Cyan
Write-Host "🔍 Alternative docs:   http://localhost:8010/redoc" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press CTRL+C to stop" -ForegroundColor Gray
Write-Host ""

cd backend
python -m uvicorn app.main:app --reload --port 8010
