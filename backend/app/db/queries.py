
import sqlite3
import time
from datetime import datetime, timedelta
from app.config import ROOM_CAPACITY, DEFAULT_ROOM_CAPACITY
from app.db.session import get_db_connection

def log_chat(audience, question, answer, model="gemini-flash-latest", latency_ms=0, tenant_id=None):
    """Log a chat interaction."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO chat_logs (audience, question, answer, model_used, latency_ms, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (audience, question, answer, model, latency_ms, tenant_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error logging chat: {e}")

def log_tool_call(session_id, audience, tool_name, params_str, result_str, risk_level, status, latency_ms=0):
    """Log a tool execution."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO tool_calls (session_id, audience, tool_name, params_json, result_json, risk_level, status, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, audience, tool_name, params_str, result_str, risk_level, status, latency_ms))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error logging tool call: {e}")

def create_action(action_id, session_id, tool_name, params_str, requires_confirmation=True, tenant_id=None):
    """Create a pending action."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO actions (action_id, session_id, tool_name, params_json, requires_confirmation, confirmed, status, tenant_id)
            VALUES (?, ?, ?, ?, ?, 0, 'pending', ?)
        ''', (action_id, session_id, tool_name, params_str, 1 if requires_confirmation else 0, tenant_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error creating action: {e}")

def confirm_action(action_id):
    """Mark an action as confirmed."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE actions 
            SET confirmed = 1, status = 'confirmed'
            WHERE action_id = ?
        ''', (action_id,))
        conn.commit()
        conn.close()
        return c.rowcount > 0
    except Exception as e:
        print(f"[Database] Error confirming action: {e}")
        return False

def update_action_status(action_id, status):
    """Update action status (e.g. to 'completed' or 'failed')."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE actions 
            SET status = ?
            WHERE action_id = ?
        ''', (status, action_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error updating action status: {e}")

def get_analytics_stats():
    """Get real stats from the DB."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. Total chats today
        c.execute("SELECT COUNT(*) FROM chat_logs WHERE date(timestamp) = date('now')")
        chats_today = c.fetchone()[0]
        
        # 2. Total active chats (simulated as queries in last hour)
        c.execute("SELECT COUNT(*) FROM chat_logs WHERE timestamp > datetime('now', '-1 hour')")
        active_now = c.fetchone()[0]
        
        # 3. Recent queries
        c.execute("SELECT timestamp, question, audience FROM chat_logs ORDER BY timestamp DESC LIMIT 5")
        recent_rows = c.fetchall()
        recent_queries = []
        for row in recent_rows:
            # Parse timestamp for simpler display
            try:
                dt = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")
                time_str = dt.strftime("%I:%M %p")
            except:
                time_str = row['timestamp']
            
            recent_queries.append({
                "time": time_str,
                "query": row['question'],
                "sentiment": "neutral" # Placeholder until we have sentiment analysis
            })
            
        conn.close()
        
        return {
            "daily_stats": {
                "active_chats": active_now,
                "queries_today": chats_today,
                "avg_sentiment": 0.0, # Placeholder
                "unresolved_issues": 0
            },
            "recent_queries": recent_queries
        }
    except Exception as e:
        print(f"[Database] Error getting analytics: {e}")
        return {}

def create_booking(guest_name, room_type, date, status="confirmed"):
    """Create a new booking in the DB."""
    try:
        booking_id = f"BK-{int(time.time())}"
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO bookings (booking_id, guest_name, room_type, date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (booking_id, guest_name, room_type, date, status))
        conn.commit()
        conn.close()
        return booking_id
    except Exception as e:
        print(f"[Database] Error creating booking: {e}")
        return None

def check_room_availability(room_type, date):
    """Check if a room type is available on a given date."""
    try:
        # Normalize room type
        normalized_type = room_type.strip().lower()
        capacity = ROOM_CAPACITY.get(normalized_type, DEFAULT_ROOM_CAPACITY)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Count confirmed bookings
        c.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE lower(room_type) = ? AND date = ? AND status = 'confirmed'
        ''', (normalized_type, date))
        count = c.fetchone()[0]
        conn.close()
        
        is_available = count < capacity
        return is_available, count, capacity
        
    except Exception as e:
        print(f"[Database] Error checking availability: {e}")
        return False, 0, 0

def get_bookings(date_filter=None, room_type=None, status_filter=None, limit=50, offset=0, order="desc"):
    """Get bookings with filters and stats."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. Build Base Filter Clause
        conditions = []
        params = []
        
        if date_filter:
            conditions.append("date = ?")
            params.append(date_filter)
        if room_type:
            conditions.append("room_type = ?")
            params.append(room_type)
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
            
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # 2. Main Query
        query = f"SELECT * FROM bookings{where_clause}"
        
        # Whitelist order
        if order.lower() not in ["asc", "desc"]:
            order = "desc"
        query += f" ORDER BY created_at {order.upper()}"
        
        # Limit/Offset
        query += " LIMIT ? OFFSET ?"
        # Copy params for main query
        query_params = params + [min(int(limit), 200), int(offset)]
        
        c.execute(query, query_params)
        rows = c.fetchall()
        
        # 3. Stats Query (Breakdown by status, respecting other filters? 
        # If we filter by status, the stats will only show that status. That's fine.)
        stats_query = f"SELECT status, COUNT(*) as count FROM bookings{where_clause} GROUP BY status"
        c.execute(stats_query, params)
        stats_rows = c.fetchall()
        
        summary = {"total": 0, "confirmed": 0, "cancelled": 0}
        for r in stats_rows:
            # Row access by name or index. row_factory is sqlite3.Row
            s_status = r["status"].lower()
            count = r["count"]
            summary["total"] += count
            if s_status == "confirmed":
                summary["confirmed"] = count
            elif s_status == "cancelled":
                summary["cancelled"] = count
                
        # If status was not in confirmed/cancelled (e.g. 'pending'), it's still in total
        
        return {
            "bookings": [dict(row) for row in rows], 
            "summary": summary
        }
    except Exception as e:
        print(f"[Database] Error getting bookings: {e}")
        return {"bookings": [], "summary": {"total":0, "confirmed":0, "cancelled":0}}
        

def create_plan(plan_id, session_id, audience, question, plan_summary, status="created"):
    """Create a new plan."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO plans (id, session_id, audience, question, plan_summary, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (plan_id, session_id, audience, question, plan_summary, status))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Error creating plan: {e}")
        return False

def add_plan_step(step_id, plan_id, step_index, step_type, tool_name, tool_args_json, risk, status="pending"):
    """Add a step to a plan."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO plan_steps (id, plan_id, step_index, step_type, tool_name, tool_args_json, risk, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (step_id, plan_id, step_index, step_type, tool_name, tool_args_json, risk, status))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database] Error adding plan step: {e}")
        return False

