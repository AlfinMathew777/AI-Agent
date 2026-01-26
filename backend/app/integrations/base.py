
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class RoomProvider(ABC):
    @abstractmethod
    def check_room_availability(self, tenant_id: str, room_type: str, date: str) -> Dict[str, Any]:
        """
        Returns: {
            "available": bool,
            "remaining": int,
            "capacity": int,
            "booked": int
        }
        """
        pass

    @abstractmethod
    def book_room(self, tenant_id: str, guest_name: str, room_type: str, date: str) -> Dict[str, Any]:
        """
        Returns: {"booking_id": str} or None if failed
        """
        pass

    @abstractmethod
    def cancel_room_booking(self, tenant_id: str, booking_id: str) -> Dict[str, Any]:
        """
        Returns: {"status": "cancelled" | "failed"}
        """
        pass

class DiningProvider(ABC):
    @abstractmethod
    def list_restaurants(self, tenant_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def check_table_availability(self, tenant_id: str, venue_id: str, date: str, time: str, party_size: int) -> Dict[str, Any]:
        """
        Returns: {"available": bool, "count": int, "first_table": str, "message": str}
        """
        pass

    @abstractmethod
    def reserve_table(self, tenant_id: str, venue_id: str, date: str, time: str, party_size: int, customer_name: str) -> Dict[str, Any]:
        """
        Returns: {"booking_id": str, "status": "confirmed", "message": str}
        """
        pass

    @abstractmethod
    def cancel_table(self, tenant_id: str, booking_id: str) -> bool:
        pass

class EventProvider(ABC):
    @abstractmethod
    def list_events(self, tenant_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def check_event_availability(self, tenant_id: str, event_id: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Returns: {"available": bool, "seats_left": int}
        """
        pass

    @abstractmethod
    def buy_tickets(self, tenant_id: str, event_id: str, quantity: int, customer_name: str) -> Dict[str, Any]:
        """
        Returns: {"booking_id": str, "status": "confirmed", "message": str}
        """
        pass

    @abstractmethod
    def cancel_tickets(self, tenant_id: str, booking_id: str) -> bool:
        pass
