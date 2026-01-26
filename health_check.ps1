# Health Check Script - Verify system is running correctly

Write-Host "🏥 Health Check - AI Hotel Assistant" -ForegroundColor Cyan
Write-Host ""

$allHealthy = $true

# Check Backend
Write-Host "Checking Backend (http://localhost:8002)..." -NoNewline
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8002/health" -TimeoutSec 5
    if ($response.status -eq "healthy") {
        Write-Host " ✅ HEALTHY" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  DEGRADED" -ForegroundColor Yellow
        $allHealthy = $false
    }
} catch {
    Write-Host " ❌ DOWN" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    $allHealthy = $false
}

# Check Frontend
Write-Host "Checking Frontend (http://localhost:5173)..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host " ✅ HEALTHY" -ForegroundColor Green
    } else {
        Write-Host " ⚠️  DEGRADED" -ForegroundColor Yellow
        $allHealthy = $false
    }
} catch {
    Write-Host " ❌ DOWN" -ForegroundColor Red
    $allHealthy = $false
}

# Check Database
Write-Host "Checking Database..." -NoNewline
if (Test-Path "backend\hotel.db") {
    Write-Host " ✅ EXISTS" -ForegroundColor Green
} else {
    Write-Host " ❌ MISSING" -ForegroundColor Red
    Write-Host "   Run: cd backend && python -c 'from app.db.session import init_db; init_db()'" -ForegroundColor Yellow
    $allHealthy = $false
}

# Check Environment
Write-Host "Checking Environment..." -NoNewline
if (Test-Path "backend\.env") {
    Write-Host " ✅ CONFIGURED" -ForegroundColor Green
} else {
    Write-Host " ⚠️  MISSING .env" -ForegroundColor Yellow
    Write-Host "   Copy .env.example to .env and configure" -ForegroundColor Yellow
}

Write-Host ""
if ($allHealthy) {
    Write-Host "🎉 All systems operational!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some systems need attention" -ForegroundColor Yellow
    exit 1
}
