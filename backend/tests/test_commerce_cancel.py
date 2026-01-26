
import pytest
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from app.db.seeds import seed_commerce_data
from app.services.commerce_service import CommerceService

def test_cancellation_logic():
    print("\n--- Starting Cancellation Test ---")
    
    # Setup
    tenant_id = "tenant_cancel_test"
    init_db()
    
    conn = get_db_connection()
    # Cleanup
    conn.execute("DELETE FROM restaurant_bookings WHERE tenant_id = ?", (tenant_id,))
    conn.execute("DELETE FROM venue_tables WHERE venue_id IN (SELECT id FROM venues WHERE tenant_id = ?)", (tenant_id,))
    conn.execute("DELETE FROM venues WHERE tenant_id = ?", (tenant_id,))
    conn.close()
    
    seed_commerce_data(tenant_id)
    service = CommerceService(tenant_id)
    
    # 1. Get a venue and fill it up
    rest = service.list_restaurants()["restaurants"][0]
    v_id = rest["id"]
    
    print(f"[Test] Venue: {rest['name']}")
    
    # Book all 10 tables
    booking_ids = []
    print("[Test] Booking 10 tables...")
    for i in range(10):
        resp = service.reserve_table(v_id, "2026-07-01", "19:00", 2, f"User {i}")
        # Extract ID (Hack: parse string "ID: <uuid> (Table 1)")
        # Ideally, return proper obj. But MVP string is fine.
        # Format: "Reservation Confirmed! Booking ID: 70dca... (Table 2)"
        bk_id = resp.split("Booking ID: ")[1].split(" ")[0]
        booking_ids.append(bk_id)
        
    # Verify Full
    avail, _ = service.get_available_tables(v_id, "2026-07-01", "19:00", 2)
    print(f"Tables available after booking: {len(avail)}")
    assert len(avail) == 0
    
    # 2. Cancel one
    target_bk = booking_ids[0]
    print(f"[Test] Cancelling booking {target_bk}...")
    success = service.cancel_restaurant_booking(target_bk)
    assert success is True
    
    # 3. Verify Availability Restored
    avail_after, _ = service.get_available_tables(v_id, "2026-07-01", "19:00", 2)
    print(f"Tables available after cancel: {len(avail_after)}")
    assert len(avail_after) == 1
    
    # 4. Verify Admin List sees status='cancelled'
    # We can't call endpoint directly without FastAPI test client, but we can query DB or simulate logic.
    # Let's query DB to check status.
    conn = get_db_connection()
    row = conn.execute("SELECT status FROM restaurant_bookings WHERE id = ?", (target_bk,)).fetchone()
    conn.close()
    
    print(f"Booking status in DB: {row[0]}")
    assert row[0] == "cancelled"

    print("--- Cancellation Test Passed ---")

if __name__ == "__main__":
    test_cancellation_logic()
