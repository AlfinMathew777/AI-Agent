# Phase 3B Safety Features - Quick Reference

## Completed Safety Implementations

### 1. Dry-Run Mode ✅
**File**: `app/acp/domains/hotel/cloudbeds_adapter.py`

**Usage**:
```python
# Test booking WITHOUT creating it
result = await adapter.execute(tx, request, dry_run=True)
# Returns: {"success": True, "dry_run": True, "would_create_booking": True, "validation": "passed"}
```

**Benefits**:
- Test integration end-to-end
- Validate payloads before real bookings
- Safe onboarding testing

---

### 2. Rate Limit Backoff ✅
**File**: `app/acp/domains/hotel/cloudbeds_adapter.py` (`_make_request`)

**Behavior**:
- Detects 429 rate limit responses
- Retries with exponential backoff: 1s → 2s → 4s
- Logs each retry attempt
- Fails gracefully after 3 attempts

**Benefits**:
- Handles Cloudbeds API rate limits automatically
- Prevents cascading failures
- Maintains system stability

---

### 3. Pause/Resume Controls ✅
**File**: `app/acp/api/routes/properties.py`

**Endpoints**:
```bash
# Pause property (emergency stop)
POST /admin/properties/{property_id}/pause
{
  "reason": "PMS integration issue detected"
}

# Resume property
POST /admin/properties/{property_id}/resume
```

**Effects of Pause**:
- Property `is_active = 0`
- Does NOT appear in marketplace
- Cross-property search skips it
- Existing bookings unaffected

---

### 4. Emergency Rollback Script ✅
**File**: `rollback_property.py`

**Usage**:
```bash
# Rollback with reason
python rollback_property.py "PMS API unreliable"

# Rollback default property
python rollback_property.py

# Resume property
python rollback_property.py --resume
```

**Safety**:
- Requires typed confirmation: "ROLLBACK"
- Logs to monitoring database
- Detailed status reporting
- Reversible with --resume flag

---

## Testing the Safety Features

### Test Dry-Run Mode
```python
# In Python REPL or test script
import asyncio
from app.acp.domains.hotel.cloudbeds_adapter import CloudbedsAdapter

async def test_dry_run():
    adapter = CloudbedsAdapter()
    await adapter.initialize()
    
    # Create mock transaction and request
    class MockTx:
        tx_id = "test_123"
        target_entity_id = "cloudbeds_001"
        final_offer = {"total_price": 450.00}
    
    class MockRequest:
        intent_payload = {
            "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
            "room_type": "standard_queen",
            "guests": 2
        }
    
    # DRY RUN
    result = await adapter.execute(MockTx(), MockRequest(), dry_run=True)
    print(result)
    # Expected: {"success": True, "dry_run": True, "would_create_booking": True}

asyncio.run(test_dry_run())
```

### Test Rate Limit Handling
```python
# Manually test by hitting Cloudbeds API repeatedly
# Or mock 429 response in tests
# Logs should show: "[Cloudbeds] Rate limit hit, retrying in 1.0s (attempt 1/3)"
```

### Test Pause/Resume
```bash
# Pause property
curl -X POST http://localhost:8000/admin/properties/cloudbeds_001/pause \
  -H "x-admin-key: $ADMIN_API_KEY" \
  -d '{"reason": "Testing pause feature"}'

# Verify not in marketplace
curl http://localhost:8000/marketplace/properties | grep cloudbeds_001
# Should return nothing

# Resume
curl -X POST http://localhost:8000/admin/properties/cloudbeds_001/resume \
  -H "x-admin-key: $ADMIN_API_KEY"

# Verify back in marketplace
curl http://localhost:8000/marketplace/properties | grep cloudbeds_001
# Should return property
```

### Test Rollback Script
```bash
# Test rollback (will prompt for confirmation)
python rollback_property.py "Testing rollback script"
# Type: ROLLBACK

# Verify property paused
python -c "from app.properties.registry import PropertyRegistry; r = PropertyRegistry(); p = r.get_property('cloudbeds_001'); print(f'Active: {p.is_active if p else 'Not found'}')"
# Expected: Active: 0

# Test resume
python rollback_property.py --resume
# Type: RESUME
```

---

## Integration with Existing Features

### Circuit Breaker (Already Exists)
- Trips after 3 consecutive failures
- 60-second timeout
- Auto-recovery in half-open state
- **Complements** rate limit backoff

### OAuth Token Management (Already Exists)
- Auto-refresh with 60s buffer
- Sandbox mode support
- **Works with** dry-run mode (uses sandbox in test)

### Inventory Cache (Already Exists)
- 120-second TTL
- Invalidates on booking
- **Unaffected by** pause/resume (still caches)

---

## Production Readiness Checklist

- [x] Dry-run mode implemented and tested
- [x] Rate limit backoff with exponential delays
- [x] Pause/resume admin endpoints functional
- [x] Emergency rollback script with confirmation
- [ ] Idempotency support (next task)
- [ ] Comprehensive integration tests
- [ ] Monitoring alerts configured
- [ ] Runbook updated with safety procedures

---

## Next Safety Feature: Idempotency

**Status**: Not yet implemented  
**Priority**: High  
**File**: `app/acp/transaction/manager.py`

**Requirements**:
1. Use `request_id` as idempotency key
2. Store result in `acp_transactions.db`
3. Return cached result for duplicate requests
4. Prevent double-bookings

**Implementation**:
```python
# In execute_transaction():
async def execute_transaction(self, tx_id: str):
    tx = self.get_transaction(tx_id)
    
    # Check idempotency
    existing = self._check_idempotency(tx.request_id)
    if existing:
        return existing["result"]  # Return previous result
    
    # Execute
    result = await self._execute_with_adapter(tx)
    
    # Store for idempotency
    self._store_idempotency_result(tx.request_id, result)
    
    return result
```

---

## Emergency Response Procedures

### If Cloudbeds Property Has Issues

1. **Immediate**: Pause via API or rollback script
   ```bash
   python rollback_property.py "PMS sync failing"
   ```

2. **Investigate**: Check logs, monitoring dashboard, PMS status

3. **Fix**: Address root cause (credentials, API issues, etc.)

4. **Test**: Use dry-run mode to verify fix
   ```python
   result = await adapter.execute(tx, request, dry_run=True)
   ```

5. **Resume**: When safe, resume property
   ```bash
   curl -X POST /admin/properties/cloudbeds_001/resume
   ```

6. **Monitor**: Watch for 1 hour, verify stability

---

**Status**: 4/5 safety features complete (dry-run ✅, rate limit ✅, pause/resume ✅, rollback ✅, idempotency ⏳)
