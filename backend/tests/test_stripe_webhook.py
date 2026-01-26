
import pytest
import asyncio
import json
import os
import sys
from uuid import uuid4

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_stripe_webhook_flow():
    print("\n--- Testing Stripe Webhook Confirmation ---")
    
    # 1. Setup Data
    init_db()
    tenant_id = "test_tenant_webhook"
    quote_id = str(uuid4())
    payment_id = str(uuid4())
    stripe_sess_id = f"cs_test_{uuid4()}"
    
    conn = get_db_connection()
    conn.execute("INSERT OR IGNORE INTO tenants (id, name) VALUES (?, ?)", (tenant_id, "Webhook Test Tenant"))
    
    # Create Quote (Awaiting Payment)
    conn.execute('''
        INSERT INTO quotes (id, tenant_id, status, total_cents, currency, payment_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (quote_id, tenant_id, "awaiting_payment", 5000, "aud", payment_id))
    
    # Create Payment (Pending)
    conn.execute('''
        INSERT INTO payments (id, tenant_id, quote_id, stripe_session_id, amount_cents, currency, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (payment_id, tenant_id, quote_id, stripe_sess_id, 5000, "aud", "pending"))
    
    conn.commit()
    conn.close()
    
    print(f"[Test] Setup: Payment {payment_id} Pending for Quote {quote_id}")
    
    # 2. Simulate Webhook Payload
    # We bypass signature check by NOT setting STRIPE_WEBHOOK_SECRET in test env (default logic in route handles fallback)
    # Ensure env var is unset for this test? 
    # The route checks `if STRIPE_WEBHOOK_SECRET:`.
    # If it IS set in config.py (from .env), we might fail verification.
    # We can override the dependency function or mocked key?
    # Or just mock `stripe.Webhook.construct_event`.
    # For now, let's assume `STRIPE_WEBHOOK_SECRET` might be set if user populated .env.
    # But `config.py` loads it.
    # I'll rely on the "Dev/Mock fallback" block in the route: `else: data = json.loads(payload) ...`
    # It enters `else` only if `STRIPE_WEBHOOK_SECRET` is Falsy.
    
    # To force fallback, I will monkeypatch app.api.routes.payments.STRIPE_WEBHOOK_SECRET or simply Unset env?
    # Unset env doesn't affect loaded module.
    # I will construct a valid mock event payload.
    
    payload = {
        "id": "evt_test_123",
        "object": "event",
        "api_version": "2020-08-27",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": stripe_sess_id,
                "metadata": {
                    "tenant_id": tenant_id,
                    "quote_id": quote_id
                }
            }
        }
    }
    
    # Patch config in the module to ensure None for secret (simulating dev mode for test)
    from app.api.routes import payments as payments_route
    original_secret = payments_route.STRIPE_WEBHOOK_SECRET
    payments_route.STRIPE_WEBHOOK_SECRET = None # Force fallback path
    
    try:
        response = client.post("/payments/webhook/stripe", json=payload)
    finally:
         payments_route.STRIPE_WEBHOOK_SECRET = original_secret
         
    print(f"[Test] Webhook Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["result"] == "confirmed"
    
    # 3. Verify DB Update
    conn = get_db_connection()
    conn.row_factory = get_db_connection().row_factory
    
    payment = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
    assert payment["status"] == "paid"
    
    quote = conn.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,)).fetchone()
    assert quote["status"] == "paid"
    
    print("✅ Payment and Quote marked as PAID.")
    
    # 4. Idempotency Test
    print("[Test] Sending Duplicate Webhook...")
    payments_route.STRIPE_WEBHOOK_SECRET = None
    try:
        response_dup = client.post("/payments/webhook/stripe", json=payload)
    finally:
         payments_route.STRIPE_WEBHOOK_SECRET = original_secret

    print(f"[Test] Duplicate Response: {response_dup.json()}")
    assert response_dup.status_code == 200
    assert response_dup.json()["result"] == "already_paid"
    
    conn.close()
    print("✅ Idempotency Verified.")

if __name__ == "__main__":
    asyncio.run(test_stripe_webhook_flow())
