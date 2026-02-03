"""Database queries for room management, reservations, and housekeeping."""
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid
from app.db.session import get_db_connection


# ==================== ROOMS ====================

def create_room(tenant_id: str, room_number: str, floor: int, room_type: str, 
                capacity: int = 2, amenities: str = "") -> Optional[str]:
    """Create a new room."""
    try:
        room_id = str(uuid.uuid4())
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO rooms (id, tenant_id, room_number, floor, room_type, capacity, amenities, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'available')
        ''', (room_id, tenant_id, room_number, floor, room_type, capacity, amenities))
        conn.commit()
        conn.close()
        return room_id
    except sqlite3.IntegrityError:
        return None
    except Exception as e:
        print(f"[Database] Error creating room: {e}")
        return None


def get_rooms(tenant_id: str, floor: Optional[int] = None, 
              room_type: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """Get rooms with optional filters."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if floor is not None:
            conditions.append("floor = ?")
            params.append(floor)
        if room_type:
            conditions.append("room_type = ?")
            params.append(room_type)
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        query = f"SELECT * FROM rooms WHERE {' AND '.join(conditions)} ORDER BY floor, room_number"
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Database] Error getting rooms: {e}")
        return []


def get_room_by_number(tenant_id: str, room_number: str) -> Optional[Dict]:
    """Get a room by room number."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM rooms WHERE tenant_id = ? AND room_number = ?', 
                  (tenant_id, room_number))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[Database] Error getting room: {e}")
        return None


def update_room_status(tenant_id: str, room_id: str, status: str) -> bool:
    """Update room status."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE rooms 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND tenant_id = ?
        ''', (status, room_id, tenant_id))
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"[Database] Error updating room status: {e}")
        return False


def get_room_statistics(tenant_id: str) -> Dict:
    """Get room statistics (total, available, occupied, cleaning needed)."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Total rooms
        c.execute('SELECT COUNT(*) as total FROM rooms WHERE tenant_id = ?', (tenant_id,))
        total = c.fetchone()['total']
        
        # By status
        c.execute('''
            SELECT status, COUNT(*) as count 
            FROM rooms 
            WHERE tenant_id = ?
            GROUP BY status
        ''', (tenant_id,))
        status_counts = {row['status']: row['count'] for row in c.fetchall()}
        
        # By type
        c.execute('''
            SELECT room_type, COUNT(*) as count 
            FROM rooms 
            WHERE tenant_id = ?
            GROUP BY room_type
        ''', (tenant_id,))
        type_counts = {row['room_type']: row['count'] for row in c.fetchall()}
        
        conn.close()
        
        return {
            "total": total,
            "available": status_counts.get('available', 0),
            "occupied": status_counts.get('occupied', 0),
            "cleaning_needed": status_counts.get('cleaning_needed', 0),
            "maintenance": status_counts.get('maintenance', 0),
            "by_type": type_counts
        }
    except Exception as e:
        print(f"[Database] Error getting room statistics: {e}")
        return {"total": 0, "available": 0, "occupied": 0, "cleaning_needed": 0, "maintenance": 0, "by_type": {}}


# ==================== RESERVATIONS ====================

def create_reservation(tenant_id: str, room_id: str, room_number: str, guest_name: str,
                       guest_phone: Optional[str] = None, guest_email: Optional[str] = None,
                       check_in_date: str = "", check_out_date: str = "",
                       total_amount: float = 0.0, special_requests: str = "") -> Optional[str]:
    """Create a new reservation."""
    try:
        reservation_id = str(uuid.uuid4())
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO reservations 
            (id, tenant_id, room_id, room_number, guest_name, guest_phone, guest_email,
             check_in_date, check_out_date, total_amount, special_requests, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (reservation_id, tenant_id, room_id, room_number, guest_name, guest_phone,
              guest_email, check_in_date, check_out_date, total_amount, special_requests))
        conn.commit()
        conn.close()
        return reservation_id
    except Exception as e:
        print(f"[Database] Error creating reservation: {e}")
        return None


def get_reservations(tenant_id: str, status: Optional[str] = None,
                     room_number: Optional[str] = None, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
    """Get reservations with filters and pagination."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        if room_number:
            conditions.append("room_number = ?")
            params.append(room_number)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # Get total count
        c.execute(f"SELECT COUNT(*) as total FROM reservations{where_clause}", params)
        total = c.fetchone()['total']
        
        # Get paginated results
        query = f"SELECT * FROM reservations{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        c.execute(query, params + [limit, offset])
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows], total
    except Exception as e:
        print(f"[Database] Error getting reservations: {e}")
        return [], 0


