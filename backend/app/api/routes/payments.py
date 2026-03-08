
from fastapi import APIRouter, Depends, HTTPException, Request
import json
from app.api.deps import get_current_tenant
from app.payments.payment_service import PaymentService
from app.core.config import STRIPE_WEBHOOK_SECRET
import stripe

router = APIRouter()

@router.post("/payments/checkout/{quote_id}")
async def create_checkout_session(
    quote_id: str,
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Create a checkout session for a quote.
    """
    service = PaymentService(tenant_id)
    try:
        result = service.create_payment_for_quote(quote_id)
        return {
            "status": "needs_payment",
            "quote_id": quote_id,
            "payment_id": result["payment_id"],
            "checkout_url": result["checkout_url"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Payment Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Payment Error")

# Webhook placeholder (full implementation in Phase 2)
# Webhook Handler
@router.post("/payments/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    event = None

    try:
        # Verify Signature
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        else:
            # Dev/Mock fallback
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
            
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle Event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extract Metadata
        metadata = session.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        
        if not tenant_id:
            print("[Payment Webhook] Warning: No tenant_id in metadata.")
            return {"status": "ignored_no_tenant"}
            
        # Confirm Payment using Service
        try:
            # 1. Update Payment/Quote Status (Idempotent inside service)
            service = PaymentService(tenant_id)
            # We should probably pass stripe_event_id to service to store `provider_event_id` in payments table
            # But confirm_payment prompt signature was simple. 
            # We can update `payments.provider_event_id` manually here or update service.
            # Let's update service later for stricter idempotency on payment creation.
            # For now, confirm_payment handles the status check.
            
            status = service.confirm_payment(session["id"])
            
            # 2. Queue Execution (instead of direct await)
            if status == "confirmed" or status == "already_paid": 
                # even if already_paid, we ensure job is queued (semantics: ensure execution happens)
                
                quote_id = metadata.get("quote_id")
                # Need payment_id for job record. Service confirms it but doesn't return it directly easily?
                # We can fetch it or trust the flow.
                # Actually, `confirm_payment` returns "confirmed".
                # For job, we need payment_id.
                
                # Let's look up payment_id quickly or pass None (job can refetch if needed, but schema wants it)
                # Optimization: PaymentService could return payment_id.
                # For now, let's query DB in a lightweight way or ignore payment_id in job args (redundant if quote known)
                # Job has args: (tenant_id, quote_id, payment_id, stripe_event_id, job_id)
                # We can verify payment_id in job.
                
                # Fetch Payment ID for data integrity
                from app.db.session import get_db_connection
                conn = get_db_connection()
                row = conn.execute("SELECT id FROM payments WHERE stripe_session_id = ?", (session["id"],)).fetchone()
                payment_id = row[0] if row else "unknown"
                conn.close()

                from app.queue import enqueue_execute_quote
                
                job_id = enqueue_execute_quote(
                    tenant_id=tenant_id,
                    quote_id=quote_id,
                    payment_id=payment_id,
                    stripe_event_id=event["id"]
                )
                
                return {"status": "queued", "job_id": job_id}
            
            return {"status": "success", "result": status}
        except Exception as e:
             print(f"[Payment Webhook] Processing Error: {e}")
             # Return 200 to Stripe so they don't retry indefinitely on logic errors?
             # Standard practice: 500 triggers retry. 200 OK.
             # If logic error is transient (DB lock), 500 is good.
             # If logic error is permanent (bug), 200 avoids queue clog.
             # Capturing error.
             raise HTTPException(status_code=500, detail=str(e))
             
    return {"status": "received"}
