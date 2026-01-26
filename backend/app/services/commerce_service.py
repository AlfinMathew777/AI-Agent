import uuid
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.db.session import get_db_connection

class CommerceService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def list_restaurants(self, date: str = None, party_size: int = 2) -> Dict[str, List[Dict]]:
        """List restaurants for the tenant."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM venues WHERE tenant_id = ? AND type = 'restaurant'", 
            (self.tenant_id,)
        ).fetchall()
        
        results = []
        for row in rows:
            r = dict(row)
            # Check simple availability hint (are there ANY tables?)
            avail, _ = self.get_available_tables(r["id"], date or "tomorrow", "19:00", party_size)
            r["availability_hint"] = "Available" if avail else "Full"
            results.append(r)
        
        conn.close()
        return {"restaurants": results}

    def list_events(self, date: str = None, party_size: int = 2) -> Dict[str, List[Dict]]:
        """List events for the tenant."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM events WHERE tenant_id = ?"
        params = [self.tenant_id]
        
        # Simple date filter if provided (exact match or future)
        # For agent UX, 'list events for tomorrow' usually means filtering.
        # MVP: List all future events.
        # query += " AND start_time >= datetime('now')" 
        
        rows = conn.execute(query, params).fetchall()
        
        results = []
        for row in rows:
            e = dict(row)
            # Check ticket availability
            avail = self.check_event_availability(e["id"], date, party_size)
            e["availability_hint"] = f"{avail['seats_left']} seats left"
            if avail['available']:
                results.append(e)
                
        conn.close()
        return {"events": results}

    def get_available_tables(self, venue_id: str, date: str, time: str, party_size: int) -> Tuple[List[Dict], Any]:
        """
        Find specific available tables that fit the party size.
        """
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        # 1. Get all tables for venue that fit payload
        # Fit logic: capacity >= party_size
        tables = conn.execute(
            "SELECT * FROM venue_tables WHERE venue_id = ? AND capacity >= ? ORDER BY capacity ASC",
            (venue_id, party_size)
        ).fetchall()
        
        if not tables:
            conn.close()
            return [], "No tables with sufficient capacity."
            
        # 2. Get booked tables for this slot
        # Mock Logic: Time slots are rigid (e.g. Booking locks the table for the 'time' spec).
        # In real world, we'd check ranges. Here, exact match on 'time' and 'date'.
        booked_rows = conn.execute(
            "SELECT table_id FROM restaurant_bookings WHERE venue_id = ? AND date = ? AND time = ? AND status = 'confirmed' AND tenant_id = ?",
            (venue_id, date, time, self.tenant_id)
        ).fetchall()
        booked_ids = {r["table_id"] for r in booked_rows}
        
        # 3. Filter
        available = []
        for t in tables:
            if t["id"] not in booked_ids:
                available.append(dict(t))
                
        conn.close()
        return available, None

    def check_event_availability(self, event_id: str, date: str, party_size: int) -> Dict[str, Any]:
        """Check if event has enough tickets."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        event = conn.execute("SELECT total_tickets FROM events WHERE id = ? AND tenant_id = ?", (event_id, self.tenant_id)).fetchone()
        if not event:
            conn.close()
            return {"available": False, "seats_left": 0}
            
        total = event["total_tickets"] or 0
        
        # Sum sold
        sold_row = conn.execute(
            "SELECT SUM(quantity) as sold FROM event_bookings WHERE event_id = ? AND status = 'confirmed' AND tenant_id = ?",
            (event_id, self.tenant_id)
        ).fetchone()
        sold = sold_row["sold"] or 0
        
        left = total - sold
        conn.close()
        
        return {
            "available": left >= party_size, 
            "seats_left": left
        }

    # --- WRITES ---

    def reserve_table(self, venue_id: str, date: str, time: str, party_size: int, customer_name: str) -> str:
        """Reserve a table transactionally."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        try:
            # Use immediate transaction to lock
            conn.execute("BEGIN IMMEDIATE")
            
            # 1. Find best table again (inside transaction)
            # Same logic as get_available_tables but inline
            tables = conn.execute(
                "SELECT * FROM venue_tables WHERE venue_id = ? AND capacity >= ? ORDER BY capacity ASC",
                (venue_id, party_size)
            ).fetchall()
            
            booked_rows = conn.execute(
                "SELECT table_id FROM restaurant_bookings WHERE venue_id = ? AND date = ? AND time = ? AND status = 'confirmed'",
                (venue_id, date, time)
            ).fetchall()
            booked_ids = {r["table_id"] for r in booked_rows}
            
            selected_table = None
            for t in tables:
                if t["id"] not in booked_ids:
                    selected_table = t
                    break
            
            if not selected_table:
                conn.rollback()
                return "Failed: No available table for that time."
            
            # 2. Book
            res_id = str(uuid.uuid4())
            conn.execute(
                '''INSERT INTO restaurant_bookings (id, tenant_id, venue_id, table_id, date, time, party_size, customer_name, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (res_id, self.tenant_id, venue_id, selected_table["id"], date, time, party_size, customer_name, "confirmed")
            )
            
            conn.commit()
            return f"Reservation Confirmed! Booking ID: {res_id} (Table {selected_table['table_number']})"
            
        except Exception as e:
            conn.rollback()
            print(f"[Commerce] Reserve Error: {e}")
            return f"System Error: {str(e)}"
        finally:
            conn.close()

    def buy_event_tickets(self, event_id: str, date: str, quantity: int, customer_name: str) -> str:
        """Buy tickets transactionally."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        
        try:
            conn.execute("BEGIN IMMEDIATE")
            
            # 1. Check Capacity
            event = conn.execute("SELECT total_tickets FROM events WHERE id = ?", (event_id,)).fetchone()
            if not event:
                conn.rollback()
                return "Failed: Event not found."
            
            total = event["total_tickets"]
            
            sold_row = conn.execute(
                "SELECT SUM(quantity) as sold FROM event_bookings WHERE event_id = ? AND status = 'confirmed'",
                (event_id,)
            ).fetchone()
            sold = sold_row["sold"] or 0
            
            if (total - sold) < quantity:
                conn.rollback()
                return f"Failed: Not enough tickets. Only {total - sold} left."
            
            # 2. Book
            bk_id = str(uuid.uuid4())
            conn.execute(
                '''INSERT INTO event_bookings (id, tenant_id, event_id, customer_name, quantity, status)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (bk_id, self.tenant_id, event_id, customer_name, quantity, "confirmed")
            )
            
            conn.commit()
            return f"Tickets Purchased! Booking ID: {bk_id}"
            
        except Exception as e:
            conn.rollback()
            print(f"[Commerce] Ticket Error: {e}")
            return f"System Error: {str(e)}"
        finally:
            conn.close()

    def cancel_restaurant_booking(self, booking_id: str) -> bool:
        """Cancel a restaurant booking."""
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE restaurant_bookings SET status = 'cancelled' WHERE id = ? AND tenant_id = ?", 
                (booking_id, self.tenant_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[Commerce] Cancel Rest Error: {e}")
            return False
        finally:
            conn.close()

    def cancel_event_booking(self, booking_id: str) -> bool:
        """Cancel an event booking."""
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE event_bookings SET status = 'cancelled' WHERE id = ? AND tenant_id = ?", 
                (booking_id, self.tenant_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[Commerce] Cancel Event Error: {e}")
            return False
        finally:
            conn.close()
