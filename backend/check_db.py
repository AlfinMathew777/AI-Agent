import sqlite3
import os

db_path = "hotel.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check if users table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    users_exists = bool(c.fetchone())
    print(f"Users table exists: {users_exists}")
    
    if users_exists:
        c.execute("SELECT COUNT(*) FROM users")
        count = c.fetchone()[0]
        print(f"User count: {count}")
        
        if count > 0:
            c.execute("SELECT email, role FROM users LIMIT 5")
            users = c.fetchall()
            print("Sample users:")
            for email, role in users:
                print(f"  - {email} ({role})")
    
    conn.close()
else:
    print(f"Database file not found: {db_path}")
