"""
External Agent Self-Registration Routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import sqlite3
import json
from app.acp.trust.authenticator import ACPAuthenticator, AgentIdentity

router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentRegisterRequest(BaseModel):
    agent_id: str
    agent_name: str
    agent_type: str
    public_key: Optional[str] = None
    company_info: Optional[Dict[str, Any]] = None


class AgentVerificationRequest(BaseModel):
    verification_status: str  # verified, rejected
    initial_reputation: float = 0.5


@router.post("/register")
async def register_agent(payload: AgentRegisterRequest):
    """Public endpoint for agent self-registration"""
    auth = ACPAuthenticator(db_path="acp_trust.db")
    await auth.initialize()
    
    # Create agent identity with pending status
    identity = AgentIdentity(
        agent_id=payload.agent_id,
        agent_name=payload.agent_name,
        agent_type=payload.agent_type,
        public_key=payload.public_key or "",
        reputation_score=0.0,  # Start at 0, requires verification
        verification_status="pending",
        allowed_domains=["hotel"],  # Default
    )
    
    # Register agent
    success = await auth.register_agent(identity)
    if not success:
        raise HTTPException(status_code=409, detail="Agent already registered")
    
    # Add to verification queue
    _add_to_verification_queue(payload.agent_id)
    
    return {
        "status": "pending_verification",
        "agent_id": payload.agent_id,
        "message": "Registration submitted. Awaiting admin verification."
    }


@router.post("/verify/{agent_id}")
async def verify_agent(agent_id: str, payload: AgentVerificationRequest):
    """Admin endpoint to verify/reject agent"""
    auth = ACPAuthenticator(db_path="acp_trust.db")
    await auth.initialize()
    
    identity = await auth._get_identity(agent_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    identity.verification_status = payload.verification_status
    if payload.verification_status == "verified":
        identity.reputation_score = payload.initial_reputation
    
    await auth._save_identity(identity)
    _remove_from_verification_queue(agent_id)
    
    return {
        "status": "updated",
        "agent_id": agent_id,
        "verification_status": payload.verification_status
    }


@router.get("/{agent_id}/profile")
async def get_agent_profile(agent_id: str):
    """Get agent profile (authorized agents only)"""
    auth = ACPAuthenticator(db_path="acp_trust.db")
    await auth.initialize()
    
    identity = await auth._get_identity(agent_id)
    if not identity:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get transaction history
    from app.acp.transaction.manager import TransactionManager
    tx_manager = TransactionManager()
    await tx_manager.initialize()
    
    # Get marketplace connections
    connections = _get_agent_connections(agent_id)
    
    return {
        "agent_id": identity.agent_id,
        "agent_name": identity.agent_name,
        "agent_type": identity.agent_type,
        "reputation_score": identity.reputation_score,
        "verification_status": identity.verification_status,
        "allowed_domains": identity.allowed_domains,
        "total_transactions": identity.total_transactions,
        "successful_transactions": identity.successful_transactions,
        "connected_properties": connections,
    }


@router.post("/{agent_id}/apikey")
async def generate_api_key(agent_id: str):
    """Generate API key for agent (MVP - simple hash)"""
    import hashlib
    import secrets
    
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Store in database
    _store_api_key(agent_id, api_key_hash)
    
    return {
        "agent_id": agent_id,
        "api_key": api_key,  # Only shown once
        "message": "Store this key securely. It will not be shown again."
    }


def _add_to_verification_queue(agent_id: str):
    """Add agent to verification queue"""
    conn = sqlite3.connect("acp_trust.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_verification_queue (
            agent_id TEXT PRIMARY KEY,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        INSERT OR IGNORE INTO agent_verification_queue (agent_id)
        VALUES (?)
    """, (agent_id,))
    
    conn.commit()
    conn.close()


def _remove_from_verification_queue(agent_id: str):
    """Remove agent from verification queue"""
    conn = sqlite3.connect("acp_trust.db")
    cur = conn.cursor()
    
    cur.execute("""
        DELETE FROM agent_verification_queue WHERE agent_id = ?
    """, (agent_id,))
    
    conn.commit()
    conn.close()


def _get_agent_connections(agent_id: str) -> list:
    """Get properties connected to agent"""
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
        SELECT property_id FROM agent_marketplace_connections
        WHERE agent_id = ?
    """, (agent_id,))
    
    rows = cur.fetchall()
    conn.close()
    
    return [row[0] for row in rows]


def _store_api_key(agent_id: str, api_key_hash: str):
    """Store hashed API key"""
    conn = sqlite3.connect("acp_trust.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_api_keys (
            agent_id TEXT PRIMARY KEY,
            api_key_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        INSERT OR REPLACE INTO agent_api_keys (agent_id, api_key_hash)
        VALUES (?, ?)
    """, (agent_id, api_key_hash))
    
    conn.commit()
    conn.close()
