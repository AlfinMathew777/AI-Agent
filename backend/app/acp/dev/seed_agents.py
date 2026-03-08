"""
Seed agent identities for ACP testing.
Run: python -m app.acp.dev.seed_agents
"""

import asyncio
from datetime import datetime
from app.acp.trust.authenticator import ACPAuthenticator, AgentIdentity


async def main():
    auth = ACPAuthenticator(db_path="acp_trust.db")
    await auth.initialize()

    # minimal identities that match stress test agent_ids
    agents = []

    for i in range(20):
        agents.append(AgentIdentity(
            agent_id=f"corp_{i:03d}",
            agent_name=f"Corporate Agent {i}",
            agent_type="corporate",
            reputation_score=0.8,
            allowed_domains=["hotel"],
            blocked_entities=[],
            registration_date=datetime.utcnow(),
            last_active=datetime.utcnow(),
            verification_status="verified"
        ))

    for i in range(20):
        agents.append(AgentIdentity(
            agent_id=f"budget_{i:03d}",
            agent_name=f"Budget Agent {i}",
            agent_type="budget",
            reputation_score=0.4,
            allowed_domains=["hotel"],
            blocked_entities=[],
            registration_date=datetime.utcnow(),
            last_active=datetime.utcnow(),
            verification_status="verified"
        ))

    for i in range(10):
        agents.append(AgentIdentity(
            agent_id=f"luxury_{i:03d}",
            agent_name=f"Luxury Agent {i}",
            agent_type="luxury",
            reputation_score=0.95,
            allowed_domains=["hotel"],
            blocked_entities=[],
            registration_date=datetime.utcnow(),
            last_active=datetime.utcnow(),
            verification_status="verified"
        ))

    ok = 0
    for a in agents:
        if await auth.register_agent(a):
            ok += 1

    print(f"Seeded {ok}/{len(agents)} agents")


if __name__ == "__main__":
    asyncio.run(main())
