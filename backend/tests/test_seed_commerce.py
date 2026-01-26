
import pytest
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from app.db.seeds import seed_commerce_data

def test_seed_isolation_and_idempotency():
    """Verify that seeding works for multiple tenants and is idempotent."""
    
    # 1. Setup
    init_db()
    conn = get_db_connection()
    c = conn.cursor()
    
    tenant_a = "tenant-A-123"
    tenant_b = "tenant-B-456"
    
    # Clear existing data for these test tenants (in case of re-run)
    # 1. Booking Tables (have tenant_id)
    tables_with_tenant = ["restaurant_bookings", "event_bookings", "venues", "events"]
    for t in tables_with_tenant:
        # We need to be careful with Foreign Keys. Delete child tables first.
        pass
        
    # Correct Order: Bookings -> Venue Tables -> Venues -> Events
    c.execute("DELETE FROM restaurant_bookings WHERE tenant_id IN (?, ?)", (tenant_a, tenant_b))
    c.execute("DELETE FROM event_bookings WHERE tenant_id IN (?, ?)", (tenant_a, tenant_b))
    
    # Venue Tables (JOIN delete not supported in default sqlite DELETE? Use subquery)
    c.execute(f"DELETE FROM venue_tables WHERE venue_id IN (SELECT id FROM venues WHERE tenant_id IN (?, ?))", (tenant_a, tenant_b))
    
    c.execute("DELETE FROM venues WHERE tenant_id IN (?, ?)", (tenant_a, tenant_b))
    c.execute("DELETE FROM events WHERE tenant_id IN (?, ?)", (tenant_a, tenant_b))
    
    conn.commit()
    
    # 2. Seed Tenant A
    print("\n[Test] Seeding Tenant A...")
    assert seed_commerce_data(tenant_a) == True
    
    # Check A counts
    venues_a = c.execute("SELECT COUNT(*) FROM venues WHERE tenant_id = ?", (tenant_a,)).fetchone()[0]
    events_a = c.execute("SELECT COUNT(*) FROM events WHERE tenant_id = ?", (tenant_a,)).fetchone()[0]
    tables_a = c.execute("SELECT COUNT(*) FROM venue_tables WHERE venue_id IN (SELECT id FROM venues WHERE tenant_id = ?)", (tenant_a,)).fetchone()[0]
    
    print(f"Tenant A: Venues={venues_a}, Events={events_a}, Tables={tables_a}")
    assert venues_a == 3
    assert events_a == 3 # Updated to 3 (Jazz, Comedy, Gala)
    assert tables_a == 30 # 3 venues * 10 tables
    
    # 3. Seed Tenant B
    print("\n[Test] Seeding Tenant B...")
    assert seed_commerce_data(tenant_b) == True
    
    # Check B counts
    venues_b = c.execute("SELECT COUNT(*) FROM venues WHERE tenant_id = ?", (tenant_b,)).fetchone()[0]
    tables_b = c.execute("SELECT COUNT(*) FROM venue_tables WHERE venue_id IN (SELECT id FROM venues WHERE tenant_id = ?)", (tenant_b,)).fetchone()[0]
    
    print(f"Tenant B: Venues={venues_b}, Tables={tables_b}")
    assert venues_b == 3
    assert tables_b == 30
    
    # Verify Separation (Total counts)
    total_venues = c.execute("SELECT COUNT(*) FROM venues WHERE tenant_id IN (?, ?)", (tenant_a, tenant_b)).fetchone()[0]
    assert total_venues == 6
    
    # 4. Idempotency Check (Seed A again)
    print("\n[Test] Seeding Tenant A Again (Idempotency)...")
    assert seed_commerce_data(tenant_a) == True
    
    venues_a_after = c.execute("SELECT COUNT(*) FROM venues WHERE tenant_id = ?", (tenant_a,)).fetchone()[0]
    events_a_after = c.execute("SELECT COUNT(*) FROM events WHERE tenant_id = ?", (tenant_a,)).fetchone()[0]
    tables_to_venue = c.execute("SELECT COUNT(*) FROM venue_tables vt JOIN venues v ON vt.venue_id = v.id WHERE v.tenant_id = ?", (tenant_a,)).fetchone()[0]
    
    print(f"Tenant A After: Venues={venues_a_after}, Events={events_a_after}, Tables={tables_to_venue}")
    assert venues_a_after == 3
    assert events_a_after == 3
    assert tables_to_venue == 30
    
    conn.close()

if __name__ == "__main__":
    test_seed_isolation_and_idempotency()
    print("\n✅ Seed Verification Passed!")
