# ACP Test Suite Quick Reference

## 🚨 First Time Setup

**Start server on port 8010** (port 8000 is Splunk!):
```powershell
.\scripts\start_server.ps1
```

Update `.env.test`:
```bash
ACP_BASE_URL=http://localhost:8010
```

See [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md) for full guide.

## Essential Commands

```bash
# Full release gate (critical tests only)
python scripts/run_release_gate.py

# All tests including optional
ACP_RUN_PERFORMANCE=true python scripts/run_release_gate.py

# Specific test file
pytest tests/test_03_idempotency.py -v

# Specific test by name
pytest tests/test_01_contract_endpoints.py::test_agent_register_contract -v

# With detailed output
pytest tests/ -vv -s

# Only critical tests (exclude probes/performance)
pytest tests/ -m "contract or safety or idempotency or schema"
```

## Environment Setup

```bash
# Linux/Mac
chmod +x scripts/setup_test_env.sh
./scripts/setup_test_env.sh

# Windows PowerShell
.\scripts\setup_test_env.ps1
```

## Safety Rules

| Environment | Real Booking Tests | Default |
|-------------|-------------------|---------|
| `local` | Allowed with flag | `dry_run=true` |
| `staging` | Allowed with flag | `dry_run=true` |
| `prod` | Blocked | Skipped |

Override: `ACP_ALLOW_REAL_BOOKING_TESTS=true`

## Quick Checks

```python
# Verify idempotency working
pytest tests/test_03_idempotency.py::test_idempotency_duplicate_returns_cached_result -v

# Check API paths match docs
pytest tests/test_00_probes_paths.py -v -s

# Validate commission calculations
cd backend && python validate_commissions_advanced.py

# Test standalone idempotency
cd backend && python test_idempotency_standalone.py
```

## Common Issues

**"No module named 'app'"**  
→ Add `__init__.py` to `tests/` directory

**"Database not found"**  
→ Check `ACP_BACKEND_DIR` env var

**"Connection refused"**  
→ Ensure ACP server running on `ACP_BASE_URL`

**Tests passing but release gate fails**  
→ Check `release_gate_report.json` for critical suite failures

## Full Documentation

See [ACP_TEST_SUITE.md](ACP_TEST_SUITE.md) for complete documentation.
