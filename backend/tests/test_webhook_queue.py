
import pytest
import asyncio
import json
import os
import sys
from uuid import uuid4
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import init_db, get_db_connection
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Mock Redis
# We need to mock redis before app imports queue stuff? 
# Already imported. We can patch app.queue.redis_conn or q.
# Actually, the route imports `enqueue_execute_quote` from `app.queue`
# Inside `app.queue`, `q` is the Queue object.
# We can patch `app.queue.q.enqueue`.

@pytest.mark.asyncio
async def test_webhook_enqueues_job():
    print("\n--- Testing Webhook -> Queue Flow ---")
    
    init_db()
    tenant_id = "test_queue_tenant"
    conn = get_db_connection()
    conn.execute("DELETE FROM execution_jobs WHERE tenant_id = ?", (tenant_id,))
    conn.execute("INSERT OR IGNORE INTO tenants (id, name) VALUES (?, ?)", (tenant_id, "Queue Test Tenant"))
    
    quote_id = str(uuid4())
    payment_id = str(uuid4())
    stripe_sess_id = f"cs_test_q_{uuid4()}"
    
    # Create Quote
    conn.execute('''
        INSERT INTO quotes (id, tenant_id, status, total_cents) VALUES (?, ?, ?, ?)
    ''', (quote_id, tenant_id, "awaiting_payment", 5000))
    
    # Create Payment (Pending)
    conn.execute('''
        INSERT INTO payments (id, tenant_id, quote_id, stripe_session_id, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (payment_id, tenant_id, quote_id, stripe_sess_id, "pending"))
    
    conn.commit()
    conn.close()
    
    # Payload
    payload = {
        "id": "evt_queue_123",
        "object": "event",
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
    
    # Patch Webhook Secret & Queue
    from app.api.routes import payments as payments_route
    from app import queue as queue_module
    
    original_secret = payments_route.STRIPE_WEBHOOK_SECRET
    payments_route.STRIPE_WEBHOOK_SECRET = None
    
    with patch.object(queue_module.q, 'enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock() # Mock Job
        
        response = client.post("/payments/webhook/stripe", json=payload)
        
        print(f"[Test] Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["status"] == "queued"
        assert "job_id" in response.json()
        
        job_id = response.json()["job_id"]
        
        # Verify enqueue called
        mock_enqueue.assert_called_once()
        
        # Verify DB Job created
        conn = get_db_connection()
        conn.row_factory = get_db_connection().row_factory
        job = conn.execute("SELECT * FROM execution_jobs WHERE id = ?", (job_id,)).fetchone()
        assert job is not None
        assert job["status"] == "queued"
        assert job["stripe_event_id"] == "evt_queue_123"
        
        # Verify Idempotency (Send again)
        print("[Test] Sending Duplicate Webhook...")
        response_dup = client.post("/payments/webhook/stripe", json=payload)
        
        print(f"[Test] Duplicate Response: {response_dup.json()}")
        # Should return same job_id and status=queued (or handled gracefully)
        # Our logic: confirm_payment returns 'already_paid'.
        # Then `if status == 'already_paid'` -> enqueue_execute_quote.
        # enqueue_execute_quote catches unique constraint and returns existing job ID.
        
        assert response_dup.status_code == 200
        assert response_dup.json()["job_id"] == job_id
        
        # Verify enqueue called again?
        # If we return existing ID inside enqueue, do we re-enqueue in Redis?
        # Look at implementation:
        # If existing_job found -> return existing_job["id"].
        # Does NOT enqueue in Redis again (which is good for noise, but what if Redis dropped it?)
        # For strict robustness, we might want to ensure it's in Redis.
        # But for this test, we verify it returns same ID.
        
        # enqueue count should be 1 (since we returned early in 2nd call)
        mock_enqueue.assert_called_once()
        
        conn.close()
        print("✅ Webhook Queue Flow Verified")

    payments_route.STRIPE_WEBHOOK_SECRET = original_secret

if __name__ == "__main__":
    asyncio.run(test_webhook_enqueues_job())
