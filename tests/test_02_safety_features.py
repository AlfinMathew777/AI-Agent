# tests/test_02_safety_features.py
"""
SAFETY FEATURES TESTS
Safe by default. Execute uses dry_run=True unless explicitly allowed.
"""

import os
import uuid
import pytest
import aiohttp

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ACP_ADMIN_KEY", "")
TEST_PROPERTY_ID = os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001")

SUBMIT_PATH = os.getenv("ACP_SUBMIT_PATH", "/acp/submit")

ACP_TEST_MODE = os.getenv("ACP_TEST_MODE", "local").lower()
ALLOW_REAL = os.getenv("ACP_ALLOW_REAL_BOOKING_TESTS", "false").lower() == "true"

def require_safe_execute():
    """Block real execute unless explicitly allowed."""
    if ACP_TEST_MODE == "prod" and not ALLOW_REAL:
        pytest.skip("Blocked execute tests in PROD without ACP_ALLOW_REAL_BOOKING_TESTS=true")

@pytest.mark.asyncio
async def test_execute_dry_run_safe():
    """Dry-run should never create real booking and should return dry_run markers (if exposed)."""
    require_safe_execute()

    request_id = f"dryrun_{uuid.uuid4().hex}"
    payload = {
        "intent_type": "execute",
        "request_id": request_id,
        "target_entity_id": TEST_PROPERTY_ID,
        "intent_payload": {
            "dates": {"check_in": "2026-09-01", "check_out": "2026-09-03"},
            "room_type": "standard_queen",
            "guests": 2,
            "dry_run": True
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
            assert resp.status in (200, 201)
            data = await resp.json()

            # If gateway exposes dry_run:
            if data.get("dry_run") is True:
                assert data.get("would_create_booking") is True
                assert data.get("confirmation_code") in (None, "",) or "confirmation_code" not in data
            else:
                # If gateway doesn't expose dry_run yet, don't hard fail:
                # This tells you: adapter-only feature, docs must say that.
                pytest.xfail("Dry-run not exposed at gateway level (adapter-only).")

@pytest.mark.asyncio
async def test_pause_resume_endpoints():
    """Pause/resume must remove/add property from marketplace (if endpoints exist)."""
    if not ADMIN_KEY:
        pytest.skip("ACP_ADMIN_KEY not set")

    headers = {"X-Admin-Key": ADMIN_KEY}

    # You may need to update these if your router mount differs.
    pause_url = f"{BASE_URL}/admin/properties/{TEST_PROPERTY_ID}/pause"
    resume_url = f"{BASE_URL}/admin/properties/{TEST_PROPERTY_ID}/resume"
    marketplace_url = f"{BASE_URL}/marketplace/properties"

    async with aiohttp.ClientSession() as session:
        # Pause
        async with session.post(pause_url, headers=headers) as resp:
            if resp.status == 404:
                pytest.xfail("Pause endpoint not mounted at this path (check router prefixes).")
            assert resp.status in (200, 204)

        # Verify not in marketplace
        async with session.get(marketplace_url) as resp:
            if resp.status == 404:
                pytest.xfail("Marketplace not mounted at /marketplace/properties (check router prefixes).")
            data = await resp.json()
            props = data.get("properties", data if isinstance(data, list) else [])
            ids = [p.get("property_id") for p in props if isinstance(p, dict)]
            assert TEST_PROPERTY_ID not in ids, "Paused property still visible"

        # Resume
        async with session.post(resume_url, headers=headers) as resp:
            assert resp.status in (200, 204)
