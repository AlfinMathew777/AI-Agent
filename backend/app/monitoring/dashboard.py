"""
Monitoring Dashboard - Track system health per property
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.properties.registry import PropertyRegistry


def _init_monitoring_db():
    """Initialize monitoring database"""
    conn = sqlite3.connect("acp_monitoring.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pms_sync_status (
            property_id TEXT,
            last_sync_at TIMESTAMP,
            sync_status TEXT,
            error_message TEXT,
            PRIMARY KEY (property_id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS booking_metrics (
            property_id TEXT,
            date TEXT,
            total_requests INTEGER,
            successful_bookings INTEGER,
            failed_bookings INTEGER,
            avg_latency_ms REAL,
            PRIMARY KEY (property_id, date)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT,
            error_type TEXT,
            error_message TEXT,
            endpoint TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_errors_property ON error_logs(property_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_errors_time ON error_logs(created_at)")
    
    conn.commit()
    conn.close()


async def record_pms_sync(property_id: str, status: str, error_message: Optional[str] = None):
    """Record PMS sync status"""
    _init_monitoring_db()
    
    conn = sqlite3.connect("acp_monitoring.db")
    cur = conn.cursor()
    
    cur.execute("""
        INSERT OR REPLACE INTO pms_sync_status
        (property_id, last_sync_at, sync_status, error_message)
        VALUES (?, ?, ?, ?)
    """, (property_id, datetime.utcnow().isoformat(), status, error_message))
    
    conn.commit()
    conn.close()


async def record_booking_metric(
    property_id: str,
    success: bool,
    latency_ms: float
):
    """Record booking metric"""
    _init_monitoring_db()
    
    conn = sqlite3.connect("acp_monitoring.db")
    cur = conn.cursor()
    
    today = datetime.utcnow().date().isoformat()
    
    # Get existing metrics
    cur.execute("""
        SELECT total_requests, successful_bookings, failed_bookings, avg_latency_ms
        FROM booking_metrics
        WHERE property_id = ? AND date = ?
    """, (property_id, today))
    
    row = cur.fetchone()
    
    if row:
        total = row[0] + 1
        successful = row[1] + (1 if success else 0)
        failed = row[2] + (1 if not success else 0)
        avg_latency = ((row[3] * (total - 1)) + latency_ms) / total
        
        cur.execute("""
            UPDATE booking_metrics
            SET total_requests = ?, successful_bookings = ?, failed_bookings = ?, avg_latency_ms = ?
            WHERE property_id = ? AND date = ?
        """, (total, successful, failed, avg_latency, property_id, today))
    else:
        cur.execute("""
            INSERT INTO booking_metrics
            (property_id, date, total_requests, successful_bookings, failed_bookings, avg_latency_ms)
            VALUES (?, ?, 1, ?, ?, ?)
        """, (property_id, today, 1 if success else 0, 1 if not success else 0, latency_ms))
    
    conn.commit()
    conn.close()


async def get_dashboard_stats(property_id: Optional[str] = None) -> Dict[str, Any]:
    """Get dashboard statistics"""
    _init_monitoring_db()
    
    registry = PropertyRegistry()
    properties = registry.list_active_properties() if not property_id else [registry.get_property(property_id)]
    
    stats = []
    for prop in properties:
        if not prop:
            continue
        
        conn = sqlite3.connect("acp_monitoring.db")
        cur = conn.cursor()
        
        # Get sync status
        cur.execute("""
            SELECT last_sync_at, sync_status, error_message
            FROM pms_sync_status
            WHERE property_id = ?
        """, (prop.property_id,))
        sync_row = cur.fetchone()
        
        # Get today's metrics
        today = datetime.utcnow().date().isoformat()
        cur.execute("""
            SELECT total_requests, successful_bookings, failed_bookings, avg_latency_ms
            FROM booking_metrics
            WHERE property_id = ? AND date = ?
        """, (prop.property_id, today))
        metric_row = cur.fetchone()
        
        # Get error count (last 24h)
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        cur.execute("""
            SELECT COUNT(*) FROM error_logs
            WHERE property_id = ? AND created_at >= ?
        """, (prop.property_id, since))
        error_count = cur.fetchone()[0]
        
        conn.close()
        
        stats.append({
            "property_id": prop.property_id,
            "name": prop.name,
            "pms_sync": {
                "last_sync": sync_row[0] if sync_row else None,
                "status": sync_row[1] if sync_row else "unknown",
                "error": sync_row[2] if sync_row else None,
            },
            "today_metrics": {
                "total_requests": metric_row[0] if metric_row else 0,
                "successful": metric_row[1] if metric_row else 0,
                "failed": metric_row[2] if metric_row else 0,
                "avg_latency_ms": metric_row[3] if metric_row else 0.0,
                "success_rate": (
                    (metric_row[1] / metric_row[0]) if metric_row and metric_row[0] > 0 else 0.0
                ),
            },
            "errors_24h": error_count,
        })
    
    return {
        "properties": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


async def check_alerts() -> List[Dict[str, Any]]:
    """Check for alert conditions"""
    _init_monitoring_db()
    alerts = []
    
    registry = PropertyRegistry()
    properties = registry.list_active_properties()
    
    for prop in properties:
        conn = sqlite3.connect("acp_monitoring.db")
        cur = conn.cursor()
        
        # Check PMS downtime
        cur.execute("""
            SELECT last_sync_at, sync_status FROM pms_sync_status
            WHERE property_id = ?
        """, (prop.property_id,))
        sync_row = cur.fetchone()
        
        if sync_row:
            last_sync = datetime.fromisoformat(sync_row[0])
            if (datetime.utcnow() - last_sync).total_seconds() > 120:  # 2 minutes
                alerts.append({
                    "type": "pms_downtime",
                    "property_id": prop.property_id,
                    "severity": "high",
                    "message": f"PMS sync overdue for {prop.property_id}"
                })
        
        # Check error spike
        since = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        cur.execute("""
            SELECT COUNT(*) FROM error_logs
            WHERE property_id = ? AND created_at >= ?
        """, (prop.property_id, since))
        recent_errors = cur.fetchone()[0]
        
        if recent_errors > 10:
            alerts.append({
                "type": "error_spike",
                "property_id": prop.property_id,
                "severity": "medium",
                "message": f"{recent_errors} errors in last 10 minutes"
            })
        
        conn.close()
    
    return alerts
