"""
Management Intelligence Agent

This agent provides real-time business intelligence for hotel managers and admins.
It queries the live database for metrics and uses Gemini for summarization and insights.
"""

import sqlite3
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Any
from app.db.session import get_db_connection
from app.services.llm_service import HotelAI

# Metric query templates
METRIC_QUERIES = {
    "occupancy": """
        SELECT 
            COUNT(CASE WHEN status = 'occupied' THEN 1 END) as occupied,
            COUNT(*) as total
        FROM rooms WHERE tenant_id = ?
    """,
    "reservations_today": """
        SELECT COUNT(*) as count, SUM(COALESCE(total_amount, 0)) as revenue
        FROM reservations 
        WHERE tenant_id = ? AND DATE(check_in_date) = DATE('now')
    """,
    "reservations_active": """
        SELECT COUNT(*) as count
        FROM reservations 
        WHERE tenant_id = ? 
        AND DATE(check_in_date) <= DATE('now') 
        AND DATE(check_out_date) >= DATE('now')
        AND status != 'cancelled'
    """,
    "checkouts_today": """
        SELECT COUNT(*) as count
        FROM reservations 
        WHERE tenant_id = ? AND DATE(check_out_date) = DATE('now')
    """,
    "revenue_today": """
        SELECT COALESCE(SUM(total_amount), 0) as total
        FROM reservations 
        WHERE tenant_id = ? 
        AND DATE(created_at) = DATE('now')
        AND status != 'cancelled'
    """,
    "revenue_week": """
        SELECT COALESCE(SUM(total_amount), 0) as total
        FROM reservations 
        WHERE tenant_id = ? 
        AND DATE(created_at) >= DATE('now', '-7 days')
        AND status != 'cancelled'
    """,
    "revenue_month": """
        SELECT COALESCE(SUM(total_amount), 0) as total
        FROM reservations 
        WHERE tenant_id = ? 
        AND DATE(created_at) >= DATE('now', '-30 days')
        AND status != 'cancelled'
    """,
    "cancellations_week": """
        SELECT COUNT(*) as count
        FROM reservations 
        WHERE tenant_id = ? 
        AND status = 'cancelled'
        AND DATE(created_at) >= DATE('now', '-7 days')
    """,
    "pending_reservations": """
        SELECT COUNT(*) as count
        FROM reservations 
        WHERE tenant_id = ? AND status = 'pending'
    """,
    "rooms_available": """
        SELECT COUNT(*) as count
        FROM rooms 
        WHERE tenant_id = ? AND status = 'available'
    """,
    "rooms_maintenance": """
        SELECT COUNT(*) as count
        FROM rooms 
        WHERE tenant_id = ? AND status = 'maintenance'
    """,
    "room_types_summary": """
        SELECT room_type, 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as available
        FROM rooms 
        WHERE tenant_id = ?
        GROUP BY room_type
    """,
    "recent_reservations": """
        SELECT guest_name, guest_email, room_number, check_in_date, check_out_date, 
               total_amount, status, created_at
        FROM reservations 
        WHERE tenant_id = ?
        ORDER BY created_at DESC
        LIMIT 10
    """,
    "upcoming_arrivals": """
        SELECT guest_name, room_number, check_in_date, total_amount
        FROM reservations 
        WHERE tenant_id = ? 
        AND DATE(check_in_date) >= DATE('now')
        AND DATE(check_in_date) <= DATE('now', '+3 days')
        AND status != 'cancelled'
        ORDER BY check_in_date
        LIMIT 10
    """,
    "departures_today": """
        SELECT guest_name, room_number, check_out_date
        FROM reservations 
        WHERE tenant_id = ? 
        AND DATE(check_out_date) = DATE('now')
        AND status = 'confirmed'
    """
}


