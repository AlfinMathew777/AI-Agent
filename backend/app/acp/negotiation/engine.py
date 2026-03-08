"""
ACP Negotiation Engine (prototype)
- Multi-round offers
- Integrates with HotelDomainAdapter for base price + demand
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.acp.transaction.manager import Transaction, TransactionManager


@dataclass
class Offer:
    price: float
    currency: str
    terms: Dict[str, Any]
    valid_until: datetime
    offer_id: str


class NegotiationEngine:
    def __init__(self, tx_manager: TransactionManager):
        self.tx_manager = tx_manager
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.max_rounds = 5

    async def start_negotiation(self, tx: Transaction, request) -> Dict[str, Any]:
        await self.tx_manager.set_status(tx, "negotiating")

        session_id = f"neg_{tx.tx_id}"
        tx.negotiation_session_id = session_id
        self.active_sessions[tx.tx_id] = {
            "session_id": session_id,
            "round": 0,
            "constraints": request.constraints,
            "agent_context": request.agent_context,
            "history": []
        }

        offer = await self._generate_initial_offer(tx, request)

        if self._is_acceptable(offer, request.constraints):
            return await self._accept_offer(tx, offer, session_id)

        return await self._counter_offer(tx, offer, session_id)

    async def continue_negotiation(self, tx: Transaction, request) -> Dict[str, Any]:
        session = self.active_sessions.get(tx.tx_id)
        if not session:
            # Try to find session by looking up transaction status
            if tx.status != "negotiating":
                return {"status": "error", "code": 410, "payload": {"error": "Negotiation session expired or not found"}}
            # Recreate session from transaction
            session_id = f"neg_{tx.tx_id}"
            session = {
                "session_id": session_id,
                "round": tx.negotiation_round,
                "constraints": tx.agent_constraints or {},
                "agent_context": tx.agent_context or {},
                "history": []
            }
            self.active_sessions[tx.tx_id] = session

        session_id = session["session_id"]
        session["round"] += 1
        tx.negotiation_round = session["round"]

        if session["round"] > self.max_rounds:
            return {"status": "rejected", "code": 406, "payload": {"error": "max_rounds_exceeded"}}

        # Extract counter_offer from intent_payload
        agent_counter = request.intent_payload.get("counter_offer")
        if not agent_counter:
            return {"status": "rejected", "code": 400, "payload": {"error": "Missing counter_offer in intent_payload"}}

        # Get their price from counter_offer
        their_price = float(agent_counter.get("price", 0))
        if their_price <= 0:
            return {"status": "rejected", "code": 400, "payload": {"error": "Invalid counter_offer price"}}

        # Get our last offer price from history or current_offer
        last_offer_price = None
        if session["history"]:
            last_offer_price = session["history"][-1].get("our_offer", {}).get("price")
        elif tx.current_offer:
            last_offer_price = tx.current_offer.get("price")
        
        if last_offer_price is None:
            # Fallback: use their price * 1.1 as starting point
            last_offer_price = their_price * 1.1

        # Split the difference
        next_price = (last_offer_price + their_price) / 2

        offer = Offer(
            price=round(next_price, 2),
            currency="AUD",
            terms={"cancellation": "24h_free"},
            valid_until=datetime.utcnow() + timedelta(minutes=10),
            offer_id=f"offer_{tx.tx_id}_r{session['round']}"
        )

        # If agent's price >= our new price, accept
        if their_price >= next_price:
            return await self._accept_offer(tx, offer, session_id)

        return await self._counter_offer(tx, offer, session_id)

    async def _generate_initial_offer(self, tx: Transaction, request) -> Offer:
        from app.acp.domains.hotel.adapter_factory import get_adapter
        from app.properties.registry import PropertyRegistry
        
        adapter = await get_adapter(tx.target_entity_id)
        
        # Get property tier configuration
        registry = PropertyRegistry()
        property = registry.get_property(tx.target_entity_id)
        tier = property.config_json.get("tier", "standard") if property else "standard"

        dates = request.intent_payload.get("dates", {})
        room_type = request.intent_payload.get("room_type", "deluxe_king")

        base_price = await adapter.get_base_price(tx.target_entity_id, dates, room_type)
        demand = await adapter.get_demand_multiplier(tx.target_entity_id, dates)

        rep = float(request.agent_context.get("reputation_score", 0.5))
        
        # Apply tier-specific discount rules
        if tier == "budget":
            discount = base_price * (rep * 0.10)  # Smaller discounts
        elif tier == "luxury":
            discount = base_price * (rep * 0.20)  # Larger discounts for high-rep agents
        else:  # standard
            discount = base_price * (rep * 0.15)

        price = (base_price * demand) - discount
        price = max(1.0, price)

        # Tier-specific terms
        terms = {"cancellation": "24h_free"}
        
        if tier == "luxury":
            if rep > 0.7:
                terms["breakfast_included"] = True
                terms["late_checkout"] = True
            if rep > 0.9:
                terms["spa_access"] = True
        elif tier == "standard":
            if rep > 0.7:
                terms["breakfast_included"] = True
        # budget tier: minimal bundling

        return Offer(
            price=round(price, 2),
            currency="AUD",
            terms=terms,
            valid_until=datetime.utcnow() + timedelta(minutes=15),
            offer_id=f"offer_{tx.tx_id}_r0"
        )

    def _is_acceptable(self, offer: Offer, constraints: Dict[str, Any]) -> bool:
        budget = constraints.get("budget_max")
        if budget is not None and offer.price > float(budget):
            return False
        return True

    async def _accept_offer(self, tx: Transaction, offer: Offer, session_id: str) -> Dict[str, Any]:
        tx.negotiation_session_id = session_id
        await self.tx_manager.set_status(tx, "negotiated")

        return {
            "status": "negotiated",
            "code": 200,
            "session_id": session_id,
            "payload": {
                "our_offer": {
                    "price": offer.price,
                    "currency": offer.currency,
                    "terms": offer.terms,
                    "valid_until": offer.valid_until.isoformat(),
                    "offer_id": offer.offer_id
                },
                "next_step": "Call execute with negotiation_session_id"
            }
        }

    async def _counter_offer(self, tx: Transaction, offer: Offer, session_id: str) -> Dict[str, Any]:
        session = self.active_sessions.get(tx.tx_id)
        if session is not None:
            session["history"].append({"our_offer": {"price": offer.price}})

        return {
            "status": "counter",
            "code": 202,
            "session_id": session_id,
            "payload": {
                "our_offer": {
                    "price": offer.price,
                    "currency": offer.currency,
                    "terms": offer.terms,
                    "valid_until": offer.valid_until.isoformat(),
                    "offer_id": offer.offer_id
                },
                "round": session["round"] if session else 1,
                "message": "Respond with counter_offer in intent_payload"
            }
        }
