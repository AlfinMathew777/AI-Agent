"""
Admin Property Onboarding Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.properties.registry import PropertyRegistry
from app.acp.domains.hotel.adapter_factory import get_adapter
from app.api.deps import verify_admin_role, get_tenant_header

router = APIRouter()


class PropertyRegisterRequest(BaseModel):
    property_id: str
    name: str
    pms_type: str  # cloudbeds, mews, opera, sandbox
    pms_credentials: Optional[Dict[str, Any]] = None
    tier: str = "standard"  # budget, standard, luxury
    location: Optional[str] = None
    amenities: Optional[Dict[str, Any]] = None


@router.post("/admin/properties", dependencies=[Depends(verify_admin_role)])
async def register_property(
    payload: PropertyRegisterRequest,
    tenant_id: str = Depends(get_tenant_header)
):
    """Register a new property with PMS integration"""
    registry = PropertyRegistry()
    
    # Validate PMS credentials by making test call
    if payload.pms_credentials and payload.pms_type == "cloudbeds":
        try:
            # Test credentials
            import os
            os.environ["CLOUDBEDS_CLIENT_ID"] = payload.pms_credentials.get("client_id", "")
            os.environ["CLOUDBEDS_CLIENT_SECRET"] = payload.pms_credentials.get("client_secret", "")
            
            adapter = await get_adapter(payload.property_id)
            # Try a simple query to validate
            test_result = await adapter.get_base_price(payload.property_id, {"check_in": "2026-01-01"}, "standard_queen")
            if test_result <= 0:
                raise HTTPException(status_code=400, detail="PMS credentials validation failed")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PMS credentials invalid: {str(e)}")
    
    # Auto-discover room types and rate plans (stub for now)
    # In production, would query PMS API
    room_types = ["standard_queen", "deluxe_king"]  # Default
    rate_plans = {}  # Would be discovered from PMS
    
    # Generate default config based on tier
    config = {
        "tier": payload.tier,
        "location": payload.location,
        "amenities": payload.amenities or {},
        "room_types": room_types,
        "rate_plans": rate_plans,
        "negotiation_settings": _get_tier_negotiation_settings(payload.tier),
    }
    
    # Register property
    success = registry.register_property({
        "property_id": payload.property_id,
        "name": payload.name,
        "pms_type": payload.pms_type,
        "pms_credentials": payload.pms_credentials,
        "config": config,
    })
    
    if not success:
        raise HTTPException(status_code=409, detail="Property already exists")
    
    return {
        "status": "registered",
        "property_id": payload.property_id,
        "config": config
    }


def _get_tier_negotiation_settings(tier: str) -> Dict[str, Any]:
    """Get tier-specific negotiation settings"""
    if tier == "budget":
        return {
            "discount_multiplier": 0.10,
            "prioritize_availability": True,
            "minimal_bundling": True,
        }
    elif tier == "luxury":
        return {
            "discount_multiplier": 0.20,
            "heavy_bundling": True,
            "experience_addons": True,
        }
    else:  # standard
        return {
            "discount_multiplier": 0.15,
            "balanced_approach": True,
        }


@router.get("/admin/properties", dependencies=[Depends(verify_admin_role)])
async def list_properties(tenant_id: str = Depends(get_tenant_header)):
    """List all registered properties"""
    registry = PropertyRegistry()
    properties = registry.list_active_properties()
    
    return {
        "properties": [
            {
                "property_id": p.property_id,
                "name": p.name,
                "pms_type": p.pms_type,
                "tier": p.config_json.get("tier", "standard"),
                "is_active": p.is_active,
            }
            for p in properties
        ]
    }


# Phase 3B: Property Pause/Resume Controls
@router.post("/admin/properties/{property_id}/pause", dependencies=[Depends(verify_admin_role)])
async def pause_property(
    property_id: str,
    reason: str = "Manual pause by admin",
    tenant_id: str = Depends(get_tenant_header)
):
    """Pause a property - prevents new booking requests from routing to it
    
    Use cases:
    - Emergency rollback during Phase 3B onboarding
    - PMS integration issues
    - Maintenance window
    - Property requests temporary suspension
    """
    registry = PropertyRegistry()
    property = registry.get_property(property_id)
    
    if not property:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    
    # Update property to inactive
    import sqlite3
    conn = sqlite3.connect("acp_properties.db")
    cur = conn.cursor()
    cur.execute("""
        UPDATE properties 
        SET is_active = 0,
            config_json = json_set(config_json, '$.paused_reason', ?)
        WHERE property_id = ?
    """, (reason, property_id))
    conn.commit()
    conn.close()
    
    # Log to monitoring
    import datetime
    log_msg = f"Property {property_id} paused: {reason}"
    print(f"[ADMIN] {log_msg}")
    
    # TODO: Record in monitoring database
    
    return {
        "status": "paused",
        "property_id": property_id,
        "reason": reason,
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "Property will not receive new booking requests. Existing bookings unaffected."
    }


@router.post("/admin/properties/{property_id}/resume", dependencies=[Depends(verify_admin_role)])
async def resume_property(
    property_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    """Resume a paused property - re-enable for bookings"""
    registry = PropertyRegistry()
    property = registry.get_property(property_id)
    
    if not property:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    
    # Update property to active
    import sqlite3
    conn = sqlite3.connect("acp_properties.db")
    cur = conn.cursor()
    cur.execute("""
        UPDATE properties 
        SET is_active = 1,
            config_json = json_set(config_json, '$.paused_reason', NULL)
        WHERE property_id = ?
    """, (property_id,))
    conn.commit()
    conn.close()
    
    # Log to monitoring
    import datetime
    log_msg = f"Property {property_id} resumed"
    print(f"[ADMIN] {log_msg}")
    
    return {
        "status": "active",
        "property_id": property_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "message": "Property is now active and will receive booking requests."
    }

