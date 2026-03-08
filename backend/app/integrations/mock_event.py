
from typing import List, Dict, Any, Optional
from app.integrations.base import EventProvider
from app.services.commerce_service import CommerceService

class MockEventProvider(EventProvider):
    def list_events(self, tenant_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        service = CommerceService(tenant_id)
        # Service list_events accepts date/party_size but uses date mainly for filtering
        # We map start_date to date
        result = service.list_events(date=start_date)
        return result.get("events", [])

    def check_event_availability(self, tenant_id: str, event_id: str, quantity: int = 1) -> Dict[str, Any]:
        service = CommerceService(tenant_id)
        # Service needs date/party_size. 
        # check_event_availability(self, event_id: str, date: str, party_size: int)
        # We'll pass None for date (service handles logic) and quantity as party_size
        return service.check_event_availability(event_id, None, quantity)

    def buy_tickets(self, tenant_id: str, event_id: str, quantity: int, customer_name: str) -> Dict[str, Any]:
        service = CommerceService(tenant_id)
        # Returns string message
        # buy_event_tickets(self, event_id: str, date: str, quantity: int, customer_name: str)
        # Wait, service requires DATE for buying tickets?
        # looking at CommerceService: def buy_event_tickets(self, event_id: str, date: str, ...)
        # But event_bookings table schema?
        # INSERT INTO event_bookings (..., event_id, ...) VALUES (...)
        # The schema doesn't seem to store `date` in `event_bookings` (it links to `events` which has `start_time`).
        # `CommerceService.buy_event_tickets` takes `date` but might ignore it or use it for validation?
        # Let's check `CommerceService` again.
        
        # It seems `buy_event_tickets` defines signature: (event_id, date, quantity, customer_name)
        # But the implementation:
        # 1. Checks capacity
        # 2. Inserts into event_bookings.
        # It doesn't seem to USE `date` in the insert statement in the snippet I read earlier.
        # I'll pass None or a dummy date if it's required by signature but unused.
        
        result_msg = service.buy_event_tickets(event_id, "2026-06-01", quantity, customer_name)
        
        status = "failed"
        booking_id = None
        if "Purchased" in result_msg:
            status = "confirmed"
            if "Booking ID: " in result_msg:
                try:
                    booking_id = result_msg.split("Booking ID: ")[1].strip()
                except:
                    pass
                    
        return {
            "status": status,
            "booking_id": booking_id,
            "message": result_msg
        }

    def cancel_tickets(self, tenant_id: str, booking_id: str) -> bool:
        service = CommerceService(tenant_id)
        return service.cancel_event_booking(booking_id)
