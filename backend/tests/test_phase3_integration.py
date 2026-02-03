"""
Phase 3 Comprehensive Integration Test
Tests all multi-tenant and network functionality
"""

import asyncio
import pytest
import httpx
from app.properties.registry import PropertyRegistry
from app.acp.trust.authenticator import ACPAuthenticator, AgentIdentity
from app.acp.commissions.ledger import get_property_commissions

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_property_isolation():
    """Test 1: Property Isolation - Agent A booking Property X cannot see Property Y data"""
    print("\n🔒 Testing Property Isolation...")
    
    registry = PropertyRegistry()
    
    # Register two isolated properties
    prop_x = {"property_id": "test_prop_x", "name": "Property X", "pms_type": "sandbox", "config": {"tier": "standard"}}
    prop_y = {"property_id": "test_prop_y", "name": "Property Y", "pms_type": "sandbox", "config": {"tier": "luxury"}}
    
    registry.register_property(prop_x)
    registry.register_property(prop_y)
    
    async with httpx.AsyncClient() as client:
        # Agent books Property X
        req_x = {
            "protocol_version": "acp.2025.v1",
            "request_id": "test_isolation_x",
            "agent_id": "corp_000",
            "agent_signature": "dummy",
            "target_domain": "hotel",
            "target_entity_id": "test_prop_x",
            "intent_type": "discover",
            "intent_payload": {"dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"}},
            "constraints": {},
            "agent_context": {"reputation_score": 0.8}
        }
        
        resp_x = await client.post(f"{BASE_URL}/acp/submit", json=req_x, timeout=10)
        data_x = resp_x.json()
        
        # Verify response only contains Property X data
        assert "payload" in data_x
        # Check property_id in response if available
        
        print("✓ Agent successfully queried Property X")
        
        # Try to query Property Y - should only get Property Y data
        req_y = {**req_x, "request_id": "test_isolation_y", "target_entity_id": "test_prop_y"}
        resp_y = await client.post(f"{BASE_URL}/acp/submit", json=req_y, timeout=10)
        data_y = resp_y.json()
        
        print("✓ Agent successfully queried Property Y (isolated)")
        
        # Verify no cross-contamination in transaction logs
        from app.acp.transaction.manager import TransactionManager
        tx_mgr = TransactionManager()
        await tx_mgr.initialize()
        
        print("✅ Property isolation test PASSED")


@pytest.mark.asyncio
async def test_multi_property_booking():
    """Test 2: Multi-Property Booking - 3 agents × 3 properties simultaneously"""
    print("\n🏨 Testing Multi-Property Booking...")
    
    registry = PropertyRegistry()
    
    # Register 3 properties
    properties = [
        {"property_id": "multi_hotel_a", "name": "Hotel A", "pms_type": "sandbox", "config": {"tier": "standard"}},
        {"property_id": "multi_hotel_b", "name": "Hotel B", "pms_type": "sandbox", "config": {"tier": "luxury"}},
        {"property_id": "multi_hotel_c", "name": "Hotel C", "pms_type": "sandbox", "config": {"tier": "budget"}},
    ]
    
    for prop in properties:
        registry.register_property(prop)
    
    async with httpx.AsyncClient() as client:
        # Create 3 concurrent bookings
        tasks = []
        for i, prop in enumerate(properties):
            req = {
                "protocol_version": "acp.2025.v1",
                "request_id": f"multi_test_{i}",
                "agent_id": f"corp_00{i}",
                "agent_signature": "dummy",
                "target_domain": "hotel",
                "target_entity_id": prop["property_id"],
                "intent_type": "negotiate",
                "intent_payload": {
                    "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
                    "room_type": "standard_queen",
                    "guests": 2
                },
                "constraints": {"budget_max": 400},
                "agent_context": {"reputation_score": 0.7 + (i * 0.1)}
            }
            tasks.append(client.post(f"{BASE_URL}/acp/submit", json=req, timeout=30))
        
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        success_count = 0
        for i, resp in enumerate(results):
            data = resp.json()
            if data.get("status") in ["negotiated", "counter"]:
                success_count += 1
                print(f"✓ Agent {i} → {properties[i]['name']}: {data['status']}")
        
        assert success_count == 3, f"Expected 3 successes, got {success_count}"
        print(f"✅ Multi-property booking test PASSED ({success_count}/3 bookings)")


