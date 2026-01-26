
import pytest
import sqlite3
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from app.db.seeds import seed_commerce_data
from app.services.commerce_service import CommerceService

def test_commerce_e2e():
    print("\n--- Starting Commerce E2E Test ---")
    
    # 1. Setup
    init_db()
    tenant_id = "tenant_e2e"
    
    # Clean up
    conn = get_db_connection()
    tables = ["restaurant_bookings", "event_bookings", "venue_tables", "venues", "events", "orders"]
    for t in tables:
        # Check if table exists (orders might not be seeded but created)
        try:
            conn.execute(f"DELETE FROM {t} WHERE tenant_id = ?", (tenant_id,))
        except:
            pass
            
    # Cleanup venues via subquery for venue_tables
    conn.execute(f"DELETE FROM venue_tables WHERE venue_id IN (SELECT id FROM venues WHERE tenant_id = ?)", (tenant_id,))
    conn.commit()
    conn.close()
    
    # 2. Seed
    print("[Test] Seeding...")
    seed_commerce_data(tenant_id)
    
    service = CommerceService(tenant_id)
    
    # 3. List
    print("[Test] Listing Restaurants...")
    result = service.list_restaurants()
    renders = result["restaurants"]
    assert len(renders) == 3
    print(f"Found {len(renders)} restaurants.")
    
    target_venue = renders[0]
    v_id = target_venue["id"]
    print(f"Target Venue: {target_venue['name']} ({v_id})")
    
    # 4. Check Availability (Should be 10 tables)
    print("[Test] Checking Availability...")
    tables, err = service.get_available_tables(v_id, "2026-06-01", "19:00", 2)
    assert len(tables) == 10
    print(f"Available Tables: {len(tables)}")
    
    # 5. Reserve ALL tables
    print("[Test] Reserving ALL tables...")
    for i in range(10):
        resp = service.reserve_table(v_id, "2026-06-01", "19:00", 2, f"Guest {i}")
        assert "Confirmed" in resp
        
    # 6. Check Availability (Should be 0)
    print("[Test] Verifying Sold Out...")
    tables_after, err = service.get_available_tables(v_id, "2026-06-01", "19:00", 2)
    assert len(tables_after) == 0
    print(f"Available Tables after booking: {len(tables_after)}")
    
    # 7. Events & Tickets
    print("[Test] Event Tickets...")
    events = service.list_events()["events"]
    target_event = events[0]
    e_id = target_event["id"]
    
    # Check initial
    avail = service.check_event_availability(e_id, "2026-06-01", 1)
    initial_left = avail['seats_left']
    print(f"Event '{target_event['name']}' has {initial_left} tickets left.")
    
    # Buy 5
    print("[Test] Buying 5 tickets...")
    resp = service.buy_event_tickets(e_id, "2026-06-01", 5, "Guest Ticket")
    assert "Purchased" in resp
    
    # Check after
    avail_after = service.check_event_availability(e_id, "2026-06-01", 1)
    print(f"Left after: {avail_after['seats_left']}")
    assert avail_after['seats_left'] == initial_left - 5

    print("--- Commerce E2E Passed ---")

if __name__ == "__main__":
    test_commerce_e2e()
