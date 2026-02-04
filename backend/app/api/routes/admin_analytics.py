from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime
from app.core.security.admin import verify_admin
from app.api.deps import get_tenant_header
from app.db.queries import get_analytics_stats, get_bookings, get_tool_stats

router = APIRouter()

@router.get("/admin/analytics", dependencies=[Depends(verify_admin)])
async def get_analytics():
    """Real analytics data from the database."""
    stats = get_analytics_stats()
    return stats if stats else {}

@router.get("/admin/bookings", dependencies=[Depends(verify_admin)])
async def list_bookings(
    date: str = Query(None, description="Filter by date YYYY-MM-DD"),
    room_type: str = Query(None, description="Filter by room type"),
    status: str = Query(None, description="Filter by booking status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order: str = Query("desc", regex="^(asc|desc)$"),
    tenant_id: str = Depends(get_tenant_header)
):
    """List bookings with filters."""
    # Optional date validation
    if date:
        try:
             datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
    data = get_bookings(
        date_filter=date,
        room_type=room_type,
        status_filter=status,
        limit=limit,
        offset=offset,
        order=order,
        tenant_id=tenant_id
    )
    
    return data

@router.get("/admin/tools/stats", dependencies=[Depends(verify_admin)])
async def get_tools_stats(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(20, ge=1, le=100),
    audience: str = Query(None, description="Filter by audience"),
    tool: str = Query(None, description="Filter by tool name")
):
    """Get aggregated tool usage stats."""
    return get_tool_stats(
        days=days,
        limit=limit,
        audience=audience,
        tool=tool
    )
