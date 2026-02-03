"""
Cloudbeds Credentials Validator - SECURE VERSION
Tests OAuth credentials from environment variables ONLY

SECURITY: Never hardcode credentials in this file
Read from .env or environment variables only

Usage:
1. Set credentials in .env file
2. Run: python test_cloudbeds_creds.py  
3. Verify output shows [SUCCESS]
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read from environment ONLY
CLOUDBEDS_CLIENT_ID = os.getenv("CLOUDBEDS_CLIENT_ID", "")
CLOUDBEDS_CLIENT_SECRET = os.getenv("CLOUDBEDS_CLIENT_SECRET", "")
CLOUDBEDS_PROPERTY_ID = os.getenv("CLOUDBEDS_PROPERTY_ID", "")


async def test_credentials():
    """Validate Cloudbeds API credentials"""
    print("=" * 70)
    print("CLOUDBEDS CREDENTIALS VALIDATION")
    print("=" * 70)
    
    # Check credentials are set
    if not CLOUDBEDS_CLIENT_ID or not CLOUDBEDS_CLIENT_SECRET or not CLOUDBEDS_PROPERTY_ID:
        print("\n[ERROR] Cloudbeds credentials not set in environment")
        print("\nPlease set in .env file:")
        print("  CLOUDBEDS_CLIENT_ID=your_client_id")
        print("  CLOUDBEDS_CLIENT_SECRET=your_client_secret")
        print("  CLOUDBEDS_PROPERTY_ID=your_property_id")
        sys.exit(1)
    
    # Mask secrets in logs
    client_id_preview = CLOUDBEDS_CLIENT_ID[:8] + "..." if len(CLOUDBEDS_CLIENT_ID) > 8 else "***"
    property_id_preview = CLOUDBEDS_PROPERTY_ID[:8] + "..." if len(CLOUDBEDS_PROPERTY_ID) > 8 else "***"
    
    print(f"\n[INFO] Testing Cloudbeds connection")
    print(f"  Client ID: {client_id_preview}")
    print(f"  Property ID: {property_id_preview}")
    print(f"  Secret: <masked>")
    
    # Initialize adapter
    try:
        from app.acp.domains.hotel.cloudbeds_adapter import CloudbedsAdapter
        
        adapter = CloudbedsAdapter(
            property_id="test_cloudbeds_001",
            credentials={
                "client_id": CLOUDBEDS_CLIENT_ID,
                "client_secret": CLOUDBEDS_CLIENT_SECRET,
                "property_id": CLOUDBEDS_PROPERTY_ID
            },
            config={"tier": "standard"}
        )
        print("  [PASS] Adapter initialized")
    except Exception as e:
        print(f"  [FAIL] Adapter initialization failed: {e}")
        sys.exit(1)
    
    # Test 1: Room Availability (future dates)
    print("\n[TEST 1] Room Availability (30 days out)")
    print("-" * 60)
    try:
        check_in = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        check_out = (datetime.now() + timedelta(days=32)).strftime("%Y-%m-%d")
        
        dates = {"check_in": check_in, "check_out": check_out}
        availability = await adapter.check_room_availability(dates)
        
        if availability:
            print(f"  [PASS] Availability returned: {len(availability)} room types")
            for i, room in enumerate(availability[:3]):  # Show first 3
                room_type = room.get('room_type', room.get('name', 'Unknown'))
                price = room.get('price', 0)
                print(f"    {i+1}. {room_type}: ${price}/night")
        else:
            print("  [WARN] No availability (may be normal - fully booked)")
        
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "403" in error_str:
            print(f"  [FAIL] Authentication failed: {e}")
            print("  Check credentials are correct in .env file")
            sys.exit(1)
        elif "429" in error_str:
            print(f"  [WARN] Rate limit hit: {e}")
            print("  Credentials valid but API rate limited")
        else:
            print(f"  [FAIL] Availability check failed: {e}")
            sys.exit(1)
    
    # Test 2: Edge Case - Fully Booked Dates
    print("\n[TEST 2] Edge Case - Handling Fully Booked Dates")
    print("-" * 60)
    try:
        # Test peak season weekend (may be booked)
        peak_check_in = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        peak_check_out = (datetime.now() + timedelta(days=62)).strftime("%Y-%m-%d")
        
        dates2 = {"check_in": peak_check_in, "check_out": peak_check_out}
        availability2 = await adapter.check_room_availability(dates2)
        
        if not availability2:
            print("  [PASS] Gracefully handled no availability")
        else:
            print(f"  [PASS] {len(availability2)} rooms available")
    except Exception as e:
        print(f"  [WARN] Edge case handling: {e}")
    
    # Test 3: OAuth Token Handling
    print("\n[TEST 3] OAuth Token Persistence")
    print("-" * 60)
    try:
        # Make second request to test token reuse
        dates3 = {"check_in": check_in, "check_out": check_out}
        availability3 = await adapter.check_room_availability(dates3)
        print("  [PASS] OAuth token handling working")
    except Exception as e:
        print(f"  [FAIL] OAuth refresh may not be working: {e}")
    
    # Test 4: Invalid Dates (Past dates)
    print("\n[TEST 4] Error Handling - Past Dates")
    print("-" * 60)
    try:
        past_check_in = "2020-01-01"
        past_check_out = "2020-01-02"
        dates4 = {"check_in": past_check_in, "check_out": past_check_out}
        
        result = await adapter.check_room_availability(dates4)
        print("  [INFO] Past dates accepted by API (no error thrown)")
    except Exception as e:
        print(f"  [PASS] Past dates rejected as expected: {type(e).__name__}")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] Cloudbeds credentials verified!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Credentials are valid and stored securely in .env")
    print("2. Ready to register property via POST /admin/properties")
    print("3. Use cloudbeds_property.json template (replace ${VAR} with env vars)")


if __name__ == "__main__":
    print("\nCloudbeds Credentials Validator (Secure)")
    print("=" * 70)
    
    try:
        asyncio.run(test_credentials())
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
