
import sqlite3
import os
from pathlib import Path

# Path to DB
DB_PATH = Path("backend/hotel.db").absolute()

def check_db():
    print(f"Checking Database at: {DB_PATH}")
    
    if not DB_PATH.exists():
        print("ERROR: Database file NOT found!")
        return

    size = DB_PATH.stat().st_size
    print(f"Database file found. Size: {size} bytes")

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count rows
        c.execute("SELECT COUNT(*) FROM chat_logs")
        count = c.fetchone()[0]
        print(f"Total Chat Logs: {count}")

        # Show last 5 entries
        print("\n--- Last 5 Logged Chats ---")
        c.execute("SELECT id, timestamp, audience, question, answer FROM chat_logs ORDER BY id DESC LIMIT 5")
        rows = c.fetchall()
        for row in rows:
            print(f"ID: {row[0]} | Time: {row[1]} | By: {row[2]}")
            print(f"Q: {row[3]}")
            print(f"A: {row[4][:50]}...") # Truncate answer
            print("-" * 30)
            
        conn.close()
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    check_db()
