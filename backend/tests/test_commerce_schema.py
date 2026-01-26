import sqlite3
import pytest
from app.core.config import DB_PATH

def test_commerce_tables_exist():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = [
        "restaurants", "menus", "menu_items", 
        "events", "event_tickets", "table_reservations", 
        "orders", "order_items"
    ]
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        assert cursor.fetchone() is not None, f"Table {table} missing"
        
    conn.close()

def test_seed_data_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Restaurants
    cursor.execute("SELECT count(*) FROM restaurants")
    count = cursor.fetchone()[0]
    assert count >= 2, f"Expected at least 2 restaurants, found {count}"
    
    # Check Menus
    cursor.execute("SELECT count(*) FROM menus")
    assert cursor.fetchone()[0] >= 2
    
    # Check Items
    cursor.execute("SELECT count(*) FROM menu_items")
    assert cursor.fetchone()[0] >= 6
    
    # Check Events
    cursor.execute("SELECT count(*) FROM events")
    assert cursor.fetchone()[0] >= 2
    
    # Check Tickets
    cursor.execute("SELECT count(*) FROM event_tickets")
    assert cursor.fetchone()[0] >= 3
    
    conn.close()
