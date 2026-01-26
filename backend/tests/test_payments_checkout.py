
import pytest
import asyncio
import json
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from app.payments.payment_service import PaymentService
from uuid import uuid4

@pytest.mark.asyncio
async def test_payment_checkout_flow():
    print("\n--- Testing Payment Checkout Flow ---")
    
    # 1. Setup DB
    init_db()
    
    tenant_id = "test_tenant_pay"
    
    # Ensure tenant exists
    conn = get_db_connection()
    conn.execute("INSERT OR IGNORE INTO tenants (id, name) VALUES (?, ?)", (tenant_id, "Payment Test Tenant"))
    conn.commit()
    
    # 2. Create a Quote (Proposed)
    quote_id = str(uuid4())
    conn.execute('''
        INSERT INTO quotes (id, tenant_id, status, total_cents, currency)
        VALUES (?, ?, ?, ?, ?)
    ''', (quote_id, tenant_id, "proposed", 10000, "aud"))
    conn.commit()
    conn.close()
    
    print(f"[Test] Created Quote {quote_id}")
    
    # 3. Call Payment Service (Mock Mode)
    service = PaymentService(tenant_id)
    result = service.create_payment_for_quote(quote_id)
    
    print(f"[Test] Create Payment Result: {json.dumps(result, indent=2)}")
    
    assert "checkout_url" in result
    assert "payment_id" in result
    assert "stripe_session_id" in result
    
    # 4. Verify DB State
    conn = get_db_connection()
    conn.row_factory = get_db_connection().row_factory
    
    # Verify Payment Row
    payment = conn.execute("SELECT * FROM payments WHERE id = ?", (result["payment_id"],)).fetchone()
    assert payment is not None
    assert payment["status"] == "pending"
    assert payment["amount_cents"] == 10000
    assert payment["quote_id"] == quote_id
    
    # Verify Quote Status Update
    quote = conn.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    assert quote["status"] == "awaiting_payment"
    assert quote["payment_id"] == result["payment_id"]
    
    conn.close()
    print("✅ Payment Checkout Flow Verified")

if __name__ == "__main__":
    asyncio.run(test_payment_checkout_flow())
