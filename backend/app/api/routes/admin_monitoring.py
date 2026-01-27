from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.api.deps import verify_admin_role, get_current_tenant
from app.db.queries import get_db_connection
import sqlite3

router = APIRouter()

@router.get("/admin/chats")
async def get_chat_history(
    tenant_id: str = Depends(get_current_tenant),
    audience: Optional[str] = Query(None, description="Filter by audience: guest or staff"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    admin: dict = Depends(verify_admin_role)
):
    """Get chat history with filters."""
    try:
        conn = get_db_connection()
        
        # Build query
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if audience:
            conditions.append("audience = ?")
            params.append(audience)
        
        where_clause = " AND ".join(conditions)
        
        # Get chats
        query = f"""
            SELECT id, timestamp, audience, question, answer, 
                   model_used, latency_ms
            FROM chat_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        chats = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM chat_logs WHERE {where_clause}"
        total = conn.execute(count_query, params[:-2]).fetchone()[0]
        
        conn.close()
        
        return {
            "chats": chats,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/operations")
async def get_operations_summary(
    tenant_id: str = Depends(get_current_tenant),
    admin: dict = Depends(verify_admin_role)
):
    """Get operations summary and recent activity."""
    try:
        conn = get_db_connection()
        
        # Bookings today
        bookings_today = conn.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE tenant_id = ? AND date(created_at) = date('now')
        """, (tenant_id,)).fetchone()[0]
        
        # Restaurant reservations today
        reservations_today = conn.execute("""
            SELECT COUNT(*) FROM restaurant_bookings 
            WHERE tenant_id = ? AND date(created_at) = date('now')
        """, (tenant_id,)).fetchone()[0]
        
        # Event tickets today
        tickets_today = conn.execute("""
            SELECT COUNT(*) FROM event_bookings 
            WHERE tenant_id = ? AND date(created_at) = date('now')
        """, (tenant_id,)).fetchone()[0]
        
        # Revenue from receipts (today)
        revenue_query = conn.execute("""
            SELECT SUM(total_cents) FROM receipts 
            WHERE tenant_id = ? AND date(created_at) = date('now')
        """, (tenant_id,)).fetchone()
        revenue_today = revenue_query[0] if revenue_query[0] else 0
        
        # Recent operations (last 10)
        recent_bookings = conn.execute("""
            SELECT 'Room Booking' as type, booking_id as ref, guest_name as customer, 
                   created_at, status
            FROM bookings 
            WHERE tenant_id = ?
            ORDER BY created_at DESC LIMIT 5
        """, (tenant_id,)).fetchall()
        
        recent_reservations = conn.execute("""
            SELECT 'Table Reservation' as type, id as ref, customer_name as customer,
                   created_at, status
            FROM restaurant_bookings
            WHERE tenant_id = ?
            ORDER BY created_at DESC LIMIT 5
        """, (tenant_id,)).fetchall()
        
        recent_ops = [dict(row) for row in list(recent_bookings) + list(recent_reservations)]
        recent_ops.sort(key=lambda x: x['created_at'], reverse=True)
        
        conn.close()
        
        return {
            "summary": {
                "bookings_today": bookings_today,
                "reservations_today": reservations_today,
                "tickets_today": tickets_today,
                "revenue_today_cents": revenue_today
            },
            "recent_operations": recent_ops[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/payments")
async def get_payments(
    tenant_id: str = Depends(get_current_tenant),
    status: Optional[str] = Query(None, description="Filter by status: paid, pending, failed"),
    limit: int = Query(50, le=200),
    admin: dict = Depends(verify_admin_role)
):
    """Get payment transactions."""
    try:
        conn = get_db_connection()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT id, quote_id, stripe_session_id, amount_cents, 
                   currency, status, created_at, updated_at
            FROM payments
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor = conn.execute(query, params)
        payments = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {"payments": payments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/receipts")
async def get_receipts(
    tenant_id: str = Depends(get_current_tenant),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    admin: dict = Depends(verify_admin_role)
):
    """Get receipts with date filtering."""
    try:
        conn = get_db_connection()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if date_from:
            conditions.append("date(created_at) >= date(?)")
            params.append(date_from)
        
        if date_to:
            conditions.append("date(created_at) <= date(?)")
            params.append(date_to)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT id, quote_id, session_id, currency, 
                   subtotal_cents, tax_cents, fees_cents, total_cents,
                   status, created_at
            FROM receipts
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor = conn.execute(query, params)
        receipts = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {"receipts": receipts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/system/health")
async def get_system_health(
    admin: dict = Depends(verify_admin_role)
):
    """Get system health status."""
    try:
        from pathlib import Path
        
        health = {
            "database": "unknown",
            "ai_service": "unknown",
            "redis": "unknown"
        }
        
        # Check database
        try:
            conn = get_db_connection()
            conn.execute("SELECT 1")
            conn.close()
            health["database"] = "healthy"
        except:
            health["database"] = "unhealthy"
        
        # Check AI service (simple check if env vars exist)
        import os
        if os.getenv("GEMINI_API_KEY"):
            health["ai_service"] = "configured"
        else:
            health["ai_service"] = "not configured"
        
        # Check Redis (if applicable)
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            health["redis"] = "healthy"
        except:
            health["redis"] = "unavailable"
        
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
