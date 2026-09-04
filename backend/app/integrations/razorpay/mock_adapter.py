"""Mock payment adapter for offline, deterministic testing and simulation."""

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json


class MockPaymentAdapter:
    """
    Deterministic offline payment adapter implementing PaymentGateway.
    Simulates Razorpay API responses without external dependencies.
    """

    def __init__(self, default_status: str = "captured"):
        self.default_status = default_status
        self.simulated_payments: Dict[str, Dict[str, Any]] = {}
        self.simulated_links: Dict[str, Dict[str, Any]] = {}
        self.simulated_subscriptions: Dict[str, Dict[str, Any]] = {}

    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch simulated payment status."""
        if payment_id in self.simulated_payments:
            return self.simulated_payments[payment_id]

        # Generate deterministic mock payment record
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": 2499900,  # paise
            "currency": "INR",
            "status": self.default_status,
            "order_id": f"order_{payment_id}",
            "method": "card",
            "captured": (self.default_status == "captured"),
            "created_at": int(datetime.utcnow().timestamp()),
        }

    async def retry_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str = "INR",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate payment retry."""
        mock_id = f"pay_retry_{hashlib.md5(f'{payment_id}_{idempotency_key}'.encode()).hexdigest()[:12]}"
        response = {
            "id": mock_id,
            "entity": "payment",
            "original_payment_id": payment_id,
            "amount": int(amount * 100),
            "currency": currency,
            "status": self.default_status,
            "method": "retry",
            "idempotency_key": idempotency_key,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.simulated_payments[mock_id] = response
        return response

    async def create_payment_link(
        self,
        case_id: str,
        amount: float,
        currency: str = "INR",
        description: str = "",
        customer: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate payment link creation."""
        link_id = f"plink_{hashlib.md5(f'{case_id}_{idempotency_key}'.encode()).hexdigest()[:12]}"
        response = {
            "id": link_id,
            "entity": "payment_link",
            "short_url": f"https://rzp.io/i/{link_id}",
            "amount": int(amount * 100),
            "currency": currency,
            "status": "created",
            "description": description or f"Recovery for {case_id}",
            "customer": customer or {"name": "Customer", "contact": "+919876543210"},
            "idempotency_key": idempotency_key,
            "created_at": int(datetime.utcnow().timestamp()),
        }
        self.simulated_links[link_id] = response
        return response

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Fetch simulated subscription details."""
        if subscription_id in self.simulated_subscriptions:
            return self.simulated_subscriptions[subscription_id]

        return {
            "id": subscription_id,
            "entity": "subscription",
            "plan_id": "plan_monthly_pro",
            "status": "active",
            "current_start": int(datetime.utcnow().timestamp()),
            "current_end": int(datetime.utcnow().timestamp()) + 2592000,
        }

    async def recover_subscription(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Simulate subscription charge recovery."""
        charge_id = f"sub_chg_{hashlib.md5(f'{subscription_id}_{idempotency_key}'.encode()).hexdigest()[:12]}"
        response = {
            "id": charge_id,
            "subscription_id": subscription_id,
            "status": "active",
            "recovery_status": "success",
            "idempotency_key": idempotency_key,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.simulated_subscriptions[subscription_id] = response
        return response

    async def get_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Fetch simulated payment link."""
        if link_id in self.simulated_links:
            return self.simulated_links[link_id]
        return {
            "id": link_id,
            "entity": "payment_link",
            "status": "paid" if self.default_status == "captured" else "created",
            "amount": 2499900,
            "currency": "INR",
            "short_url": f"https://rzp.io/i/{link_id}",
        }

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch simulated order."""
        return {
            "id": order_id,
            "entity": "order",
            "amount": 2499900,
            "currency": "INR",
            "status": "paid" if self.default_status == "captured" else "attempted",
            "attempts": 1,
            "created_at": int(datetime.utcnow().timestamp()),
        }

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Quick status check for payment verification."""
        payment = await self.get_payment(payment_id)
        return {
            "payment_id": payment_id,
            "status": payment.get("status", self.default_status),
            "captured": payment.get("captured", self.default_status == "captured"),
            "amount": payment.get("amount", 2499900),
        }
