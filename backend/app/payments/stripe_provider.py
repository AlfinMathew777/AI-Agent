
import stripe
import os
from typing import Dict, Any, Optional
from app.core.config import STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY, INTEGRATION_MODE

# Configure Stripe
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

class StripeProvider:
    def __init__(self):
        self.enabled = bool(STRIPE_SECRET_KEY)
        self.mode = INTEGRATION_MODE

    def create_checkout_session(
        self, 
        amount_cents: int, 
        currency: str, 
        success_url: str, 
        cancel_url: str,
        metadata: Dict[str, Any] = None,
        line_items: list = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session.
        If mode is 'mock' or keys missing, return a mock URL.
        """
        
        # If in mock mode or keys missing, return mock response
        if self.mode == "mock" or not self.enabled:
            # Generate a mock ID
            import uuid
            mock_id = f"cs_mock_{uuid.uuid4()}"
            return {
                "id": mock_id,
                "url": f"http://localhost:3000/mock-checkout/{mock_id}?success_url={success_url}", # Frontend simulation
                # Or just return success_url directly for pure backend test? 
                # Prompt says: "return checkout_url" and "UI must show button".
                # For mock, we can point to a fake page or just the success url if we want 
                # manual triggering. But let's stick to a mock format.
                "payment_intent": f"pi_mock_{uuid.uuid4()}" 
            }

        try:
             # Use provided line items or construct simple one
            if not line_items:
                line_items = [{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': 'Hotel Booking Quote',
                        },
                        'unit_amount': amount_cents,
                    },
                    'quantity': 1,
                }]

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            return {
                "id": session.id,
                "url": session.url,
                "payment_intent": session.payment_intent
            }
        except Exception as e:
            print(f"[Stripe] Error creating session: {e}")
            raise e
