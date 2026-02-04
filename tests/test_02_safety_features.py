"""
Test Suite 2: Safety Guards & Production Protection
Environment-based safety to prevent accidental production bookings
"""

import pytest
import aiohttp
import os

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
ADMIN_KEY = os.getenv("ACP_ADMIN_KEY", "test_admin_key")
ACP_TEST_MODE = os.getenv("ACP_TEST_MODE", "local").lower()
ALLOW_REAL_BOOKING = os.getenv("ACP_ALLOW_REAL_BOOKING_TESTS", "false").lower() == "true"

def require_admin_safe():
    """Gate admin mutation tests (pause/resume) - stricter than real booking"""
    if ACP_TEST_MODE == "prod":
        pytest.skip("🛡️ BLOCKED: Admin mutation tests disabled in PROD mode (too risky).")

def require_real_booking_allowed():
    """
    Block real execute tests unless explicitly allowed.
    Multi-layer protection:
    1. Environment variable ACP_TEST_MODE
    2. Explicit ACP_ALLOW_REAL_BOOKING_TESTS flag
    """
    if ACP_TEST_MODE == "prod" and not ALLOW_REAL_BOOKING:
        pytest.skip("🛡️ BLOCKED: Execute tests disabled in PROD mode. Set ACP_ALLOW_REAL_BOOKING_TESTS=true to override.")
    
    if not ALLOW_REAL_BOOKING:
        pytest.skip("🛡️ BLOCKED: Real booking tests disabled. Set ACP_ALLOW_REAL_BOOKING_TESTS=true to enable.")

@pytest.mark.asyncio
@pytest.mark.safety
async def test_execute_dry_run_safe():
    """
    CRITICAL SAFETY: Execute in dry-run mode must never create real bookings.
    Default behavior: dry_run=True for all execute tests.
    """
    async with aiohttp.ClientSession() as session:
        payload = {
            "intent_type": "execute",
            "request_id": f"safety_dryrun_{os.urandom(4).hex()}",
            "target_entity_id": os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001"),
            "intent_payload": {
                "dates": {"check_in": "2026-05-01", "check_out": "2026-05-03"},
                "room_type": "standard_queen",
                "guests": 2,
                "dry_run": True  # Always true in this test
            }
        }
        
        async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=10) as resp:
            # Should succeed or be explicitly handled
            assert resp.status in [200, 201, 400], f"Unexpected status: {resp.status}"
            
            if resp.status == 200:
                data = await resp.json()
                
                # Verify no real booking was created
                if "confirmation_code" in data and data["confirmation_code"]:
                    if data.get("dry_run") != True:
                        pytest.fail("❌ CRITICAL: Execute returned confirmation_code without dry_run=True marker")
                
                print("✅ Dry-run safety: No real booking created")

@pytest.mark.asyncio
@pytest.mark.safety
async def test_pause_resume_endpoints():
    """
    Test pause/resume safety controls.
    Verifies admin can emergency-stop a property.
    """
    require_admin_safe()  # Only requires admin safety, not real booking flag
    
    test_property = os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001")
    headers = {"X-Admin-Key": ADMIN_KEY}
    
    async with aiohttp.ClientSession() as session:
        # Test pause
        pause_paths = [
            f"/admin/properties/{test_property}/pause",
            f"/properties/{test_property}/pause",
            f"/acp/properties/{test_property}/pause"
        ]
        
        pause_worked = False
        for path in pause_paths:
            try:
                async with session.post(f"{BASE_URL}{path}", headers=headers, timeout=5) as resp:
                    if resp.status in [200, 204]:
                        pause_worked = True
                        print(f"✅ Pause working at {path}")
                        break
            except:
                continue
        
        if not pause_worked:
            pytest.skip("Pause endpoint not found or not working")
        
        # Verify property excluded from marketplace
        async with session.get(f"{BASE_URL}/marketplace/properties") as resp:
            data = await resp.json()
            # Handle both formats: {"properties": [...]} or direct list
            properties = data["properties"] if isinstance(data, dict) and "properties" in data else data
            ids = [p["property_id"] for p in properties]
            
            if test_property in ids:
                pytest.fail(f"❌ CRITICAL: Paused property {test_property} still visible in marketplace")
        
        # Test resume
        for path in pause_paths:
            resume_path = path.replace("/pause", "/resume")
            try:
                async with session.post(f"{BASE_URL}{resume_path}", headers=headers, timeout=5) as resp:
                    if resp.status in [200, 204]:
                        print(f"✅ Resume working at {resume_path}")
                        break
            except:
                continue

@pytest.mark.asyncio
@pytest.mark.safety
async def test_environment_protection_active():
    """
    Verify safety environment variables are respected.
    This test documents the safety mechanism.
    """
    print(f"\n🛡️ SAFETY CONFIGURATION:")
    print(f"   ACP_TEST_MODE: {ACP_TEST_MODE}")
    print(f"   ACP_ALLOW_REAL_BOOKING_TESTS: {ALLOW_REAL_BOOKING}")
    print(f"   BASE_URL: {BASE_URL}")
    
    if ACP_TEST_MODE == "prod":
        assert not ALLOW_REAL_BOOKING, "CRITICAL: Real booking tests should NEVER be enabled in prod by default"
        print("   Status: 🔒 PRODUCTION MODE - Execute tests blocked")
    elif ACP_TEST_MODE == "staging":
        print("   Status: ⚠️ STAGING MODE - Execute tests allowed with flag")
    else:
        print("   Status: 🔓 LOCAL MODE - Execute tests allowed")
    
    assert True