def update_plan_status(plan_id, status):
    """Update plan status."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE plans 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, plan_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error updating plan status: {e}")

def update_step_status(step_id, status, result_json=None):
    """Update step status and optionally result."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        if result_json is not None:
            c.execute('''
                UPDATE plan_steps 
                SET status = ?, result_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, result_json, step_id))
        else:
            c.execute('''
                UPDATE plan_steps 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, step_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error updating step status: {e}")

def get_plan(plan_id):
    """Get plan and its steps."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        plan = c.fetchone()
        
        if not plan:
            conn.close()
            return None
            
        c.execute("SELECT * FROM plan_steps WHERE plan_id = ? ORDER BY step_index ASC", (plan_id,))
        steps = c.fetchall()
        
        conn.close()
        
        return {
            "plan": dict(plan),
            "steps": [dict(s) for s in steps]
        }
    except Exception as e:
        print(f"[Database] Error getting plan: {e}")
        return None
        

def get_tool_stats(days=7, limit=20, audience=None, tool=None):
    """Get aggregated tool stats and recent history."""
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Validation checks
        days = max(1, min(int(days), 30))
        limit = max(1, min(int(limit), 100))
        
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Filter Clauses
        conditions = ["created_at >= ?"]
        params = [start_date]
        
        if audience:
            conditions.append("audience = ?")
            params.append(audience)
        if tool:
            conditions.append("tool_name = ?")
            params.append(tool)
            
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # 1. Totals
        c.execute(f'''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN lower(status) = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN lower(status) = 'failed' OR lower(status) = 'error' THEN 1 ELSE 0 END) as failed,
                AVG(latency_ms) as avg_latency
            FROM tool_calls
            {where_clause}
        ''', params)
        total_row = c.fetchone()
        
        totals = {
            "tool_calls": total_row["total"] or 0,
            "success": total_row["success"] or 0,
            "failed": total_row["failed"] or 0,
            "cancelled": 0, # Not tracked in tool_calls, but required by API spec. 0 for now.
            "avg_latency_ms": round(total_row["avg_latency"] or 0, 2)
        }
        
        # 2. By Tool
        c.execute(f'''
            SELECT 
                tool_name,
                COUNT(*) as total,
                SUM(CASE WHEN lower(status) = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN lower(status) = 'failed' OR lower(status) = 'error' THEN 1 ELSE 0 END) as failed,
                AVG(latency_ms) as avg_latency
            FROM tool_calls
            {where_clause}
            GROUP BY tool_name
        ''', params)
        by_tool_rows = c.fetchall()
        
        by_tool = []
        for r in by_tool_rows:
            by_tool.append({
                "tool_name": r["tool_name"],
                "tool_calls": r["total"],
                "success": r["success"],
                "failed": r["failed"],
                "avg_latency_ms": round(r["avg_latency"] or 0, 2)
            })
            
        # 3. Recent
        query_recent = f"SELECT * FROM tool_calls {where_clause} ORDER BY created_at DESC LIMIT ?"
        c.execute(query_recent, params + [limit])
        recent_rows = c.fetchall()
        
        recent = [dict(r) for r in recent_rows]
        
        conn.close()
        
        return {
            "totals": totals,
            "by_tool": by_tool,
            "recent": recent
        }
    except Exception as e:
        print(f"[Database] Error getting tool stats: {e}")
        return {}
