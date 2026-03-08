"""
Booking API Tests - Guided Booking Flow + Stripe Integration

Tests for:
- GET /api/booking/services - Available add-on services
- POST /api/booking/rooms/available - Available rooms for date range
- POST /api/booking/summary - Booking summary with price breakdown
- POST /api/booking/checkout - Stripe checkout session creation (MOCKED - uses test key)
- GET /api/booking/status/{booking_id} - Booking status lookup
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TENANT_ID = "default-tenant-0000"

# Calculate future dates for testing
today = datetime.now()
check_in_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")
check_out_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")


@pytest.fixture
def api_client():
    """Shared requests session with tenant header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID
    })
    return session


class TestBookingServices:
    """Tests for GET /api/booking/services - Add-on services endpoint"""
    
    def test_get_services_success(self, api_client):
        """Should return list of 6 available services"""
        response = api_client.get(f"{BASE_URL}/api/booking/services")
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Data validation
        data = response.json()
        assert "services" in data
        services = data["services"]
        
        # Should have 6 services
        assert len(services) == 6, f"Expected 6 services, got {len(services)}"
        
        # Check service IDs
        expected_ids = {"breakfast", "airport_pickup", "late_checkout", "extra_bed", "parking", "spa_access"}
        actual_ids = {s["id"] for s in services}
        assert expected_ids == actual_ids, f"Expected services {expected_ids}, got {actual_ids}"
        
        # Validate service structure
        for service in services:
            assert "id" in service
            assert "name" in service
            assert "description" in service
            assert "price" in service
            assert "per_night" in service
            assert isinstance(service["price"], (int, float))
            assert service["price"] > 0
    
    def test_services_prices_correct(self, api_client):
        """Should return correct prices for each service"""
        response = api_client.get(f"{BASE_URL}/api/booking/services")
        data = response.json()
        
        expected_prices = {
            "breakfast": 25.0,
            "airport_pickup": 45.0,
            "late_checkout": 35.0,
            "extra_bed": 30.0,
            "parking": 20.0,
            "spa_access": 40.0
        }
        
        for service in data["services"]:
            assert service["price"] == expected_prices[service["id"]], \
                f"Service {service['id']} price mismatch: expected {expected_prices[service['id']]}, got {service['price']}"


