# ACP Test Suite - Quick Reference

## 🚀 Quick Start

### Setup (Windows)
```powershell
.\scripts\setup_test_env.ps1

$env:ACP_BASE_URL="http://localhost:8000"
$env:ACP_ADMIN_KEY="your_admin_key"
$env:ACP_TEST_MODE="local"
$env:ACP_TEST_PROPERTY_ID="cloudbeds_001"
```

## 🧪 Common Commands

### Release Gate (GO/NO-GO)
```powershell
python scripts\run_release_gate.py
```

### Individual Test Suites
```powershell
# Path discovery (non-failing)
pytest -v tests/test_00_probes_paths.py

# Contract validation (STRICT)
pytest -v tests/test_01_contract_endpoints.py

# Safety features
pytest -v tests/test_02_safety_features.py

# Idempotency
pytest -v tests/test_03_idempotency.py

# Database schema
pytest -v tests/test_04_database_schema.py

# Performance (optional)
pytest -m performance -v tests/test_99_performance.py
```

### Standalone Validators
```powershell
# Idempotency standalone test
python backend\test_idempotency_standalone.py

# Commission validator
python backend\validate_commissions_advanced.py
```

## 📋 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ACP_BASE_URL` | ✅ | - | Server base URL |
| `ACP_ADMIN_KEY` | ✅ | - | Admin key |
| `ACP_TEST_MODE` | ✅ | `local` | `local`, `staging`, `prod` |
| `ACP_TEST_PROPERTY_ID` | ✅ | `cloudbeds_001` | Test property |
| `ACP_ALLOW_REAL_BOOKING_TESTS` | ❌ | `false` | Enable prod bookings |
| `ACP_RUN_PERFORMANCE` | ❌ | `false` | Include perf tests |

## ⚠️ Safety Rules

1. ✅ **Local/Staging**: Always use `dry_run=True`
2. 🔒 **Production**: Execute tests BLOCKED unless explicitly allowed
3. ⚡ **Never** set `ACP_ALLOW_REAL_BOOKING_TESTS=true` without review

## 📊 Test Categories

| Test | Critical | Purpose |
|------|----------|---------|
| **Probes** | ❌ | Discover working paths |
| **Contract** | ✅ | Validate API contracts |
| **Safety** | ✅ | Verify safety guards |
| **Idempotency** | ✅ | Check caching |
| **Schema** | ✅ | Database validation |
| **Performance** | ❌ | Latency diagnostics |

## 🎯 Release Gate Decision

**✅ GO**: All critical tests pass  
**❌ NO-GO**: Any critical test fails

Critical tests:
- Contract endpoints
- Safety features
- Idempotency
- Database schema

## 🔍 Troubleshooting

### Connection Refused
```powershell
# Verify server is running
curl http://localhost:8000/health

# Start backend
cd backend
python -m uvicorn app.main:app --reload
```

### Idempotency Test Fails
```powershell
# Check database exists
ls backend\acp_transactions.db

# Verify table structure
sqlite3 backend\acp_transactions.db "PRAGMA table_info(idempotency_log)"
```

### Path Probes Empty
```powershell
# Check server logs
# Review router mount prefixes in app/main.py
```

## 📖 Full Documentation

See [ACP_TEST_SUITE.md](ACP_TEST_SUITE.md) for complete documentation.
