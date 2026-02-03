"""
Emergency Rollback Script for Cloudbeds Property (Phase 3B)
Immediately pauses a property to stop receiving new booking requests

Usage:
    python rollback_property.py "reason for rollback"
    python rollback_property.py  # Uses default reason

Safety:
- Only sets is_active = 0, does not delete anything
- Existing bookings in Cloudbeds are unaffected
- Property can be resumed later via API or manual database update
"""

import sys
import sqlite3
from datetime import datetime


PROPERTY_ID = "cloudbeds_001"  # Default property to rollback
DB_PATH = "acp_properties.db"


def rollback_property(property_id: str = PROPERTY_ID, reason: str = "Emergency rollback"):
    """Pause property immediately"""
    
    print("=" * 70)
    print("EMERGENCY ROLLBACK - PHASE 3B")
    print("=" * 70)
    print(f"\nProperty: {property_id}")
    print(f"Reason: {reason}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Confirm
    confirm = input("Type 'ROLLBACK' to confirm: ")
    if confirm != "ROLLBACK":
        print("\n[CANCELLED] Rollback aborted")
        return
    
    try:
        # Update database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        # Check property exists
        cur.execute("SELECT name, is_active FROM properties WHERE property_id = ?", (property_id,))
        row = cur.fetchone()
        
        if not row:
            print(f"\n[ERROR] Property {property_id} not found in database")
            conn.close()
            return
        
        property_name, current_status = row
        
        # Pause property
        cur.execute("""
            UPDATE properties 
            SET is_active = 0,
                config_json = json_set(
                    config_json, 
                    '$.paused_reason', 
                    ?,
                    '$.paused_at',
                    ?
                )
            WHERE property_id = ?
        """, (f"ROLLBACK: {reason}", datetime.now().isoformat(), property_id))
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 70)
        print("[SUCCESS] PROPERTY PAUSED")
        print("=" * 70)
        print(f"\nProperty '{property_name}' has been paused.")
        print(f"Previous status: {'Active' if current_status == 1 else 'Inactive'}")
        print(f"New status: Inactive (paused)")
        print()
        print("Impact:")
        print("  - Property will NOT appear in marketplace listings")
        print("  - New booking requests will NOT route to this property")
        print("  - Cross-property search will skip this property")
        print("  - Existing bookings in Cloudbeds are UNAFFECTED")
        print()
        print("To resume:")
        print(f"  1. API: POST /admin/properties/{property_id}/resume")
        print(f"  2. Manual: UPDATE properties SET is_active=1 WHERE property_id='{property_id}'")
        print()
        print("Monitoring:")
        print("  - Check marketplace: GET /marketplace/properties")
        print("  - Check dashboard: GET /admin/monitoring/dashboard")
        print()
        
        # Log to monitoring database if it exists
        try:
            mon_conn = sqlite3.connect("acp_monitoring.db")
            mon_cur = mon_conn.cursor()
            mon_cur.execute("""
                CREATE TABLE IF NOT EXISTS property_events (
                    event_id TEXT PRIMARY KEY,
                    property_id TEXT,
                    event_type TEXT,
                    event_data TEXT,
                    created_at TEXT
                )
            """)
            mon_cur.execute("""
                INSERT INTO property_events (event_id, property_id, event_type, event_data, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"rollback_{property_id}_{int(datetime.now().timestamp())}",
                property_id,
                "ROLLBACK",
                reason,
                datetime.now().isoformat()
            ))
            mon_conn.commit()
            mon_conn.close()
            print("[INFO] Rollback event logged to monitoring database")
        except Exception as e:
            print(f"[WARN] Could not log to monitoring database: {e}")
        
    except Exception as e:
        print(f"\n[ERROR] Rollback failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def resume_property(property_id: str = PROPERTY_ID):
    """Resume a paused property (opposite of rollback)"""
    
    print("=" * 70)
    print("RESUME PROPERTY")
    print("=" * 70)
    print(f"\nProperty: {property_id}")
    print()
    
    confirm = input("Type 'RESUME' to confirm: ")
    if confirm != "RESUME":
        print("\n[CANCELLED] Resume aborted")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE properties 
            SET is_active = 1,
                config_json = json_set(
                    config_json,
                    '$.paused_reason',
                    NULL,
                    '$.resumed_at',
                    ?
                )
            WHERE property_id = ?
        """, (datetime.now().isoformat(), property_id))
        
        conn.commit()
        conn.close()
        
        print("\n[SUCCESS] Property resumed and active")
        print(f"Property {property_id} will now receive booking requests")
        
    except Exception as e:
        print(f"\n[ERROR] Resume failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Emergency rollback for Cloudbeds property")
    parser.add_argument("--property", default=PROPERTY_ID, help="Property ID to rollback")
    parser.add_argument("--resume", action="store_true", help="Resume instead of rollback")
    parser.add_argument("reason", nargs="?", default="Manual emergency rollback", help="Reason for rollback")
    
    args = parser.parse_args()
    
    if args.resume:
        resume_property(args.property)
    else:
        rollback_property(args.property, args.reason)
