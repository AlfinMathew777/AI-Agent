"""
Management Intelligence API Routes

Provides endpoints for the management AI assistant and dashboard metrics.
Restricted to manager and admin roles only.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.api.deps import get_current_user, require_manager_or_above
from app.schemas.auth import TokenData
from app.agents.management_agent import get_management_agent

router = APIRouter()


class ManagementChatRequest(BaseModel):
    """Request model for management chat."""
    message: str
    include_metrics: bool = True


class ManagementChatResponse(BaseModel):
    """Response model for management chat."""
    answer: str
    metrics: Optional[Dict[str, Any]] = None
    timestamp: str


class DashboardMetrics(BaseModel):
    """Response model for dashboard metrics."""
    occupancy_rate: float
    occupied_rooms: int
    total_rooms: int
    available_rooms: int
    active_reservations: int
    pending_reservations: int
    checkins_today: int
    checkouts_today: int
    revenue_today: float
    revenue_week: float
    revenue_month: float
    cancellations_week: int
    room_types: List[Dict[str, Any]]
    recent_reservations: List[Dict[str, Any]]
    upcoming_arrivals: List[Dict[str, Any]]
    generated_at: str


# Example questions for the UI
EXAMPLE_QUESTIONS = [
    {"icon": "TrendingUp", "text": "What is today's occupancy rate?", "category": "occupancy"},
    {"icon": "DollarSign", "text": "Show me today's revenue summary", "category": "revenue"},
    {"icon": "Users", "text": "How many guests are checking in today?", "category": "guests"},
    {"icon": "BedDouble", "text": "Which room types have availability?", "category": "rooms"},
    {"icon": "Calendar", "text": "What reservations are pending?", "category": "reservations"},
    {"icon": "BarChart3", "text": "Give me a weekly performance summary", "category": "summary"},
]


@router.post("/management/chat", response_model=ManagementChatResponse)
async def management_chat(
    request: ManagementChatRequest,
    user: TokenData = Depends(require_manager_or_above)
):
    """
    Management AI chat endpoint.
    
    Provides intelligent answers to business questions using live database data.
    Restricted to manager and admin roles.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Get the management agent
    agent = get_management_agent()
    
    try:
        # Get AI-powered answer with live metrics
        result = await agent.answer(
            question=request.message,
            tenant_id=user.tenant_id,
            include_metrics=request.include_metrics
        )
        
        return ManagementChatResponse(
            answer=result["answer"],
            metrics=result.get("metrics"),
            timestamp=result.get("timestamp", datetime.now(timezone.utc).isoformat())
        )
        
    except Exception as e:
        print(f"[ManagementChat] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response. Please try again."
        )


@router.get("/management/metrics")
async def get_dashboard_metrics(user: TokenData = Depends(require_manager_or_above)):
    """
    Get current dashboard metrics.
    
    Returns real-time KPIs from the live database.
    Restricted to manager and admin roles.
    """
    agent = get_management_agent()
    
    try:
        metrics = agent.get_dashboard_metrics(user.tenant_id)
        return metrics
    except Exception as e:
        print(f"[ManagementMetrics] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve metrics."
        )


@router.get("/management/examples")
async def get_example_questions(user: TokenData = Depends(require_manager_or_above)):
    """
    Get example questions for the management AI.
    """
    return {"examples": EXAMPLE_QUESTIONS}


@router.get("/management/insights")
async def get_quick_insights(user: TokenData = Depends(require_manager_or_above)):
    """
    Get AI-generated quick insights based on current metrics.
    """
    agent = get_management_agent()
    
    try:
        # Get metrics
        metrics = agent.get_dashboard_metrics(user.tenant_id)
        
        # Generate insights
        insights = []
        
        # Occupancy insight
        occ_rate = metrics.get("occupancy_rate", 0)
        if occ_rate >= 90:
            insights.append({
                "type": "success",
                "title": "High Occupancy",
                "message": f"Excellent! Hotel is at {occ_rate}% occupancy.",
                "category": "occupancy"
            })
        elif occ_rate >= 70:
            insights.append({
                "type": "info",
                "title": "Good Occupancy",
                "message": f"Hotel is at {occ_rate}% occupancy. Consider promotions to fill remaining rooms.",
                "category": "occupancy"
            })
        elif occ_rate < 50:
            insights.append({
                "type": "warning",
                "title": "Low Occupancy",
                "message": f"Occupancy at {occ_rate}%. Consider marketing campaigns or special rates.",
                "category": "occupancy"
            })
        
        # Pending reservations insight
        pending = metrics.get("pending_reservations", 0)
        if pending > 5:
            insights.append({
                "type": "warning",
                "title": "Pending Confirmations",
                "message": f"{pending} reservations pending. Review and confirm to secure bookings.",
                "category": "reservations"
            })
        
        # Cancellations insight
        cancellations = metrics.get("cancellations_week", 0)
        if cancellations > 3:
            insights.append({
                "type": "warning",
                "title": "Cancellation Alert",
                "message": f"{cancellations} cancellations this week. Review reasons and consider retention strategies.",
                "category": "cancellations"
            })
        
        # Check-ins today
        checkins = metrics.get("checkins_today", 0)
        if checkins > 0:
            insights.append({
                "type": "info",
                "title": "Arrivals Today",
                "message": f"{checkins} guests arriving today. Ensure rooms are ready.",
                "category": "arrivals"
            })
        
        # Revenue insight
        rev_today = metrics.get("revenue_today", 0)
        rev_week = metrics.get("revenue_week", 0)
        if rev_week > 0:
            daily_avg = rev_week / 7
            if rev_today > daily_avg * 1.2:
                insights.append({
                    "type": "success",
                    "title": "Strong Revenue Day",
                    "message": f"Today's revenue (${rev_today:,.0f}) is above weekly average.",
                    "category": "revenue"
                })
        
        return {
            "insights": insights,
            "metrics_summary": {
                "occupancy_rate": occ_rate,
                "active_reservations": metrics.get("active_reservations", 0),
                "revenue_today": rev_today,
                "pending_reservations": pending
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"[ManagementInsights] Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate insights."
        )
