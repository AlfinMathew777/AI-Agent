from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import uuid
import json
from datetime import datetime

from app.api.deps import get_current_tenant
from app.core.security.admin import verify_admin
from app.db.session import get_db_connection
from app.schemas.commerce import (
    RestaurantCreate, RestaurantResponse,
    MenuCreate, MenuResponse,
    MenuItemCreate, MenuItemResponse,
    EventCreate, EventResponse
)

from app.db.seeds import seed_commerce_data

router = APIRouter(dependencies=[Depends(verify_admin)])

@router.post("/admin/commerce/seed")
async def seed_data(tenant_id: str = Depends(get_current_tenant)):
    """Seed commerce data (Venues, Tables, Events) for the current tenant."""
    success = seed_commerce_data(tenant_id)
    if not success:
        raise HTTPException(status_code=500, detail="Seeding failed")
    return {"status": "success", "message": f"Seeded commerce data for tenant {tenant_id}"}

# --- Restaurants ---

@router.get("/admin/restaurants", response_model=List[RestaurantResponse])
async def list_restaurants(tenant_id: str = Depends(get_current_tenant)):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM restaurants WHERE tenant_id = ?", (tenant_id,)).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        r = dict(row)
        r["hours_json"] = json.loads(r["hours_json"]) if r["hours_json"] else {}
        results.append(r)
    return results

@router.post("/admin/restaurants", response_model=RestaurantResponse)
async def create_restaurant(
    payload: RestaurantCreate,
    tenant_id: str = Depends(get_current_tenant)
):
    r_id = str(uuid.uuid4())
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO restaurants (id, tenant_id, name, location, phone, hours_json) VALUES (?, ?, ?, ?, ?, ?)",
            (r_id, tenant_id, payload.name, payload.location, payload.phone, json.dumps(payload.hours_json))
        )
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    
    # Fetch back
    row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (r_id,)).fetchone()
    conn.close()
    
    r = dict(row)
    r["hours_json"] = json.loads(r["hours_json"])
    return r

# --- Menus ---

@router.get("/admin/restaurants/{restaurant_id}/menus", response_model=List[MenuResponse])
async def list_menus(
    restaurant_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    # Verify restaurant belongs to tenant
    exists = conn.execute("SELECT 1 FROM restaurants WHERE id = ? AND tenant_id = ?", (restaurant_id, tenant_id)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Restaurant not found")

    rows = conn.execute("SELECT * FROM menus WHERE restaurant_id = ? AND tenant_id = ?", (restaurant_id, tenant_id)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Items ---

@router.post("/admin/menu_items", response_model=MenuItemResponse)
async def create_menu_item(
    payload: MenuItemCreate,
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    # Verify menu belongs to tenant
    exists = conn.execute("SELECT 1 FROM menus WHERE id = ? AND tenant_id = ?", (payload.menu_id, tenant_id)).fetchone()
    if not exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Menu not found")
    
    i_id = str(uuid.uuid4())
    conn.execute(
        '''INSERT INTO menu_items (id, tenant_id, menu_id, name, description, price, tags_json, image_url, is_available)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (i_id, tenant_id, payload.menu_id, payload.name, payload.description, payload.price, 
         json.dumps(payload.tags), payload.image_url, 1 if payload.is_available else 0)
    )
    conn.commit()
    conn.close()
    
    return {
        **payload.dict(),
        "id": i_id,
        "tenant_id": tenant_id
    }

# --- Events ---

@router.get("/admin/events", response_model=List[EventResponse])
async def list_events(
    start_after: Optional[datetime] = None,
    status: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    query = "SELECT * FROM events WHERE tenant_id = ?"
    params = [tenant_id]
    
    if start_after:
        query += " AND start_time >= ?"
        params.append(start_after)
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY start_time ASC"
    
    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/admin/events", response_model=EventResponse)
async def create_event(
    payload: EventCreate,
    tenant_id: str = Depends(get_current_tenant)
):
    e_id = str(uuid.uuid4())
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO events (id, tenant_id, title, description, venue, start_time, end_time, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (e_id, tenant_id, payload.title, payload.description, payload.venue, payload.start_time, payload.end_time, payload.status)
    )
    conn.commit()
    
    row = conn.execute("SELECT * FROM events WHERE id = ?", (e_id,)).fetchone()
    conn.close()
    return dict(row)

# --- Bookings (Admin View) ---

@router.get("/admin/restaurant-bookings")
async def list_restaurant_bookings(
    date: Optional[str] = None,
    venue_id: Optional[str] = None,
    # status: Optional[str] = None, # Optional filter later
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row # Ensure we get dict-like access
    
    query = "SELECT rb.*, v.name as venue_name FROM restaurant_bookings rb JOIN venues v ON rb.venue_id = v.id WHERE rb.tenant_id = ?"
    params = [tenant_id]
    
    if date:
        query += " AND rb.date = ?"
        params.append(date)
    if venue_id:
        query += " AND rb.venue_id = ?"
        params.append(venue_id)
        
    query += " ORDER BY rb.date DESC, rb.time DESC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.get("/admin/event-bookings")
async def list_event_bookings(
    event_id: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    
    query = "SELECT eb.*, e.title as event_title FROM event_bookings eb JOIN events e ON eb.event_id = e.id WHERE eb.tenant_id = ?"
    params = [tenant_id]
    
    if event_id:
        query += " AND eb.event_id = ?"
        params.append(event_id)
        
    query += " ORDER BY eb.created_at DESC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Finance (Quotes & Receipts) ---

@router.get("/admin/quotes")
async def list_quotes(
    status: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM quotes WHERE tenant_id = ?"
    params = [tenant_id]
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        q = dict(row)
        q["breakdown_json"] = json.loads(q["breakdown_json"]) if q["breakdown_json"] else []
        results.append(q)
    return results

@router.get("/admin/receipts")
async def list_receipts(
    tenant_id: str = Depends(get_current_tenant)
):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM receipts WHERE tenant_id = ? ORDER BY created_at DESC"
    rows = conn.execute(query, (tenant_id,)).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        r = dict(row)
        r["breakdown_json"] = json.loads(r["breakdown_json"]) if r["breakdown_json"] else []
        r["booking_refs_json"] = json.loads(r["booking_refs_json"]) if r["booking_refs_json"] else {}
        results.append(r)
    return results
