"""
Stress test: Multiple AI agents negotiating simultaneously (ACP Gateway)
Endpoint: POST http://localhost:8000/acp/submit
"""

import asyncio
import json
import time
from typing import Dict, Any, List

import httpx


GATEWAY_URL = "http://localhost:8000/acp/submit"


class SyntheticAgent:
    def __init__(self, agent_id: str, agent_type: str, reputation: float):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.reputation = reputation

    async def negotiate_booking(self, scenario: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        req = {
            "protocol_version": "acp.2025.v1",
            "request_id": f"req_{self.agent_id}_{int(time.time()*1000)}",
            "agent_id": self.agent_id,
            "agent_signature": "dummy_signature",
            "target_domain": "hotel",
            "target_entity_id": scenario["property"],
            "intent_type": "negotiate",
            "intent_payload": {
                "dates": {"check_in": scenario["check_in"], "check_out": scenario["check_out"]},
                "room_type": scenario.get("room_type", "deluxe_king"),
                "guests": scenario.get("guests", 2),
                "counter_offer": None,
            },
            "constraints": {
                "budget_max": scenario["budget"],
                "budget_currency": "AUD",
                "time_flexibility_hours": scenario.get("flexibility", 0),
            },
            "agent_context": {
                "reputation_score": self.reputation,
                "booking_urgency": scenario.get("urgency", "normal"),
                "company_tier": scenario.get("tier", "standard"),
                "agent_type": self.agent_type,
            },
        }

        # Round 1
        result = await self._post(client, req)

        rounds = 0
        max_rounds = 5

        while result.get("status") == "counter" and rounds < max_rounds:
            rounds += 1
            offer = (result.get("payload") or {}).get("our_offer") or {}
            decision = self._evaluate_offer(offer, scenario["budget"])

            if decision.get("accept"):
                # Accept -> execute
                req["intent_type"] = "execute"
                req["negotiation_session_id"] = result.get("negotiation_session_id")
                return await self._post(client, req)

            if decision.get("counter"):
                # Continue negotiation (send counter_offer inside intent_payload)
                req["intent_type"] = "negotiate"
                req["negotiation_session_id"] = result.get("negotiation_session_id")
                req["intent_payload"]["counter_offer"] = decision["offer"]
                result = await self._post(client, req)
                continue

            return {"status": "abandoned", "reason": "Price too high"}

        return result

    def _evaluate_offer(self, offer: Dict[str, Any], budget: float) -> Dict[str, Any]:
        price = float(offer.get("price", 10**9))

        if self.agent_type == "corporate":
            if price <= budget * 1.1:
                return {"accept": True}
            if price <= budget * 1.2:
                return {"counter": True, "offer": {"price": budget * 1.05, "terms": {"cancellation": "flexible"}}}
            return {"accept": False, "counter": False}

        if self.agent_type == "budget":
            if price <= budget:
                return {"accept": True}
            return {"counter": True, "offer": {"price": budget * 0.9, "terms": {"date_shift": "2_days"}}}

        if self.agent_type == "luxury":
            return {"accept": True}

        return {"accept": False, "counter": False}

    async def _post(self, client: httpx.AsyncClient, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = await client.post(GATEWAY_URL, json=payload, timeout=30)
        return resp.json()


async def register_agent(client: httpx.AsyncClient, agent_id: str, agent_type: str, reputation: float):
    """Register an agent before using it"""
    try:
        resp = await client.post(
            "http://localhost:8000/acp/register",
            json={
                "agent_id": agent_id,
                "agent_name": agent_id,
                "agent_type": agent_type,
                "reputation_score": reputation,
                "requests_per_minute": 100,
                "allowed_domains": ["hotel"]
            },
            timeout=10
        )
        return resp.status_code == 200
    except Exception as e:
        print(f"Warning: Failed to register {agent_id}: {e}")
        return False


async def run_stress_test():
    # Use pilot property if enabled, otherwise synthetic
    scenarios = [
        {"property": "pillinger_house", "budget": 300, "check_in": "2026-03-01", "check_out": "2026-03-03", "room_type": "standard_queen"},
        {"property": "pillinger_house", "budget": 500, "check_in": "2026-03-15", "check_out": "2026-03-17", "room_type": "deluxe_king"},
        {"property": "pillinger_house", "budget": 350, "check_in": "2026-04-01", "check_out": "2026-04-05", "room_type": "standard_queen"},
    ]

    agents: List[SyntheticAgent] = []
    for i in range(20):
        agents.append(SyntheticAgent(f"corp_{i:03d}", "corporate", 0.8))
    for i in range(20):
        agents.append(SyntheticAgent(f"budget_{i:03d}", "budget", 0.4))
    for i in range(10):
        agents.append(SyntheticAgent(f"luxury_{i:03d}", "luxury", 0.95))

    async with httpx.AsyncClient() as client:
        # Register all agents first
        print("Registering agents...")
        registration_tasks = [
            register_agent(client, agent.agent_id, agent.agent_type, agent.reputation)
            for agent in agents
        ]
        await asyncio.gather(*registration_tasks, return_exceptions=True)
        print(f"Registered {len(agents)} agents")
        tasks = []
        for i, agent in enumerate(agents):
            scenario = scenarios[i % len(scenarios)]
            tasks.append(agent.negotiate_booking(scenario, client))

        start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start

    confirmed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "confirmed")
    negotiated = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "negotiated")
    counter = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "counter")
    errors = sum(1 for r in results if isinstance(r, Exception) or (isinstance(r, dict) and r.get("status") == "error"))

    print(f"""
STRESS TEST RESULTS
===================
Total agents: {len(agents)}
Duration: {duration:.2f}s
Throughput: {len(agents)/duration:.1f} req/sec

Confirmed: {confirmed}
Negotiated: {negotiated}
Counter (still negotiating): {counter}
Errors: {errors}
Success-ish rate: {(confirmed+negotiated)/len(agents)*100:.1f}%
""")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
