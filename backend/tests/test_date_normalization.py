"""
Date Normalization Tests - P0 Bug Fix Verification

Tests for:
- Malformed year normalization (0026 -> 2026)
- Invalid year rejection (0001 -> error)
- Normal date processing
- Edge cases in date handling

Bug Context:
The browser date picker behavior can result in years like '0026' when user types '26'.
The fix normalizes these malformed years in both frontend and backend.
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TENANT_ID = "default-tenant-0000"

# Calculate future dates for testing
today = datetime.now()
current_year = today.year
future_month = (today + timedelta(days=60)).strftime("%m")
future_day = (today + timedelta(days=60)).strftime("%d")


@pytest.fixture
def api_client():
    """Shared requests session with tenant header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID
    })
    return session


class TestBackendDateNormalization:
    """Tests for backend normalize_date_string function via /api/booking/rooms/available"""
    
    def test_normal_dates_accepted(self, api_client):
        """Should accept properly formatted dates"""
        check_in = f"{current_year}-{future_month}-15"
        check_out = f"{current_year}-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["nights"] == 2
    
    def test_malformed_year_0026_normalized_to_2026(self, api_client):
        """Should normalize malformed year 0026 to 2026 (P0 Bug Fix)"""
        # This is the main bug scenario: year '0026' should become '2026'
        check_in = f"0026-{future_month}-15"
        check_out = f"0026-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        # Should succeed (0026 normalized to 2026)
        assert response.status_code == 200, f"Failed to normalize 0026: {response.text}"
        data = response.json()
        assert data["nights"] == 2
    
    def test_malformed_year_0027_normalized(self, api_client):
        """Should normalize malformed year 0027 to 2027"""
        check_in = f"0027-{future_month}-15"
        check_out = f"0027-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 200, f"Failed to normalize 0027: {response.text}"
    
    def test_malformed_year_026_normalized(self, api_client):
        """Should normalize malformed year 026 to 2026"""
        check_in = f"026-{future_month}-15"
        check_out = f"026-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        # Should succeed (026 normalized to 2026)
        assert response.status_code == 200, f"Failed to normalize 026: {response.text}"
    
    def test_invalid_year_0001_rejected(self, api_client):
        """Should reject years like 0001 that can't be normalized to valid range"""
        check_in = f"0001-{future_month}-15"
        check_out = f"0001-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        # Should fail with error about invalid year
        assert response.status_code == 400, f"Expected 400 for year 0001, got {response.status_code}"
        assert "year" in response.text.lower() or "date" in response.text.lower()
    
    def test_two_digit_year_26_normalized(self, api_client):
        """Should normalize two-digit year 26 to 2026"""
        check_in = f"26-{future_month}-15"
        check_out = f"26-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        # Should succeed with normalization
        assert response.status_code == 200, f"Failed to normalize 26: {response.text}"
    
    def test_far_future_year_rejected(self, api_client):
        """Should reject years too far in the future"""
        far_future = current_year + 10
        check_in = f"{far_future}-{future_month}-15"
        check_out = f"{far_future}-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        # Should fail with error about year range
        assert response.status_code == 400, f"Expected 400 for year {far_future}, got {response.status_code}"


class TestBookingSummaryDateNormalization:
    """Tests for date normalization in booking summary endpoint"""
    
    @pytest.fixture
    def room_id(self, api_client):
        """Get a valid room ID"""
        check_in = f"{current_year}-{future_month}-15"
        check_out = f"{current_year}-{future_month}-17"
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        if response.status_code != 200:
            pytest.skip("No rooms available")
        
        data = response.json()
        if data["room_types"]:
            return data["room_types"][0]["rooms"][0]["id"]
        pytest.skip("No rooms available")
    
    def test_summary_with_malformed_dates(self, api_client, room_id):
        """Should handle malformed dates in summary request"""
        payload = {
            "room_id": room_id,
            "check_in": f"0026-{future_month}-15",
            "check_out": f"0026-{future_month}-17",
            "guests": 2,
            "services": []
        }
        response = api_client.post(f"{BASE_URL}/api/booking/summary", json=payload)
        
        # Should succeed with normalized dates
        assert response.status_code == 200, f"Summary failed with malformed dates: {response.text}"
        data = response.json()
        assert data["nights"] == 2


class TestDateValidationEdgeCases:
    """Edge cases for date validation"""
    
    def test_same_checkin_checkout_rejected(self, api_client):
        """Should reject when check-in and check-out are the same date"""
        check_date = f"{current_year}-{future_month}-15"
        
        payload = {
            "check_in": check_date,
            "check_out": check_date,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 400
        assert "after" in response.text.lower()
    
    def test_max_stay_30_nights(self, api_client):
        """Should reject stays longer than 30 nights"""
        check_in = f"{current_year}-{future_month}-01"
        check_out = f"{current_year + 1}-{future_month}-15"  # More than 30 days
        
        payload = {
            "check_in": check_in,
            "check_out": check_out,
            "guests": 2
        }
        response = api_client.post(f"{BASE_URL}/api/booking/rooms/available", json=payload)
        
        assert response.status_code == 400
        assert "30" in response.text or "maximum" in response.text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
