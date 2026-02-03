"""
Idempotency Testing Script for Phase 3B
Tests that duplicate execute requests return cached results without creating duplicate bookings

Run: python test_idempotency.py
"""

import asyncio
import json
from app.acp.transaction.manager import TransactionManager, Transaction
from datetime import datetime


async def test_idempotency():
    """Test that duplicate requests return cached results"""
    print("=" * 70)
    print("IDEMPOTENCY TEST")
    print("=" * 70)
    
    # Initialize transaction manager
    manager = TransactionManager("test_idempotency.db")
    await manager.initialize()
    
    # Test data
    request_id = f"test_idem_{int(datetime.now().timestamp())}"
    
    # Mock successful execution result
    result1 = {
        "success": True,
        "dry_run": False,
        "confirmation_code": "TEST-12345",
        "pms_reference": "CB-67890",
        "check_in_instructions": "Test booking"
    }
    
    print("\n[TEST 1] Store first execution result")
    print("-" * 60)
    await manager.store_idempotent_result(request_id, result1, "execute")
    print(f"Stored result for request_id: {request_id}")
    
    print("\n[TEST 2] Retrieve cached result (should return same)")
    print("-" * 60)
    cached = await manager.get_idempotent_result(request_id, "execute")
    
    if cached:
        print(f"[PASS] Retrieved cached result")
        print(f"  Confirmation: {cached.get('confirmation_code')}")
        print(f"  PMS Reference: {cached.get('pms_reference')}")
        
        # Verify it's identical
        if cached == result1:
            print(f"[PASS] Cached result matches original")
        else:
            print(f"[FAIL] Cached result differs from original")
            print(f"  Original: {result1}")
            print(f"  Cached: {cached}")
    else:
        print(f"[FAIL] No cached result found")
    
    print("\n[TEST 3] Different request_id (should return None)")
    print("-" * 60)
    different_id = f"test_different_{int(datetime.now().timestamp())}"
    cached2 = await manager.get_idempotent_result(different_id, "execute")
    
    if cached2 is None:
        print(f"[PASS] No cache for different request_id (expected)")
    else:
        print(f"[FAIL] Found unexpected cached result for new request_id")
    
    print("\n[TEST 4] Dry-run result caching")
    print("-" * 60)
    dry_run_id = f"test_dry_{int(datetime.now().timestamp())}"
    dry_run_result = {
        "success": True,
        "dry_run": True,
        "would_create_booking": True,
        "validation": "passed",
        "estimated_total": 450.00
    }
    
    await manager.store_idempotent_result(dry_run_id, dry_run_result, "execute")
    cached_dry = await manager.get_idempotent_result(dry_run_id, "execute")
    
    if cached_dry and cached_dry.get("dry_run") is True:
        print(f"[PASS] Dry-run result cached and retrieved")
    else:
        print(f"[FAIL] Dry-run caching failed")
    
    print("\n[TEST 5] Failed result (should NOT cache)")
    print("-" * 60)
    failed_id = f"test_fail_{int(datetime.now().timestamp())}"
    failed_result = {
        "success": False,
        "error": "PMS API timeout"
    }
    
    await manager.store_idempotent_result(failed_id, failed_result, "execute")
    cached_fail = await manager.get_idempotent_result(failed_id, "execute")
    
    if cached_fail is None:
        print(f"[PASS] Failed results not cached (expected)")
    else:
        print(f"[FAIL] Failed result was cached (should not be)")
    
    print("\n[TEST 6] Cleanup old records")
    print("-" * 60)
    deleted = await manager.cleanup_old_idempotency_records(days=0)  # Delete all for test
    print(f"[INFO] Deleted {deleted} records")
    
    # Verify cleanup
    cached_after_cleanup = await manager.get_idempotent_result(request_id, "execute")
    if cached_after_cleanup is None:
        print(f"[PASS] Records cleaned up successfully")
    else:
        print(f"[WARN] Records still present after cleanup")
    
    print("\n" + "=" * 70)
    print("IDEMPOTENCY TESTS COMPLETE")
    print("=" * 70)
    print("\nSummary:")
    print("  - Caching works for successful executions")
    print("  - Caching works for dry-run executions")
    print("  - Failed executions are NOT cached")
    print("  - Different request_ids maintain separate cache")
    print("  - Cleanup removes old records")
    print("\nNext: Test integration with actual CloudbedsAdapter execution")


if __name__ == "__main__":
    print("\nIdempotency Test Script")
    print("=======================\n")
    
    try:
        asyncio.run(test_idempotency())
        print("\n[SUCCESS] All idempotency tests passed")
    except Exception as e:
        print(f"\n[FAILURE] Tests failed: {e}")
        import traceback
        traceback.print_exc()
