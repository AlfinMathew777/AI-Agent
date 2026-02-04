# ACP Complete Test Suite Documentation

## ⚠️ IMPORTANT: Server Startup

**Port 8000 is occupied by Splunk on your system!**

Before running tests, start the ACP server on a different port:
```powershell
.\scripts\start_server.ps1  # Windows
# OR
./scripts/start_server.sh   # Linux/Mac
```

Server will run on **http://localhost:8010**. See [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md) for details.

## Overview

This test suite provides comprehensive validation of the Agent Communication Protocol (ACP) implementation, with special focus on documentation-to-code alignment and production safety.

## Test Structure

### 1. Path Discovery (`test_00_probes_paths.py`)
**Purpose**: Discover actual API paths without breaking CI/CD  
**Behavior**: Never fails, reports findings for documentation updates

Tests:
- `test_probe_agent_registration_paths()`: Finds working registration endpoints
- `test_probe_marketplace_paths()`: Discovers marketplace routes  
- `test_probe_monitoring_paths()`: Locates admin dashboard paths

### 2. Contract Validation (`test_01_contract_endpoints.py`)
**Purpose**: Enforce API contract integrity  
**Behavior**: Fails if contracts break (blocks release)

Critical tests:
- Agent registration must work
- Discover intent must return properties array
- Negotiate intent must return valid offers
- Execute dry-run must validate safely

### 3. Safety Features (`test_02_safety_features.py`)
**Purpose**: Validate production safety mechanisms

Environment-based guards:
```python
ACP_TEST_MODE = os.getenv("ACP_TEST_MODE", "local")
ALLOW_REAL = os.getenv("ACP_ALLOW_REAL_BOOKING_TESTS", "false") == "true"
```
Tests block real bookings in production unless explicitly enabled.

### 4. Idempotency (`test_03_idempotency.py`)
**Purpose**: Prevent duplicate bookings and commissions  
Critical validations:
- Duplicate request_id returns cached result
- Different request_ids create separate entries
- Database schema supports idempotency

### 5. Database Schema (`test_04_database_schema.py`)
**Purpose**: Validate all 6 ACP databases  
Validates:
- All databases exist
- Tables have required columns
- Indexes are present
- Data integrity constraints

### 6. Performance (`test_99_performance.py`)
**Purpose**: Measure against documented claims (200-300ms latency, 100+ rps)  
Optional: Only runs when `ACP_RUN_PERFORMANCE=true`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ACP_BASE_URL` | `http://localhost:8000` | Server base URL |
| `ACP_ADMIN_KEY` | `test_admin_key` | Admin API key |
| `ACP_TEST_MODE` | `local` | Test environment mode |
| `ACP_ALLOW_REAL_BOOKING_TESTS` | `false` | Enable real booking tests |
| `ACP_TEST_PROPERTY_ID` | `cloudbeds_001` | Test property ID |
| `ACP_RUN_PERFORMANCE` | `false` | Enable performance tests |
| `ACP_BACKEND_DIR` | `backend` | Backend directory path |

## Release Gate

The `run_release_gate.py` script automates GO/NO-GO decisions:

```bash
# Standard run
python scripts/run_release_gate.py

# With performance validation
ACP_RUN_PERFORMANCE=true python scripts/run_release_gate.py
```

Output: `release_gate_report.json` with decision and details.

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: ACP Release Gate

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Setup Environment
        run: |
          chmod +x scripts/setup_test_env.sh
          ./scripts/setup_test_env.sh
      
      - name: Start ACP Server
        run: |
          cd backend
          python -m uvicorn app.main:app --reload &
          sleep 5
      
      - name: Run Release Gate
        run: |
          source venv/bin/activate
          python scripts/run_release_gate.py
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: release-gate-report
          path: release_gate_report.json
```

## Troubleshooting

**Issue**: Tests can't find backend modules  
**Solution**: Ensure `__init__.py` exists in `tests/` directory

**Issue**: Database locked errors  
**Solution**: Close any open database connections before running tests

**Issue**: Performance tests timeout  
**Solution**: Increase timeout in `pytest.ini` or reduce concurrency

**Issue**: "Blocked execute tests in PROD"  
**Solution**: This is expected safety behavior. Set `ACP_ALLOW_REAL_BOOKING_TESTS=true` only when intentionally testing real bookings.
