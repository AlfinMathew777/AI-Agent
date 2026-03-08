
import sqlite3
from pathlib import Path

# DB_PATH was: Path(__file__).parent.parent / "hotel.db"
# If this file is in app/db/session.py, parent is app/db, parent.parent is app, parent.parent.parent is backend.
# Original was app/database.py -> backend/app -> parent.parent is hotel.db in backend/
# New: app/db/session.py -> backend/app/db -> parent.parent.parent is backend?
# Wait.
# Original: backend/app/database.py
# Path(__file__) = backend/app/database.py
# .parent = backend/app
# .parent.parent = backend/
# DB_PATH = backend/hotel.db

# New: backend/app/db/session.py
# Path(__file__) = backend/app/db/session.py
# .parent = backend/app/db
# .parent.parent = backend/app
# .parent.parent.parent = backend/
# So we need 3 parents.

from app.core.config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Chat Logs Table (Enhanced with internal trace)
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            tenant_id TEXT,
            session_id TEXT,
            audience TEXT,
            question TEXT,
            answer TEXT,
            internal_trace_json TEXT,
            model_used TEXT,
            latency_ms INTEGER,
            tokens_in INTEGER,
            tokens_out INTEGER,
            feedback_score INTEGER,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    # Add session_id and internal_trace_json if missing
    try:
        c.execute("ALTER TABLE chat_logs ADD COLUMN session_id TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE chat_logs ADD COLUMN internal_trace_json TEXT")
    except: pass
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_tenant ON chat_logs(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_audience ON chat_logs(audience)")

    # Tool Calls Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tool_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            audience TEXT,
            tool_name TEXT,
            params_json TEXT,
            result_json TEXT,
            risk_level TEXT,
            status TEXT,
            latency_ms INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Actions Table (for confirmation)
    c.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            action_id TEXT PRIMARY KEY,
            session_id TEXT,
            tool_name TEXT,
            params_json TEXT,
            requires_confirmation INTEGER,
            confirmed INTEGER DEFAULT 0,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Bookings Table (Real Data)
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id TEXT PRIMARY KEY,
            guest_name TEXT,
            room_type TEXT,
            date TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Plans Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            audience TEXT,
            question TEXT,
            plan_summary TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Plan Steps Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS plan_steps (
            id TEXT PRIMARY KEY,
            plan_id TEXT,
            step_index INTEGER,
            step_type TEXT,
            tool_name TEXT,
            tool_args_json TEXT,
            risk TEXT,
            status TEXT,
            result_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        )
    ''')

    import uuid
    
    # ---------------------------------------------------------
    # Multi-Tenant Migration (Non-Destructive)
    # ---------------------------------------------------------
    
    # 1. Tenants Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            role TEXT, 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    
    # 3. Create Default Tenant (Migration Backfill Source)
    DEFAULT_TENANT_ID = "default-tenant-0000"
    try:
        c.execute("INSERT OR IGNORE INTO tenants (id, name) VALUES (?, ?)", (DEFAULT_TENANT_ID, "Default Hotel"))
    except Exception as e:
        print(f"[Database] Default tenant check ignored: {e}")

    # 4. Add tenant_id column to existing tables if missing
    tables_to_migrate = [
        "chat_logs", "tool_calls", "actions", "bookings", "plans", "plan_steps"
    ]
    
    for table in tables_to_migrate:
        try:
            # Check if column exists
            c.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in c.fetchall()]
            
            if "tenant_id" not in columns:
                print(f"[Database] Migrating {table}: Adding tenant_id column...")
                # Add column (nullable first)
                c.execute(f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT REFERENCES tenants(id)")
                
                # Backfill with default tenant
                c.execute(f"UPDATE {table} SET tenant_id = ? WHERE tenant_id IS NULL", (DEFAULT_TENANT_ID,))
                print(f"[Database] Backfilled {table} with default tenant.")
        except Exception as e:
            print(f"[Database] Migration warning for {table}: {e}")


    # ---------------------------------------------------------
    # Commerce & Agentic Tables
    # ---------------------------------------------------------

    # 1. Restaurants
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurants (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            name TEXT,
            location TEXT,
            phone TEXT,
            hours_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')

    # 2. Menus
    c.execute('''
        CREATE TABLE IF NOT EXISTS menus (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            restaurant_id TEXT,
            title TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
        )
    ''')
    
    # 3. Menu Items
    c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            menu_id TEXT,
            name TEXT,
            description TEXT,
            price REAL,
            tags_json TEXT, -- e.g. ["vegan", "spicy"]
            image_url TEXT,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(menu_id) REFERENCES menus(id)
        )
    ''')
    
    # 4. Events
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            title TEXT,
            description TEXT,
            venue TEXT,
            start_time DATETIME,
            end_time DATETIME,
            status TEXT, -- scheduled, cancelled, completed
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')

    # 5. Event Tickets (Inventory)
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_tickets (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            event_id TEXT,
            ticket_type TEXT, -- VIP, General, EarlyBird
            price REAL,
            capacity INTEGER,
            sold_count INTEGER DEFAULT 0,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    ''')

    # 6. Table Reservations
    c.execute('''
        CREATE TABLE IF NOT EXISTS table_reservations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            restaurant_id TEXT,
            customer_name TEXT,
            customer_email TEXT,
            date TEXT, -- YYYY-MM-DD
            time TEXT, -- HH:MM
            party_size INTEGER,
            status TEXT, -- confirmed, cancelled
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
        )
    ''')

    # 7. Orders (Generic for Room Service, Dining, etc.)
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            customer_name TEXT,
            room_number TEXT,
            order_type TEXT, -- dining, room_service, event
            status TEXT, -- pending, confirmed, delivered, cancelled
            total_price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')

    # 8. Order Items
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            order_id TEXT,
            item_id TEXT, -- loose reference to menu_item or ticket
            item_name TEXT, 
            quantity INTEGER,
            unit_price REAL,
            total_price REAL,
            special_requests TEXT,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')

    # 9. Rooms Table (Individual Room Inventory)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            room_number TEXT NOT NULL,
            floor INTEGER,
            room_type TEXT, -- standard, deluxe, suite
            status TEXT DEFAULT 'available', -- available, occupied, cleaning_needed, maintenance
            capacity INTEGER DEFAULT 2,
            amenities TEXT, -- JSON string or comma-separated
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            UNIQUE(tenant_id, room_number)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_rooms_tenant ON rooms(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(floor)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rooms_status ON rooms(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_rooms_type ON rooms(room_type)")

    # 10. Reservations Table (Enhanced with Room Assignment)
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            room_id TEXT, -- FK to rooms
            room_number TEXT, -- Denormalized for quick access
            guest_name TEXT NOT NULL,
            guest_phone TEXT,
            guest_email TEXT,
            check_in_date TEXT, -- YYYY-MM-DD
            check_out_date TEXT, -- YYYY-MM-DD
            status TEXT DEFAULT 'pending', -- pending, checked_in, checked_out, cancelled
            total_amount REAL,
            payment_status TEXT DEFAULT 'pending', -- pending, paid, refunded
            special_requests TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_reservations_tenant ON reservations(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_reservations_room ON reservations(room_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_reservations_dates ON reservations(check_in_date, check_out_date)")

    # 11. Housekeeping Table (Cleaning Workflow)
    c.execute('''
        CREATE TABLE IF NOT EXISTS housekeeping (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            room_id TEXT, -- FK to rooms
            room_number TEXT, -- Denormalized
            cleaner_id TEXT, -- FK to users (optional, can be NULL)
            cleaner_name TEXT, -- Denormalized
            status TEXT DEFAULT 'pending', -- pending, in_progress, completed
            started_at DATETIME,
            completed_at DATETIME,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_housekeeping_tenant ON housekeeping(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_housekeeping_room ON housekeeping(room_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_housekeeping_status ON housekeeping(status)")

    # ---------------------------------------------------------
    # Task 13.1-A: New Commerce Inventory Schema
    # ---------------------------------------------------------

    # 1. Venues (Generic)
    c.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            name TEXT,
            type TEXT, -- restaurant, bar, theater
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_venues_tenant_id ON venues(tenant_id)")

    # 2. Venue Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS venue_tables (
            id TEXT PRIMARY KEY,
            venue_id TEXT,
            table_number TEXT,
            capacity INTEGER,
            FOREIGN KEY(venue_id) REFERENCES venues(id)
        )
    ''')

    # 3. Events (Update existing or create)
    # Existing `events` table: id, tenant_id, title, description, venue, start_time, end_time, status, created_at
    # Request `events`: id, tenant_id, name, start_time, total_tickets, created_at
    # We will ensure colums exist.
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            title TEXT, 
            name TEXT, -- added for spec compliance
            start_time DATETIME,
            total_tickets INTEGER, -- added for spec compliance
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_events_tenant_id ON events(tenant_id)")
    
    # Migration for events columns if they don't exist
    try:
        c.execute("ALTER TABLE events ADD COLUMN name TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN total_tickets INTEGER")
    except: pass
    try:
        c.execute("ALTER TABLE events ADD COLUMN ticket_price_cents INTEGER DEFAULT 0")
    except: pass

    # Migration for venues columns
    try:
        c.execute("ALTER TABLE venues ADD COLUMN tags TEXT")
    except: pass


    # 4. Restaurant Bookings
    c.execute('''
        CREATE TABLE IF NOT EXISTS restaurant_bookings (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            venue_id TEXT,
            table_id TEXT,
            date TEXT,
            time TEXT,
            party_size INTEGER,
            customer_name TEXT,
            status TEXT, -- confirmed/cancelled
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(venue_id) REFERENCES venues(id),
            FOREIGN KEY(table_id) REFERENCES venue_tables(id)
        )
    ''')
    # restaurant_bookings(tenant_id,date,venue_id,status)
    c.execute("CREATE INDEX IF NOT EXISTS idx_rest_bookings_search ON restaurant_bookings(tenant_id, date, venue_id, status)")

    # 5. Event Bookings
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_bookings (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            event_id TEXT,
            customer_name TEXT,
            quantity INTEGER,
            status TEXT, -- confirmed/cancelled
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    ''')
    # event_bookings(tenant_id,event_id,status)
    c.execute("CREATE INDEX IF NOT EXISTS idx_event_bookings_search ON event_bookings(tenant_id, event_id, status)")

    # ---------------------------------------------------------
    # Task 13.2: Pricing, Quotes & Receipts
    # ---------------------------------------------------------
    
    # 6. Quotes
    c.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            session_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            audience TEXT, -- guest/staff
            status TEXT, -- proposed, accepted, expired, cancelled
            currency TEXT DEFAULT "AUD",
            subtotal_cents INTEGER,
            tax_cents INTEGER,
            fees_cents INTEGER,
            total_cents INTEGER,
            breakdown_json TEXT, -- JSON string of line items
            notes TEXT,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_quotes_tenant ON quotes(tenant_id)")
    
    # 7. Receipts
    c.execute('''
        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            quote_id TEXT, -- nullable, link back to quote
            session_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            currency TEXT DEFAULT "AUD",
            subtotal_cents INTEGER,
            tax_cents INTEGER,
            fees_cents INTEGER,
            total_cents INTEGER,
            booking_refs_json TEXT, -- JSON: booking_id, reservation_id, etc.
            breakdown_json TEXT, 
            status TEXT, -- paid, confirmed, cancelled
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_receipts_tenant ON receipts(tenant_id)")

    c.execute("CREATE INDEX IF NOT EXISTS idx_receipts_tenant ON receipts(tenant_id)")

    # ---------------------------------------------------------
    # Task 9: Stripe Payments
    # ---------------------------------------------------------
    
    # 8. Payments
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            quote_id TEXT,
            stripe_session_id TEXT,
            amount_cents INTEGER,
            currency TEXT,
            status TEXT, -- pending, paid, failed
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id),
            FOREIGN KEY(quote_id) REFERENCES quotes(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_payments_tenant ON payments(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_payments_quote ON payments(quote_id)")

    # Migration for quotes payment_id
    try:
        c.execute("ALTER TABLE quotes ADD COLUMN payment_id TEXT")
    except: pass

    # Migration for quotes pending_plan_id (Task 9.3)
    try:
        c.execute("ALTER TABLE quotes ADD COLUMN pending_plan_id TEXT")
    except: pass

    # ---------------------------------------------------------
    # Task 10: Queue & Hardening
    # ---------------------------------------------------------
    
    # 9. Execution Jobs
    c.execute('''
        CREATE TABLE IF NOT EXISTS execution_jobs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT,
            quote_id TEXT,
            payment_id TEXT,
            stripe_event_id TEXT,
            status TEXT, -- queued, running, success, failed
            attempts INTEGER DEFAULT 0,
            last_error TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    # Unique constraint for idempotency: One execution job per stripe event per tenant
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_exec_jobs_idempotent ON execution_jobs(tenant_id, stripe_event_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_exec_jobs_status ON execution_jobs(status)")

    # Migration for payments (provider_event_id)
    try:
        c.execute("ALTER TABLE payments ADD COLUMN provider_event_id TEXT")
    except: pass
    
    # Migration for quotes (execution status)
    try:
        c.execute("ALTER TABLE quotes ADD COLUMN executed_at DATETIME")
    except: pass
    try:
        c.execute("ALTER TABLE quotes ADD COLUMN execution_error TEXT")
    except: pass

    # ---------------------------------------------------------
    # Admin Panel: Operations & Monitoring Tables
    # ---------------------------------------------------------
    
    # Operations Table (for tracking bookings, reservations, tickets, etc.)
    c.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            type TEXT NOT NULL,
            entity_id TEXT,
            amount_cents INTEGER DEFAULT 0,
            status TEXT,
            metadata_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_operations_tenant ON operations(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_operations_type ON operations(type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_operations_status ON operations(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_operations_created ON operations(created_at)")
    
    # System Errors Table (for monitoring)
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            endpoint TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(tenant_id) REFERENCES tenants(id)
        )
    ''')
    c.execute("CREATE INDEX IF NOT EXISTS idx_errors_tenant ON system_errors(tenant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_errors_created ON system_errors(created_at)")

    conn.commit()
    conn.close()
    print(f"[Database] Initialized and Migrated at {DB_PATH}")
