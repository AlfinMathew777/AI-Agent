
import pytest
import sqlite3
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from app.services.pricing_service import PricingService

def test_pricing_logic():
    print("\n--- Starting Pricing Service Test ---")
    
    # Setup
    init_db()
    tenant_id = "tenant_pricing_test"
    service = PricingService(tenant_id)
    
    # 1. Test Calculation
    context = {
        "room_type": "deluxe",
        "party_size": 2,
        "selected_restaurant": {"name": "Test Grill"},
        "selected_event": {"name": "Test Show", "ticket_price_cents": 5000}
    }
    
    quote = service.calculate_quote(context)
    print(f"[Test] Quote: {json.dumps(quote, indent=2)}")
    
    # Verify Totals
    # Room: 25000
    # Dinner: 4500 * 2 = 9000
    # Event: 5000 * 2 = 10000
    # Subtotal: 44000
    # Tax: 4400
    # Fees: 250
    # Total: 48650
    
    assert quote["totals"]["subtotal_cents"] == 44000
    assert quote["totals"]["tax_cents"] == 4400
    assert quote["totals"]["total_cents"] == 48650
    
    # 2. DB Persistence (Quote)
    session_id = "sess_123"
    saved_quote = service.create_quote(session_id, context)
    quote_id = saved_quote["quote_id"]
    print(f"[Test] Created Quote ID: {quote_id}")
    
    conn = get_db_connection()
    row = conn.execute("SELECT status, total_cents FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    assert row[0] == "proposed"
    assert row[1] == 48650
    
    # 3. Create Receipt
    refs = {"hotel": "bk_hotel_1", "dinner": "bk_dine_1"}
    receipt = service.create_receipt(quote_id, session_id, refs)
    print(f"[Test] Created Receipt: {receipt}")
    
    # Verify Receipt
    r_row = conn.execute("SELECT status, total_cents FROM receipts WHERE id = ?", (receipt["receipt_id"],)).fetchone()
    assert r_row[0] == "confirmed"
    assert r_row[1] == 48650
    
    # Verify Quote Updated
    q_row = conn.execute("SELECT status FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    assert q_row[0] == "accepted"
    
    conn.close()
    print("--- Pricing Test Passed ---")

if __name__ == "__main__":
    test_pricing_logic()
