# ACP Test Suite Documentation

## Overview

This comprehensive test suite provides automated validation for the ACP (Agent Communication Protocol) system with environment-based safety features, idempotency validation, and release gate automation.

## Test Structure

```
/tests
  test_00_probes_paths.py       # Non-failing path discovery
  test_01_contract_endpoints.py # Strict API contract validation
  test_02_safety_features.py    # Dry-run & safety guards
  test_03_idempotency.py         # Cached behavior validation
  test_04_database_schema.py     # Schema validation
  test_99_performance.py         # Latency diagnostics (optional)

/scripts
  run_release_gate.py            # GO/NO-GO decision engine
  setup_test_env.sh             # Linux/Mac setup
  setup_test_env.ps1            # Windows setup

/backend
  test_idempotency_standalone.py # Standalone idempotency tests
  validate_commissions_advanced.py # Commission validator
```

## Quick Start

### 1. Setup Environment (Windows)

```powershell
# Run setup script
.\scripts\setup_test_env.ps1

# OR manually:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install pytest pytest-asyncio aiohttp requests
```

### 2. Configure Environment Variables

```powershell
# Copy example configuration
Copy-Item .env.test.example .env.test

# Set environment variables
$env:ACP_BASE_URL="http://localhost:8000"
$env:ACP_ADMIN_KEY="your_admin_key"
$env:ACP_TEST_MODE="local"
$env:ACP_ALLOW_REAL_BOOKING_TESTS="false"
$env:ACP_TEST_PROPERTY_ID="cloudbeds_001"
```

### 3. Run Tests

```powershell
# Run all critical tests via release gate
python scripts/run_release_gate.py

# Run specific test suite
pytest -v tests/test_01_contract_endpoints.py

# Run with performance tests
$env:ACP_RUN_PERFORMANCE="true"
python scripts/run_release_gate.py
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ACP_BASE_URL` | ACP server base URL | `http://localhost:8000` |
| `ACP_ADMIN_KEY` | Admin authentication key | `your_admin_key` |
| `ACP_TEST_MODE` | Test environment mode | `local`, `staging`, `prod` |
| `ACP_TEST_PROPERTY_ID` | Property ID for testing | `cloudbeds_001` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACP_ALLOW_REAL_BOOKING_TESTS` | Allow real bookings in prod | `false` |
| `ACP_RUN_PERFORMANCE` | Include performance tests | `false` |
| `ACP_AGENT_REGISTER_PATH` | Agent registration endpoint | `/acp/register` |
| `ACP_SUBMIT_PATH` | Intent submission endpoint | `/acp/submit` |

## Safety Features

### Dry-Run Mode
- **Local/Staging**: Execute tests MUST use `dry_run=True`
- **Production**: Execute tests are BLOCKED unless `ACP_ALLOW_REAL_BOOKING_TESTS=true`
- Prevents accidental real bookings during testing

### Test Mode Guards
```python
def require_safe_execute():
    """Block real execute unless explicitly allowed."""
    if ACP_TEST_MODE == "prod" and not ALLOW_REAL:
        pytest.skip("Blocked execute tests in PROD")
