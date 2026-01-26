
from typing import List, Dict, Any
from app.integrations.base import DiningProvider
from app.services.commerce_service import CommerceService

class MockDiningProvider(DiningProvider):
    def list_restaurants(self, tenant_id: str) -> List[Dict[str, Any]]:
        service = CommerceService(tenant_id)
        result = service.list_restaurants() # Returns {"restaurants": [...]}
        return result.get("restaurants", [])

    def check_table_availability(self, tenant_id: str, venue_id: str, date: str, time: str, party_size: int) -> Dict[str, Any]:
        service = CommerceService(tenant_id)
        tables, msg = service.get_available_tables(venue_id, date, time, party_size)
        
        if tables:
            return {
                "available": True,
                "count": len(tables),
                "first_table": tables[0]['table_number'],
                "message": "Available"
            }
        return {
            "available": False,
            "count": 0,
            "first_table": None,
            "message": msg or "No tables found"
        }

    def reserve_table(self, tenant_id: str, venue_id: str, date: str, time: str, party_size: int, customer_name: str) -> Dict[str, Any]:
        service = CommerceService(tenant_id)
        # Service returns a string message like "Reservation Confirmed! Booking ID: ... " or "Failed..."
        result_msg = service.reserve_table(venue_id, date, time, party_size, customer_name)
        
        status = "failed"
        booking_id = None
        
        if "Confirmed" in result_msg:
            status = "confirmed"
            # Extract ID if possible, or just pass message
            if "Booking ID: " in result_msg:
                try:
                    booking_id = result_msg.split("Booking ID: ")[1].split(" ")[0]
                except:
                    pass
        
        return {
            "status": status,
            "booking_id": booking_id,
            "message": result_msg
        }

    def cancel_table(self, tenant_id: str, booking_id: str) -> bool:
        service = CommerceService(tenant_id)
        return service.cancel_restaurant_booking(booking_id)
