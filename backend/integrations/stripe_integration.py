"""
Stripe Payment Integration using emergentintegrations
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

logger = logging.getLogger(__name__)

class StripeIntegration:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_API_KEY", "sk_test_emergent")
        self.stripe_checkout = None
        
        # Payment packages
        self.PACKAGES = {
            "starter": {"amount": 2500.00, "currency": "aed", "name": "Starter Package"},
            "growth": {"amount": 5000.00, "currency": "aed", "name": "Growth Package"},
            "enterprise": {"amount": 10000.00, "currency": "aed", "name": "Enterprise Package"}
        }
    
    def initialize(self, webhook_url: str):
        self.stripe_checkout = StripeCheckout(api_key=self.api_key, webhook_url=webhook_url)
    
    async def create_session(self, package_id: str, host_url: str, metadata: Optional[Dict] = None):
        try:
            if not self.stripe_checkout:
                self.initialize(f"{host_url}/api/integrations/payments/webhook")
            
            if package_id not in self.PACKAGES:
                return {"error": "Invalid package"}
            
            pkg = self.PACKAGES[package_id]
            request = CheckoutSessionRequest(
                amount=pkg["amount"],
                currency=pkg["currency"],
                success_url=f"{host_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{host_url}/payment-cancel",
                metadata=metadata or {"package_id": package_id}
            )
            
            session = await self.stripe_checkout.create_checkout_session(request)
            return {"url": session.url, "session_id": session.session_id, "package": pkg}
        except Exception as e:
            logger.error(f"Stripe session error: {e}")
            return {"error": str(e)}
    
    async def get_status(self, session_id: str):
        try:
            status = await self.stripe_checkout.get_checkout_status(session_id)
            return {
                "status": status.status,
                "payment_status": status.payment_status,
                "amount_total": status.amount_total,
                "currency": status.currency
            }
        except Exception as e:
            return {"error": str(e)}

stripe_integration = StripeIntegration()
