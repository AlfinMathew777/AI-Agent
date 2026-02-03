"""
Inventory Cache for Cloudbeds Adapter
Hybrid mode: cache + live API fallback
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class InventoryCache:
    """SQLite cache for Cloudbeds availability and rates"""
    
    def __init__(self, db_path: str = "cloudbeds_cache.db"):
        self.db_path = db_path
        self.cache_ttl_seconds = 120  # 2 minutes

    async def initialize(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS availability_cache (
                property_id TEXT,
                check_in TEXT,
                check_out TEXT,
                room_type TEXT,
                cached_data TEXT,
                cached_at TEXT,
                PRIMARY KEY (property_id, check_in, check_out, room_type)
            )
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cache_property ON availability_cache(property_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_cache_dates ON availability_cache(check_in, check_out)")
        
        conn.commit()
        conn.close()

    async def get_cached_availability(
        self, 
        property_id: str, 
        check_in: str, 
        check_out: str, 
        room_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached availability if not stale"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT cached_data, cached_at
            FROM availability_cache
            WHERE property_id = ? AND check_in = ? AND check_out = ? AND room_type = ?
        """, (property_id, check_in, check_out, room_type))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        cached_data, cached_at_str = row
        cached_at = datetime.fromisoformat(cached_at_str)
        age_seconds = (datetime.utcnow() - cached_at).total_seconds()
        
        if age_seconds > self.cache_ttl_seconds:
            # Cache expired
            return None
        
        import json
        return json.loads(cached_data)

    async def cache_availability(
        self,
        property_id: str,
        check_in: str,
        check_out: str,
        room_type: str,
        data: Dict[str, Any]
    ):
        """Cache availability data"""
        import json
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT OR REPLACE INTO availability_cache
            (property_id, check_in, check_out, room_type, cached_data, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            property_id,
            check_in,
            check_out,
            room_type,
            json.dumps(data),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()

    async def invalidate_dates(
        self,
        property_id: str,
        check_in: str,
        check_out: str,
        room_type: str
    ):
        """Invalidate cache for specific dates (after booking)"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM availability_cache
            WHERE property_id = ? 
              AND check_in <= ?
              AND check_out >= ?
              AND room_type = ?
        """, (property_id, check_out, check_in, room_type))
        
        conn.commit()
        conn.close()

    async def clear_stale_entries(self):
        """Remove entries older than TTL"""
        cutoff = (datetime.utcnow() - timedelta(seconds=self.cache_ttl_seconds)).isoformat()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM availability_cache
            WHERE cached_at < ?
        """, (cutoff,))
        
        conn.commit()
        conn.close()
