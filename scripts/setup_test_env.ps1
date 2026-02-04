# scripts/setup_test_env.ps1
# Windows PowerShell Environment Setup

Write-Host "🛠️  ACP Test Environment Setup (Windows)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "⚠ Virtual environment already exists" -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
pip install --quiet --upgrade pip

# Install dependencies
Write-Host "Installing test dependencies..." -ForegroundColor Yellow
pip install --quiet pytest pytest-asyncio aiohttp requests

Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Create .env.test if not exists
if (-not (Test-Path ".env.test")) {
    Write-Host "Creating .env.test from template..." -ForegroundColor Yellow
    @"
# ACP Test Environment Configuration
# Copy this to .env.test and customize for your environment

# Server Configuration
ACP_BASE_URL=http://localhost:8000
ACP_ADMIN_KEY=your_admin_key_here

# Test Mode: local | staging | prod
ACP_TEST_MODE=local

# Safety: Set to true ONLY when you want to test real bookings
ACP_ALLOW_REAL_BOOKING_TESTS=false

# Test Data
ACP_TEST_PROPERTY_ID=cloudbeds_001

# Performance Test Settings
ACP_PERF_ITERATIONS=50
ACP_PERF_DURATION=10
ACP_PERF_CONCURRENCY=50

# Database Paths (relative to project root)
ACP_BACKEND_DIR=backend
"@ | Out-File -FilePath ".env.test" -Encoding utf8
    
    Write-Host "✓ Created .env.test template" -ForegroundColor Green
    Write-Host "⚠ Please edit .env.test with your actual configuration" -ForegroundColor Yellow
} else {
    Write-Host "⚠ .env.test already exists" -ForegroundColor Yellow
}

# Verify test files
Write-Host ""
Write-Host "Verifying test files..." -ForegroundColor Yellow
if (Test-Path "tests") {
    $testCount = (Get-ChildItem -Path "tests" -Filter "test_*.py").Count
    Write-Host "✓ Found $testCount test files" -ForegroundColor Green
} else {
    Write-Host "✗ tests/ directory not found" -ForegroundColor Red
    exit 1
}

# Create __init__.py
if (-not (Test-Path "tests/__init__.py")) {
    New-Item -ItemType File -Path "tests/__init__.py" -Force | Out-Null
    Write-Host "✓ Created tests/__init__.py" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Edit .env.test with your configuration"
Write-Host "  2. Start your ACP server:"
Write-Host "     cd backend; python -m uvicorn app.main:app --reload"
Write-Host "  3. Run tests: python scripts/run_release_gate.py"
Write-Host ""
Write-Host "Quick commands:" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate.ps1  # Activate environment"
Write-Host "  pytest tests/ -v             # Run all tests"
Write-Host "  pytest tests/ -m contract    # Run contract tests only"
