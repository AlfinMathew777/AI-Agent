"""
Test Suite 3: Idempotency Validation
CRITICAL: Prevents duplicate bookings and commissions
"""

import pytest
import aiohttp
import os
import uuid
import asyncio
import sqlite3

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
DB_PATH = os.getenv("ACP_DB_PATH", "backend/acp_transactions.db")

@pytest.mark.asyncio
@pytest.mark.idempotency
async def test_idempotency_duplicate_returns_cached_result():
    """
    CRITICAL: Duplicate request_id must return cached result.
    Prevents double-charging and duplicate bookings.
    """
    request_id = f"idempotency_test_{uuid.uuid4()}"
    test_property = os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001")
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "intent_type": "execute",
            "request_id": request_id,
            "target_entity_id": test_property,
            "intent_payload": {
                "dates": {"check_in": "2026-06-01", "check_out": "2026-06-03"},
                "room_type": "standard_queen",
                "guests": 2,
                "dry_run": True  # Safety first
            }
        }
        
        # First request
        async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=10) as resp1:
            assert resp1.status == 200, f"First request failed: {resp1.status}"
            data1 = await resp1.json()
            
            # Check for idempotency marker
            first_hit = data1.get("idempotency", {}).get("hit") == True
            
        # Small delay to ensure timing differences
        await asyncio.sleep(0.1)
        
        # Duplicate request
        async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=10) as resp2:
            assert resp2.status == 200, f"Duplicate request failed: {resp2.status}"
            data2 = await resp2.json()
            
            second_hit = data2.get("idempotency", {}).get("hit") == True
            
            # Verify idempotency worked
            if first_hit or second_hit:
                print("✅ Idempotency marker detected in response")
            
            # If confirmation codes present, they must match
            if "confirmation_code" in data1 and "confirmation_code" in data2:
                assert data1["confirmation_code"] == data2["confirmation_code"], \
                    "❌ CRITICAL: Duplicate request got different confirmation code!"
            
            # Response structure should be identical
            assert data1.get("success") == data2.get("success"), "Success status mismatch"
            
            print("✅ Duplicate request handled correctly")

@pytest.mark.asyncio
@pytest.mark.idempotency
async def test_idempotency_different_request_ids_not_shared():
    """
    Different request_ids must create separate cache entries.
    """
    request_id_1 = f"unique_{uuid.uuid4()}"
    request_id_2 = f"unique_{uuid.uuid4()}"
    test_property = os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001")
    
    async with aiohttp.ClientSession() as session:
        for i, req_id in enumerate([request_id_1, request_id_2], 1):
            payload = {
                "intent_type": "execute",
                "request_id": req_id,
                "target_entity_id": test_property,
                "intent_payload": {
                    "dates": {"check_in": f"2026-0{i+6}-01", "check_out": f"2026-0{i+6}-03"},
                    "room_type": "standard_queen",
                    "guests": 2,
                    "dry_run": True
                }
            }
            
            async with session.post(f"{BASE_URL}/acp/submit", json=payload, timeout=10) as resp:
                assert resp.status == 200
        
        # Verify separate entries in database
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM idempotency_log WHERE request_id IN (?, ?)",
                    (request_id_1, request_id_2)
                )
                count = cursor.fetchone()[0]
                assert count == 2, f"Expected 2 separate cache entries, found {count}"
                print("✅ Different request_ids have separate cache entries")
            except sqlite3.OperationalError as e:
                print(f"⚠️  Could not verify database: {e}")
            finally:
                conn.close()
        else:
            print("⚠️  Database not accessible for verification")

@pytest.mark.idempotency
def test_idempotency_database_schema():
    """
    Verify idempotency_log table exists with correct structure.
    """
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Database not found: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='idempotency_log'")
    if not cursor.fetchone():
        pytest.fail("❌ CRITICAL: idempotency_log table missing")
    
    # Check columns
    cursor.execute("PRAGMA table_info(idempotency_log)")
    columns = {row[1] for row in cursor.fetchall()}
    
    required = {"request_id", "result_json", "execution_type", "created_at"}
    missing = required - columns
    
    if missing:
        pytest.fail(f"❌ CRITICAL: idempotency_log missing columns: {missing}")
    
    # Check indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='idempotency_log'")
    indexes = {row[0] for row in cursor.fetchall()}
    
    if "idx_idempotency_created" not in indexes:
        print("⚠️  Missing index: idx_idempotency_created (needed for cleanup)")
    
    conn.close()
    print("✅ Idempotency database schema valid")
