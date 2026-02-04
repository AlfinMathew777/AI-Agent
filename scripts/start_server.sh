#!/bin/bash
# Start ACP Server on Port 8010 (avoiding Splunk on 8000)

echo "🚀 Starting ACP Server"
echo "================================"

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ ERROR: backend/ directory not found"
    echo "   Run this script from the project root"
    exit 1
fi

# Check if uvicorn is installed
if ! python3 -m uvicorn --version &> /dev/null; then
    echo "❌ ERROR: uvicorn not installed"
    echo "   Run: pip install uvicorn fastapi aiohttp"
    exit 1
fi

echo ""
echo "⚠️  PORT NOTICE:"
echo "   Port 8000 is occupied by Splunk"
echo "   Starting ACP on port 8010 instead"
echo ""

# Start server
echo "Starting server on http://localhost:8010..."
echo ""
echo "📖 API Documentation: http://localhost:8010/docs"
echo "🔍 Alternative docs:   http://localhost:8010/redoc"
echo ""
echo "Press CTRL+C to stop"
echo ""

cd backend
python3 -m uvicorn app.main:app --reload --port 8010
