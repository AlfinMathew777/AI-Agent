
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from app.db.session import get_db_connection
from app.payments.stripe_provider import StripeProvider
from app.core.config import BACKEND_BASE_URL, INTEGRATION_MODE

class PaymentService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.provider = StripeProvider()
        # Fallback base URL if not configured
        self.base_url = BACKEND_BASE_URL or "http://localhost:8002"

    def create_payment_for_quote(self, quote_id: str) -> Dict[str, Any]:
        """
        Creates a Stripe Checkout session for a specific quote.
        Returns checkput_url and payment_id.
        """
        conn = get_db_connection()
        conn.row_factory = get_db_connection().row_factory # Ensure dict access
        
        # 1. Fetch Quote & Validate
        quote = conn.execute(
            "SELECT * FROM quotes WHERE id = ? AND tenant_id = ?", 
            (quote_id, self.tenant_id)
        ).fetchone()
        
        if not quote:
            conn.close()
            raise ValueError("Quote not found")
            
        if quote["status"] not in ["proposed", "awaiting_payment"]:
            conn.close()
            raise ValueError(f"Quote status '{quote['status']}' invalid for payment.")

        # 2. Prepare Checkout Session
        amount_cents = quote["total_cents"]
        currency = quote["currency"] or "aud"
        
        # Determine URLs
        # Success -> Frontend success page or straight to webhook simulation in dev?
        # Ideally: Frontend URL. But for MVP backend test, we might point to a generic success page.
        # Let's say frontend runs on localhost:5173 usually.
        # We can use metadata to handle post-payment logic via webhook.
        success_url = f"{self.base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{self.base_url}/payment/cancel"
        
        metadata = {
            "tenant_id": self.tenant_id,
            "quote_id": quote_id
        }
        
        # Line Items (simplified or detailed)
        # Using simplified single item for now as breakdown might be complex to map to Stripe lines
        
        # 3. Call Provider
        try:
            session_data = self.provider.create_checkout_session(
                amount_cents=amount_cents,
                currency=currency,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )
        except Exception as e:
            conn.close()
            raise e
            
        # 4. Create Payment Record
        payment_id = str(uuid.uuid4())
        stripe_sess_id = session_data.get("id")
        
        conn.execute(
            '''INSERT INTO payments (
                id, tenant_id, quote_id, stripe_session_id, amount_cents, currency, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                payment_id, self.tenant_id, quote_id, stripe_sess_id,
                amount_cents, currency, "pending"
            )
        )
        
        # 5. Update Quote
        conn.execute(
            "UPDATE quotes SET status = 'awaiting_payment', payment_id = ? WHERE id = ?",
            (payment_id, quote_id)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "payment_id": payment_id,
            "checkout_url": session_data.get("url"),
            "stripe_session_id": stripe_sess_id
        }

    def confirm_payment(self, stripe_session_id: str) -> str:
        """
        Confirm a payment via Stripe Session ID.
        Updates payment and quote status to 'paid'.
        Idempotent: if already paid, returns 'already_paid'.
        """
        conn = get_db_connection()
        conn.row_factory = get_db_connection().row_factory
        
        # 1. Find Payment
        payment = conn.execute(
            "SELECT * FROM payments WHERE stripe_session_id = ? AND tenant_id = ?",
            (stripe_session_id, self.tenant_id)
        ).fetchone()
        
        if not payment:
            conn.close()
            # If not found, maybe it's for another tenant? (Should be handled by caller context)
            print(f"[Payment] Notification for unknown session {stripe_session_id} in tenant {self.tenant_id}")
            return "not_found"
            
        if payment["status"] == "paid":
            conn.close()
            return "already_paid"
            
        quote_id = payment["quote_id"]
        
        # 2. Update Payment
        conn.execute(
            "UPDATE payments SET status = 'paid', updated_at = ? WHERE id = ?",
            (datetime.now(), payment["id"])
        )
        
        # 3. Update Quote
        conn.execute(
            "UPDATE quotes SET status = 'paid' WHERE id = ?",
            (quote_id,)
        )
        
        conn.commit()
        conn.close()
        
        print(f"[Payment] Confirmed payment {payment['id']} for quote {quote_id}")
        return "confirmed"
