from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from app.api.deps import verify_admin_role, get_current_tenant, get_tenant_header
from app.core.security.admin import verify_admin
from app.db.admin_queries import (
    get_chat_history, get_chat_thread, get_operations_summary, 
    get_recent_operations, get_payment_transactions, get_receipts_list,
    get_recent_errors
)
from app.db.queries import get_db_connection
import sqlite3

router = APIRouter()

@router.get("/admin/chats", dependencies=[Depends(verify_admin)])
async def get_chat_history_endpoint(
    tenant_id: str = Depends(get_tenant_header),  # Allow header-based for testing
    audience: Optional[str] = Query(None, description="Filter by audience: guest or staff"),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """Get chat history with filters and pagination."""
    try:
        chats, total = get_chat_history(tenant_id, audience=audience, limit=limit, offset=offset)
        return {
            "chats": chats,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/chats/thread", dependencies=[Depends(verify_admin)])
async def get_chat_thread_endpoint(
    session_id: str = Query(..., description="Session ID to get thread for"),
    tenant_id: str = Depends(get_tenant_header)
):
    """Get all messages in a chat thread."""
    try:
        messages = get_chat_thread(session_id, tenant_id)
        return {"messages": messages, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/operations", dependencies=[Depends(verify_admin)])
async def get_operations_summary_endpoint(
    tenant_id: str = Depends(get_tenant_header)
):
    """Get operations summary and recent activity."""
    try:
        summary = get_operations_summary(tenant_id)
        recent = get_recent_operations(tenant_id, limit=50)
        
        return {
            "summary": summary,
            "recent_operations": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/payments", dependencies=[Depends(verify_admin)])
async def get_payments_endpoint(
    tenant_id: str = Depends(get_tenant_header),
    status: Optional[str] = Query(None, description="Filter by status: paid, pending, failed"),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """Get payment transactions with pagination."""
    try:
        payments, total = get_payment_transactions(tenant_id, status=status, limit=limit, offset=offset)
        return {
            "payments": payments,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/receipts", dependencies=[Depends(verify_admin)])
async def get_receipts_endpoint(
    tenant_id: str = Depends(get_tenant_header),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0)
):
    """Get receipts with date filtering and pagination."""
    try:
        receipts, total = get_receipts_list(tenant_id, date_from=date_from, date_to=date_to, limit=limit, offset=offset)
        return {
            "receipts": receipts,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/system/status", dependencies=[Depends(verify_admin)])
async def get_system_status():
    """Get system health status and recent errors."""
    try:
        health = {
            "database": "unknown",
            "ai_service": "unknown",
            "queue": "unknown"
        }
        
        # Check database
        try:
            conn = get_db_connection()
            conn.execute("SELECT 1")
            conn.close()
            health["database"] = "healthy"
        except Exception as e:
            health["database"] = f"unhealthy: {str(e)}"
        
        # Check AI service (simple check if env vars exist)
        import os
        if os.getenv("GOOGLE_API_KEY"):
            health["ai_service"] = "configured"
        else:
            health["ai_service"] = "not configured"
        
        # Check queue (if applicable)
        try:
            # For now, just check if queue table exists
            conn = get_db_connection()
            conn.execute("SELECT 1 FROM execution_jobs LIMIT 1")
            conn.close()
            health["queue"] = "available"
        except:
            health["queue"] = "unavailable"
        
        # Get recent errors
        recent_errors = get_recent_errors(limit=20)
        
        return {
            "database": health["database"],
            "queue": health["queue"],
            "ai_service": health["ai_service"],
            "recent_errors": recent_errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
