"""
Commission Validation - Advanced
Validates commission ledger internal consistency + tier compliance
Does not assume bookings table exists in same DB.
"""

import sqlite3
import os
from datetime import datetime


def validate_commissions_advanced():
    """Advanced commission validation with best-effort checks."""
    print("=" * 70)
    print("ADVANCED COMMISSION VALIDATION")
    print("=" * 70)
    
    db_path = os.path.join("backend", "acp_commissions.db")
    
    if not os.path.exists(db_path):
        print(f"\n[ERROR] Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    all_passed = True
    
    # Check 1: Ledger internal consistency
    print("\n[CHECK 1] Ledger Internal Consistency")
    print("-" * 70)
    cur.execute("""
        SELECT 
            commission_id,
            booking_value,
            commission_rate,
            commission_amount
        FROM commissions_accrued
    """)
    
    rows = cur.fetchall()
    mismatches = []
    
    for row in rows:
        comm_id, booking_val, rate, commission = row
        expected = round(booking_val * rate, 2)
        actual = round(commission, 2)
        
        if abs(expected - actual) > 0.01:
            mismatches.append({
                "id": comm_id,
                "booking_value": booking_val,
                "rate": rate,
                "expected": expected,
                "actual": actual
            })
    
    if mismatches:
        print(f"  [FAIL] Found {len(mismatches)} commission calculation mismatches:")
        for m in mismatches[:5]:  # Show first 5
            print(f"    ID {m['id']}: ${m['booking_value']} × {m['rate']*100}% = ${m['expected']} (got ${m['actual']})")
        all_passed = False
    else:
        print(f"  [PASS] All {len(rows)} commission calculations are correct")
    
    # Check 2: Tier compliance
    print("\n[CHECK 2] Commission Rate Tier Compliance")
    print("-" * 70)
    
    VALID_RATES = {0.05, 0.10, 0.12, 0.15}  # budget, standard, premium, luxury
    
    cur.execute("""
        SELECT DISTINCT commission_rate, COUNT(*) as count
        FROM commissions_accrued
        GROUP BY commission_rate
    """)
    
    rates = cur.fetchall()
    invalid_rates = []
    
    for rate, count in rates:
        if rate not in VALID_RATES:
            invalid_rates.append((rate, count))
    
    if invalid_rates:
        print(f"  [WARN] Found non-standard commission rates:")
        for rate, count in invalid_rates:
            print(f"    {rate*100:.1f}% ({count} records)")
        print(f"  Valid rates: {', '.join([f'{r*100:.0f}%' for r in sorted(VALID_RATES)])}")
    else:
        print(f"  [PASS] All commission rates are within standard tiers")
    
    # Check 3: Property-level aggregation
    print("\n[CHECK 3] Property-Level Commission Summary")
    print("-" * 70)
    
    cur.execute("""
        SELECT 
            property_id,
            COUNT(*) as booking_count,
            SUM(booking_value) as total_bookings,
            SUM(commission_amount) as total_commissions,
            AVG(commission_rate) as avg_rate
        FROM commissions_accrued
        GROUP BY property_id
        ORDER BY total_commissions DESC
    """)
    
    summaries = cur.fetchall()
    
    if summaries:
        print(f"  Found {len(summaries)} properties with commissions:")
        for prop_id, count, total_bookings, total_comm, avg_rate in summaries:
            print(f"\n    Property: {prop_id}")
            print(f"      Bookings: {count}")
            print(f"      Total Booking Value: ${total_bookings:.2f}")
            print(f"      Total Commissions: ${total_comm:.2f}")
            print(f"      Average Rate: {avg_rate*100:.2f}%")
            print(f"      Effective Rate: {(total_comm/total_bookings*100):.2f}%")
    else:
        print("  [INFO] No commission data found (expected if no bookings yet)")
    
    # Check 4: Temporal distribution
    print("\n[CHECK 4] Monthly Commission Distribution")
    print("-" * 70)
    
    cur.execute("""
        SELECT 
            strftime('%Y-%m', accrued_at) as month,
            COUNT(*) as bookings,
            SUM(commission_amount) as monthly_commission
        FROM commissions_accrued
        WHERE accrued_at >= datetime('now', '-6 months')
        GROUP BY strftime('%Y-%m', accrued_at)
        ORDER BY month DESC
        LIMIT 6
    """)
    
    monthly = cur.fetchall()
    
    if monthly:
        print("  Last 6 months:")
        for month, bookings, commission in monthly:
            print(f"    {month}: {bookings} bookings, ${commission:.2f}")
    else:
        print("  [INFO] No commission data in last 6 months")
    
    # Check 5: Orphaned records (optional - best effort)
    print("\n[CHECK 5] Data Integrity (Best Effort)")
    print("-" * 70)
    
    # Check for null or invalid values
    cur.execute("""
        SELECT COUNT(*) FROM commissions_accrued
        WHERE booking_value IS NULL 
           OR commission_rate IS NULL 
           OR commission_amount IS NULL
    """)
    
    null_count = cur.fetchone()[0]
    
    if null_count > 0:
        print(f"  [FAIL] Found {null_count} records with NULL critical values")
        all_passed = False
    else:
        print(f"  [PASS] No NULL values in critical columns")
    
    # Check for negative values
    cur.execute("""
        SELECT COUNT(*) FROM commissions_accrued
        WHERE booking_value < 0 
           OR commission_rate < 0 
           OR commission_amount < 0
    """)
    
    negative_count = cur.fetchone()[0]
    
    if negative_count > 0:
        print(f"  [FAIL] Found {negative_count} records with negative values")
        all_passed = False
    else:
        print(f"  [PASS] No negative values found")
    
    conn.close()
    
    print("\n" + "=" * 70)
    if all_passed:
        print("VALIDATION RESULT: ✓ PASSED")
    else:
        print("VALIDATION RESULT: ✗ FAILED (see errors above)")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    print("\nAdvanced Commission Validator")
    print("=============================\n")
    
    try:
        success = validate_commissions_advanced()
        
        if success:
            print("\n[SUCCESS] All validation checks passed")
        else:
            print("\n[WARNING] Some validation checks failed")
            exit(1)
            
    except Exception as e:
        print(f"\n[ERROR] Validation failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
