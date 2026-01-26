
import pytest
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection

def test_commerce_schema_exists():
    """Verify that commerce inventory tables exist."""
    
    # 1. Run init to ensure migration
    init_db()
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # 2. Check Tables
    tables = ["venues", "venue_tables", "events", "restaurant_bookings", "event_bookings"]
    for t in tables:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
        row = c.fetchone()
        assert row is not None, f"Table {t} missing!"
        print(f"Table {t} (OK)")

    # 3. Check Events Columns
    c.execute("PRAGMA table_info(events)")
    columns = [row["name"] for row in c.fetchall()]
    print(f"Events Columns: {columns}")
    
    assert "name" in columns, "Column 'name' missing in events"
    assert "total_tickets" in columns, "Column 'total_tickets' missing in events"
    
    conn.close()

if __name__ == "__main__":
    test_commerce_schema_exists()
    print("Schema Verification Passed!")