class TestRoomsAvailable:
    """Tests for POST /api/booking/rooms/available - Room availability endpoint"""
    
    def test_get_available_rooms_success(self, api_client):
        """Should return available rooms for valid date range"""
        payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        # Status check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data validation
        data = response.json()
        assert "check_in" in data
        assert "check_out" in data
        assert "nights" in data
        assert "guests" in data
        assert "room_types" in data
        assert "total_available" in data
        
        # Verify dates match request
        assert data["check_in"] == check_in_date
        assert data["check_out"] == check_out_date
        assert data["guests"] == 2
        assert data["nights"] == 2
        
        # Room types should be list
        assert isinstance(data["room_types"], list)
        assert data["total_available"] > 0, "Should have available rooms"
    
    def test_room_types_structure(self, api_client):
        """Should return properly structured room type data"""
        payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        data = response.json()
        
        # Check room type structure
        for room_type in data["room_types"]:
            assert "room_type" in room_type
            assert "price_per_night" in room_type
            assert "total_price" in room_type
            assert "capacity" in room_type
            assert "description" in room_type
            assert "available_count" in room_type
            assert "rooms" in room_type
            
            # Rooms should be list with room details
            assert isinstance(room_type["rooms"], list)
            if room_type["rooms"]:
                room = room_type["rooms"][0]
                assert "id" in room
                assert "room_number" in room
                assert "price_per_night" in room
    
    def test_room_prices_match_expected(self, api_client):
        """Should return correct base prices for room types"""
        payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        data = response.json()
        
        expected_prices = {
            "Standard": 180.0,
            "Deluxe": 260.0,
            "Suite": 420.0,
            "Ocean View": 320.0,
            "Penthouse": 780.0
        }
        
        for room_type in data["room_types"]:
            type_name = room_type["room_type"]
            if type_name in expected_prices:
                assert room_type["price_per_night"] == expected_prices[type_name], \
                    f"{type_name} price mismatch: expected {expected_prices[type_name]}, got {room_type['price_per_night']}"
    
    def test_past_checkin_date_rejected(self, api_client):
        """Should reject check-in dates in the past"""
        past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        payload = {
            "check_in": past_date,
            "check_out": check_out_date,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()
    
    def test_checkout_before_checkin_rejected(self, api_client):
        """Should reject checkout date before or equal to check-in"""
        payload = {
            "check_in": check_out_date,
            "check_out": check_in_date,  # Before check-in
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 400
        assert "after" in response.json()["detail"].lower()
    
    def test_guests_capacity_filter(self, api_client):
        """Should filter rooms by guest capacity"""
        # Request for large group
        payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 6
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned rooms should have capacity >= 6
        for room_type in data["room_types"]:
            assert room_type["capacity"] >= 6, \
                f"{room_type['room_type']} has capacity {room_type['capacity']} but guest count is 6"


class TestBookingSummary:
    """Tests for POST /api/booking/summary - Booking summary with price breakdown"""
    
    @pytest.fixture
    def room_id(self, api_client):
        """Get a valid room ID from available rooms"""
        payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        data = response.json()
        
        if data["room_types"]:
            return data["room_types"][0]["rooms"][0]["id"]
        pytest.skip("No rooms available for testing")
    
    def test_create_summary_success(self, api_client, room_id):
        """Should create booking summary with correct calculations"""
        payload = {
            "room_id": room_id,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": []
        }
        response = api_client.post(f"{BASE_URL}/api/booking/summary", json=payload)
        
        assert response.status_code == 200
        
        data = response.json()
        # Verify summary structure
        assert "room" in data
        assert "check_in" in data
        assert "check_out" in data
        assert "nights" in data
        assert "guests" in data
        assert "services" in data
        assert "room_total" in data
        assert "services_total" in data
        assert "taxes" in data
        assert "total" in data
        assert "breakdown" in data
    
    def test_summary_with_services(self, api_client, room_id):
        """Should correctly calculate services in summary"""
        payload = {
            "room_id": room_id,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": ["breakfast", "parking"]
        }
        response = api_client.post(f"{BASE_URL}/api/booking/summary", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Services should be populated
        assert len(data["services"]) == 2
        
        service_ids = [s["id"] for s in data["services"]]
        assert "breakfast" in service_ids
        assert "parking" in service_ids
        
        # Services total should be > 0
        assert data["services_total"] > 0
    
    def test_summary_price_breakdown(self, api_client, room_id):
        """Should return correct price breakdown"""
        payload = {
            "room_id": room_id,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": ["breakfast"]
        }
        response = api_client.post(f"{BASE_URL}/api/booking/summary", json=payload)
        data = response.json()
        
        # Breakdown should include room + services + taxes
        breakdown = data["breakdown"]
        assert len(breakdown) >= 2  # At least room + taxes
        
        # Last item should be taxes
        assert "Taxes" in breakdown[-1]["item"]
    
    def test_summary_tax_calculation(self, api_client, room_id):
        """Should calculate 10% tax correctly"""
        payload = {
            "room_id": room_id,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": []
        }
        response = api_client.post(f"{BASE_URL}/api/booking/summary", json=payload)
        data = response.json()
        
        subtotal = data["room_total"] + data["services_total"]
        expected_taxes = round(subtotal * 0.10, 2)
        
        assert data["taxes"] == expected_taxes, \
            f"Tax calculation wrong: expected {expected_taxes}, got {data['taxes']}"
        
        # Total should be subtotal + taxes
        expected_total = round(subtotal + expected_taxes, 2)
        assert data["total"] == expected_total
    
    def test_summary_invalid_room_id(self, api_client):
        """Should return 404 for invalid room ID"""
        payload = {
            "room_id": "invalid-room-id-12345",
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": []
        }
        response = api_client.post(f"{BASE_URL}/api/booking/summary", json=payload)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestBookingCheckout:
    """Tests for POST /api/booking/checkout - Stripe checkout session creation
    
    NOTE: This uses Stripe test key 'sk_test_emergent' - may have limited functionality
    """
    
    @pytest.fixture
    def booking_summary(self, api_client):
        """Get a valid booking summary for checkout"""
        # First get a room
        rooms_payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2
        }
        rooms_response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=rooms_payload)
        if rooms_response.status_code != 200:
            pytest.skip("No rooms available")
        
        room_id = rooms_response.json()["room_types"][0]["rooms"][0]["id"]
        
        # Then get summary
        summary_payload = {
            "room_id": room_id,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": ["breakfast"]
        }
        summary_response = api_client.post(f"{BASE_URL}/api/booking/summary", json=summary_payload)
        return summary_response.json()
    
    def test_checkout_creates_session(self, api_client, booking_summary):
        """Should create Stripe checkout session successfully"""
        payload = {
            "booking_summary": booking_summary,
            "guest_name": "TEST_Checkout_User",
            "guest_email": "test_checkout@example.com"
        }
        response = api_client.post(f"{BASE_URL}/api/booking/checkout", json=payload)
        
        # Should succeed with checkout URL
        assert response.status_code == 200, f"Checkout failed: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert "booking_id" in data
        
        # Checkout URL should be Stripe
        assert "stripe.com" in data["checkout_url"]
        
        # Session ID should start with cs_test
        assert data["session_id"].startswith("cs_test")
    
    def test_checkout_returns_booking_id(self, api_client, booking_summary):
        """Should return valid booking ID"""
        payload = {
            "booking_summary": booking_summary,
            "guest_name": "TEST_BookingID_User",
            "guest_email": "test_bookingid@example.com"
        }
        response = api_client.post(f"{BASE_URL}/api/booking/checkout", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Booking ID should be UUID format
        booking_id = data["booking_id"]
        assert len(booking_id) == 36  # UUID length with dashes
    
    def test_checkout_invalid_total_rejected(self, api_client):
        """Should reject checkout with zero or negative total"""
        payload = {
            "booking_summary": {"total": 0},
            "guest_name": "Test",
            "guest_email": "test@test.com"
        }
        response = api_client.post(f"{BASE_URL}/api/booking/checkout", json=payload)
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestBookingStatus:
    """Tests for GET /api/booking/status/{booking_id}"""
    
    def test_status_not_found(self, api_client):
        """Should return 404 for non-existent booking"""
        response = api_client.get(f"{BASE_URL}/api/booking/status/invalid-booking-id")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_status_returns_booking_details(self, api_client):
        """Should return booking details when found
        
        Create a real booking first via checkout
        """
        # First create a booking
        rooms_payload = {
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2
        }
        rooms_response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=rooms_payload)
        if rooms_response.status_code != 200:
            pytest.skip("No rooms available")
        
        room_data = rooms_response.json()["room_types"][0]["rooms"][0]
        room_id = room_data["id"]
        
        # Get summary
        summary_payload = {
            "room_id": room_id,
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "services": []
        }
        summary_response = api_client.post(f"{BASE_URL}/api/booking/summary", json=summary_payload)
        summary = summary_response.json()
        
        # Create checkout to get booking ID
        checkout_payload = {
            "booking_summary": summary,
            "guest_name": "TEST_Status_User",
            "guest_email": "test_status@example.com"
        }
        checkout_response = api_client.post(f"{BASE_URL}/api/booking/checkout", json=checkout_payload)
        booking_id = checkout_response.json()["booking_id"]
        
        # Now check status
        status_response = api_client.get(f"{BASE_URL}/api/booking/status/{booking_id}")
        
        assert status_response.status_code == 200
        data = status_response.json()
        
        assert data["booking_id"] == booking_id
        assert data["status"] == "pending_payment"
        assert data["guest_name"] == "TEST_Status_User"
        assert data["check_in"] == check_in_date
        assert data["check_out"] == check_out_date


class TestBookingWebhook:
    """Tests for POST /api/booking/webhook - Stripe webhook handler"""
    
    def test_webhook_endpoint_exists(self, api_client):
        """Should accept POST to webhook endpoint (even without valid signature)"""
        # Without valid Stripe signature, this will fail validation
        # but endpoint should exist and not 404
        response = api_client.post(f"{BASE_URL}/api/booking/webhook", data="{}")
        
        # Should not be 404
        assert response.status_code != 404, "Webhook endpoint not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