class ManagementAgent:
    """
    Management Intelligence Agent that provides real-time business insights.
    Connects to live database and uses Gemini for intelligent summarization.
    """
    
    def __init__(self, hotel_ai: HotelAI):
        self.hotel_ai = hotel_ai
        self.provider = hotel_ai.provider
    
    def _execute_query(self, query: str, tenant_id: str) -> List[Dict]:
        """Execute a database query and return results as list of dicts."""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(query, (tenant_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_dashboard_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get all dashboard KPI metrics."""
        metrics = {}
        
        # Occupancy
        occ_result = self._execute_query(METRIC_QUERIES["occupancy"], tenant_id)
        if occ_result:
            occupied = occ_result[0].get("occupied", 0) or 0
            total = occ_result[0].get("total", 0) or 1
            metrics["occupancy_rate"] = round((occupied / total) * 100, 1) if total > 0 else 0
            metrics["occupied_rooms"] = occupied
            metrics["total_rooms"] = total
        
        # Available rooms
        avail_result = self._execute_query(METRIC_QUERIES["rooms_available"], tenant_id)
        metrics["available_rooms"] = avail_result[0].get("count", 0) if avail_result else 0
        
        # Active reservations
        active_result = self._execute_query(METRIC_QUERIES["reservations_active"], tenant_id)
        metrics["active_reservations"] = active_result[0].get("count", 0) if active_result else 0
        
        # Pending reservations
        pending_result = self._execute_query(METRIC_QUERIES["pending_reservations"], tenant_id)
        metrics["pending_reservations"] = pending_result[0].get("count", 0) if pending_result else 0
        
        # Today's check-ins
        checkin_result = self._execute_query(METRIC_QUERIES["reservations_today"], tenant_id)
        metrics["checkins_today"] = checkin_result[0].get("count", 0) if checkin_result else 0
        
        # Today's check-outs
        checkout_result = self._execute_query(METRIC_QUERIES["checkouts_today"], tenant_id)
        metrics["checkouts_today"] = checkout_result[0].get("count", 0) if checkout_result else 0
        
        # Revenue
        rev_today = self._execute_query(METRIC_QUERIES["revenue_today"], tenant_id)
        metrics["revenue_today"] = float(rev_today[0].get("total", 0) or 0) if rev_today else 0
        
        rev_week = self._execute_query(METRIC_QUERIES["revenue_week"], tenant_id)
        metrics["revenue_week"] = float(rev_week[0].get("total", 0) or 0) if rev_week else 0
        
        rev_month = self._execute_query(METRIC_QUERIES["revenue_month"], tenant_id)
        metrics["revenue_month"] = float(rev_month[0].get("total", 0) or 0) if rev_month else 0
        
        # Cancellations
        cancel_result = self._execute_query(METRIC_QUERIES["cancellations_week"], tenant_id)
        metrics["cancellations_week"] = cancel_result[0].get("count", 0) if cancel_result else 0
        
        # Room types breakdown
        room_types = self._execute_query(METRIC_QUERIES["room_types_summary"], tenant_id)
        metrics["room_types"] = room_types
        
        # Recent reservations
        recent = self._execute_query(METRIC_QUERIES["recent_reservations"], tenant_id)
        metrics["recent_reservations"] = recent[:5]  # Top 5
        
        # Upcoming arrivals
        arrivals = self._execute_query(METRIC_QUERIES["upcoming_arrivals"], tenant_id)
        metrics["upcoming_arrivals"] = arrivals
        
        metrics["generated_at"] = datetime.now(timezone.utc).isoformat()
        
        return metrics
    
    def _build_context_from_metrics(self, metrics: Dict) -> str:
        """Build a context string from metrics for LLM."""
        context = f"""
## Current Hotel Metrics (Real-time Data)

### Occupancy
- Occupancy Rate: {metrics.get('occupancy_rate', 0)}%
- Occupied Rooms: {metrics.get('occupied_rooms', 0)} / {metrics.get('total_rooms', 0)}
- Available Rooms: {metrics.get('available_rooms', 0)}

### Reservations
- Active Reservations: {metrics.get('active_reservations', 0)}
- Pending Reservations: {metrics.get('pending_reservations', 0)}
- Check-ins Today: {metrics.get('checkins_today', 0)}
- Check-outs Today: {metrics.get('checkouts_today', 0)}

### Revenue
- Revenue Today: ${metrics.get('revenue_today', 0):,.2f}
- Revenue This Week: ${metrics.get('revenue_week', 0):,.2f}
- Revenue This Month: ${metrics.get('revenue_month', 0):,.2f}

### Issues & Cancellations
- Cancellations (7 days): {metrics.get('cancellations_week', 0)}

### Room Types Breakdown
"""
        for rt in metrics.get('room_types', []):
            context += f"- {rt.get('room_type', 'Unknown')}: {rt.get('available', 0)} available / {rt.get('total', 0)} total\n"
        
        if metrics.get('upcoming_arrivals'):
            context += "\n### Upcoming Arrivals (Next 3 Days)\n"
            for arr in metrics.get('upcoming_arrivals', [])[:5]:
                context += f"- {arr.get('guest_name', 'Guest')} - Room {arr.get('room_number', 'N/A')} on {arr.get('check_in_date', 'N/A')}\n"
        
        return context
    
    def _build_prompt(self, question: str, metrics_context: str) -> str:
        """Build the LLM prompt with metrics context."""
        return f"""You are an intelligent Hotel Management Assistant with access to real-time hotel data.
Your role is to help hotel managers and administrators understand their business metrics and make data-driven decisions.

{metrics_context}

## Manager's Question
{question}

## Response Guidelines
1. **Use the actual data provided above** - never make up numbers
2. Provide specific metrics when answering
3. If asked about trends, note this is current snapshot data
4. Give actionable insights when relevant
5. Be concise but comprehensive
6. Highlight any concerns or opportunities you notice

Format your response with:
- **Answer**: Direct response to the question
- **Key Metrics**: Relevant numbers from the data
- **Insight**: Business insight or recommendation (if applicable)
"""
    
    async def answer(
        self,
        question: str,
        tenant_id: str,
        include_metrics: bool = True
    ) -> Dict:
        """
        Answer a management question using live data and AI.
        
        Returns:
            Dict with 'answer', 'metrics', 'timestamp'
        """
        # 1. Get current metrics
        metrics = self.get_dashboard_metrics(tenant_id)
        
        # 2. Build context from metrics
        metrics_context = self._build_context_from_metrics(metrics)
        
        # 3. Build prompt
        prompt = self._build_prompt(question, metrics_context)
        
        # 4. Generate response using LLM
        try:
            if self.provider == "gemini" and self.hotel_ai._gemini_model:
                answer = await self._generate_gemini_response(prompt)
            else:
                answer = self._generate_offline_response(question, metrics)
        except Exception as e:
            print(f"[ManagementAgent] Error generating response: {e}")
            answer = self._generate_offline_response(question, metrics)
        
        return {
            "answer": answer,
            "metrics": metrics if include_metrics else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _generate_gemini_response(self, prompt: str) -> str:
        """Generate response using Gemini."""
        import asyncio
        import functools
        
        try:
            loop = asyncio.get_running_loop()
            func = functools.partial(
                self.hotel_ai._gemini_model.generate_content,
                prompt
            )
            
            response = await asyncio.wait_for(
                loop.run_in_executor(None, func),
                timeout=30.0
            )
            
            if hasattr(response, 'text') and response.text:
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    return part.text
            
            return "I was unable to generate a response. Please try again."
            
        except asyncio.TimeoutError:
            return "The request timed out. Please try again."
        except Exception as e:
            print(f"[ManagementAgent] Gemini error: {e}")
            raise
    
    def _generate_offline_response(self, question: str, metrics: Dict) -> str:
        """Generate a basic response using metrics data when LLM is unavailable."""
        q_lower = question.lower()
        
        if "occupancy" in q_lower:
            return f"""**Answer**: Current occupancy rate is {metrics.get('occupancy_rate', 0)}%.

**Key Metrics**:
- Occupied Rooms: {metrics.get('occupied_rooms', 0)}
- Total Rooms: {metrics.get('total_rooms', 0)}
- Available Rooms: {metrics.get('available_rooms', 0)}

**Insight**: This is real-time data from the hotel database."""
        
        elif "revenue" in q_lower:
            return f"""**Answer**: Here's the revenue summary:

**Key Metrics**:
- Revenue Today: ${metrics.get('revenue_today', 0):,.2f}
- Revenue This Week: ${metrics.get('revenue_week', 0):,.2f}
- Revenue This Month: ${metrics.get('revenue_month', 0):,.2f}

**Insight**: Revenue tracking is based on confirmed reservations."""
        
        elif "reservation" in q_lower or "booking" in q_lower:
            return f"""**Answer**: Here's the reservation summary:

**Key Metrics**:
- Active Reservations: {metrics.get('active_reservations', 0)}
- Pending Reservations: {metrics.get('pending_reservations', 0)}
- Check-ins Today: {metrics.get('checkins_today', 0)}
- Check-outs Today: {metrics.get('checkouts_today', 0)}

**Insight**: Monitor pending reservations for follow-up."""
        
        else:
            return f"""**Answer**: Here's a summary of current hotel metrics:

**Key Metrics**:
- Occupancy: {metrics.get('occupancy_rate', 0)}%
- Active Reservations: {metrics.get('active_reservations', 0)}
- Revenue Today: ${metrics.get('revenue_today', 0):,.2f}
- Available Rooms: {metrics.get('available_rooms', 0)}

**Insight**: For more specific information, please ask about occupancy, revenue, or reservations."""


# Singleton instance
_management_agent: Optional[ManagementAgent] = None


def get_management_agent() -> ManagementAgent:
    """Get or create the ManagementAgent singleton."""
    global _management_agent
    if _management_agent is None:
        from app.ai_service import hotel_ai
        _management_agent = ManagementAgent(hotel_ai)
    return _management_agent