def update_reservation_status(tenant_id: str, reservation_id: str, status: str) -> bool:
    """Update reservation status (e.g., check-in, check-out)."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Update reservation
        c.execute('''
            UPDATE reservations 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND tenant_id = ?
        ''', (status, reservation_id, tenant_id))
        
        # If checking in, update room status to occupied
        if status == 'checked_in':
            c.execute('''
                UPDATE rooms 
                SET status = 'occupied', updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT room_id FROM reservations WHERE id = ? AND tenant_id = ?)
            ''', (reservation_id, tenant_id))
        
        # If checking out, mark room for cleaning
        if status == 'checked_out':
            c.execute('''
                UPDATE rooms 
                SET status = 'cleaning_needed', updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT room_id FROM reservations WHERE id = ? AND tenant_id = ?)
            ''', (reservation_id, tenant_id))
        
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"[Database] Error updating reservation status: {e}")
        return False


# ==================== HOUSEKEEPING ====================

def create_housekeeping_task(tenant_id: str, room_id: str, room_number: str,
                             cleaner_id: Optional[str] = None, cleaner_name: Optional[str] = None,
                             notes: str = "") -> Optional[str]:
    """Create a new housekeeping task."""
    try:
        task_id = str(uuid.uuid4())
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO housekeeping 
            (id, tenant_id, room_id, room_number, cleaner_id, cleaner_name, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (task_id, tenant_id, room_id, room_number, cleaner_id, cleaner_name, notes))
        conn.commit()
        conn.close()
        return task_id
    except Exception as e:
        print(f"[Database] Error creating housekeeping task: {e}")
        return None


def get_housekeeping_tasks(tenant_id: str, status: Optional[str] = None,
                          cleaner_id: Optional[str] = None, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
    """Get housekeeping tasks with filters and pagination."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        if cleaner_id:
            conditions.append("cleaner_id = ?")
            params.append(cleaner_id)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # Get total count
        c.execute(f"SELECT COUNT(*) as total FROM housekeeping{where_clause}", params)
        total = c.fetchone()['total']
        
        # Get paginated results
        query = f"SELECT * FROM housekeeping{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        c.execute(query, params + [limit, offset])
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows], total
    except Exception as e:
        print(f"[Database] Error getting housekeeping tasks: {e}")
        return [], 0


def start_cleaning(tenant_id: str, task_id: str, cleaner_id: Optional[str] = None,
                   cleaner_name: Optional[str] = None) -> bool:
    """Start a cleaning task."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Update task
        update_fields = ["status = 'in_progress'", "started_at = CURRENT_TIMESTAMP"]
        params = []
        
        if cleaner_id:
            update_fields.append("cleaner_id = ?")
            params.append(cleaner_id)
        if cleaner_name:
            update_fields.append("cleaner_name = ?")
            params.append(cleaner_name)
        
        params.append(task_id)
        params.append(tenant_id)
        
        c.execute(f'''
            UPDATE housekeeping 
            SET {', '.join(update_fields)}
            WHERE id = ? AND tenant_id = ?
        ''', params)
        
        # Update room status
        c.execute('''
            UPDATE rooms 
            SET status = 'maintenance', updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT room_id FROM housekeeping WHERE id = ? AND tenant_id = ?)
        ''', (task_id, tenant_id))
        
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"[Database] Error starting cleaning: {e}")
        return False


def complete_cleaning(tenant_id: str, task_id: str, notes: str = "") -> bool:
    """Complete a cleaning task."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Update task
        c.execute('''
            UPDATE housekeeping 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP,
                notes = CASE WHEN ? != '' THEN ? ELSE notes END
            WHERE id = ? AND tenant_id = ?
        ''', (notes, notes, task_id, tenant_id))
        
        # Update room status to available
        c.execute('''
            UPDATE rooms 
            SET status = 'available', updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT room_id FROM housekeeping WHERE id = ? AND tenant_id = ?)
        ''', (task_id, tenant_id))
        
        conn.commit()
        success = c.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"[Database] Error completing cleaning: {e}")
        return False


def get_housekeeping_statistics(tenant_id: str) -> Dict:
    """Get housekeeping statistics."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Count by status
        c.execute('''
            SELECT status, COUNT(*) as count 
            FROM housekeeping 
            WHERE tenant_id = ?
            GROUP BY status
        ''', (tenant_id,))
        status_counts = {row['status']: row['count'] for row in c.fetchall()}
        
        # Today's tasks
        c.execute('''
            SELECT COUNT(*) as count 
            FROM housekeeping 
            WHERE tenant_id = ? AND DATE(created_at) = DATE('now')
        ''', (tenant_id,))
        today_count = c.fetchone()['count']
        
        conn.close()
        
        return {
            "pending": status_counts.get('pending', 0),
            "in_progress": status_counts.get('in_progress', 0),
            "completed": status_counts.get('completed', 0),
            "today": today_count
        }
    except Exception as e:
        print(f"[Database] Error getting housekeeping statistics: {e}")
        return {"pending": 0, "in_progress": 0, "completed": 0, "today": 0}
