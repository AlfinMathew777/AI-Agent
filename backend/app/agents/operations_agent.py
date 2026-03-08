"""Operations Agent - Housekeeping, check-in/out, and operational tasks."""

from datetime import datetime, UTC
from .base_agent import BaseAgent


SYSTEM = "You are the Operations Agent for Southern Horizons Hotel. Coordinate housekeeping and operational tasks."


class OperationsAgent(BaseAgent):
    def __init__(self, broadcast_fn=None):
        super().__init__(
            agent_id="operations_agent",
            name="Operations Agent",
            system_message=SYSTEM,
            broadcast_fn=broadcast_fn,
        )

    async def post_booking_ops(self, confirmation: str, room_type: str, check_in: str, session_id: str = "") -> dict:
        await self.broadcast(
            action="Triggering Ops Tasks",
            content=f"Scheduling housekeeping and pre-arrival setup for {confirmation}...",
            status="processing",
            session_id=session_id,
        )

        tasks = [
            {"task": "Room preparation", "assigned_to": "Housekeeping Team A", "due": check_in, "status": "scheduled"},
            {"task": "Welcome amenities", "assigned_to": "Concierge", "due": check_in, "status": "scheduled"},
            {"task": "Key card activation", "assigned_to": "Front Desk", "due": check_in, "status": "pending"},
        ]

        try:
            from app.db.session import get_db_connection
            import uuid
            conn = get_db_connection()
            c = conn.cursor()
            for task in tasks:
                c.execute("""
                    INSERT OR IGNORE INTO housekeeping_tasks (id, tenant_id, task_type, assigned_to, due_date, status, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), "default-tenant-0000",
                    task["task"], task["assigned_to"], task["due"], task["status"],
                    f"Auto-created for reservation {confirmation}", datetime.now(UTC).isoformat()
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[OpsAgent] DB error: {e}")

        result = {"tasks_created": len(tasks), "tasks": tasks, "reservation": confirmation}

        await self.broadcast(
            action="Ops Tasks Scheduled",
            content=f"{len(tasks)} operational tasks created for {confirmation}: {', '.join(t['task'] for t in tasks)}",
            status="completed",
            metadata=result,
            session_id=session_id,
        )

        return result
