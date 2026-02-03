#!/bin/bash
set -e

echo "🛠️ Setting up ACP Test Environment..."

python -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install pytest pytest-asyncio aiohttp requests

echo "✅ Done."
echo "Next:"
echo "  export ACP_BASE_URL=http://localhost:8000"
echo "  export ACP_ADMIN_KEY=..."
echo "  export ACP_TEST_MODE=local"
echo "  python scripts/run_release_gate.py"
