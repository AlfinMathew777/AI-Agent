
import pytest
import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db
from app.integrations.registry import get_provider_set
from app.integrations.mock_room import MockRoomProvider
from app.integrations.mock_dining import MockDiningProvider
from app.integrations.mock_event import MockEventProvider
from app.agent.tools import ToolRegistry

# Mock MCP Client (stub)
class MockMCP:
    pass

@pytest.mark.asyncio
async def test_provider_registry():
    print("\n--- Testing Provider Registry ---")
    tenant_id = "tenant_prov_test"
    providers = get_provider_set(tenant_id)
    
    assert isinstance(providers.room, MockRoomProvider)
    assert isinstance(providers.dining, MockDiningProvider)
    assert isinstance(providers.event, MockEventProvider)
    print("✅ Registry returned correct mock providers.")

@pytest.mark.asyncio
async def test_tools_use_providers():
    print("\n--- Testing Tools Integration ---")
    init_db()
    
    # Clear bookings to ensure availability
    from app.db.session import get_db_connection
    conn = get_db_connection()
    conn.execute("DELETE FROM bookings")
    conn.commit()
    conn.close()
    
    # 1. Setup
    registry = ToolRegistry(MockMCP())
    tenant_id = "tenant_prov_test_2" # Use unique tenant to avoid collisions if persistence
    
    # 2. List Restaurants (Using Provider)
    # Note: Commerce Logic relies on DB data. We might need to seed if empty.
    # But list_restaurants just queries 'venues'. If empty, returns empty list.
    # Checks if format matches.
    
    res_json = await registry.execute("list_restaurants", {"party_size": 2}, tenant_id)
    res = json.loads(res_json)
    assert "restaurants" in res
    print("✅ list_restaurants executed successfully via provider.")

    # 3. Check Room Availability (Using Provider)
    # Check "Standard" room "Tomorrow"
    res_str = await registry.execute(
        "check_room_availability", 
        {"room_type": "Standard", "date": "Tomorrow"}, 
        tenant_id
    )
    print(f"Room Avail Result: {res_str}")
    assert "Standard rooms are" in res_str
    print("✅ check_room_availability executed successfully via provider.")
    
    # 4. Book Room (Using Provider)
    res_book = await registry.execute(
        "book_room",
        {"guest_name": "Provider Tester", "room_type": "Standard", "date": "Tomorrow"},
        tenant_id
    )
    print(f"Book Room Result: {res_book}")
    # Default mock logic (and underlying create_booking) should succeed if DB init correct.
    # "🎉 Success! Room booked..."
    assert "Success!" in res_book or "booked" in res_book
    print("✅ book_room executed successfully via provider.")

if __name__ == "__main__":
    asyncio.run(test_provider_registry())
    asyncio.run(test_tools_use_providers())
