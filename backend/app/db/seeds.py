
import uuid
from datetime import datetime
from app.db.session import get_db_connection

def seed_commerce_data(tenant_id: str):
    """
    Idempotent seed of commerce data for a tenant.
    Creates:
    - 3 Venues (Restaurants)
    - 10 Tables per Venue
    - 2 Events
    """
    print(f"[Seed] Starting commerce seed for tenant: {tenant_id}")
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # ---------------------------------------------------------
        # 1. Seed Venues
        # ---------------------------------------------------------
        venues = [
            {"name": "Harbour Grill", "type": "restaurant"},
            {"name": "Sky Bar Bistro", "type": "restaurant"},
            {"name": "The Atrium Cafe", "type": "restaurant"}
        ]
        
        venue_ids = {} # name -> id
        
        for v in venues:
            # Check existance by name + tenant
            c.execute("SELECT id FROM venues WHERE tenant_id = ? AND name = ?", (tenant_id, v["name"]))
            row = c.fetchone()
            
            if row:
                venue_ids[v["name"]] = row[0]
                print(f"[Seed] Venue '{v['name']}' already exists.")
            else:
                v_id = str(uuid.uuid4())
                c.execute('''
                    INSERT INTO venues (id, tenant_id, name, type)
                    VALUES (?, ?, ?, ?)
                ''', (v_id, tenant_id, v["name"], v["type"]))
                venue_ids[v["name"]] = v_id
                print(f"[Seed] Created Venue '{v['name']}'.")
        
        # ---------------------------------------------------------
        # 2. Seed Tables (for each venue)
        # ---------------------------------------------------------
        # Strategy: table_number 1..10. varying capacity.
        # Check if ANY tables exist for venue. If 0, insert all.
        
        for v_name, v_id in venue_ids.items():
            c.execute("SELECT COUNT(*) FROM venue_tables WHERE venue_id = ?", (v_id,))
            count = c.fetchone()[0]
            
            if count == 0:
                print(f"[Seed] Seeding 10 tables for {v_name}...")
                for i in range(1, 11):
                    # Cycle capacity 2, 4, 6
                    cap = 2
                    if i % 3 == 0: cap = 6
                    elif i % 2 == 0: cap = 4
                    
                    t_id = str(uuid.uuid4())
                    t_num = str(i)
                    
                    c.execute('''
                        INSERT INTO venue_tables (id, venue_id, table_number, capacity)
                        VALUES (?, ?, ?, ?)
                    ''', (t_id, v_id, t_num, cap))
            else:
                print(f"[Seed] Tables already exist for {v_name} ({count}). Skipping.")

        # ---------------------------------------------------------
        # 3. Seed Events
        # ---------------------------------------------------------
        events = [
            {"name": "Live Jazz Night", "total_tickets": 50, "price": 1500},
            {"name": "Comedy Showcase", "total_tickets": 100, "price": 2500},
            {"name": "Gala Dinner", "total_tickets": 200, "price": 0} # Free event
        ]
        
        for e in events:
            # Check existence
            c.execute("SELECT id FROM events WHERE tenant_id = ? AND name = ?", (tenant_id, e["name"]))
            row = c.fetchone()
            
            if row:
                print(f"[Seed] Event '{e['name']}' already exists.")
            else:
                e_id = str(uuid.uuid4())
                start_time = "2026-06-01 20:00:00" 
                
                c.execute('''
                    INSERT INTO events (id, tenant_id, title, name, start_time, total_tickets, ticket_price_cents, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (e_id, tenant_id, e["name"], e["name"], start_time, e["total_tickets"], e["price"], "scheduled"))
                print(f"[Seed] Created Event '{e['name']}' with price {e['price']}.")

        conn.commit()
        return True
        
    except Exception as e:
        print(f"[Seed] Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
