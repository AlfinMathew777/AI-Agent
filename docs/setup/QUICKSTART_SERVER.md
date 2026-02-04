# ACP Server Quick Start Guide

## ⚠️ Port Conflict Warning

**Port 8000 is occupied by Splunk on your system!**

If you see "Oops. Page not found!" or `/en-GB/` URLs, you're hitting Splunk, not ACP.

## ✅ Correct Startup

### 1. Start ACP Server on Port 8010

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8010
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8010 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 2. Verify Server is Running

**Open in browser**: http://localhost:8010/docs

You should see **FastAPI Swagger UI** with your endpoints listed.

### 3. Quick Smoke Test in Swagger UI

1. Find **POST /acp/submit** endpoint
2. Click **"Try it out"**
3. Use this payload:
```json
{
  "intent_type": "discover",
  "target_entity_id": "*",
  "intent_payload": {
    "dates": {
      "check_in": "2026-05-01",
      "check_out": "2026-05-03"
    },
    "location": "Hobart"
  }
}
```
4. Click **Execute**
5. Should return list of properties

### 4. Update Test Configuration

Edit `.env.test`:
```bash
ACP_BASE_URL=http://localhost:8010  # NOT 8000!
ACP_PREFIX=/acp
ACP_ADMIN_KEY=your_actual_admin_key
```

### 5. Run Tests

```powershell
# Path discovery
pytest tests/test_00_probes_paths.py -v -s

# Full release gate
python scripts/run_release_gate.py
```

## 🎥 Demo Flow (Professional)

### Terminal Window
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8010
```

### Browser Window (http://localhost:8010/docs)
1. **Discover Intent**: Shows 5 properties
2. **Negotiate Intent**: Shows accepted/countered offer
3. **Execute Intent** (dry_run=true): Shows no real booking created

### Back to Terminal
```powershell
cd ..
python scripts/run_release_gate.py
```

### Show Results
```powershell
cat release_gate_report.json
```

Look for:
```json
{
  "decision": "GO",
  "reason": "All critical test suites passed",
  ...
}
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Address already in use` | Port 8010 also taken? Try 8011, 8012, etc. |
| `ModuleNotFoundError: app` | You're not in `backend/` directory |
| Tests hit Splunk | Check `ACP_BASE_URL` in `.env.test` |
| `Connection refused` | Server not running or wrong port |

## 📝 Common Ports on Your System

- **8000**: Splunk Web ❌ Don't use for ACP
- **8010**: Recommended for ACP ✅
- **5173**: Vite dev server (if using)

## Quick Verification Commands

```powershell
# Check if port 8010 is working
curl http://localhost:8010/docs

# Check if server responds to health check (if you have one)
curl http://localhost:8010/health

# Test with actual payload
curl -X POST http://localhost:8010/acp/submit \
  -H "Content-Type: application/json" \
  -d '{"intent_type":"discover","target_entity_id":"*","intent_payload":{"dates":{"check_in":"2026-05-01","check_out":"2026-05-03"}}}'
```

**You're all set!** 🚀
