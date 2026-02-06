
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'backend', 'hotel.db')
print(f"Checking DB at: {DB_PATH}")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("ERROR: 'users' table does not exist!")
    else:
        print("'users' table exists.")
        
        # Check if any user exists
        cursor.execute("SELECT id, email, role FROM users")
        users = cursor.fetchall()
        if not users:
            print("WARNING: No users found in the database. You need to register first.")
        else:
            print(f"Found {len(users)} users:")
            for u in users:
                print(f" - {u[1]} ({u[2]})")
                
    conn.close()
    
except Exception as e:
    print(f"Error accessing database: {e}")
