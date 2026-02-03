# tests/test_01_contract_endpoints.py
"""
STRICT API CONTRACT TESTS
This one fails if core API contract breaks.
"""

import os
import uuid
import pytest
import aiohttp

BASE_URL = os.getenv("ACP_BASE_URL", "http://localhost:8000")
TEST_PROPERTY_ID = os.getenv("ACP_TEST_PROPERTY_ID", "cloudbeds_001")

# Use the actual implementation path as contract
AGENT_REGISTER_PATH = os.getenv("ACP_AGENT_REGISTER_PATH", "/acp/register")
SUBMIT_PATH = os.getenv("ACP_SUBMIT_PATH", "/acp/submit")

@pytest.mark.asyncio
async def test_agent_register_contract():
    """Test agent registration contract."""
    agent_id = f"test_agent_{uuid.uuid4().hex[:8]}"
    payload = {
        "agent_id": agent_id,
        "name": "Contract Test Agent",
        "agent_type": "travel_aggregator",
        "identity_blob": {"email": "contract@test.com"},
        "initial_reputation": 0.5
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}{AGENT_REGISTER_PATH}", json=payload) as resp:
            assert resp.status in (200, 201, 409), f"Agent register failed: {resp.status}"
            if resp.status in (200, 201):
                data = await resp.json()
                assert data.get("agent_id") == agent_id

@pytest.mark.asyncio
async def test_submit_discover_contract():
    """Test discover intent contract."""
    payload = {
        "intent_type": "discover",
        "target_entity_id": "*",
        "intent_payload": {
            "dates": {"check_in": "2026-03-15", "check_out": "2026-03-17"},
            "location": "Hobart"
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
            assert resp.status == 200
            data = await resp.json()

            # Strong shape checks to avoid false positives
            assert "properties" in data, f"Missing properties key: {data}"
            assert isinstance(data["properties"], list)

@pytest.mark.asyncio
async def test_submit_negotiate_contract():
    """Test negotiate intent contract."""
    payload = {
        "intent_type": "negotiate",
        "target_entity_id": TEST_PROPERTY_ID,
        "intent_payload": {
            "room_type": "standard_queen",
            "base_price": 250.0,
            "requested_discount": 0.10
        },
        "agent_context": {"reputation_score": 0.95}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}{SUBMIT_PATH}", json=payload) as resp:
            assert resp.status == 200
            data = await resp.json()
            assert data.get("status") in ("accepted", "rejected", "countered")
