"""
Phase 3B Verification Test Suite
Comprehensive tests for first Cloudbeds property onboarding

Run after property registration to verify all functionality
"""

import asyncio
import json
import sys
import httpx
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
PROPERTY_ID = "cloudbeds_001"
AGENT_ID = "corp_travel_001"  # High-reputation demo agent
ADMIN_API_KEY = "YOUR_ADMIN_API_KEY"  # Set from environment

TEST_RESULTS = {"passed": 0, "failed": 0, "warnings": 0}


def log_test(name, status, message=""):
    """Log test result"""
    prefix = {
        "PASS": "  [PASS]",
        "FAIL": "  [FAIL]",
        "WARN": "  [WARN]",
        "INFO": "  [INFO]"
    }
    print(f"{prefix.get(status, '  [???]')} {name}")
    if message:
        print(f"         {message}")
    
    if status == "PASS":
        TEST_RESULTS["passed"] += 1
    elif status == "FAIL":
        TEST_RESULTS["failed"] += 1
    elif status == "WARN":
        TEST_RESULTS["warnings"] += 1


async def test_1_marketplace_visibility():
    """Test 1: Property appears in marketplace"""
    print("\n[TEST 1] Marketplace Visibility")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        # List all properties
        response = await client.get(f"{BASE_URL}/marketplace/properties")
        
        if response.status_code == 200:
            data = response.json()
            properties = data.get("properties", [])
            
            # Find our property
            cloudbeds_prop = None
            for prop in properties:
                if prop["property_id"] == PROPERTY_ID:
                    cloudbeds_prop = prop
                    break
            
            if cloudbeds_prop:
                log_test("Property visible in marketplace", "PASS")
                log_test(f"Property name: {cloudbeds_prop['name']}", "INFO")
                log_test(f"Property tier: {cloudbeds_prop['tier']}", "INFO")
                return True
            else:
                log_test("Property NOT found in marketplace", "FAIL", 
                        f"Expected {PROPERTY_ID} in response")
                return False
        else:
            log_test("Marketplace endpoint failed", "FAIL", 
                    f"Status: {response.status_code}")
            return False


async def test_2_property_registry():
    """Test 2: Property registered in database"""
    print("\n[TEST 2] Property Registry")
    print("-" * 60)
    
    try:
        from app.properties.registry import PropertyRegistry
        
        registry = PropertyRegistry()
        property = registry.get_property(PROPERTY_ID)
        
        if property:
            log_test("Property found in registry", "PASS")
            log_test(f"Name: {property.name}", "INFO")
            log_test(f"PMS Type: {property.pms_type}", "INFO")
            
            if property.pms_type == "cloudbeds":
                log_test("PMS type correct", "PASS")
            else:
                log_test("PMS type incorrect", "WARN", 
                        f"Expected 'cloudbeds', got '{property.pms_type}'")
            
            tier = property.config_json.get("tier", "unknown")
            log_test(f"Tier: {tier}", "INFO")
            
            return True
        else:
            log_test("Property NOT in registry", "FAIL")
            return False
            
    except Exception as e:
        log_test("Registry check failed", "FAIL", str(e))
        return False


