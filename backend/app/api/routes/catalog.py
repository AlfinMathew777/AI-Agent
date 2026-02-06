from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional
import json
from datetime import datetime
from pydantic import BaseModel
import uuid

from app.api.deps import get_tenant_header
from app.db.session import get_db_connection
from app.schemas.commerce import RestaurantResponse, MenuResponse, EventResponse

router = APIRouter()

@router.get("/catalog/restaurants", response_model=List[RestaurantResponse])
async def catalog_list_restaurants(tenant_id: str = Depends(get_tenant_header)):
    """Public list of restaurants for the tenant."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM restaurants WHERE tenant_id = ?", (tenant_id,)).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        r = dict(row)
        r["hours_json"] = json.loads(r["hours_json"]) if r["hours_json"] else {}
        results.append(r)
    return results

@router.get("/catalog/restaurants/{restaurant_id}/menus", response_model=List[MenuResponse])
async def catalog_list_menus(
    restaurant_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    """Public list of menus for a restaurant."""
    conn = get_db_connection()
    # Check if restaurant exists in tenant
    exists = conn.execute("SELECT 1 FROM restaurants WHERE id = ? AND tenant_id = ?", (restaurant_id, tenant_id)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Restaurant not found")

    rows = conn.execute("SELECT * FROM menus WHERE restaurant_id = ? AND tenant_id = ? AND is_active = 1", (restaurant_id, tenant_id)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# We might also want public menu items? The user request said "/catalog/restaurants/{id}/menu", singular.
# I interpreted it as "get the menu(s)". Usually you want items too.
# Let's add an endpoint for items of a menu for completeness, or include them?
# The prompt asked specifically for: GET /catalog/restaurants/{id}/menu
# Let's stick to that => list of menus. The frontend would ostensibly drill down.
# But for the Agent, it might need items. Let's add GET /catalog/menus/{id}/items

@router.get("/catalog/menus/{menu_id}/items")
async def catalog_get_menu_items(
    menu_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM menu_items WHERE menu_id = ? AND tenant_id = ? AND is_available = 1", 
        (menu_id, tenant_id)
    ).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item["tags_json"]) if item["tags_json"] else []
        results.append(item)
    return results


@router.get("/catalog/rooms")
async def catalog_list_available_rooms(
    check_in: Optional[str] = Query(None, description="Check-in date (YYYY-MM-DD)"),
    check_out: Optional[str] = Query(None, description="Check-out date (YYYY-MM-DD)"),
    room_type: Optional[str] = Query(None, description="Filter by room type (standard, deluxe, suite)"),
    tenant_id: str = Depends(get_tenant_header)
):
    """
    Public endpoint to search for available rooms.
    If check_in and check_out are provided, returns rooms that are not booked during that period.
    """
    conn = get_db_connection()
    
    try:
        # Base query to get all rooms
        query = """
            SELECT 
                r.id,
                r.room_number,
                r.floor,
                r.room_type,
                r.capacity,
                r.amenities,
                r.status as current_status
            FROM rooms r
            WHERE r.tenant_id = ?
        """
        params = [tenant_id]
        
        # Filter by room type if specified
        if room_type:
            query += " AND r.room_type = ?"
            params.append(room_type)
        
        # Execute initial query
        rooms = conn.execute(query, params).fetchall()
        
        # Convert to list of dicts
        available_rooms = []
        for room in rooms:
            room_dict = dict(room)
            
            # Check availability if dates are provided
            if check_in and check_out:
                # Check for conflicting reservations
                conflict_query = """
                    SELECT COUNT(*) as count
                    FROM reservations
                    WHERE room_id = ?
                    AND status NOT IN ('cancelled', 'checked_out')
                    AND (
                        (check_in_date <= ? AND check_out_date > ?)
                        OR (check_in_date < ? AND check_out_date >= ?)
                        OR (check_in_date >= ? AND check_out_date <= ?)
                    )
                """
                conflict_result = conn.execute(
                    conflict_query,
                    (room_dict['id'], check_out, check_in, check_out, check_in, check_in, check_out)
                ).fetchone()
                
                is_available = conflict_result['count'] == 0
                room_dict['is_available'] = is_available
                
                # Only include available rooms when dates are specified
                if is_available:
                    available_rooms.append(room_dict)
            else:
                # If no dates specified, return all rooms with general status
                room_dict['is_available'] = room_dict['current_status'] == 'available'
                available_rooms.append(room_dict)
        
        return {
            "rooms": available_rooms,
            "total": len(available_rooms),
            "check_in": check_in,
            "check_out": check_out,
            "room_type": room_type
        }
        
    finally:
        conn.close()


class RoomBookingRequest(BaseModel):
    room_id: str
    guest_name: str
    guest_email: str
    guest_phone: Optional[str] = None
    check_in_date: str  # YYYY-MM-DD format
    check_out_date: str  # YYYY-MM-DD format
    special_requests: Optional[str] = None
    total_amount: Optional[float] = 0.0


@router.post("/catalog/rooms/book")
async def book_room(
    booking: RoomBookingRequest,
    tenant_id: str = Depends(get_tenant_header)
):
    """
    Public endpoint for customers to book a room.
    Validates availability before creating the reservation.
    """
    conn = get_db_connection()
    
    try:
        # 1. Verify the room exists
        room = conn.execute(
            "SELECT * FROM rooms WHERE id = ? AND tenant_id = ?",
            (booking.room_id, tenant_id)
        ).fetchone()
        
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # 2. Check for conflicting reservations
        conflict_query = """
            SELECT COUNT(*) as count
            FROM reservations
            WHERE room_id = ?
            AND tenant_id = ?
            AND status NOT IN ('cancelled', 'checked_out')
            AND (
                (check_in_date <= ? AND check_out_date > ?)
                OR (check_in_date < ? AND check_out_date >= ?)
                OR (check_in_date >= ? AND check_out_date <= ?)
            )
        """
        conflict = conn.execute(
            conflict_query,
            (booking.room_id, tenant_id, booking.check_out_date, booking.check_in_date, 
             booking.check_out_date, booking.check_in_date, booking.check_in_date, booking.check_out_date)
        ).fetchone()
        
        if conflict['count'] > 0:
            raise HTTPException(
                status_code=409,
                detail="Room is not available for the selected dates"
            )
        
        # 3. Create the reservation
        reservation_id = str(uuid.uuid4())
        conn.execute("""
            INSERT INTO reservations (
                id, tenant_id, room_id, room_number, guest_name, guest_phone,
                guest_email, check_in_date, check_out_date, status,
                total_amount, special_requests, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            reservation_id,
            tenant_id,
            booking.room_id,
            room['room_number'],
            booking.guest_name,
            booking.guest_phone,
            booking.guest_email,
            booking.check_in_date,
            booking.check_out_date,
            booking.total_amount,
            booking.special_requests
        ))
        
        conn.commit()
        
        return {
            "success": True,
            "reservation_id": reservation_id,
            "message": "Room booked successfully",
            "details": {
                "room_number": room['room_number'],
                "room_type": room['room_type'],
                "check_in": booking.check_in_date,
                "check_out": booking.check_out_date,
                "guest_name": booking.guest_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")
    finally:
        conn.close()


@router.get("/catalog/events", response_model=List[EventResponse])
async def catalog_list_events(
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    tenant_id: str = Depends(get_tenant_header)
):
    """Public list of events."""
    query = "SELECT * FROM events WHERE tenant_id = ? AND status != 'cancelled'"
    params = [tenant_id]
    
    if from_date:
        query += " AND start_time >= ?"
        params.append(from_date)
    if to_date:
        query += " AND start_time <= ?"
        params.append(to_date)
        
    query += " ORDER BY start_time ASC"
    
    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]