```

## Test Suites

### 1. Probes (test_00_probes_paths.py)
**Purpose**: Non-failing path discovery  
**Behavior**: Identifies working API endpoints without causing test failures  
**Use Case**: Update documentation if probes discover different paths

```powershell
pytest -v tests/test_00_probes_paths.py
```

### 2. Contract Endpoints (test_01_contract_endpoints.py)
**Purpose**: Strict API contract validation  
**Behavior**: FAILS if core API contracts break  
**Critical**: ✅ Required for release gate

**Tests**:
- Agent registration contract
- Discover intent contract
- Negotiate intent contract

### 3. Safety Features (test_02_safety_features.py)
**Purpose**: Validate safety guards  
**Behavior**: Ensures dry-run works and production guards are active  
**Critical**: ✅ Required for release gate

**Tests**:
- Dry-run execution safety
- Pause/resume endpoints

### 4. Idempotency (test_03_idempotency.py)
**Purpose**: Validate caching behavior  
**Behavior**: Ensures duplicate requests return cached results  
**Critical**: ✅ Required for release gate

**Validation Methods**:
1. Response marker (`idempotency.hit == True`)
2. Database cache entry verification
3. Response equality check

### 5. Database Schema (test_04_database_schema.py)
**Purpose**: Schema validation  
**Behavior**: Verifies database tables and indexes exist  
**Critical**: ✅ Required for release gate

**Validates**:
- All 6 ACP databases exist
- Properties table schema
- Idempotency_log table schema
- Required indexes

### 6. Performance (test_99_performance.py)
**Purpose**: Latency diagnostics  
**Behavior**: Reports performance metrics, doesn't enforce hard limits  
**Critical**: ❌ Optional (run via `ACP_RUN_PERFORMANCE=true`)

```powershell
pytest -m performance -v tests/test_99_performance.py
```

## Standalone Validators

### Backend Idempotency Test
```powershell
python backend/test_idempotency_standalone.py
```

Tests idempotency at the manager level:
- Store and retrieve results
- Dry-run caching
- Failed result handling
- Cleanup operations

### Commission Validator
```powershell
python backend/validate_commissions_advanced.py
```

Validates:
- Ledger internal consistency
- Commission rate tier compliance
- Property-level aggregation
- Data integrity

## Release Gate

The release gate automation provides a GO/NO-GO decision based on test results.

### Run Release Gate

```powershell
python scripts/run_release_gate.py
```

### Decision Logic

**GO**: All critical suites pass
- ✅ Contract endpoints
- ✅ Safety features
- ✅ Idempotency
- ✅ Database schema

**NO-GO**: Any critical suite fails

### Report Output

Results saved to `release_gate_report.json`:

```json
{
  "timestamp": "2026-02-03T14:30:00",
  "decision": "GO",
  "reason": "All critical suites passed",
  "env": {
    "ACP_BASE_URL": "http://localhost:8000",
    "ACP_TEST_MODE": "local"
  },
  "suites": [...]
}
```

## Common Workflows

### Pre-Deployment Validation
```powershell
# 1. Start ACP server
cd backend
python -m uvicorn app.main:app --reload

# 2. Set environment
$env:ACP_BASE_URL="http://localhost:8000"
$env:ACP_TEST_MODE="local"

# 3. Run release gate
python scripts/run_release_gate.py

# 4. Review report
cat release_gate_report.json
```

### Fix Documentation Mismatch
```powershell
# 1. Run probes to discover working paths
pytest -v tests/test_00_probes_paths.py

# 2. Check output for working paths
# [PROBE] Agent register working paths: [('/acp/register', 200)]

# 3. Update documentation if needed
```

### Staging Validation
```powershell
$env:ACP_BASE_URL="https://staging.example.com"
$env:ACP_TEST_MODE="staging"
python scripts/run_release_gate.py
```

### Production Smoke Test (Safe)
```powershell
# Execute tests are automatically blocked in prod
$env:ACP_BASE_URL="https://prod.example.com"
$env:ACP_TEST_MODE="prod"
$env:ACP_ALLOW_REAL_BOOKING_TESTS="false"

# Only runs safe tests (discover, negotiate, schema)
python scripts/run_release_gate.py
```

## Troubleshooting

### Tests Fail with Connection Errors
**Issue**: Cannot connect to `ACP_BASE_URL`  
**Solution**: 
- Verify server is running
- Check `ACP_BASE_URL` is correct
- Ensure firewall allows connections

### Idempotency Tests Fail
**Issue**: No cached results found  
**Solution**:
- Check `acp_transactions.db` exists
- Verify database path in test
- Ensure idempotency_log table exists

### Path Probes Return Empty
**Issue**: No working paths discovered  
**Solution**:
- Verify server is running
- Check router mount prefixes
- Review server logs for errors

### Permission Errors in Production
**Issue**: Tests blocked in production  
**Solution**:
- This is expected behavior (safety feature)
- Set `ACP_ALLOW_REAL_BOOKING_TESTS=true` only if intentional
- Review test mode setting

## Best Practices

1. **Always use dry_run=True in local/staging**
2. **Never set ALLOW_REAL_BOOKING_TESTS=true in prod without review**
3. **Run release gate before deployment**
4. **Update probes output in documentation**
5. **Review commission validator monthly**
6. **Keep performance tests optional**
7. **Version control release gate reports**

## CI/CD Integration

### GitHub Actions Example

```yaml
name: ACP Release Gate

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio aiohttp requests
      
      - name: Start ACP Server
        run: |
          cd backend
          python -m uvicorn app.main:app &
          sleep 5
      
      - name: Run Release Gate
        env:
          ACP_BASE_URL: http://localhost:8000
          ACP_TEST_MODE: local
          ACP_ADMIN_KEY: ${{ secrets.ACP_ADMIN_KEY }}
        run: python scripts/run_release_gate.py
      
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: release-gate-report
          path: release_gate_report.json
```

## Support

For issues or questions:
1. Check `release_gate_report.json` for detailed output
2. Review server logs
3. Verify environment variables
4. Run individual test suites for debugging
5. Check probe output for path mismatches