async def test_3_availability_discovery():
    """Test 3: Room availability through ACP gateway"""
    print("\n[TEST 3] Availability Discovery")
    print("-" * 60)
    
    check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")
    
    payload = {
        "protocol_version": "acp.2025.v1",
        "request_id": f"test_availability_{int(datetime.now().timestamp())}",
        "agent_id": AGENT_ID,
        "agent_signature": "test_signature",
        "target_domain": "hotel",
        "target_entity_id": PROPERTY_ID,
        "intent_type": "discover",
        "intent_payload": {
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            },
            "room_requirements": {
                "room_type": "standard_queen",
                "guests": 2
            }
        },
        "constraints": {},
        "agent_context": {
            "reputation_score": 0.95
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        start_time = datetime.now()
        response = await client.post(
            f"{BASE_URL}/acp/submit",
            json=payload
        )
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        if response.status_code == 200:
            data = response.json()
            log_test("Availability request successful", "PASS")
            log_test(f"Latency: {latency:.0f}ms", 
                    "PASS" if latency < 500 else "WARN")
            
            # Check response has availability data
            if "available_rooms" in str(data) or "offers" in str(data):
                log_test("Availability data present", "PASS")
            else:
                log_test("No availability data", "WARN", 
                        "Response may indicate no rooms available")
            
            return True
        else:
            log_test("Availability request failed", "FAIL", 
                    f"Status: {response.status_code}")
            return False


async def test_4_negotiation():
    """Test 4: Negotiation flow"""
    print("\n[TEST 4] Negotiation")
    print("-" * 60)
    
    check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")
    
    payload = {
        "protocol_version": "acp.2025.v1",
        "request_id": f"test_negotiate_{int(datetime.now().timestamp())}",
        "agent_id": AGENT_ID,
        "agent_signature": "test_signature",
        "target_domain": "hotel",
        "target_entity_id": PROPERTY_ID,
        "intent_type": "negotiate",
        "intent_payload": {
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            },
            "room_type": "standard_queen",
            "base_price": 250.00,
            "requested_discount": 0.10
        },
        "agent_context": {
            "reputation_score": 0.95
        }
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{BASE_URL}/acp/submit",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test("Negotiation request successful", "PASS")
            
            # Check for offer in response
            if "offer" in str(data).lower():
                log_test("Offer generated", "PASS")
                
                # For standard tier, expect ~10% discount
                log_test("Tier-based pricing applied", "INFO", 
                        "Verify discount matches standard tier (10%)")
            else:
                log_test("No offer in response", "WARN")
            
            return True
        else:
            log_test("Negotiation failed", "FAIL", 
                    f"Status: {response.status_code}")
            return False


async def test_5_cross_property_search():
    """Test 5: Cross-property search includes Cloudbeds property"""
    print("\n[TEST 5] Cross-Property Search")
    print("-" * 60)
    
    check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")
    
    payload = {
        "protocol_version": "acp.2025.v1",
        "request_id": f"test_cross_{int(datetime.now().timestamp())}",
        "agent_id": AGENT_ID,
        "agent_signature": "test_signature",
        "target_domain": "hotel",
        "target_entity_id": "*",  # All properties
        "intent_type": "discover",
        "intent_payload": {
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            }
        },
        "agent_context": {
            "reputation_score": 0.95
        }
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        start_time = datetime.now()
        response = await client.post(
            f"{BASE_URL}/acp/submit",
            json=payload
        )
        latency = (datetime.now() - start_time).total_seconds() * 1000
        
        if response.status_code == 200:
            data = response.json()
            response_str = str(data)
            
            log_test("Cross-property search successful", "PASS")
            log_test(f"Latency: {latency:.0f}ms", 
                    "PASS" if latency < 1000 else "WARN")
            
            # Check if cloudbeds_001 is in results
            if PROPERTY_ID in response_str:
                log_test("Cloudbeds property in results", "PASS")
            else:
                log_test("Cloudbeds property NOT in results", "FAIL")
            
            # Count how many properties responded
            # This is rough - adjust based on actual response structure
            property_count = response_str.count("property_id")
            log_test(f"Properties in response: ~{property_count}", "INFO")
            
            return True
        else:
            log_test("Cross-property search failed", "FAIL", 
                    f"Status: {response.status_code}")
            return False


async def test_6_monitoring_dashboard():
    """Test 6: Property appears in monitoring dashboard"""
    print("\n[TEST 6] Monitoring Dashboard")
    print("-" * 60)
    
    headers = {"x-admin-key": ADMIN_API_KEY}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/admin/monitoring/dashboard",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            properties = data.get("properties", [])
            
            # Find our property
            cloudbeds_metrics = None
            for prop in properties:
                if prop["property_id"] == PROPERTY_ID:
                    cloudbeds_metrics = prop
                    break
            
            if cloudbeds_metrics:
                log_test("Property in monitoring dashboard", "PASS")
                
                sync_status = cloudbeds_metrics.get("pms_sync", {}).get("status", "unknown")
                log_test(f"PMS sync status: {sync_status}", "INFO")
                
                errors_24h = cloudbeds_metrics.get("errors_24h", 0)
                if errors_24h == 0:
                    log_test("No errors in last 24 hours", "PASS")
                else:
                    log_test(f"{errors_24h} errors in last 24 hours", "WARN")
                
                return True
            else:
                log_test("Property NOT in dashboard", "FAIL")
                return False
        else:
            log_test("Dashboard endpoint failed", "FAIL", 
                    f"Status: {response.status_code}")
            return False


async def test_7_commission_setup():
    """Test 7: Commission configuration"""
    print("\n[TEST 7] Commission Configuration")
    print("-" * 60)
    
    try:
        from app.properties.registry import PropertyRegistry
        
        registry = PropertyRegistry()
        property = registry.get_property(PROPERTY_ID)
        
        if property:
            commission_rate = property.config_json.get("commission_rate", 0)
            
            # For standard tier, expect 10%
            if commission_rate == 0.10:
                log_test("Commission rate correct", "PASS", "10% for standard tier")
            else:
                log_test(f"Commission rate: {commission_rate*100}%", "WARN", 
                        "Expected 10% for standard tier")
            
            # Check commission ledger exists
            import sqlite3
            conn = sqlite3.connect("acp_commissions.db")
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='commissions_accrued'")
            if cur.fetchone():
                log_test("Commission database ready", "PASS")
            else:
                log_test("Commission table missing", "FAIL")
            conn.close()
            
            return True
        else:
            log_test("Property not found", "FAIL")
            return False
            
    except Exception as e:
        log_test("Commission check failed", "FAIL", str(e))
        return False


async def test_8_idempotency():
    """Test 8: Idempotency - duplicate requests return cached results"""
    print("\n[TEST 8] Idempotency (Phase 3B)")
    print("-" * 60)
    
    try:
        from app.acp.transaction.manager import TransactionManager
        
        manager = TransactionManager()
        await manager.initialize()
        
        # Use unique request_id for this test
        test_request_id = f"idem_test_{int(datetime.now().timestamp())}"
        
        # Mock successful dry-run result
        mock_result = {
            "success": True,
            "dry_run": True,
            "would_create_booking": True,
            "validation": "passed",
            "confirmation_code": "TEST-IDEM-001"
        }
        
        # Test 8.1: Store result
        await manager.store_idempotent_result(test_request_id, mock_result, "execute")
        log_test("Idempotency result stored", "PASS")
        
        # Test 8.2: Retrieve cached result
        cached = await manager.get_idempotent_result(test_request_id, "execute")
        
        if cached:
            log_test("Cached result retrieved", "PASS")
            
            # Test 8.3: Verify contents match
            if cached.get("confirmation_code") == mock_result.get("confirmation_code"):
                log_test("Cached result matches original", "PASS")
            else:
                log_test("Cached result differs", "FAIL",
                        f"Expected {mock_result}, got {cached}")
                return False
        else:
            log_test("Failed to retrieve cached result", "FAIL")
            return False
        
        # Test 8.4: Different request_id returns None
        different_id = f"different_{int(datetime.now().timestamp())}"
        cached2 = await manager.get_idempotent_result(different_id, "execute")
        
        if cached2 is None:
            log_test("Different request_id returns None (correct)", "PASS")
        else:
            log_test("Unexpected cache hit for different ID", "FAIL")
            return False
        
        # Test 8.5: Failed results NOT cached
        failed_result = {"success": False, "error": "Test error"}
        failed_id = f"failed_{int(datetime.now().timestamp())}"
        
        await manager.store_idempotent_result(failed_id, failed_result, "execute")
        cached_fail = await manager.get_idempotent_result(failed_id, "execute")
        
        if cached_fail is None:
            log_test("Failed results not cached (correct)", "PASS")
        else:
            log_test("Failed result was cached (incorrect)", "FAIL")
            return False
        
        # Test 8.6: Verify idempotency_log table exists
        import sqlite3
        conn = sqlite3.connect("acp_transactions.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='idempotency_log'")
        
        if cur.fetchone():
            log_test("Idempotency log table exists", "PASS")
        else:
            log_test("Idempotency log table missing", "FAIL")
            conn.close()
            return False
        
        # Test 8.7: Verify cached record in database
        cur.execute("SELECT COUNT(*) FROM idempotency_log WHERE request_id = ?", (test_request_id,))
        count = cur.fetchone()[0]
        conn.close()
        
        if count == 1:
            log_test("Exactly 1 record in idempotency_log", "PASS")
        else:
            log_test(f"Wrong record count: {count}", "FAIL",
                    "Expected 1 record")
            return False
        
        log_test("Idempotency prevents duplicate bookings", "INFO",
                "Duplicate requests will return cached results")
        
        return True
        
    except Exception as e:
        log_test("Idempotency test failed", "FAIL", str(e))
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run complete test suite"""
    print("=" * 70)
    print("PHASE 3B VERIFICATION TEST SUITE")
    print("=" * 70)
    print(f"\nProperty ID: {PROPERTY_ID}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Agent: {AGENT_ID}")
    print("\n" + "=" * 70)
    
    # Run all tests
    await test_1_marketplace_visibility()
    await test_2_property_registry()
    await test_3_availability_discovery()
    await test_4_negotiation()
    await test_5_cross_property_search()
    await test_6_monitoring_dashboard()
    await test_7_commission_setup()
    await test_8_idempotency()  # Phase 3B: New idempotency test
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"PASSED:   {TEST_RESULTS['passed']}")
    print(f"FAILED:   {TEST_RESULTS['failed']}")
    print(f"WARNINGS: {TEST_RESULTS['warnings']}")
    
    if TEST_RESULTS['failed'] == 0:
        print("\n[SUCCESS] All critical tests passed!")
        print("Cloudbeds property is ready for production.")
        return True
    else:
        print("\n[FAILURE] Some tests failed.")
        print("Review failures above and fix before going live.")
        return False



if __name__ == "__main__":
    print("\nPhase 3B Verification Tests")
    print("============================\n")
    
    # Check admin key is set
    if "YOUR_ADMIN" in ADMIN_API_KEY:
        print("[WARNING] ADMIN_API_KEY not set. Some tests will fail.")
        print("Set ADMIN_API_KEY on line 11 before running.\n")
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Tests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
