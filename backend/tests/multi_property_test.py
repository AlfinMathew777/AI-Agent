"""
Multi-Property Network Test
Tests 3 synthetic agents booking across 3 properties simultaneously
"""

import asyncio
import time
from typing import Dict, Any, List
import httpx
from app.properties.registry import PropertyRegistry

GATEWAY_URL = "http://localhost:8000/acp/submit"


async def test_multi_property_booking():
    """Test agents booking across multiple properties"""
    
    # Register 3 properties
    registry = PropertyRegistry()
    
    properties = [
        {"property_id": "hotel_a", "name": "Boutique Hotel A", "pms_type": "sandbox", "tier": "standard"},
        {"property_id": "hotel_b", "name": "Boutique Hotel B", "pms_type": "sandbox", "tier": "luxury"},
        {"property_id": "hotel_c", "name": "Boutique Hotel C", "pms_type": "sandbox", "tier": "budget"},
    ]
    
    for prop in properties:
        registry.register_property({
            "property_id": prop["property_id"],
            "name": prop["name"],
            "pms_type": prop["pms_type"],
            "config": {"tier": prop["tier"], "location": "TAS"}
        })
    
    # Create 3 agents
    agents = [
        {"agent_id": "agent_001", "reputation": 0.8},
        {"agent_id": "agent_002", "reputation": 0.6},
        {"agent_id": "agent_003", "reputation": 0.9},
    ]
    
    # Register agents
    async with httpx.AsyncClient() as client:
        for agent in agents:
            await client.post(
                "http://localhost:8000/agents/register",
                json={
                    "agent_id": agent["agent_id"],
                    "agent_name": f"Agent {agent['agent_id']}",
                    "agent_type": "corporate"
                }
            )
        
        # Verify agents
        for agent in agents:
            await client.post(
                f"http://localhost:8000/agents/verify/{agent['agent_id']}",
                json={
                    "verification_status": "verified",
                    "initial_reputation": agent["reputation"]
                }
            )
        
        # Test bookings across properties
        tasks = []
        for i, agent in enumerate(agents):
            property_id = properties[i % len(properties)]["property_id"]
            task = _book_property(client, agent["agent_id"], property_id, agent["reputation"])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n=== Multi-Property Test Results ===")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Agent {agents[i]['agent_id']}: ERROR - {result}")
            else:
                print(f"Agent {agents[i]['agent_id']}: {result.get('status', 'unknown')}")


async def _book_property(client: httpx.AsyncClient, agent_id: str, property_id: str, reputation: float) -> Dict[str, Any]:
    """Book a property"""
    req = {
        "protocol_version": "acp.2025.v1",
        "request_id": f"req_{agent_id}_{int(time.time()*1000)}",
        "agent_id": agent_id,
        "agent_signature": "dummy_signature",
        "target_domain": "hotel",
        "target_entity_id": property_id,
        "intent_type": "negotiate",
        "intent_payload": {
            "dates": {"check_in": "2026-03-01", "check_out": "2026-03-03"},
            "room_type": "standard_queen",
            "guests": 2,
        },
        "constraints": {"budget_max": 400, "budget_currency": "AUD"},
        "agent_context": {"reputation_score": reputation},
    }
    
    resp = await client.post(GATEWAY_URL, json=req, timeout=30)
    return resp.json()


if __name__ == "__main__":
    asyncio.run(test_multi_property_booking())
