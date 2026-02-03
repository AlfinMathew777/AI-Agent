"""
Admin Panel Query Functions
For monitoring, operations, payments, and receipts
"""
import sqlite3
from datetime import datetime, timedelta
from app.db.session import get_db_connection

def get_chat_history(tenant_id: str, audience: str = None, limit: int = 50, offset: int = 0):
    """Get chat history with pagination."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if audience:
            conditions.append("audience = ?")
            params.append(audience)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # Get total count
        c.execute(f"SELECT COUNT(*) FROM chat_logs{where_clause}", params)
        total = c.fetchone()[0]
        
        # Get paginated results
        query = f'''
            SELECT id, timestamp, session_id, audience, question, answer, latency_ms, created_at
            FROM chat_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        '''
        c.execute(query, params + [limit, offset])
        rows = c.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows], total
    except Exception as e:
        print(f"[Database] Error getting chat history: {e}")
        return [], 0

def get_chat_thread(session_id: str, tenant_id: str):
    """Get all messages in a chat thread (grouped by session_id)."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, timestamp, audience, question, answer, latency_ms
            FROM chat_logs
            WHERE session_id = ? AND tenant_id = ?
            ORDER BY timestamp ASC
        ''', (session_id, tenant_id))
        rows = c.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Database] Error getting chat thread: {e}")
        return []

def create_operation(tenant_id: str, op_type: str, entity_id: str = None, amount_cents: int = 0, status: str = "completed", metadata_json: str = None):
    """Create an operation record."""
    try:
        import uuid
        import json
        op_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO operations (id, tenant_id, type, entity_id, amount_cents, status, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (op_id, tenant_id, op_type, entity_id, amount_cents, status, metadata_json or json.dumps({})))
        conn.commit()
        conn.close()
        return op_id
    except Exception as e:
        print(f"[Database] Error creating operation: {e}")
        return None

def get_operations_summary(tenant_id: str):
    """Get operations summary for today."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Summary by type
        c.execute('''
            SELECT 
                type,
                COUNT(*) as count,
                SUM(amount_cents) as total_cents
            FROM operations
            WHERE tenant_id = ? AND date(created_at) = date(?)
            GROUP BY type
        ''', (tenant_id, today))
        by_type = c.fetchall()
        
        # Overall totals
        c.execute('''
            SELECT 
                COUNT(*) as total_ops,
                SUM(amount_cents) as revenue_cents
            FROM operations
            WHERE tenant_id = ? AND date(created_at) = date(?)
        ''', (tenant_id, today))
        totals = c.fetchone()
        
        conn.close()
        
        summary = {
            "total_operations": totals["total_ops"] or 0,
            "revenue_today_cents": totals["revenue_cents"] or 0,
            "by_type": {}
        }
        
        for row in by_type:
            summary["by_type"][row["type"]] = {
                "count": row["count"],
                "revenue_cents": row["total_cents"] or 0
            }
        
        return summary
    except Exception as e:
        print(f"[Database] Error getting operations summary: {e}")
        return {"total_operations": 0, "revenue_today_cents": 0, "by_type": {}}

def get_recent_operations(tenant_id: str, limit: int = 50):
    """Get recent operations."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, type, entity_id, amount_cents, status, created_at, metadata_json
            FROM operations
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (tenant_id, limit))
        rows = c.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Database] Error getting recent operations: {e}")
        return []

def get_payment_transactions(tenant_id: str, status: str = None, limit: int = 50, offset: int = 0):
    """Get payment transactions with pagination."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # Get total count
        c.execute(f"SELECT COUNT(*) FROM payments{where_clause}", params)
        total = c.fetchone()[0]
        
        # Get paginated results
        query = f'''
            SELECT id, quote_id, stripe_session_id, amount_cents, currency, status, created_at
            FROM payments
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        c.execute(query, params + [limit, offset])
        rows = c.fetchall()
        
        conn.close()
        return [dict(row) for row in rows], total
    except Exception as e:
        print(f"[Database] Error getting payments: {e}")
        return [], 0

def get_receipts_list(tenant_id: str, date_from: str = None, date_to: str = None, limit: int = 50, offset: int = 0):
    """Get receipts list with date filtering."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        conditions = ["tenant_id = ?"]
        params = [tenant_id]
        
        if date_from:
            conditions.append("date(created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            conditions.append("date(created_at) <= date(?)")
            params.append(date_to)
        
        where_clause = " WHERE " + " AND ".join(conditions)
        
        # Get total count
        c.execute(f"SELECT COUNT(*) FROM receipts{where_clause}", params)
        total = c.fetchone()[0]
        
        # Get paginated results
        query = f'''
            SELECT id, quote_id, total_cents, currency, status, created_at, booking_refs_json
            FROM receipts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        c.execute(query, params + [limit, offset])
        rows = c.fetchall()
        
        conn.close()
        return [dict(row) for row in rows], total
    except Exception as e:
        print(f"[Database] Error getting receipts: {e}")
        return [], 0

def get_recent_errors(limit: int = 20):
    """Get recent system errors."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, tenant_id, error_type, error_message, endpoint, created_at
            FROM system_errors
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        rows = c.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[Database] Error getting recent errors: {e}")
        return []

def log_error(tenant_id: str, error_type: str, error_message: str, stack_trace: str = None, endpoint: str = None):
    """Log a system error."""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO system_errors (tenant_id, error_type, error_message, stack_trace, endpoint)
            VALUES (?, ?, ?, ?, ?)
        ''', (tenant_id, error_type, error_message, stack_trace, endpoint))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Database] Error logging error: {e}")
