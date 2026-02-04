"""
Demo Data Seed Script for AI Hotel Assistant
Populates the database with realistic demo data for presentations
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.database import SessionLocal
from app.db.models import User, Room, Booking
from datetime import datetime, timedelta
import random

def seed_demo_data():
    """Populate database with impressive demo data"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding demo data...")
        
        # Create demo users
        users = [
            User(email="john.doe@example.com", tenant_id="demo-tenant", hashed_password="demo123"),
            User(email="jane.smith@example.com", tenant_id="demo-tenant", hashed_password="demo123"),
            User(email="admin@shhg.com", tenant_id="demo-tenant", hashed_password="admin123"),
        ]
        
        for user in users:
            existing = db.query(User).filter(User.email == user.email).first()
            if not existing:
                db.add(user)
                print(f"  ✅ Created user: {user.email}")
        
        db.commit()
        
        # Create demo rooms
        room_types = ["Deluxe", "Suite", "Standard", "Presidential", "Ocean View"]
        floors = [1, 2, 3, 4, 5]
        
        for i, room_type in enumerate(room_types):
            for floor in floors[:3]:  # 3 rooms of each type
                room_number = f"{floor}{100 + i*10 + random.randint(1,9)}"
                existing = db.query(Room).filter(Room.room_number == room_number).first()
                
                if not existing:
                    room = Room(
                        room_number=room_number,
                        room_type=room_type,
                        floor=floor,
                        status="available",
                        price_per_night=100 + (i * 50),  # $100-$300
                        tenant_id="demo-tenant"
                    )
                    db.add(room)
                    print(f"  ✅ Created room: {room_number} ({room_type})")
        
        db.commit()
        
        # Create demo bookings
        rooms = db.query(Room).all()
        users_list = db.query(User).all()
        
        if rooms and users_list:
            for i in range(10):
                room = random.choice(rooms)
                user = random.choice(users_list)
                
                check_in = datetime.now() + timedelta(days=random.randint(-10, 30))
                check_out = check_in + timedelta(days=random.randint(1, 7))
                
                booking = Booking(
                    user_id=user.id,
                    room_id=room.id,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    total_price=(check_out - check_in).days * room.price_per_night,
                    status=random.choice(["confirmed", "pending", "completed"]),
                    tenant_id="demo-tenant"
                )
                db.add(booking)
                print(f"  ✅ Created booking: Room {room.room_number} for {user.email}")
        
        db.commit()
        
        print("\n✅ Demo data seeded successfully!")
        print(f"   - {len(users)} users")
        print(f"   - {len(room_types) * 3} rooms")
        print(f"   - 10 bookings")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
