#!/bin/bash
# scripts/setup_test_env.sh
# Linux/Mac Environment Setup

set -e

echo "🛠️  ACP Test Environment Setup"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
pip install --quiet --upgrade pip

# Install dependencies
echo "Installing test dependencies..."
pip install --quiet pytest pytest-asyncio aiohttp requests

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env.test if not exists
if [ ! -f ".env.test" ]; then
    echo "Creating .env.test from template..."
    cat > .env.test << 'EOF'
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
EOF
    echo -e "${GREEN}✓ Created .env.test template${NC}"
    echo -e "${YELLOW}⚠ Please edit .env.test with your actual configuration${NC}"
else
    echo -e "${YELLOW}⚠ .env.test already exists${NC}"
fi

# Verify test files exist
echo ""
echo "Verifying test files..."
if [ -d "tests" ]; then
    TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
    echo -e "${GREEN}✓ Found $TEST_COUNT test files${NC}"
else
    echo -e "${RED}✗ tests/ directory not found${NC}"
    exit 1
fi

# Create __init__.py files if missing
if [ ! -f "tests/__init__.py" ]; then
    touch tests/__init__.py
    echo -e "${GREEN}✓ Created tests/__init__.py${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env.test with your configuration"
echo "  2. Start your ACP server (cd backend && python -m uvicorn app.main:app --reload)"
echo "  3. Run tests: python scripts/run_release_gate.py"
echo ""
echo "Quick commands:"
echo "  source venv/bin/activate  # Activate environment"
echo "  pytest tests/ -v          # Run all tests"
echo "  pytest tests/ -m contract # Run contract tests only"
