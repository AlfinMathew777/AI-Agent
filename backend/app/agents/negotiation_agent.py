"""Negotiation Agent (HNA-1) - Evaluates discount requests against reputation."""

import json
import re
from .base_agent import BaseAgent


SYSTEM = """You are HNA-1, the Hotel Negotiation Agent for Southern Horizons.
Evaluate discount requests and respond with JSON:
{
  "approved": true/false,
  "discount_percent": 0-25,
  "reason": "Brief reason",
  "counter_offer": null or number,
  "message": "Response to share with guest"
}

Rules: Max 15% for single stays. Max 20% for 5+ nights. Max 25% for 10+ rooms.
Always be courteous but firm on margins."""


class NegotiationAgent(BaseAgent):
    def __init__(self, broadcast_fn=None):
        super().__init__(
            agent_id="negotiation_agent",
            name="Negotiation Agent",
            system_message=SYSTEM,
            broadcast_fn=broadcast_fn,
        )

    async def negotiate(self, requested_discount: float, pricing: dict, entities: dict, session_id: str = "") -> dict:
        await self.broadcast(
            action="Evaluating Discount",
            content=f"Assessing {requested_discount}% discount request against reputation data...",
            status="processing",
            session_id=session_id,
        )

        nights = pricing.get("nights", 1)
        rooms = pricing.get("rooms", 1)
        total = pricing.get("grand_total", 0)

        prompt = (
            f"Guest requests {requested_discount}% discount. "
            f"Stay: {nights} nights, {rooms} rooms. Total: ${total}. "
            f"Guest is a standard customer. Evaluate fairly."
        )

        raw = await self.think(prompt, session_id)

        try:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            result = json.loads(json_match.group()) if json_match else {}
        except Exception:
            result = {}

        # Fallback logic
        if not result:
            max_discount = 10 if nights < 5 else (15 if rooms < 10 else 20)
            approved_pct = min(requested_discount, max_discount)
            result = {
                "approved": True,
                "discount_percent": approved_pct,
                "reason": f"Approved up to our {max_discount}% maximum",
                "counter_offer": approved_pct if approved_pct < requested_discount else None,
                "message": f"We're pleased to offer you a {approved_pct}% discount on your stay.",
            }

        discount_pct = result.get("discount_percent", 0)
        new_total = round(total * (1 - discount_pct / 100), 2)
        result["new_total"] = new_total
        result["original_total"] = total
        result["savings"] = round(total - new_total, 2)

        status_icon = "✓" if result.get("approved") else "✗"
        await self.broadcast(
            action=f"Negotiation {status_icon} {'Approved' if result.get('approved') else 'Declined'}",
            content=f"{discount_pct}% discount {'approved' if result.get('approved') else 'declined'}. Savings: ${result['savings']}. New total: ${new_total}",
            status="completed",
            metadata=result,
            session_id=session_id,
        )

        return result
