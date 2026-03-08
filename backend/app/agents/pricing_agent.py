"""Pricing Agent - Dynamic pricing calculation with demand & occupancy factors."""

from datetime import date
from .base_agent import BaseAgent


SYSTEM = """You are the Pricing Agent for Southern Horizons Hotel.
Calculate total costs based on dynamic pricing factors."""


class PricingAgent(BaseAgent):
    def __init__(self, broadcast_fn=None):
        super().__init__(
            agent_id="pricing_agent",
            name="Pricing Agent",
            system_message=SYSTEM,
            broadcast_fn=broadcast_fn,
        )

    async def calculate(self, rooms: list, entities: dict, session_id: str = "") -> dict:
        await self.broadcast(
            action="Calculating Price",
            content="Applying dynamic pricing model...",
            status="processing",
            session_id=session_id,
        )

        # Determine nights
        nights = entities.get("nights") or 1
        try:
            from datetime import date as d_
            ci = entities.get("check_in")
            co = entities.get("check_out")
            if ci and co:
                nights = max(1, (d_.fromisoformat(co) - d_.fromisoformat(ci)).days)
        except Exception:
            pass

        num_rooms = entities.get("rooms") or 1
        base_price = rooms[0].get("price_per_night", 200) if rooms else 200

        # Dynamic pricing factors
        today = date.today()
        is_weekend = today.weekday() >= 4
        demand_multiplier = 1.15 if is_weekend else 1.0
        seasonal_multiplier = 1.2 if today.month in [12, 1, 7, 8] else 1.0

        adjusted_price = round(base_price * demand_multiplier * seasonal_multiplier, 2)
        total = round(adjusted_price * nights * num_rooms, 2)
        taxes = round(total * 0.12, 2)
        grand_total = round(total + taxes, 2)

        factors = []
        if is_weekend:
            factors.append("Weekend premium +15%")
        if seasonal_multiplier > 1.0:
            factors.append("Peak season +20%")

        result = {
            "base_price": base_price,
            "adjusted_price": adjusted_price,
            "nights": nights,
            "rooms": num_rooms,
            "subtotal": total,
            "taxes": taxes,
            "grand_total": grand_total,
            "factors": factors,
            "currency": "USD",
        }

        factors_str = f" ({', '.join(factors)})" if factors else " (Standard rate)"
        await self.broadcast(
            action="Pricing Calculated",
            content=f"${adjusted_price}/night × {nights} nights × {num_rooms} room(s){factors_str} = Total: ${grand_total}",
            status="completed",
            metadata=result,
            session_id=session_id,
        )

        return result
