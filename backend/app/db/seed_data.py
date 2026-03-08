"""Seed demo data for the hotel database on startup."""

import uuid
from datetime import datetime, UTC, date, timedelta


ROOMS_SEED = [
    {"room_number": "101", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 180, "is_available": 1},
    {"room_number": "102", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 180, "is_available": 1},
    {"room_number": "103", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 185, "is_available": 0},
    {"room_number": "201", "room_type": "Deluxe",     "floor": 2, "capacity": 2, "price_per_night": 260, "is_available": 1},
    {"room_number": "202", "room_type": "Deluxe",     "floor": 2, "capacity": 2, "price_per_night": 260, "is_available": 1},
    {"room_number": "203", "room_type": "Deluxe",     "floor": 2, "capacity": 3, "price_per_night": 280, "is_available": 0},
    {"room_number": "204", "room_type": "Deluxe",     "floor": 2, "capacity": 2, "price_per_night": 265, "is_available": 1},
    {"room_number": "301", "room_type": "Suite",      "floor": 3, "capacity": 4, "price_per_night": 420, "is_available": 1},
    {"room_number": "302", "room_type": "Suite",      "floor": 3, "capacity": 4, "price_per_night": 440, "is_available": 0},
    {"room_number": "401", "room_type": "Ocean View", "floor": 4, "capacity": 2, "price_per_night": 320, "is_available": 1},
    {"room_number": "402", "room_type": "Ocean View", "floor": 4, "capacity": 2, "price_per_night": 340, "is_available": 1},
    {"room_number": "403", "room_type": "Ocean View", "floor": 4, "capacity": 3, "price_per_night": 360, "is_available": 0},
    {"room_number": "501", "room_type": "Penthouse",  "floor": 5, "capacity": 6, "price_per_night": 780, "is_available": 1},
    {"room_number": "104", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 175, "is_available": 1},
    {"room_number": "105", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 180, "is_available": 0},
    {"room_number": "205", "room_type": "Deluxe",     "floor": 2, "capacity": 2, "price_per_night": 270, "is_available": 1},
    {"room_number": "303", "room_type": "Suite",      "floor": 3, "capacity": 4, "price_per_night": 430, "is_available": 1},
    {"room_number": "404", "room_type": "Ocean View", "floor": 4, "capacity": 2, "price_per_night": 330, "is_available": 1},
    {"room_number": "106", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 182, "is_available": 1},
    {"room_number": "107", "room_type": "Standard",   "floor": 1, "capacity": 2, "price_per_night": 178, "is_available": 0},
]

GUESTS = [
    ("James Wilson",   "james.wilson@gmail.com"),
    ("Sarah Chen",     "sarah.chen@corporate.com"),
    ("Liam Murphy",    "l.murphy@travel.io"),
    ("Emma Davis",     "emma.davis@email.com"),
    ("Noah Thompson",  "nthompson@biztravel.net"),
    ("Olivia Garcia",  "ogarcia@hotel.demo"),
    ("William Brown",  "w.brown@example.org"),
    ("Ava Martinez",   "ava.m@gmail.com"),
]


def seed_demo_data():
    """Seed rooms, reservations, and payments for all existing tenants."""
    try:
        from app.db.session import get_db_connection
        conn = get_db_connection()
        c = conn.cursor()

        # Get all tenants
        c.execute("SELECT id FROM tenants")
        tenant_ids = [row[0] for row in c.fetchall()]
        if not tenant_ids:
            tenant_ids = ["default-tenant-0000"]

        for tenant_id in tenant_ids:
            # Check if rooms already seeded for this tenant
            c.execute("SELECT COUNT(*) FROM rooms WHERE tenant_id=?", (tenant_id,))
            room_count = c.fetchone()[0]

            if room_count == 0:
                for room in ROOMS_SEED:
                    rid = str(uuid.uuid4())
                    c.execute("""
                        INSERT OR IGNORE INTO rooms
                        (id, tenant_id, room_number, room_type, floor, capacity, amenities, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rid, tenant_id,
                        room["room_number"], room["room_type"], room["floor"],
                        room["capacity"], "WiFi,AC,TV,Safe",
                        "available" if room["is_available"] else "occupied",
                        datetime.now(UTC).isoformat(),
                    ))
                print(f"[Seed] Created {len(ROOMS_SEED)} rooms for tenant {tenant_id[:8]}")

            # Seed reservations
            c.execute("SELECT COUNT(*) FROM reservations WHERE tenant_id=?", (tenant_id,))
            res_count = c.fetchone()[0]

            if res_count < 4:
                today = date.today()
                for i, (name, email) in enumerate(GUESTS[:6]):
                    check_in = today + timedelta(days=i - 2)
                    check_out = check_in + timedelta(days=2 + (i % 3))
                    price = [180, 260, 420, 320, 265, 180][i]
                    nights = (check_out - check_in).days
                    total = price * nights * (1 + (i % 2))
                    status = "confirmed" if i < 5 else "pending"
                    rid = str(uuid.uuid4())
                    c.execute("""
                        INSERT OR IGNORE INTO reservations
                        (id, tenant_id, room_number, guest_name, guest_email,
                         check_in_date, check_out_date, total_amount, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rid, tenant_id, ROOMS_SEED[i]["room_number"],
                        name, email,
                        check_in.isoformat(), check_out.isoformat(),
                        round(total, 2), status,
                        (datetime.now(UTC) - timedelta(days=6 - i)).isoformat(),
                    ))
                print(f"[Seed] Created demo reservations for tenant {tenant_id[:8]}")

        conn.commit()
        conn.close()
        print("[Seed] Database seeding complete")

    except Exception as e:
        print(f"[Seed] Seeding error (non-fatal): {e}")
