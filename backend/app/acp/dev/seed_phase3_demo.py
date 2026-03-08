"""
Phase 3 Demo Data Seeder
Seeds 3-5 properties and 5-10 verified agents for testing
"""

import asyncio
from app.properties.registry import PropertyRegistry
from app.acp.trust.authenticator import ACPAuthenticator, AgentIdentity
from app.acp.domains.hotel.adapter import HotelDomainAdapter


async def seed_demo_properties():
    """Seed demo properties across different tiers"""
    registry = PropertyRegistry()
    
    properties = [
        {
            "property_id": "hotel_tas_luxury",
            "name": "The Grand Tasman Hotel",
            "pms_type": "sandbox",
            "config": {
                "tier": "luxury",
                "location": "Hobart, TAS",
                "amenities": {
                    "spa": True,
                    "fine_dining": True,
                    "concierge": True,
                    "late_checkout": True
                },
                "share_demand_signals": True
            }
        },
        {
            "property_id": "hotel_tas_standard",
            "name": "Boutique Salamanca Inn",
            "pms_type": "sandbox",
            "config": {
                "tier": "standard",
                "location": "Hobart, TAS",
                "amenities": {
                    "breakfast": True,
                    "wifi": True,
                    "parking": True
                },
                "share_demand_signals": True
            }
        },
        {
            "property_id": "hotel_tas_budget",
            "name": "Hobart Central Budget Stay",
            "pms_type": "sandbox",
            "config": {
                "tier": "budget",
                "location": "Hobart, TAS",
                "amenities": {
                    "wifi": True,
                    "24hr_checkin": True
                },
                "share_demand_signals": False  # Budget tier opts out
            }
        },
        {
            "property_id": "hotel_launceston_standard",
            "name": "Launceston Riverside Hotel",
            "pms_type": "sandbox",
            "config": {
                "tier": "standard",
                "location": "Launceston, TAS",
                "amenities": {
                    "breakfast": True,
                    "river_view": True,
                    "wifi": True
                },
                "share_demand_signals": True
            }
        },
        {
            "property_id": "hotel_devonport_budget",
            "name": "Devonport Express Lodge",
            "pms_type": "sandbox",
            "config": {
                "tier": "budget",
                "location": "Devonport, TAS",
                "amenities": {
                    "wifi": True,
                    "parking": True
                },
                "share_demand_signals": False
            }
        }
    ]
    
    registered_count = 0
    for prop in properties:
        success = registry.register_property(prop)
        if success:
            registered_count += 1
            print(f"[OK] Registered property: {prop['name']} ({prop['config']['tier']} tier)")
        else:
            print(f"[SKIP] Property already exists: {prop['name']}")
    
    print(f"\n[SUCCESS] Registered {registered_count}/5 properties")
    
    # Initialize synthetic inventory for each property
    for prop in properties:
        adapter = HotelDomainAdapter(db_path=f"synthetic_{prop['property_id']}.db")
        await adapter.initialize()
        print(f"[OK] Initialized inventory for {prop['name']}")


async def seed_demo_agents():
    """Seed demo agents with varying reputations"""
    auth = ACPAuthenticator(db_path="acp_trust.db")
    await auth.initialize()
    
    agents = [
        {
            "agent_id": "corp_travel_001",
            "agent_name": "Global Corporate Travel",
            "agent_type": "corporate",
            "reputation": 0.95,
            "tier": "platinum"
        },
        {
            "agent_id": "boutique_agent_001",
            "agent_name": "Boutique Tasmania Tours",
            "agent_type": "agency",
            "reputation": 0.85,
            "tier": "gold"
        },
        {
            "agent_id": "online_booking_001",
            "agent_name": "TravelNow Online",
            "agent_type": "ota",
            "reputation": 0.70,
            "tier": "standard"
        },
        {
            "agent_id": "startup_agent_001",
            "agent_name": "TripStart AI Agent",
            "agent_type": "ai_agent",
            "reputation": 0.60,
            "tier": "standard"
        },
        {
            "agent_id": "new_agent_001",
            "agent_name": "Fresh Travel Co",
            "agent_type": "agency",
            "reputation": 0.50,
            "tier": "bronze"
        },
        {
            "agent_id": "enterprise_001",
            "agent_name": "Enterprise Business Travel",
            "agent_type": "corporate",
            "reputation": 0.90,
            "tier": "platinum"
        },
        {
            "agent_id": "regional_agent_001",
            "agent_name": "TAS Regional Tours",
            "agent_type": "agency",
            "reputation": 0.75,
            "tier": "silver"
        },
        {
            "agent_id": "ai_concierge_001",
            "agent_name": "AI Concierge Network",
            "agent_type": "ai_agent",
            "reputation": 0.80,
            "tier": "gold"
        }
    ]
    
    registered_count = 0
    for agent in agents:
        identity = AgentIdentity(
            agent_id=agent["agent_id"],
            agent_name=agent["agent_name"],
            agent_type=agent["agent_type"],
            reputation_score=agent["reputation"],
            verification_status="verified",  # Pre-verified for demo
            tier=agent["tier"],
            allowed_domains=["hotel"],
            requests_per_minute=100 if agent["tier"] == "platinum" else 60
        )
        
        success = await auth.register_agent(identity)
        if success:
            registered_count += 1
            print(f"[OK] Registered agent: {agent['agent_name']} (rep: {agent['reputation']}, tier: {agent['tier']})")
        else:
            # Update existing agent
            await auth._save_identity(identity)
            print(f"[SKIP] Updated existing agent: {agent['agent_name']}")
    
    print(f"\n[SUCCESS] Registered/updated {len(agents)} agents")


async def seed_marketplace_connections():
    """Create some demo marketplace connections"""
    import sqlite3
    
    connections = [
        ("corp_travel_001", "hotel_tas_luxury"),
        ("corp_travel_001", "hotel_tas_standard"),
        ("boutique_agent_001", "hotel_tas_luxury"),
        ("boutique_agent_001", "hotel_launceston_standard"),
        ("online_booking_001", "hotel_tas_standard"),
        ("online_booking_001", "hotel_tas_budget"),
        ("startup_agent_001", "hotel_tas_budget"),
        ("enterprise_001", "hotel_tas_luxury"),
        ("regional_agent_001", "hotel_launceston_standard"),
        ("ai_concierge_001", "hotel_tas_luxury"),
    ]
    
    conn = sqlite3.connect("acp_trust.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_marketplace_connections (
            agent_id TEXT,
            property_id TEXT,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (agent_id, property_id)
        )
    """)
    
    for agent_id, property_id in connections:
        cur.execute("""
            INSERT OR IGNORE INTO agent_marketplace_connections (agent_id, property_id)
            VALUES (?, ?)
        """, (agent_id, property_id))
    
    conn.commit()
    conn.close()
    
    print(f"\n[SUCCESS] Created {len(connections)} marketplace connections")


async def main():
    """Run all seeders"""
    print("=" * 60)
    print("Phase 3 Demo Data Seeder")
    print("=" * 60)
    
    print("\n[HOTELS] Seeding Properties...")
    await seed_demo_properties()
    
    print("\n[AGENTS] Seeding Agents...")
    await seed_demo_agents()
    
    print("\n[CONNECT] Seeding Marketplace Connections...")
    await seed_marketplace_connections()
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Demo data seeding complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  - Test multi-property bookings via /acp/submit")
    print("  - Browse marketplace at /marketplace/properties and /marketplace/agents")
    print("  - View agent profiles at /agents/{agent_id}/profile")
    print("  - Monitor properties at /admin/monitoring/dashboard")


if __name__ == "__main__":
    asyncio.run(main())
