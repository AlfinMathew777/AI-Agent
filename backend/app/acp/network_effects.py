"""
Network Effects Module - Demand Signal Tracking
Tracks anonymized occupancy data and enables network insights
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.properties.registry import PropertyRegistry


def _init_network_db():
    """Initialize network effects database"""
    conn = sqlite3.connect("acp_network.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS demand_signals (
            property_id TEXT,
            date TEXT,
            total_requests INTEGER DEFAULT 0,
            bookings INTEGER DEFAULT 0,
            occupancy_estimate REAL DEFAULT 0.0,
            PRIMARY KEY (property_id, date)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weekly_summaries (
            week_start TEXT,
            property_id TEXT,
            avg_occupancy REAL,
            total_requests INTEGER,
            total_bookings INTEGER,
            shared BOOLEAN DEFAULT 0,
            PRIMARY KEY (week_start, property_id)
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_demand_date ON demand_signals(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_weekly_property ON weekly_summaries(property_id)")
    
    conn.commit()
    conn.close()


async def record_demand_signal(
    property_id: str,
    date: str,
    booking_made: bool = False
):
    """Record a demand signal for a property on a specific date"""
    _init_network_db()
    
    conn = sqlite3.connect("acp_network.db")
    cur = conn.cursor()
    
    # Get current values
    cur.execute("""
        SELECT total_requests, bookings FROM demand_signals
        WHERE property_id = ? AND date = ?
    """, (property_id, date))
    
    row = cur.fetchone()
    
    if row:
        new_requests = row[0] + 1
        new_bookings = row[1] + (1 if booking_made else 0)
        occupancy = new_bookings / max(new_requests, 1)
        
        cur.execute("""
            UPDATE demand_signals
            SET total_requests = ?, bookings = ?, occupancy_estimate = ?
            WHERE property_id = ? AND date = ?
        """, (new_requests, new_bookings, occupancy, property_id, date))
    else:
        cur.execute("""
            INSERT INTO demand_signals (property_id, date, total_requests, bookings, occupancy_estimate)
            VALUES (?, ?, 1, ?, ?)
        """, (property_id, date, 1 if booking_made else 0, 1.0 if booking_made else 0.0))
    
    conn.commit()
    conn.close()


async def get_property_demand(property_id: str, days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Get demand signals for a property"""
    _init_network_db()
    
    conn = sqlite3.connect("acp_network.db")
    cur = conn.cursor()
    
    start_date = datetime.utcnow().date().isoformat()
    end_date = (datetime.utcnow() + timedelta(days=days_ahead)).date().isoformat()
    
    cur.execute("""
        SELECT date, total_requests, bookings, occupancy_estimate
        FROM demand_signals
        WHERE property_id = ? AND date >= ? AND date <= ?
        ORDER BY date
    """, (property_id, start_date, end_date))
    
    rows = cur.fetchall()
    conn.close()
    
    return [
        {
            "date": row[0],
            "requests": row[1],
            "bookings": row[2],
            "occupancy_estimate": row[3]
        }
        for row in rows
    ]


async def generate_weekly_summary(property_id: Optional[str] = None):
    """Generate weekly demand summary for properties (opt-in)"""
    _init_network_db()
    
    # Calculate current week start (Monday)
    today = datetime.utcnow().date()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    
    registry = PropertyRegistry()
    properties = [registry.get_property(property_id)] if property_id else registry.list_active_properties()
    
    conn = sqlite3.connect("acp_network.db")
    cur = conn.cursor()
    
    for prop in properties:
        if not prop:
            continue
        
        # Check if property has opted in to sharing
        opt_in = prop.config_json.get("share_demand_signals", False)
        
        # Calculate stats for the week
        cur.execute("""
            SELECT 
                AVG(occupancy_estimate) as avg_occ,
                SUM(total_requests) as total_req,
                SUM(bookings) as total_book
            FROM demand_signals
            WHERE property_id = ? AND date >= ? AND date < ?
        """, (prop.property_id, week_start, (datetime.fromisoformat(week_start) + timedelta(days=7)).date().isoformat()))
        
        row = cur.fetchone()
        
        if row and row[0] is not None:
            cur.execute("""
                INSERT OR REPLACE INTO weekly_summaries
                (week_start, property_id, avg_occupancy, total_requests, total_bookings, shared)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (week_start, prop.property_id, row[0], row[1] or 0, row[2] or 0, 1 if opt_in else 0))
    
    conn.commit()
    conn.close()


async def get_network_insights() -> Dict[str, Any]:
    """Get anonymized network-wide demand insights"""
    _init_network_db()
    
    conn = sqlite3.connect("acp_network.db")
    cur = conn.cursor()
    
    # Get current week
    today = datetime.utcnow().date()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    
    # Get shared summaries only
    cur.execute("""
        SELECT 
            AVG(avg_occupancy) as network_avg_occ,
            SUM(total_requests) as network_requests,
            SUM(total_bookings) as network_bookings,
            COUNT(*) as properties_sharing
        FROM weekly_summaries
        WHERE week_start = ? AND shared = 1
    """, (week_start,))
    
    row = cur.fetchone()
    conn.close()
    
    return {
        "week_start": week_start,
        "network_avg_occupancy": row[0] or 0.0,
        "network_requests": row[1] or 0,
        "network_bookings": row[2] or 0,
        "properties_sharing": row[3] or 0,
        "anonymized": True
    }
