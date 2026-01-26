
import os
import sys
from pathlib import Path

# Add backend root to path (one level up from tests/)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import init_db, log_chat, get_analytics_stats, get_db_connection

def test_db_workflow():
    print("--- Testing Database Workflow ---")
    
    # 1. Init
    print("1. Initializing DB...")
    init_db()
    
    # 2. Log Chat
    print("2. Logging a test chat...")
    log_chat(
        audience="guest", 
        question="Is the database working?", 
        answer="Yes, seemingly so.", 
        latency_ms=123
    )
    
    # 3. Verify Row
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM chat_logs ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    print(f"3. Retrieved Log: ID={row['id']}, Q='{row['question']}'")
    conn.close()
    
    # 4. Check Analytics
    print("4. Checking Analytics Stats...")
    stats = get_analytics_stats()
    print(f"   Active Chats: {stats['daily_stats']['active_chats']}")
    print(f"   Queries Today: {stats['daily_stats']['queries_today']}")
    print(f"   Recent Queries: {len(stats['recent_queries'])}")
    print("   First Recent Query:", stats['recent_queries'][0]['query'])
    
    assert stats['daily_stats']['queries_today'] >= 1
    print("\nSUCCESS: Database logging and analytics are working.")

if __name__ == "__main__":
    test_db_workflow()
