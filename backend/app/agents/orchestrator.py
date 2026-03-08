"""
Agent Orchestrator - Coordinates all agents in the A2A pipeline.
Manages WebSocket connections for live event broadcasting.
"""

import json
import asyncio
import uuid
from datetime import datetime, UTC
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect

from .base_agent import AgentEvent
from .guest_agent import GuestAgent
from .booking_agent import BookingAgent
from .pricing_agent import PricingAgent
from .negotiation_agent import NegotiationAgent
from .payment_agent import PaymentAgent
from .inventory_agent import InventoryAgent
from .operations_agent import OperationsAgent


# ─── WebSocket Connection Manager ────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self.active.append(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            if ws in self.active:
                self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        msg = json.dumps(data)
        for ws in list(self.active):
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    @property
    def connected_count(self):
        return len(self.active)


connection_manager = ConnectionManager()


# ─── Agent Status Store ────────────────────────────────────────────────────────

class AgentStatusStore:
    """Tracks current status of all agents for the dashboard."""

    AGENTS = [
        {"agent_id": "guest_agent",       "name": "Guest Agent",       "role": "Intent & NLP"},
        {"agent_id": "booking_agent",     "name": "Booking Agent",     "role": "Availability"},
        {"agent_id": "pricing_agent",     "name": "Pricing Agent",     "role": "Dynamic Pricing"},
        {"agent_id": "negotiation_agent", "name": "Negotiation Agent", "role": "Discount Engine"},
        {"agent_id": "payment_agent",     "name": "Payment Agent",     "role": "Transactions"},
        {"agent_id": "inventory_agent",   "name": "Inventory Agent",   "role": "Room Inventory"},
        {"agent_id": "operations_agent",  "name": "Operations Agent",  "role": "Housekeeping"},
        {"agent_id": "orchestrator",      "name": "Orchestrator",      "role": "Coordinator"},
    ]

    def __init__(self):
        self._statuses = {a["agent_id"]: "idle" for a in self.AGENTS}

    def update(self, agent_id: str, status: str):
        self._statuses[agent_id] = status

    def get_all(self) -> list:
        return [
            {**agent, "status": self._statuses.get(agent["agent_id"], "idle")}
            for agent in self.AGENTS
        ]


agent_status_store = AgentStatusStore()


# ─── Orchestrator ──────────────────────────────────────────────────────────────

