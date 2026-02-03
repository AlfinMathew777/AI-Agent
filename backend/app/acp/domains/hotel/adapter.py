"""
Hotel Domain Adapter (synthetic SQLite)
- Provides base price + demand
- query() supports availability/amenities patterns
- execute() produces synthetic confirmation
"""

import json
import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class HotelDomainAdapter:
    def __init__(self, db_path: str = "synthetic_hotel.db"):
        self.db_path = db_path
        self._init_synthetic_data()

    async def initialize(self):
        return

    def _init_synthetic_data(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                property_id TEXT PRIMARY KEY,
                name TEXT,
                room_count INTEGER,
                base_rate REAL,
                property_type TEXT
            )
        """)

        cur.execute("""
            INSERT OR IGNORE INTO properties VALUES
            ('wrest_point', 'Wrest Point Hotel', 152, 250.0, 'casino_resort'),
            ('henry_jones', 'The Henry Jones Art Hotel', 56, 400.0, 'boutique')
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS availability (
                date TEXT,
                property_id TEXT,
                room_type TEXT,
                rooms_available INTEGER,
                demand_score REAL,
                PRIMARY KEY (date, property_id, room_type)
            )
        """)

        base_date = datetime.utcnow().date()
        for day_offset in range(90):
            d = (base_date + timedelta(days=day_offset)).isoformat()
            for prop in ("wrest_point", "henry_jones"):
                for room_type in ("deluxe_king", "suite", "art_room"):
                    weekend = (base_date + timedelta(days=day_offset)).weekday() >= 5
                    base_demand = 1.3 if weekend else 1.0
                    demand = round(base_demand * random.uniform(0.7, 1.5), 2)
                    rooms_avail = random.randint(5, 50)

                    cur.execute("""
                        INSERT OR REPLACE INTO availability VALUES (?, ?, ?, ?, ?)
                    """, (d, prop, room_type, rooms_avail, demand))

        conn.commit()
        conn.close()

    async def query(self, request) -> Dict[str, Any]:
        intent = request.intent_payload

        if intent.get("availability"):
            return await self._query_availability(intent["availability"])
        if intent.get("amenities"):
            return {"amenities": ["wifi", "minibar", "pool", "gym"]}
        return {"error": "Unknown query type"}

    async def _query_availability(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prop = payload.get("property_id", "wrest_point")
        check_in = payload.get("check_in")
        check_out = payload.get("check_out")
        room_type = payload.get("room_type", "deluxe_king")

        if not check_in or not check_out:
            return {"available": False, "reason": "Missing check_in/check_out"}

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT date, rooms_available, demand_score
            FROM availability
            WHERE property_id = ? AND room_type = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """, (prop, room_type, check_in, check_out))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return {"available": False, "reason": "No inventory for dates"}

        min_rooms = min(r[1] for r in rows)
        avg_demand = sum(r[2] for r in rows) / len(rows)

        base_rate = await self.get_base_price(prop, {"check_in": check_in}, room_type)
        dynamic_rate = round(base_rate * avg_demand, 2)

        return {
            "available": min_rooms > 0,
            "rooms_available": min_rooms,
            "base_rate": base_rate,
            "dynamic_rate": dynamic_rate,
            "demand_factor": round(avg_demand, 2),
        }

    async def get_base_price(self, entity_id: str, dates: Any, room_type: str) -> float:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT base_rate FROM properties WHERE property_id = ?", (entity_id,))
        row = cur.fetchone()
        conn.close()

        base = float(row[0]) if row else 250.0
        multipliers = {"deluxe_king": 1.0, "suite": 1.8, "art_room": 1.2}
        return round(base * multipliers.get(room_type, 1.0), 2)

    async def get_demand_multiplier(self, entity_id: str, dates: Any) -> float:
        check_in = dates.get("check_in") if isinstance(dates, dict) else None
        if not check_in:
            return 1.0

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT AVG(demand_score) FROM availability
            WHERE property_id = ? AND date = ?
        """, (entity_id, check_in))
        row = cur.fetchone()
        conn.close()

        return float(row[0]) if row and row[0] else 1.0

    async def execute(self, tx, request) -> Dict[str, Any]:
        confirmation = self._confirmation()
        return {
            "success": True,
            "confirmation_code": confirmation,
            "pms_reference": f"acp-{tx.tx_id}",
            "check_in_instructions": "Digital key sent to agent",
        }

    def _confirmation(self) -> str:
        import string
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
