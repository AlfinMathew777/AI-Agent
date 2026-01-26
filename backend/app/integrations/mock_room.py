
from typing import Dict, Any
from app.integrations.base import RoomProvider
from app.db.queries import check_room_availability, create_booking # Wraps existing logic

class MockRoomProvider(RoomProvider):
    def check_room_availability(self, tenant_id: str, room_type: str, date: str) -> Dict[str, Any]:
        # Existing query doesn't support tenant_id yet (Task 13.1 simplified DB),
        # but the prompt requires interfaces to have it.
        # We will assume existing logic works for the tenant context provided or default.
        # Note: check_room_availability in `queries.py` currently relies on global DB tables.
        # Ideally, we update `queries.py` to accept tenant_id, but prompt said "No breaking changes".
        # We'll pass it if possible, or ignore if the underlying function doesn't take it yet 
        # (and fix `queries.py` if needed, but safe refactor first).
        
        # Checking queries.py usage in tools.py: `check_room_availability(room_type, date)`
        # It ignores tenant_id. This is a known technical debt from earlier tasks 
        # (Task 13.1 A/B/C focused on CommerceService, Rooms were legacy).
        # We will wrap it as-is.
        
        is_available, booked, capacity = check_room_availability(room_type, date)
        remaining = capacity - booked
        
        return {
            "available": is_available,
            "remaining": remaining,
            "capacity": capacity,
            "booked": booked
        }

    def book_room(self, tenant_id: str, guest_name: str, room_type: str, date: str) -> Dict[str, Any]:
        booking_id = create_booking(guest_name, room_type, date)
        if booking_id:
            return {"booking_id": booking_id, "status": "confirmed"}
        return {"booking_id": None, "status": "failed"}

    def cancel_room_booking(self, tenant_id: str, booking_id: str) -> Dict[str, Any]:
        # Existing logic didn't have room cancellation exposed in tools.
        # We'll stub it or add a query if needed.
        # For now, stub as not implemented or simple success.
        return {"status": "not_implemented"}
