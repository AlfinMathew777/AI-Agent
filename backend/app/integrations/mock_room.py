
from typing import Dict, Any
from app.integrations.base import RoomProvider
from app.db.queries import check_room_availability, create_booking # Wraps existing logic

class MockRoomProvider(RoomProvider):
    def check_room_availability(self, tenant_id: str, room_type: str, date: str) -> Dict[str, Any]:
        """Check room availability for a specific tenant."""
        is_available, booked, capacity = check_room_availability(room_type, date, tenant_id)
        remaining = capacity - booked
        
        return {
            "available": is_available,
            "remaining": remaining,
            "capacity": capacity,
            "booked": booked
        }

    def book_room(self, tenant_id: str, guest_name: str, room_type: str, date: str) -> Dict[str, Any]:
        """Book a room for a specific tenant."""
        booking_id = create_booking(guest_name, room_type, date, tenant_id=tenant_id)
        if booking_id:
            return {"booking_id": booking_id, "status": "confirmed"}
        return {"booking_id": None, "status": "failed"}

    def cancel_room_booking(self, tenant_id: str, booking_id: str) -> Dict[str, Any]:
        # Existing logic didn't have room cancellation exposed in tools.
        # We'll stub it or add a query if needed.
        # For now, stub as not implemented or simple success.
        return {"status": "not_implemented"}
