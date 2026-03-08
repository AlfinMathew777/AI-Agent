"""
Commission Ledger - Revenue Infrastructure
Tracks commissions per booking and generates monthly invoices
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from app.acp.transaction.manager import Transaction
from app.properties.registry import PropertyRegistry


def _init_commission_db():
    """Initialize commission database"""
    conn = sqlite3.connect("acp_commissions.db")
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commissions_accrued (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id TEXT UNIQUE,
            property_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            booking_value REAL NOT NULL,
            commission_rate REAL NOT NULL,
            commission_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commissions_paid (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT NOT NULL,
            month TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            paid_at TIMESTAMP,
            UNIQUE(property_id, month)
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_commissions_property ON commissions_accrued(property_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_commissions_agent ON commissions_accrued(agent_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_commissions_month ON commissions_accrued(created_at)")
    
    conn.commit()
    conn.close()


async def record_commission(tx: Transaction, execution_result: Dict[str, Any]):
    """Record commission for a successful booking"""
    _init_commission_db()
    
    # Get property tier to determine commission rate
    registry = PropertyRegistry()
    property = registry.get_property(tx.target_entity_id)
    tier = property.config_json.get("tier", "standard") if property else "standard"
    
    # Commission rates by tier
    commission_rates = {
        "budget": 0.08,  # 8%
        "standard": 0.10,  # 10%
        "luxury": 0.12,  # 12%
    }
    commission_rate = commission_rates.get(tier, 0.10)
    
    # Extract booking value from execution result
    booking_value = execution_result.get("payload", {}).get("booking_value", 0)
    if booking_value <= 0:
        # Fallback: estimate from transaction
        booking_value = tx.current_offer.get("price", 0) if tx.current_offer else 0
    
    commission_amount = booking_value * commission_rate
    
    # Store commission
    conn = sqlite3.connect("acp_commissions.db")
    cur = conn.cursor()
    
    booking_id = execution_result.get("payload", {}).get("pms_reference", tx.tx_id)
    
    cur.execute("""
        INSERT OR IGNORE INTO commissions_accrued
        (booking_id, property_id, agent_id, booking_value, commission_rate, commission_amount)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        booking_id,
        tx.target_entity_id,
        tx.agent_id,
        booking_value,
        commission_rate,
        commission_amount
    ))
    
    conn.commit()
    conn.close()


async def get_property_commissions(property_id: str, month: Optional[str] = None) -> Dict[str, Any]:
    """Get commission summary for a property"""
    _init_commission_db()
    
    conn = sqlite3.connect("acp_commissions.db")
    cur = conn.cursor()
    
    if month:
        cur.execute("""
            SELECT 
                SUM(commission_amount) as total,
                COUNT(*) as booking_count,
                AVG(commission_rate) as avg_rate
            FROM commissions_accrued
            WHERE property_id = ? AND strftime('%Y-%m', created_at) = ?
        """, (property_id, month))
    else:
        cur.execute("""
            SELECT 
                SUM(commission_amount) as total,
                COUNT(*) as booking_count,
                AVG(commission_rate) as avg_rate
            FROM commissions_accrued
            WHERE property_id = ?
        """, (property_id,))
    
    row = cur.fetchone()
    conn.close()
    
    return {
        "property_id": property_id,
        "total_commissions": row[0] or 0.0,
        "booking_count": row[1] or 0,
        "average_rate": row[2] or 0.0,
        "month": month or "all_time"
    }


async def generate_monthly_invoice(property_id: str, month: str) -> Dict[str, Any]:
    """Generate monthly commission invoice"""
    summary = await get_property_commissions(property_id, month)
    
    return {
        "property_id": property_id,
        "month": month,
        "total_commissions": summary["total_commissions"],
        "booking_count": summary["booking_count"],
        "invoice_date": datetime.utcnow().isoformat(),
        "status": "pending_payment"
    }
