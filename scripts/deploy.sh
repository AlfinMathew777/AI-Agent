#!/bin/bash
# Deployment script for AI Hotel Assistant
# Usage: ./scripts/deploy.sh

set -e  # Exit on error

echo "🚀 Starting deployment..."
echo "======================="

# Configuration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Pre-deployment validation
echo ""
echo "📋 Step 1/7: Pre-deployment validation"
echo "---------------------------------------"

cd "$BACKEND_DIR"

# Run startup validation
if python scripts/validate_startup.py; then
    print_success "Startup validation passed"
else
    print_error "Startup validation failed"
    exit 1
fi

# Step 2: Run tests
echo ""
echo "🧪 Step 2/7: Running tests"
echo "--------------------------"

if command -v pytest &> /dev/null; then
    if pytest tests/ -v --tb=short; then
        print_success "All tests passed"
    else
        print_error "Tests failed - deployment aborted"
        exit 1
    fi
else
    print_warning "pytest not found - skipping tests"
fi

# Step 3: Backup database
echo ""
echo "💾 Step 3/7: Backing up database"
echo "--------------------------------"

mkdir -p "$BACKUP_DIR"

if [ -f "hotel.db" ]; then
    cp "hotel.db" "$BACKUP_DIR/hotel.db.$TIMESTAMP"
    print_success "Database backed up to $BACKUP_DIR/hotel.db.$TIMESTAMP"
else
    print_warning "No database found - fresh deployment"
fi

# Step 4: Stop current services
echo ""
echo "🛑 Step 4/7: Stopping services"
echo "-------------------------------"

# Find and kill existing Python processes (backend)
pkill -f "uvicorn app.main:app" || print_warning "No backend process found"
sleep 2
print_success "Services stopped"

# Step 5: Pull latest code (if using git)
echo ""
echo "📥 Step 5/7: Updating code"
echo "--------------------------"

cd ..
if [ -d ".git" ]; then
    git pull origin main
    print_success "Code updated from repository"
else
    print_warning "Not a git repository - skipping"
fi

# Step 6: Install dependencies
echo ""
echo "📦 Step 6/7: Installing dependencies"
echo "------------------------------------"

cd "$BACKEND_DIR"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
else
    print_warning "No requirements.txt found"
fi

# Step 7: Start services
echo ""
echo "🚀 Step 7/7: Starting services"
echo "-------------------------------"

# Start backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Verify backend is running
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    print_success "Backend started successfully (PID: $BACKEND_PID)"
else
    print_error "Backend health check failed"
    cat ../logs/backend.log | tail -20
    exit 1
fi

# Post-deployment verification
echo ""
echo "✅ Post-deployment verification"
echo "================================"

# Check health endpoint
HEALTH_STATUS=$(curl -s http://localhost:8002/health | python -c "import sys, json; print(json.load(sys.stdin)['status'])")

if [ "$HEALTH_STATUS" = "healthy" ]; then
    print_success "System health: $HEALTH_STATUS"
else
    print_warning "System health: $HEALTH_STATUS (check components)"
fi

# Summary
echo ""
echo "📊 Deployment Summary"
echo "====================="
echo "  Backend PID: $BACKEND_PID"
echo "  Backend URL: http://localhost:8002"
echo "  Health Check: http://localhost:8002/health"
echo "  Logs: logs/backend.log"
echo "  Backup: $BACKUP_DIR/hotel.db.$TIMESTAMP"
echo ""
print_success "Deployment complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Monitor logs: tail -f logs/backend.log"
echo "   2. Check health: curl http://localhost:8002/health"
echo "   3. Test endpoints"
echo ""
