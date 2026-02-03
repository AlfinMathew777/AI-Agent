# scripts/setup_test_env.ps1
# PowerShell version of setup_test_env.sh for Windows

Write-Host "🛠️ Setting up ACP Test Environment..." -ForegroundColor Cyan

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip
pip install --upgrade pip

# Install test dependencies
pip install pytest pytest-asyncio aiohttp requests

Write-Host "✅ Done." -ForegroundColor Green
Write-Host "`nNext steps:"
Write-Host '  $env:ACP_BASE_URL="http://localhost:8000"'
Write-Host '  $env:ACP_ADMIN_KEY="your_admin_key"'
Write-Host '  $env:ACP_TEST_MODE="local"'
Write-Host "  python scripts/run_release_gate.py"