class AgentOrchestrator:
    def __init__(self):
        self._events: list[dict] = []  # Recent events buffer (last 200)
        self._setup_agents()

    def _setup_agents(self):
        self.guest    = GuestAgent(broadcast_fn=self._on_agent_event)
        self.booking  = BookingAgent(broadcast_fn=self._on_agent_event)
        self.pricing  = PricingAgent(broadcast_fn=self._on_agent_event)
        self.nego     = NegotiationAgent(broadcast_fn=self._on_agent_event)
        self.payment  = PaymentAgent(broadcast_fn=self._on_agent_event)
        self.inventory = InventoryAgent(broadcast_fn=self._on_agent_event)
        self.ops       = OperationsAgent(broadcast_fn=self._on_agent_event)

    async def _on_agent_event(self, event: AgentEvent):
        """Callback: update status store, buffer event, broadcast via WS."""
        agent_status_store.update(event.agent_id, event.status)
        payload = {
            "type": "agent_event",
            "event": {
                **event.to_dict(),
                "color": self.guest.AGENT_COLORS.get(event.agent_id, "#94A3B8"),
            },
        }
        # Also broadcast agent statuses
        statuses_payload = {
            "type": "agent_statuses",
            "agents": agent_status_store.get_all(),
        }
        self._events.append(payload)
        if len(self._events) > 200:
            self._events.pop(0)

        await connection_manager.broadcast(payload)
        await connection_manager.broadcast(statuses_payload)

    async def _orch_broadcast(self, action: str, content: str, status: str = "processing"):
        event = AgentEvent(
            agent_id="orchestrator",
            agent_name="Orchestrator",
            status=status,
            action=action,
            content=content,
        )
        await self._on_agent_event(event)

    async def run(self, message: str, session_id: str = "") -> dict:
        """Main A2A pipeline entry point."""
        if not session_id:
            session_id = str(uuid.uuid4())[:8]

        await self._orch_broadcast("Pipeline Started", f"Session {session_id}: Starting A2A pipeline")

        # Reset all agents to idle
        for aid in agent_status_store._statuses:
            agent_status_store.update(aid, "idle")
        agent_status_store.update("orchestrator", "processing")

        try:
            # 1. Guest Agent - parse intent
            intent = await self.guest.analyze(message, session_id)

            # 2. For booking/availability intents, run the full pipeline
            if intent.get("intent") in ("booking", "availability", "negotiation"):
                entities = intent.get("entities", {})

                # 3. Inventory check (parallel feel)
                await self.inventory.get_inventory_snapshot(session_id)

                # 4. Booking Agent - availability
                availability = await self.booking.check_availability(entities, session_id)

                # 5. Pricing Agent - calculate costs
                pricing = await self.pricing.calculate(availability.get("rooms", []), entities, session_id)

                # 6. Negotiation Agent (if discount requested)
                negotiation = None
                if entities.get("discount_requested") or intent.get("intent") == "negotiation":
                    discount = entities.get("discount_percent") or 10
                    negotiation = await self.nego.negotiate(discount, pricing, entities, session_id)

                # 7. Payment Agent - confirm booking
                payment = await self.payment.process(pricing, availability, entities, negotiation, session_id)

                # 8. Operations Agent - post-booking tasks
                await self.ops.post_booking_ops(
                    payment.get("confirmation", "SHH-XXX"),
                    payment.get("room_type", "Standard"),
                    availability.get("check_in", ""),
                    session_id,
                )

                await self._orch_broadcast(
                    "Pipeline Complete",
                    f"✓ Booking {payment.get('confirmation')} confirmed. Total: ${payment.get('total_charged', 0)}",
                    "completed",
                )

                # Build natural language response
                conf = payment.get("confirmation", "SHH-XXXXX")
                total = (negotiation or {}).get("new_total") or pricing.get("grand_total", 0)
                nights = pricing.get("nights", 1)
                room_type = payment.get("room_type", "Standard")
                check_in = availability.get("check_in", "")
                check_out = availability.get("check_out", "")

                discount_note = ""
                if negotiation and negotiation.get("approved"):
                    discount_note = f"\n\n✓ **{negotiation['discount_percent']}% discount applied** — you save ${negotiation.get('savings', 0)}"

                response = (
                    f"🎉 **Booking Confirmed!**\n\n"
                    f"**Confirmation:** {conf}\n"
                    f"**Room:** {room_type}\n"
                    f"**Dates:** {check_in} → {check_out} ({nights} nights)\n"
                    f"**Total:** ${total}"
                    f"{discount_note}\n\n"
                    f"✅ Your reservation is confirmed. We look forward to welcoming you!"
                )

                return {
                    "response": response,
                    "action": "booking_confirmed",
                    "session_id": session_id,
                    "data": {"confirmation": conf, "total": total},
                }

            else:
                # For general inquiries, use the existing RAG-based answer
                agent_status_store.update("orchestrator", "idle")
                return {
                    "response": None,  # Signal to use existing chatbot
                    "action": "general",
                    "session_id": session_id,
                }

        except Exception as e:
            print(f"[Orchestrator] Pipeline error: {e}")
            import traceback; traceback.print_exc()
            await self._orch_broadcast("Pipeline Error", f"Error in pipeline: gracefully recovering", "error")
            agent_status_store.update("orchestrator", "idle")
            return {"response": None, "action": "error", "session_id": session_id}

    def get_recent_events(self, limit: int = 50) -> list:
        return self._events[-limit:]

    def get_agent_statuses(self) -> list:
        return agent_status_store.get_all()


# Singleton
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