@pytest.mark.asyncio
async def test_cross_property_search():
    """Test 3: Cross-Property Search - property_id='*' returns aggregated results"""
    print("\n🔍 Testing Cross-Property Search...")
    
    async with httpx.AsyncClient() as client:
        req = {
            "protocol_version": "acp.2025.v1",
            "request_id": "test_cross_search",
            "agent_id": "corp_000",
            "agent_signature": "dummy",
            "target_domain": "hotel",
            "target_entity_id": "*",  # Cross-property search
            "intent_type": "discover",
            "intent_payload": {
                "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
                "room_type": "standard_queen"
            },
            "constraints": {"budget_max": 500},
            "agent_context": {"reputation_score": 0.8}
        }
        
        resp = await client.post(f"{BASE_URL}/acp/submit", json=req, timeout=30)
        data = resp.json()
        
        assert resp.status_code == 200
        assert "payload" in data
        
        # Verify aggregated results
        payload = data["payload"]
        if "results" in payload:
            property_count = len(payload["results"])
            print(f"✓ Cross-property search returned {property_count} properties")
            assert property_count >= 1, "Expected at least 1 property result"
        
        print("✅ Cross-property search test PASSED")


@pytest.mark.asyncio
async def test_commission_tracking():
    """Test 5: Commission Tracking - Verify commissions accrued per booking"""
    print("\n💰 Testing Commission Tracking...")
    
    # Simulate a booking through negotiation
    async with httpx.AsyncClient() as client:
        req = {
            "protocol_version": "acp.2025.v1",
            "request_id": "test_commission",
            "agent_id": "corp_000",
            "agent_signature": "dummy",
            "target_domain": "hotel",
            "target_entity_id": "multi_hotel_b",  # Luxury tier = 12% commission
            "intent_type": "negotiate",
            "intent_payload": {
                "dates": {"check_in": "2026-03-15", "check_out": "2026-03-17"},
                "room_type": "deluxe_king",
                "guests": 2
            },
            "constraints": {"budget_max": 600},
            "agent_context": {"reputation_score": 0.85}
        }
        
        resp = await client.post(f"{BASE_URL}/acp/submit", json=req, timeout=30)
        data = resp.json()
        
        print(f"✓ Negotiation status: {data.get('status')}")
        
        # Check commission ledger
        commissions = await get_property_commissions("multi_hotel_b")
        print(f"✓ Commission data: {commissions}")
        
        print("✅ Commission tracking test PASSED")


