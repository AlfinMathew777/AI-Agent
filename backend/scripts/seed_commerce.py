import sqlite3
import uuid
import json
from pathlib import Path
from datetime import datetime, timedelta
from app.core.config import DB_PATH

DEFAULT_TENANT_ID = "default-tenant-0000"

def seed_commerce():
    print(f"[Seed] Seeding commerce data for tenant: {DEFAULT_TENANT_ID}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Restaurants
    restaurants = [
        {
            "name": "Azure Horizon Grill",
            "location": "Rooftop, 15th Floor",
            "phone": "EXT 501",
            "hours": {"mon-sun": "11:00-23:00"},
            "menus": [
                {
                    "title": "Dinner Menu",
                    "items": [
                        {"name": "Grilled Salmon", "desc": "Wild caught salmon with asparagus", "price": 32.0, "tags": ["gluten-free", "healthy"]},
                        {"name": "Ribeye Steak", "desc": "12oz USDA Prime", "price": 45.0, "tags": ["meat"]},
                        {"name": "Truffle Fries", "desc": "Parmesan and truffle oil", "price": 12.0, "tags": ["vegetarian"]}
                    ]
                }
            ]
        },
        {
            "name": "The Garden Cafe",
            "location": "Lobby Level",
            "phone": "EXT 502",
            "hours": {"mon-sun": "06:00-15:00"},
            "menus": [
                {
                    "title": "Breakfast All Day",
                    "items": [
                        {"name": "Avocado Toast", "desc": "Sourdough, poached egg", "price": 16.0, "tags": ["vegetarian"]},
                        {"name": "Full English", "desc": "Eggs, beans, sausage, toast", "price": 22.0, "tags": ["meat"]},
                        {"name": "Pancakes", "desc": "Maple syrup and berries", "price": 14.0, "tags": ["vegetarian", "sweet"]}
                    ]
                }
            ]
        }
    ]
    
    for r_data in restaurants:
        r_id = str(uuid.uuid4())
        c.execute("INSERT INTO restaurants (id, tenant_id, name, location, phone, hours_json) VALUES (?, ?, ?, ?, ?, ?)",
                  (r_id, DEFAULT_TENANT_ID, r_data["name"], r_data["location"], r_data["phone"], json.dumps(r_data["hours"])))
        
        for m_data in r_data["menus"]:
            m_id = str(uuid.uuid4())
            c.execute("INSERT INTO menus (id, tenant_id, restaurant_id, title, description) VALUES (?, ?, ?, ?, ?)",
                      (m_id, DEFAULT_TENANT_ID, r_id, m_data["title"], "Main Menu"))
            
            for item in m_data["items"]:
                i_id = str(uuid.uuid4())
                c.execute('''
                    INSERT INTO menu_items (id, tenant_id, menu_id, name, description, price, tags_json, is_available)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (i_id, DEFAULT_TENANT_ID, m_id, item["name"], item["desc"], item["price"], json.dumps(item["tags"]), 1))

    # 2. Events & Tickets
    events = [
        {
            "title": "Jazz Night by the Bay",
            "venue": "Grand Ballroom",
            "start": datetime.now() + timedelta(days=2, hours=19),
            "end": datetime.now() + timedelta(days=2, hours=22),
            "tickets": [
                {"type": "General Admission", "price": 50.0, "cap": 100},
                {"type": "VIP Table", "price": 150.0, "cap": 20}
            ]
        },
        {
            "title": "Wine Tasting Class",
            "venue": "Private Dining Room",
            "start": datetime.now() + timedelta(days=5, hours=17),
            "end": datetime.now() + timedelta(days=5, hours=19),
            "tickets": [
                {"type": "Standard", "price": 75.0, "cap": 30}
            ]
        }
    ]
    
    for e_data in events:
        e_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO events (id, tenant_id, title, venue, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (e_id, DEFAULT_TENANT_ID, e_data["title"], e_data["venue"], e_data["start"], e_data["end"], "scheduled"))
        
        for t_data in e_data["tickets"]:
            t_id = str(uuid.uuid4())
            c.execute('''
                INSERT INTO event_tickets (id, tenant_id, event_id, ticket_type, price, capacity, sold_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (t_id, DEFAULT_TENANT_ID, e_id, t_data["type"], t_data["price"], t_data["cap"], 0))

    conn.commit()
    conn.close()
    print("[Seed] Commerce data seeded successfully.")

if __name__ == "__main__":
    seed_commerce()
