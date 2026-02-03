"""
Commission Validation Queries
SQL queries to verify commission tracking for Cloudbeds property
"""

import sqlite3
from datetime import datetime, timedelta

PROPERTY_ID = "cloudbeds_001"


def validate_commissions():
    """Run all commission validation queries"""
    print("=" * 70)
    print("COMMISSION VALIDATION FOR", PROPERTY_ID)
    print("=" * 70)
    
    conn = sqlite3.connect("acp_commissions.db")
    cur = conn.cursor()
    
    # Query 1: Recent commissions
    print("\n[QUERY 1] Recent Commissions (Last 5)")
    print("-" * 70)
    cur.execute("""
        SELECT 
            transaction_id,
            agent_id,
            booking_value,
            commission_rate,
            commission_amount,
            accrued_at
        FROM commissions_accrued
        WHERE property_id = ?
        ORDER BY accrued_at DESC
        LIMIT 5
    """, (PROPERTY_ID,))
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            tx_id, agent_id, booking_val, rate, commission, accrued = row
            print(f"  Transaction: {tx_id}")
            print(f"    Agent: {agent_id}")
            print(f"    Booking Value: ${booking_val:.2f}")
            print(f"    Rate: {rate*100:.1f}%")
            print(f"    Commission: ${commission:.2f}")
            print(f"    Accrued: {accrued}")
            print(f"    Verification: ${booking_val * rate:.2f} == ${commission:.2f} ? ", end="")
            if abs(booking_val * rate - commission) < 0.01:
                print("✓ CORRECT")
            else:
                print("✗ MISMATCH!")
            print()
    else:
        print("  No commissions found (expected if no bookings yet)")
    
    # Query 2: Total commissions
    print("\n[QUERY 2] Total Commissions Summary")
    print("-" * 70)
    cur.execute("""
        SELECT 
            COUNT(*) as booking_count,
            SUM(booking_value) as total_bookings,
            SUM(commission_amount) as total_commissions,
            AVG(commission_rate) as avg_rate
        FROM commissions_accrued
        WHERE property_id = ?
    """, (PROPERTY_ID,))
    
    row = cur.fetchone()
    if row and row[0] > 0:
        count, total_bookings, total_comm, avg_rate = row
        print(f"  Total Bookings: {count}")
        print(f"  Total Booking Value: ${total_bookings:.2f}")
        print(f"  Total Commissions: ${total_comm:.2f}")
        print(f"  Average Rate: {avg_rate*100:.2f}%")
        print(f"  Expected Commission: ${total_bookings * 0.10:.2f} (for 10% rate)")
    else:
        print("  No commission data yet")
    
    # Query 3: Commissions by agent
    print("\n[QUERY 3] Commissions by Agent")
    print("-" * 70)
    cur.execute("""
        SELECT 
            agent_id,
            COUNT(*) as booking_count,
            SUM(commission_amount) as total_commission
        FROM commissions_accrued
        WHERE property_id = ?
        GROUP BY agent_id
        ORDER BY total_commission DESC
    """, (PROPERTY_ID,))
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            agent_id, count, total = row
            print(f"  {agent_id}: {count} bookings, ${total:.2f} commission")
    else:
        print("  No agent commissions yet")
    
    # Query 4: Daily commission trend (last 7 days)
    print("\n[QUERY 4] Daily Commission Trend (Last 7 Days)")
    print("-" * 70)
    cur.execute("""
        SELECT 
            DATE(accrued_at) as day,
            COUNT(*) as bookings,
            SUM(commission_amount) as daily_commission
        FROM commissions_accrued
        WHERE property_id = ?
        AND accrued_at >= datetime('now', '-7 days')
        GROUP BY DATE(accrued_at)
        ORDER BY day DESC
    """, (PROPERTY_ID,))
    
    rows = cur.fetchall()
    if rows:
        for row in rows:
            day, bookings, commission = row
            print(f"  {day}: {bookings} bookings, ${commission:.2f}")
    else:
        print("  No commission data in last 7 days")
    
    # Query 5: Commission rate verification
    print("\n[QUERY 5] Commission Rate Consistency Check")
    print("-" * 70)
    cur.execute("""
        SELECT DISTINCT commission_rate
        FROM commissions_accrued
        WHERE property_id = ?
    """, (PROPERTY_ID,))
    
    rates = cur.fetchall()
    if rates:
        print(f"  Unique rates found: {len(rates)}")
        for rate in rates:
            print(f"    - {rate[0]*100:.1f}% (expected: 10.0% for standard tier)")
    else:
        print("  No commission rates to check yet")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)


def generate_monthly_invoice_preview():
    """Preview monthly invoice for current month"""
    print("\n\n" + "=" * 70)
    print("MONTHLY INVOICE PREVIEW")
    print("=" * 70)
    
    current_month = datetime.now().strftime("%Y-%m")
    
    import asyncio
    from app.acp.commissions.ledger import generate_monthly_invoice
    
    async def get_invoice():
        try:
            invoice = await generate_monthly_invoice(PROPERTY_ID, current_month)
            
            print(f"\nInvoice for {PROPERTY_ID}")
            print(f"Period: {current_month}")
            print("-" * 70)
            print(f"  Total Commissions: ${invoice.get('total_commissions', 0):.2f}")
            print(f"  Booking Count: {invoice.get('booking_count', 0)}")
            print(f"  Period Start: {invoice.get('period_start', 'N/A')}")
            print(f"  Period End: {invoice.get('period_end', 'N/A')}")
            
            if invoice.get('booking_count', 0) > 0:
                avg = invoice['total_commissions'] / invoice['booking_count']
                print(f"  Average Commission per Booking: ${avg:.2f}")
            
        except Exception as e:
            print(f"\n[ERROR] Failed to generate invoice: {e}")
    
    asyncio.run(get_invoice())


if __name__ == "__main__":
    print("\nCommission Validation for Cloudbeds Property")
    print("=" * 70)
    
    try:
        validate_commissions()
        generate_monthly_invoice_preview()
        
        print("\n\n[SUCCESS] Commission validation complete")
        print("\nNext steps:")
        print("1. Verify all commission amounts match expected")
        print("2. Check commission rates are consistent (10% for standard)")
        print("3. Generate invoices at end of month")
        print("4. Set up automated commission reporting")
        
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
