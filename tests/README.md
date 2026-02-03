# ACP Test Suite Implementation

This directory contains comprehensive tests for the ACP (Agent Communication Protocol) system.

## 📁 Structure

```
tests/
├── test_00_probes_paths.py       # Path discovery (non-failing)
├── test_01_contract_endpoints.py # API contract validation
├── test_02_safety_features.py    # Safety guards & dry-run
├── test_03_idempotency.py        # Caching validation
├── test_04_database_schema.py    # Schema verification
└── test_99_performance.py        # Performance diagnostics

scripts/
├── run_release_gate.py           # GO/NO-GO automation
├── setup_test_env.sh             # Linux/Mac setup
└── setup_test_env.ps1            # Windows setup

backend/
├── test_idempotency_standalone.py    # Standalone idempotency
└── validate_commissions_advanced.py   # Commission validator
```

## 🚀 Quick Start

```powershell
# 1. Setup
.\scripts\setup_test_env.ps1

# 2. Configure
$env:ACP_BASE_URL="http://localhost:8000"
$env:ACP_TEST_MODE="local"

# 3. Run
python scripts\run_release_gate.py
```

## 📚 Documentation

- **[ACP_TEST_SUITE.md](../ACP_TEST_SUITE.md)** - Complete documentation
- **[QUICK_REFERENCE_TESTS.md](../QUICK_REFERENCE_TESTS.md)** - Quick reference

## 🧪 Test Categories

**Critical (Required for release)**
- ✅ Contract endpoints
- ✅ Safety features
- ✅ Idempotency
- ✅ Database schema

**Informational**
- 📊 Probes (path discovery)
- ⚡ Performance (optional)

## ⚠️ Safety

All tests use `dry_run=True` by default in local/staging environments. Production execute tests are blocked unless explicitly enabled via `ACP_ALLOW_REAL_BOOKING_TESTS=true`.

## 🔗 See Also

- `.env.test.example` - Environment configuration template
- `pytest.ini` - Pytest configuration
