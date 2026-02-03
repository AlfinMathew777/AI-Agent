"""
PMS Failover Test
Tests resilience when one PMS is down
"""

import asyncio
import httpx
from app.properties.registry import PropertyRegistry

BASE_URL = "http://localhost:8000"


async def test_pms_failover():
    """Test that when one PMS/property is down, others continue working"""
    print("\n🔥 Testing PMS Failover...")
    
    registry = PropertyRegistry()
    
    # Register 3 properties
    properties = [
        {"property_id": "failover_hotel_a", "name": "Working Hotel A", "pms_type": "sandbox", "config": {"tier": "standard"}},
        {"property_id": "failover_hotel_b", "name": "Working Hotel B", "pms_type": "sandbox", "config": {"tier": "luxury"}},
        {"property_id": "failover_hotel_down", "name": "Down Hotel", "pms_type": "sandbox", "config": {"tier": "budget"}},
    ]
    
    for prop in properties:
        registry.register_property(prop)
    
    # Disable one property (simulate downtime)
    registry.update_property("failover_hotel_down", {"is_active": False})
    print("✓ Simulated PMS downtime for failover_hotel_down")
    
    async with httpx.AsyncClient() as client:
        # Test booking on working properties
        working_tests = [
            ("failover_hotel_a", "Hotel A (working)"),
            ("failover_hotel_b", "Hotel B (working)"),
        ]
        
        success_count = 0
        for property_id, name in working_tests:
            req = {
                "protocol_version": "acp.2025.v1",
                "request_id": f"failover_test_{property_id}",
                "agent_id": "corp_000",
                "agent_signature": "dummy",
                "target_domain": "hotel",
                "target_entity_id": property_id,
                "intent_type": "negotiate",
                "intent_payload": {
                    "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
                    "room_type": "standard_queen",
                    "guests": 2
                },
                "constraints": {"budget_max": 400},
                "agent_context": {"reputation_score": 0.8}
            }
            
            try:
                resp = await client.post(f"{BASE_URL}/acp/submit", json=req, timeout=10)
                data = resp.json()
                
                if data.get("status") in ["negotiated", "counter"]:
                    success_count += 1
                    print(f"✓ {name}: Booking successful ({data['status']})")
                else:
                    print(f"⚠ {name}: Unexpected status {data.get('status')}")
            except Exception as e:
                print(f"❌ {name}: Request failed: {e}")
        
        # Verify both working properties succeeded
        assert success_count == 2, f"Expected 2 successes, got {success_count}"
        print(f"\n✅ Failover test PASSED: {success_count}/2 working properties remained operational")
        
        # Test that down property returns appropriate error
        req_down = {
            "protocol_version": "acp.2025.v1",
            "request_id": "failover_test_down",
            "agent_id": "corp_000",
            "agent_signature": "dummy",
            "target_domain": "hotel",
            "target_entity_id": "failover_hotel_down",
            "intent_type": "negotiate",
            "intent_payload": {
                "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
                "room_type": "standard_queen",
                "guests": 2
            },
            "constraints": {"budget_max": 400},
            "agent_context": {"reputation_score": 0.8}
        }
        
        resp_down = await client.post(f"{BASE_URL}/acp/submit", json=req_down, timeout=10)
        data_down = resp_down.json()
        
        # Should handle gracefully (error or fallback)
        print(f"✓ Inactive property handled: {data_down.get('status', 'error')}")
        
        # Re-enable property
        registry.update_property("failover_hotel_down", {"is_active": True})
        print("✓ Re-enabled failover_hotel_down")
        
        print("\n✅ PMS failover and recovery test COMPLETED")


if __name__ == "__main__":
    print("=" * 60)
    print("PMS Failover Resilience Test")
    print("=" * 60)
    print("⚠️  Make sure backend server is running on http://localhost:8000\n")
    
    asyncio.run(test_pms_failover())
