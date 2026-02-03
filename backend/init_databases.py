"""
Quick Database Initializer
Creates all required databases with proper schemas
"""

import sqlite3
import asyncio
from app.acp.transaction.manager import TransactionManager
from app.acp.trust.authenticator import ACPAuthenticator
from app.monitoring.dashboard import init_monitoring_db

async def init_all_databases():
    print("Initializing all Phase 3 databases...")
    
    # 1. Initialize transaction manager (creates acp_transactions.db)
    print("\n1. Creating acp_transactions.db...")
    tx_mgr = TransactionManager()
    await tx_mgr.initialize()
    print("   [OK] acp_transactions.db")
    
    # 2. Initialize trust database
    print("\n2. Creating acp_trust.db...")
    auth = ACPAuthenticator()
    await auth.initialize()
    print("   [OK] acp_trust.db")
    
    # 3. Initialize monitoring database
    print("\n3. Creating acp_monitoring.db...")
    init_monitoring_db()
    print("   [OK] acp_monitoring.db")
    
    # 4. Initialize commissions database
    print("\n4. Creating acp_commissions.db...")
    conn = sqlite3.connect("acp_commissions.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commissions_accrued (
            commission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            property_id TEXT,
            agent_id TEXT,
            booking_value REAL,
            commission_rate REAL,
            commission_amount REAL,
            accrued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS commissions_paid (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT,
            period_start TEXT,
            period_end TEXT,
            total_commissions REAL,
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("   [OK] acp_commissions.db")
    
    # 5. Initialize network effects database
    print("\n5. Creating acp_network.db...")
    from app.acp.network_effects import _init_network_db
    _init_network_db()
    print("   [OK] acp_network.db")
    
    # 6. Properties database is created by PropertyRegistry
    print("\n6. acp_properties.db created by PropertyRegistry")
    from app.properties.registry import PropertyRegistry
    registry = PropertyRegistry()
    print("   [OK] acp_properties.db")
    
    print("\n" + "="*60)
    print("[SUCCESS] All 6 databases initialized!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(init_all_databases())