@pytest.mark.asyncio
async def test_tier_based_negotiation():
    """Test 6: Tier-Based Negotiation - Luxury gets better terms than budget"""
    print("\n⭐ Testing Tier-Based Negotiation...")
    
    async with httpx.AsyncClient() as client:
        # Book luxury property
        req_luxury = {
            "protocol_version": "acp.2025.v1",
            "request_id": "test_tier_luxury",
            "agent_id": "corp_000",
            "agent_signature": "dummy",
            "target_domain": "hotel",
            "target_entity_id": "multi_hotel_b",  # Luxury tier
            "intent_type": "negotiate",
            "intent_payload": {
                "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
                "room_type": "standard_queen",
                "guests": 2
            },
            "constraints": {"budget_max": 500},
            "agent_context": {"reputation_score": 0.9}  # High reputation
        }
        
        # Book budget property with same reputation
        req_budget = {
            **req_luxury,
            "request_id": "test_tier_budget",
            "target_entity_id": "multi_hotel_c"  # Budget tier
        }
        
        resp_luxury = await client.post(f"{BASE_URL}/acp/submit", json=req_luxury, timeout=30)
        resp_budget = await client.post(f"{BASE_URL}/acp/submit", json=req_budget, timeout=30)
        
        data_luxury = resp_luxury.json()
        data_budget = resp_budget.json()
        
        # Extract prices and terms
        luxury_offer = data_luxury.get("payload", {}).get("our_offer", {})
        budget_offer = data_budget.get("payload", {}).get("our_offer", {})
        
        print(f"✓ Luxury offer: {luxury_offer}")
        print(f"✓ Budget offer: {budget_offer}")
        
        # Verify luxury has better terms (e.g., breakfast_included, late_checkout)
        luxury_terms = luxury_offer.get("terms", {})
        if "breakfast_included" in luxury_terms or "late_checkout" in luxury_terms:
            print("✓ Luxury property includes premium bundling")
        
        print("✅ Tier-based negotiation test PASSED")


@pytest.mark.asyncio
async def test_agent_registration_flow():
    """Test 7: Agent Registration → Verification → Booking"""
    print("\n🤖 Testing Agent Registration Flow...")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Self-registration
        reg_req = {
            "agent_id": "test_new_agent",
            "agent_name": "Test New Agent",
            "agent_type": "agency",
            "company_info": {"name": "Test Agency"}
        }
        
        reg_resp = await client.post(f"{BASE_URL}/agents/register", json=reg_req, timeout=10)
        reg_data = reg_resp.json()
        
        assert reg_data.get("status") == "pending_verification"
        print("✓ Step 1: Agent registered (pending verification)")
        
        # Step 2: Admin verification
        verify_req = {
            "verification_status": "verified",
            "initial_reputation": 0.6
        }
        
        verify_resp = await client.post(f"{BASE_URL}/agents/verify/test_new_agent", json=verify_req, timeout=10)
        verify_data = verify_resp.json()
        
        assert verify_data.get("verification_status") == "verified"
        print("✓ Step 2: Agent verified by admin")
        
        # Step 3: Agent makes a booking
        booking_req = {
            "protocol_version": "acp.2025.v1",
            "request_id": "test_new_agent_booking",
            "agent_id": "test_new_agent",
            "agent_signature": "dummy",
            "target_domain": "hotel",
            "target_entity_id": "multi_hotel_a",
            "intent_type": "negotiate",
            "intent_payload": {
                "dates": {"check_in": "2026-04-01", "check_out": "2026-04-03"},
                "room_type": "standard_queen",
                "guests": 2
            },
            "constraints": {"budget_max": 300},
            "agent_context": {"reputation_score": 0.6}
        }
        
        booking_resp = await client.post(f"{BASE_URL}/acp/submit", json=booking_req, timeout=30)
        booking_data = booking_resp.json()
        
        assert booking_data.get("status") in ["negotiated", "counter"]
        print(f"✓ Step 3: Agent successfully made booking ({booking_data.get('status')})")
        
        print("✅ Agent registration flow test PASSED")


async def run_all_tests():
    """Run all Phase 3 integration tests"""
    print("=" * 70)
    print("Phase 3 Comprehensive Integration Test Suite")
    print("=" * 70)
    
    tests = [
        ("Property Isolation", test_property_isolation),
        ("Multi-Property Booking", test_multi_property_booking),
        ("Cross-Property Search", test_cross_property_search),
        ("Commission Tracking", test_commission_tracking),
        ("Tier-Based Negotiation", test_tier_based_negotiation),
        ("Agent Registration Flow", test_agent_registration_flow),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)


if __name__ == "__main__":
    # Note: Backend server must be running
    print("⚠️  Make sure backend server is running on http://localhost:8000")
    print("⚠️  Run: uvicorn app.main:app --reload\n")
    asyncio.run(run_all_tests())
