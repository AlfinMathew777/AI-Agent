"""
Agent Marketplace Routes (MVP Discovery)
"""

import sqlite3
from fastapi import APIRouter, Query
from typing import Optional, List
from app.properties.registry import PropertyRegistry
from app.acp.trust.authenticator import ACPAuthenticator

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/properties")
async def list_marketplace_properties(
    tier: Optional[str] = Query(None, description="Filter by tier: budget, standard, luxury"),
    location: Optional[str] = Query(None, description="Filter by location")
):
    """List active properties available in marketplace"""
    registry = PropertyRegistry()
    properties = registry.list_active_properties()
    
    filtered = []
    for prop in properties:
        if not prop.is_active:
            continue
        
        prop_tier = prop.config_json.get("tier", "standard")
        prop_location = prop.config_json.get("location", "")
        
        if tier and prop_tier != tier:
            continue
        if location and location.lower() not in prop_location.lower():
            continue
        
        filtered.append({
            "property_id": prop.property_id,
            "name": prop.name,
            "tier": prop_tier,
            "location": prop_location,
            "pms_type": prop.pms_type,
            "amenities": prop.config_json.get("amenities", {}),
        })
    
    return {
        "properties": filtered,
        "total": len(filtered)
    }


@router.get("/agents")
async def list_marketplace_agents(
    domain: Optional[str] = Query("hotel", description="Filter by domain"),
    tier: Optional[str] = Query(None, description="Filter by preferred tier")
):
    """List verified agents (no PII, only capabilities)"""
    auth = ACPAuthenticator(db_path="acp_trust.db")
    await auth.initialize()
    
    # Get all verified agents
    conn = sqlite3.connect("acp_trust.db")
    cur = conn.cursor()
    
    cur.execute("""
        SELECT identity_json FROM agent_identities
        WHERE verification_status = 'verified'
    """)
    
    rows = cur.fetchall()
    conn.close()
    
    agents = []
    for row in rows:
        import json
        identity = json.loads(row[0])
        
        # Filter by domain
        if domain and domain not in identity.get("allowed_domains", []):
            continue
        
        agents.append({
            "agent_id": identity.get("agent_id"),
            "agent_type": identity.get("agent_type"),
            "reputation_score": identity.get("reputation_score", 0.0),
            "capabilities": {
                "domains": identity.get("allowed_domains", []),
                "total_transactions": identity.get("total_transactions", 0),
                "success_rate": (
                    identity.get("successful_transactions", 0) / 
                    max(identity.get("total_transactions", 1), 1)
                ),
            }
        })
    
    # Filter by tier preference (if agents have tier preferences)
    if tier:
        # This would be enhanced with agent preferences
        pass
    
    return {
        "agents": agents,
        "total": len(agents)
    }


@router.post("/connect")
async def connect_agent_property(
    agent_id: str,
    property_id: str
):
    """Connect agent to property (logging only for MVP)"""
    import sqlite3
    
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
    
    cur.execute("""
        INSERT OR IGNORE INTO agent_marketplace_connections (agent_id, property_id)
        VALUES (?, ?)
    """, (agent_id, property_id))
    
    conn.commit()
    conn.close()
    
    return {
        "status": "connected",
        "agent_id": agent_id,
        "property_id": property_id
    }
