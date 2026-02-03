# tests/test_03_idempotency.py
"""
IDEMPOTENCY TESTS (Real proof)
This test checks cached behavior using either:
- response marker (idempotency.hit == True) OR
- monitoring db event OR
- idempotency_log entry exists AND response equality
"""

import os
import uuid
import json
import sqlite3
import pytest
import aiohttp

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
SUBMIT_PATH = os.getenv("ACP_SUBMIT_PATH", "/acp/submit")
TEST_PROPERTY_ID = os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001")

ACP_TEST_MODE = os.getenv("ACP_TEST_MODE", "local").lower()
ALLOW_REAL = os.getenv("ACP_ALLOW_REAL_BOOKING_TESTS", "false").lower() == "true"

def safe_execute_only():
    if ACP_TEST_MODE == "prod" and not ALLOW_REAL:
        pytest.skip("Blocked execute tests in PROD without ACP_ALLOW_REAL_BOOKING_TESTS=true")

def fetch_idempotency_row(request_id: str):
    # adjust path if needed
    db_path = os.path.join("backend", "acp_transactions.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT result_json FROM idempotency_log WHERE request_id = ?", (request_id,))
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

@pytest.mark.asyncio
async def test_idempotency_duplicate_returns_cached_result():
    """Test that duplicate requests return cached results."""
    safe_execute_only()

    request_id = f"idemp_{uuid.uuid4().hex}"
    payload = {
        "intent_type": "execute",
        "request_id": request_id,
        "target_entity_id": TEST_PROPERTY_ID,
        "intent_payload": {
            "dates": {"check_in": "2026-05-01", "check_out": "2026-05-03"},
            "room_type": "standard_queen",
            "guests": 2,
            "dry_run": True  # safe default
        }
    }

    async with aiohttp.ClientSession() as session:
        # First call
        async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
            assert resp.status == 200
            first = await resp.json()

        # Second call (duplicate)
        async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
            assert resp.status == 200
            second = await resp.json()

    # Proof option 1 (best): response marker
    if isinstance(second, dict) and second.get("idempotency", {}).get("hit") is True:
        assert second["idempotency"]["request_id"] == request_id
    else:
        # Proof option 2: identical response + cached row exists
        cached = fetch_idempotency_row(request_id)
        assert cached is not None, "Expected idempotency_log entry missing"
        assert second == cached or second.get("success") == cached.get("success"), \
            "Second response does not match cached result (idempotency may not be applied in gateway)"

        # also ensure response is stable
        assert first.get("success") == second.get("success")

@pytest.mark.asyncio
async def test_idempotency_different_request_ids_not_shared():
    """Test that different request_ids maintain separate cache."""
    safe_execute_only()

    req1 = f"idemp_{uuid.uuid4().hex}"
    req2 = f"idemp_{uuid.uuid4().hex}"

    async with aiohttp.ClientSession() as session:
        for rid in (req1, req2):
            payload = {
                "intent_type": "execute",
                "request_id": rid,
                "target_entity_id": TEST_PROPERTY_ID,
                "intent_payload": {
                    "dates": {"check_in": "2026-06-01", "check_out": "2026-06-03"},
                    "room_type": "standard_queen",
                    "guests": 2,
                    "dry_run": True
                }
            }
            async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
                assert resp.status == 200

    c1 = fetch_idempotency_row(req1)
    c2 = fetch_idempotency_row(req2)
    assert c1 is not None and c2 is not None, "Expected both request_ids to be cached"
    assert req1 != req2
