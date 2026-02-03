"""
ACP Gateway Server (FastAPI)
Front door for ALL external agents (ACP JSON envelope).
Fits your current backend style (FastAPI router + service objects).
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.acp.trust.authenticator import ACPAuthenticator
from app.acp.transaction.manager import TransactionManager, Transaction
from app.acp.negotiation.engine import NegotiationEngine
from app.acp.domains.hotel.adapter import HotelDomainAdapter
from app.acp.domains.hotel.pilot_config import is_pilot_enabled


# ---- Logging (safe structured-ish) ----
logger = logging.getLogger("acp.gateway")
logging.basicConfig(level=logging.INFO)


# ---- ACP Models ----
class ACPRequest(BaseModel):
    protocol_version: str = "acp.2025.v1"
    request_id: str = Field(..., description="UUID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    agent_id: str = Field(..., min_length=3, max_length=64)
    agent_signature: str = Field(..., description="Signature of request payload (can be dummy in prototype)")

    target_domain: str = Field(..., description="hotel, restaurant, venue, etc.")
    target_entity_id: str = Field(..., description="wrest_point, henry_jones, etc.")

    intent_type: str = Field(..., pattern="^(discover|query|negotiate|execute|cancel|verify)$")
    intent_payload: Dict[str, Any] = Field(default_factory=dict)

    constraints: Dict[str, Any] = Field(default_factory=dict)
    agent_context: Dict[str, Any] = Field(default_factory=dict)


class ACPResponse(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    status: str = Field(..., pattern="^(accepted|rejected|counter|pending|error|timeout|negotiated|confirmed)$")
    status_code: int = Field(..., ge=200, le=599)

    payload: Dict[str, Any] = Field(default_factory=dict)
    negotiation_session_id: Optional[str] = None

    processing_time_ms: int
    gateway_node_id: str = "acp-tas-001"


# ---- Router + singleton-ish services ----
router = APIRouter(prefix="/acp", tags=["ACP"])

authenticator = ACPAuthenticator(db_path="acp_trust.db")
tx_manager = TransactionManager(db_path="acp_transactions.db")
negotiation_engine = NegotiationEngine(tx_manager=tx_manager)

# Use Cloudbeds adapter if pilot enabled, otherwise synthetic
if is_pilot_enabled():
    from app.acp.domains.hotel.cloudbeds_adapter import CloudbedsAdapter
    domain_adapters = {
        "hotel": CloudbedsAdapter(db_path="cloudbeds_cache.db", use_sandbox=True)
    }
else:
    domain_adapters = {
        "hotel": HotelDomainAdapter(db_path="synthetic_hotel.db")
    }

_initialized = False


async def _ensure_initialized():
    """Lazy initialization on first request"""
    global _initialized
    if not _initialized:
        await authenticator.initialize()
        await tx_manager.initialize()
        await domain_adapters["hotel"].initialize()
        _initialized = True
        adapter_type = "Cloudbeds" if is_pilot_enabled() else "Synthetic"
        logger.info(f"ACP Gateway initialized (Adapter: {adapter_type})")


@router.post("/register", response_model=Dict[str, Any])
async def acp_register_agent(request: Request):
    """
    Register a new agent (for testing/prototype).
    In production, this would be a separate admin endpoint.
    """
    await _ensure_initialized()
    
    try:
        body = await request.json()
        from app.acp.trust.authenticator import AgentIdentity
        
        identity = AgentIdentity(
            agent_id=body["agent_id"],
            agent_name=body.get("agent_name", body["agent_id"]),
            agent_type=body.get("agent_type", "standard"),
            reputation_score=body.get("reputation_score", 0.5),
            requests_per_minute=body.get("requests_per_minute", 60),
            allowed_domains=body.get("allowed_domains", ["hotel"]),
        )
        
        success = await authenticator.register_agent(identity)
        if success:
            return {"status": "registered", "agent_id": identity.agent_id}
        return {"status": "error", "message": "Agent already registered"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/submit", response_model=ACPResponse)
async def acp_submit(request: Request):
    """
    PRIMARY ENTRYPOINT
    Accepts raw JSON body that must match ACPRequest.
    Returns ACPResponse.
    """
    start = time.perf_counter()

    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty body")

    try:
        req = ACPRequest.model_validate_json(raw)
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return ACPResponse(
            request_id="unknown",
            status="error",
            status_code=400,
            payload={"error": "Invalid ACPRequest JSON", "details": str(e), "retryable": False},
            processing_time_ms=duration_ms,
        )

    correlation_id = req.request_id
    logger.info(f"[{correlation_id}] ACP request received intent={req.intent_type}")

    # Ensure services are initialized
    await _ensure_initialized()

    # LAYER 2: authenticate + authorize
    auth_result = await authenticator.authenticate(req)
    if not auth_result.valid:
        return _error(req.request_id, 401, "Authentication failed", auth_result.reason, start)

    if not await authenticator.authorize(req):
        return _error(req.request_id, 403, "Not authorized for domain/entity", None, start)

    # Pilot mode: restrict to single property
    if is_pilot_enabled():
        from app.acp.domains.hotel.pilot_config import get_allowed_property_id
        allowed_property = get_allowed_property_id()
        if allowed_property and req.target_entity_id != allowed_property:
            return _error(req.request_id, 403, f"Pilot mode: only {allowed_property} allowed", None, start)

    # LAYER 3: create or get existing tx
    # For negotiation continuation, try to find existing transaction by session_id
    negotiation_session_id = req.agent_context.get("negotiation_session_id") or req.intent_payload.get("negotiation_session_id")
    
    if req.intent_type == "negotiate" and negotiation_session_id:
        # Try to find existing transaction for this negotiation session
        existing_tx = await tx_manager.get_transaction_by_session_id(negotiation_session_id)
        if existing_tx:
            tx = existing_tx
        else:
            tx = await tx_manager.create_transaction(req)
    else:
        tx = await tx_manager.create_transaction(req)

    # LAYER 4/5 routing
    try:
        if req.intent_type in ("query", "discover"):
            result = await _handle_informational(req)
        elif req.intent_type == "negotiate":
            # Check if this is a continuation (has counter_offer or existing negotiating tx)
            if req.intent_payload.get("counter_offer") or (tx.status == "negotiating" and negotiation_session_id):
                result = await negotiation_engine.continue_negotiation(tx, req)
            else:
                result = await negotiation_engine.start_negotiation(tx, req)
        elif req.intent_type == "execute":
            result = await _handle_execution(tx, req)
        else:
            result = {"status": "error", "code": 400, "payload": {"error": f"Unknown intent {req.intent_type}"}}

        # Persist tx update
        await tx_manager.update_transaction_from_result(tx, result)

        duration_ms = int((time.perf_counter() - start) * 1000)
        resp = ACPResponse(
            request_id=req.request_id,
            status=result.get("status", "error"),
            status_code=result.get("code", 500),
            payload=result.get("payload", {}),
            negotiation_session_id=result.get("session_id"),
            processing_time_ms=duration_ms,
        )
        
        # Log request for tracking
        success = resp.status not in ("error", "rejected", "timeout")
        await authenticator.log_request(
            req.agent_id,
            req.request_id,
            req.intent_type,
            success,
            duration_ms
        )
        
        # Record monitoring metrics
        if req.target_entity_id and req.target_entity_id != "*":
            from app.monitoring.dashboard import record_booking_metric
            await record_booking_metric(req.target_entity_id, success, duration_ms)
        
        logger.info(f"[{correlation_id}] ACP request completed status={resp.status} code={resp.status_code}")
        return resp

    except Exception as e:
        logger.exception(f"[{correlation_id}] Unhandled ACP error: {e}")
        return _error(req.request_id, 500, "Internal gateway error", str(e), start)


def _error(request_id: str, code: int, message: str, details: Optional[str], start: float) -> ACPResponse:
    duration_ms = int((time.perf_counter() - start) * 1000)
    return ACPResponse(
        request_id=request_id,
        status="error",
        status_code=code,
        payload={"error": message, "details": details, "retryable": code >= 500},
        processing_time_ms=duration_ms,
    )


async def _handle_informational(req: ACPRequest) -> Dict[str, Any]:
    # Use adapter factory for multi-property support
    from app.acp.domains.hotel.adapter_factory import get_adapter
    
    if req.target_domain != "hotel":
        return {"status": "error", "code": 404, "payload": {"error": f"Domain {req.target_domain} not supported"}}
    
    # Handle cross-property discovery
    if req.target_entity_id == "*":
        return await _handle_cross_property_discovery(req)
    
    adapter = await get_adapter(req.target_entity_id)
    data = await adapter.query(req)
    return {"status": "accepted", "code": 200, "payload": data}


async def _handle_execution(tx, req: ACPRequest) -> Dict[str, Any]:
    # Execute only after negotiation
    if tx.status != "negotiated":
        return {"status": "rejected", "code": 409, "payload": {"error": "Transaction not in negotiated state"}}

    # Use adapter factory for multi-property support
    from app.acp.domains.hotel.adapter_factory import get_adapter
    
    if req.target_domain != "hotel":
        return {"status": "error", "code": 404, "payload": {"error": f"Domain {req.target_domain} not supported"}}

    adapter = await get_adapter(tx.target_entity_id)
    result = await adapter.execute(tx, req)
    
    if result["success"]:
        # Record commission
        from app.acp.commissions.ledger import record_commission
        await record_commission(tx, result)
        
        return {"status": "confirmed", "code": 201, "payload": result}
    return {"status": "error", "code": 500, "payload": result}


async def _handle_cross_property_discovery(req: ACPRequest) -> Dict[str, Any]:
    """Handle cross-property discovery (property_id = '*')"""
    from app.properties.registry import PropertyRegistry
    from app.acp.domains.hotel.adapter_factory import get_adapter
    
    registry = PropertyRegistry()
    properties = registry.list_active_properties()
    
    # Query all properties in parallel
    import asyncio
    tasks = []
    for prop in properties:
        if not prop.is_active:
            continue
        task = _query_single_property(prop.property_id, req)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Aggregate results
    available_properties = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            continue
        if result.get("available"):
            available_properties.append({
                "property_id": properties[i].property_id,
                "name": properties[i].name,
                "availability": result
            })
    
    return {
        "status": "accepted",
        "code": 200,
        "payload": {
            "properties": available_properties,
            "total_found": len(available_properties)
        }
    }


async def _query_single_property(property_id: str, req: ACPRequest) -> Dict[str, Any]:
    """Query a single property for availability"""
    try:
        from app.acp.domains.hotel.adapter_factory import get_adapter
        adapter = await get_adapter(property_id)
        # Create a modified request with specific property_id
        modified_req = req
        modified_req.target_entity_id = property_id
        return await adapter.query(modified_req)
    except Exception as e:
        return {"available": False, "error": str(e)}


async def _suggest_alternative_properties(tx: Transaction, req: ACPRequest, original_result: Dict[str, Any]) -> Dict[str, Any]:
    """Suggest alternative properties if preferred is unavailable"""
    from app.properties.registry import PropertyRegistry
    from app.acp.domains.hotel.adapter_factory import get_adapter
    
    registry = PropertyRegistry()
    preferred_prop = registry.get_property(tx.target_entity_id)
    if not preferred_prop:
        return original_result
    
    preferred_tier = preferred_prop.config_json.get("tier", "standard")
    preferred_location = preferred_prop.config_json.get("location", "")
    
    # Find alternatives with same tier
    alternatives = []
    all_properties = registry.list_active_properties()
    
    for prop in all_properties:
        if prop.property_id == tx.target_entity_id or not prop.is_active:
            continue
        
        if prop.config_json.get("tier") == preferred_tier:
            # Check availability
            try:
                adapter = await get_adapter(prop.property_id)
                availability = await adapter.query(req)
                if availability.get("available"):
                    alternatives.append({
                        "property_id": prop.property_id,
                        "name": prop.name,
                        "location": prop.config_json.get("location", ""),
                        "availability": availability
                    })
            except:
                continue
    
    if alternatives:
        return {
            "status": "counter",
            "code": 202,
            "payload": {
                "message": "Preferred property unavailable. Alternatives found:",
                "alternatives": alternatives[:3],  # Top 3
                "original_error": original_result.get("payload", {}).get("error")
            }
        }
    
    return original_result
