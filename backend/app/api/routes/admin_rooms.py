"""API routes for room management, reservations, and housekeeping."""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional, List
from pydantic import BaseModel
from app.api.deps import verify_admin_role, get_tenant_header
from app.db.room_queries import (
    create_room, get_rooms, get_room_by_number, update_room_status, get_room_statistics,
    create_reservation, get_reservations, update_reservation_status,
    create_housekeeping_task, get_housekeeping_tasks, start_cleaning, complete_cleaning,
    get_housekeeping_statistics
)

router = APIRouter()


# ==================== ROOMS ====================

class RoomCreate(BaseModel):
    room_number: str
    floor: int
    room_type: str  # standard, deluxe, suite
    capacity: int = 2
    amenities: str = ""


@router.post("/admin/rooms", dependencies=[Depends(verify_admin_role)])
async def create_room_endpoint(
    room: RoomCreate,
    tenant_id: str = Depends(get_tenant_header)
):
    """Create a new room."""
    try:
        room_id = create_room(
            tenant_id=tenant_id,
            room_number=room.room_number,
            floor=room.floor,
            room_type=room.room_type,
            capacity=room.capacity,
            amenities=room.amenities
        )
        if not room_id:
            raise HTTPException(status_code=400, detail="Room already exists or creation failed")
        return {"id": room_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/rooms", dependencies=[Depends(verify_admin_role)])
async def list_rooms(
    floor: Optional[int] = Query(None),
    room_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tenant_id: str = Depends(get_tenant_header)
):
    """Get rooms with optional filters."""
    try:
        rooms = get_rooms(tenant_id, floor=floor, room_type=room_type, status=status)
        return {"rooms": rooms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/rooms/statistics", dependencies=[Depends(verify_admin_role)])
async def get_room_stats(tenant_id: str = Depends(get_tenant_header)):
    """Get room statistics."""
    try:
        stats = get_room_statistics(tenant_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/rooms/{room_id}/status", dependencies=[Depends(verify_admin_role)])
async def update_room_status_endpoint(
    room_id: str,
    status: str = Body(..., embed=True),
    tenant_id: str = Depends(get_tenant_header)
):
    """Update room status."""
    try:
        valid_statuses = ['available', 'occupied', 'cleaning_needed', 'maintenance']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        success = update_room_status(tenant_id, room_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Room not found")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RESERVATIONS ====================

class ReservationCreate(BaseModel):
    room_id: str
    room_number: str
    guest_name: str
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
    check_in_date: str
    check_out_date: str
    total_amount: float = 0.0
    special_requests: str = ""


@router.post("/admin/reservations", dependencies=[Depends(verify_admin_role)])
async def create_reservation_endpoint(
    reservation: ReservationCreate,
    tenant_id: str = Depends(get_tenant_header)
):
    """Create a new reservation."""
    try:
        reservation_id = create_reservation(
            tenant_id=tenant_id,
            room_id=reservation.room_id,
            room_number=reservation.room_number,
            guest_name=reservation.guest_name,
            guest_phone=reservation.guest_phone,
            guest_email=reservation.guest_email,
            check_in_date=reservation.check_in_date,
            check_out_date=reservation.check_out_date,
            total_amount=reservation.total_amount,
            special_requests=reservation.special_requests
        )
        if not reservation_id:
            raise HTTPException(status_code=400, detail="Failed to create reservation")
        return {"id": reservation_id, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/reservations", dependencies=[Depends(verify_admin_role)])
async def list_reservations(
    status: Optional[str] = Query(None),
    room_number: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    tenant_id: str = Depends(get_tenant_header)
):
    """Get reservations with filters and pagination."""
    try:
        reservations, total = get_reservations(
            tenant_id, status=status, room_number=room_number, limit=limit, offset=offset
        )
        return {
            "reservations": reservations,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/reservations/{reservation_id}/checkin", dependencies=[Depends(verify_admin_role)])
async def checkin_reservation(
    reservation_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    """Check in a guest (update reservation status to checked_in)."""
    try:
        success = update_reservation_status(tenant_id, reservation_id, 'checked_in')
        if not success:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return {"status": "success", "message": "Guest checked in"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/reservations/{reservation_id}/checkout", dependencies=[Depends(verify_admin_role)])
async def checkout_reservation(
    reservation_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    """Check out a guest (update reservation status to checked_out)."""
    try:
        success = update_reservation_status(tenant_id, reservation_id, 'checked_out')
        if not success:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return {"status": "success", "message": "Guest checked out, room marked for cleaning"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HOUSEKEEPING ====================

class HousekeepingTaskCreate(BaseModel):
    room_id: str
    room_number: str
    cleaner_id: Optional[str] = None
    cleaner_name: Optional[str] = None
    notes: str = ""


@router.post("/admin/housekeeping/tasks", dependencies=[Depends(verify_admin_role)])
async def create_housekeeping_task_endpoint(
    task: HousekeepingTaskCreate,
    tenant_id: str = Depends(get_tenant_header)
):
    """Create a new housekeeping task."""
    try:
        task_id = create_housekeeping_task(
            tenant_id=tenant_id,
            room_id=task.room_id,
            room_number=task.room_number,
            cleaner_id=task.cleaner_id,
            cleaner_name=task.cleaner_name,
            notes=task.notes
        )
        if not task_id:
            raise HTTPException(status_code=400, detail="Failed to create housekeeping task")
        return {"id": task_id, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/housekeeping/tasks", dependencies=[Depends(verify_admin_role)])
async def list_housekeeping_tasks(
    status: Optional[str] = Query(None),
    cleaner_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    tenant_id: str = Depends(get_tenant_header)
):
    """Get housekeeping tasks with filters and pagination."""
    try:
        tasks, total = get_housekeeping_tasks(
            tenant_id, status=status, cleaner_id=cleaner_id, limit=limit, offset=offset
        )
        return {
            "tasks": tasks,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/housekeeping/tasks/{task_id}/start", dependencies=[Depends(verify_admin_role)])
async def start_cleaning_endpoint(
    task_id: str,
    cleaner_id: Optional[str] = Body(None, embed=True),
    cleaner_name: Optional[str] = Body(None, embed=True),
    tenant_id: str = Depends(get_tenant_header)
):
    """Start a cleaning task."""
    try:
        success = start_cleaning(tenant_id, task_id, cleaner_id, cleaner_name)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Cleaning started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/housekeeping/tasks/{task_id}/complete", dependencies=[Depends(verify_admin_role)])
async def complete_cleaning_endpoint(
    task_id: str,
    notes: str = Body("", embed=True),
    tenant_id: str = Depends(get_tenant_header)
):
    """Complete a cleaning task."""
    try:
        success = complete_cleaning(tenant_id, task_id, notes)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Cleaning completed, room marked as available"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/housekeeping/statistics", dependencies=[Depends(verify_admin_role)])
async def get_housekeeping_stats(tenant_id: str = Depends(get_tenant_header)):
    """Get housekeeping statistics."""
    try:
        stats = get_housekeeping_statistics(tenant_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
