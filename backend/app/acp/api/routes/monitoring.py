"""
Monitoring & Alerts Routes
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.monitoring.dashboard import get_dashboard_stats, check_alerts
from app.api.deps import verify_admin_role, get_tenant_header

router = APIRouter(prefix="/admin/monitoring", tags=["Monitoring"])


@router.get("/dashboard", dependencies=[Depends(verify_admin_role)])
async def get_dashboard(
    property_id: Optional[str] = Query(None),
    tenant_id: str = Depends(get_tenant_header)
):
    """Get monitoring dashboard for properties"""
    stats = await get_dashboard_stats(property_id)
    return stats


@router.get("/alerts", dependencies=[Depends(verify_admin_role)])
async def get_alerts(tenant_id: str = Depends(get_tenant_header)):
    """Get current alerts"""
    alerts = await check_alerts()
    return {
        "alerts": alerts,
        "count": len(alerts)
    }
