"""
ACP Client
Wraps calls to the /acp/submit endpoint for booking, availability, negotiation, etc.
"""

import aiohttp
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime


class ACPClient:
    """Client for submitting intents to the ACP Gateway"""
    
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.acp_endpoint = f"{base_url}/acp/submit"
    
    async def submit_intent(
        self,
        intent_type: str,
        property_id: str,
        intent_payload: Dict[str, Any],
        agent_id: str = "chatbot_guest",
        agent_signature: str = "chatbot_v1",
        constraints: Optional[Dict[str, Any]] = None,
        agent_context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit an ACP intent to the gateway
        
        Args:
            intent_type: One of: discover, query, negotiate, execute, cancel, verify
            property_id: Target property ID or "*" for cross-property search
            intent_payload: Intent-specific data (dates, room_type, etc.)
            agent_id: Agent identifier
            agent_signature: Agent signature  
            constraints: Optional constraints (budget_max, etc.)
            agent_context: Optional context (reputation_score, etc.)
            request_id: Optional request ID (generates if not provided)
        
        Returns:
            ACP response dict
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Build ACP request
        acp_request = {
            "protocol_version": "acp.2025.v1",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "agent_id": agent_id,
            "agent_signature": agent_signature,
            "target_domain": "hotel",
            "target_entity_id": property_id,
            "intent_type": intent_type,
            "intent_payload": intent_payload or {},
            "constraints": constraints or {},
            "agent_context": agent_context or {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.acp_endpoint,
                    json=acp_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result = await response.json()
                    return result
        except Exception as e:
            print(f"[ACP Client] Error submitting intent: {e}")
            return {
                "status": "error",
                "status_code": 500,
                "payload": {"error": str(e), "retryable": True}
            }
    
    async def check_availability(
        self,
        property_id: str,
        check_in: str,
        check_out: str,
        room_type: str = None,
        guests: int = 2
    ) -> Dict[str, Any]:
        """
        Check room availability
        
        Args:
            property_id: Target property ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            room_type: Optional room type filter
            guests: Number of guests
        
        Returns:
            Availability response from ACP
        """
        intent_payload = {
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            },
            "guests": guests
        }
        
        if room_type:
            intent_payload["room_type"] = room_type
        
        return await self.submit_intent(
            intent_type="query",
            property_id=property_id,
            intent_payload=intent_payload
        )
    
    async def start_booking(
        self,
        property_id: str,
        check_in: str,
        check_out: str,
        room_type: str,
        guests: int,
        guest_name: str,
        guest_email: str,
        budget_max: Optional[float] = None,
        reputation_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Start a booking negotiation
        
        Args:
            property_id: Target property ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            room_type: Room type
            guests: Number of guests
            guest_name: Guest name
            guest_email: Guest email
            budget_max: Maximum budget constraint
            reputation_score: Agent reputation (0.0-1.0)
        
        Returns:
            Negotiation response from ACP
        """
        intent_payload = {
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            },
            "room_type": room_type,
            "guests": guests,
            "guest_info": {
                "name": guest_name,
                "email": guest_email
            }
        }
        
        constraints = {}
        if budget_max:
            constraints["budget_max"] = budget_max
        
        agent_context = {
            "reputation_score": reputation_score
        }
        
        return await self.submit_intent(
            intent_type="negotiate",
            property_id=property_id,
            intent_payload=intent_payload,
            constraints=constraints,
            agent_context=agent_context
        )
    
    async def continue_negotiation(
        self,
        property_id: str,
        negotiation_session_id: str,
        counter_price: float,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Continue a negotiation with a counter offer
        
        Args:
            property_id: Target property ID
            negotiation_session_id: Session ID from previous negotiation
            counter_price: Counter offer price
            request_id: Optional request ID
        
        Returns:
            Negotiation response from ACP
        """
        intent_payload = {
            "negotiation_session_id": negotiation_session_id,
            "counter_offer": {
                "price": counter_price,
                "currency": "AUD"
            }
        }
        
        agent_context = {
            "negotiation_session_id": negotiation_session_id
        }
        
        return await self.submit_intent(
            intent_type="negotiate",
            property_id=property_id,
            intent_payload=intent_payload,
            agent_context=agent_context,
            request_id=request_id
        )
    
    async def execute_booking(
        self,
        property_id: str,
        negotiation_session_id: str,
        payment_method: str = "credit_card"
    ) -> Dict[str, Any]:
        """
        Execute a negotiated booking
        
        Args:
            property_id: Target property ID
            negotiation_session_id: Session ID from negotiation
            payment_method: Payment method
        
        Returns:
            Execution response from ACP
        """
        intent_payload = {
            "negotiation_session_id": negotiation_session_id,
            "payment_method": payment_method
        }
        
        return await self.submit_intent(
            intent_type="execute",
            property_id=property_id,
            intent_payload=intent_payload
        )
    
    async def discover_properties(
        self,
        check_in: str,
        check_out: str,
        guests: int = 2,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover available properties (cross-property search)
        
        Args:
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
            location: Optional location filter
        
        Returns:
            Discovery response from ACP with list of properties
        """
        intent_payload = {
            "dates": {
                "check_in": check_in,
                "check_out": check_out
            },
            "guests": guests
        }
        
        if location:
            intent_payload["location"] = location
        
        return await self.submit_intent(
            intent_type="discover",
            property_id="*",  # Cross-property search
            intent_payload=intent_payload
        )
