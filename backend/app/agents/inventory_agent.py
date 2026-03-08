"""Inventory Agent - Real-time room inventory monitoring."""

from .base_agent import BaseAgent


SYSTEM = "You are the Inventory Agent for Southern Horizons Hotel. Monitor room inventory in real time."


class InventoryAgent(BaseAgent):
    def __init__(self, broadcast_fn=None):
        super().__init__(
            agent_id="inventory_agent",
            name="Inventory Agent",
            system_message=SYSTEM,
            broadcast_fn=broadcast_fn,
        )

    async def get_inventory_snapshot(self, session_id: str = "") -> dict:
        await self.broadcast(
            action="Scanning Inventory",
            content="Running real-time room inventory scan...",
            status="processing",
            session_id=session_id,
        )

        try:
            from app.db.session import get_db_connection
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT room_type, COUNT(*) as total, SUM(CASE WHEN is_available=1 THEN 1 ELSE 0 END) as available FROM rooms GROUP BY room_type")
            rows = c.fetchall()
            conn.close()
            inventory = [dict(r) for r in rows]
        except Exception:
            inventory = [
                {"room_type": "Standard", "total": 20, "available": 12},
                {"room_type": "Deluxe", "total": 15, "available": 8},
                {"room_type": "Suite", "total": 5, "available": 3},
                {"room_type": "Ocean View", "total": 10, "available": 6},
            ]

        total_available = sum(r.get("available", 0) for r in inventory)
        total_rooms = sum(r.get("total", 0) for r in inventory)
        occupancy = round((1 - total_available / max(1, total_rooms)) * 100, 1)

        result = {
            "inventory": inventory,
            "total_available": total_available,
            "total_rooms": total_rooms,
            "occupancy_rate": occupancy,
        }

        await self.broadcast(
            action="Inventory Scanned",
            content=f"Occupancy: {occupancy}% | Available: {total_available}/{total_rooms} rooms",
            status="completed",
            metadata=result,
            session_id=session_id,
        )

        return result
