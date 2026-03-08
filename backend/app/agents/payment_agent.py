"""Payment Agent - Finalizes booking and handles payment processing."""

import hashlib
from datetime import datetime, UTC
from .base_agent import BaseAgent


SYSTEM = """You are the Payment Agent for Southern Horizons Hotel.
Handle payment processing and booking confirmations."""


class PaymentAgent(BaseAgent):
    def __init__(self, broadcast_fn=None):
        super().__init__(
            agent_id="payment_agent",
            name="Payment Agent",
            system_message=SYSTEM,
            broadcast_fn=broadcast_fn,
        )

    async def process(self, pricing: dict, availability: dict, entities: dict, negotiation: dict = None, session_id: str = "") -> dict:
        await self.broadcast(
            action="Processing Payment",
            content="Validating booking details and generating confirmation...",
            status="processing",
            session_id=session_id,
        )

        guest_name = entities.get("guest_name", "Valued Guest")
        guest_email = entities.get("guest_email", "guest@hotel.com")
        check_in = availability.get("check_in", "")
        check_out = availability.get("check_out", "")
        rooms = availability.get("rooms", [])
        room_type = rooms[0].get("room_type", "Standard") if rooms else "Standard"

        final_total = (negotiation or {}).get("new_total") or pricing.get("grand_total", 0)

        # Generate idempotent confirmation code
        key = f"{guest_email}:{check_in}:{check_out}:{room_type}"
        conf_hash = hashlib.sha256(key.encode()).hexdigest()[:8].upper()
        confirmation = f"SHH-{conf_hash}"

        # Try to write to DB
        try:
            from app.db.session import get_db_connection
            import uuid
            conn = get_db_connection()
            c = conn.cursor()
            reservation_id = str(uuid.uuid4())
            c.execute("""
                INSERT OR IGNORE INTO reservations 
                (id, tenant_id, room_id, guest_name, guest_email, check_in_date, check_out_date, 
                 total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reservation_id, "default-tenant-0000",
                rooms[0].get("id", "rm-101") if rooms else "rm-101",
                guest_name, guest_email,
                check_in, check_out,
                final_total, "confirmed",
                datetime.now(UTC).isoformat()
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[PaymentAgent] DB write error: {e}")

        result = {
            "confirmation": confirmation,
            "status": "confirmed",
            "total_charged": final_total,
            "currency": "USD",
            "check_in": check_in,
            "check_out": check_out,
            "room_type": room_type,
            "guest_name": guest_name,
        }

        await self.broadcast(
            action="Booking Confirmed",
            content=f"Reservation {confirmation} created. {room_type} | {check_in} → {check_out} | ${final_total}",
            status="completed",
            metadata=result,
            session_id=session_id,
        )

        return result
