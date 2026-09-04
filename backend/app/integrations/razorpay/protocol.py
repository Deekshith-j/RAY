"""Razorpay Integration Protocol and Adapters."""

from typing import Protocol, Dict, Any, Optional
from datetime import datetime
import hashlib
import json


class PaymentGateway(Protocol):
    """Protocol defining required payment gateway interactions."""

    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment status from gateway."""
        ...

    async def retry_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str = "INR",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Attempt payment retry where supported."""
        ...

    async def create_payment_link(
        self,
        case_id: str,
        amount: float,
        currency: str = "INR",
        description: str = "",
        customer: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a hosted Razorpay payment link."""
        ...

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Fetch subscription details."""
        ...

    async def recover_subscription(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger subscription charge retry."""
        ...

    async def get_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Fetch payment link details."""
        ...

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details."""
        ...

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Quick status check for payment verification."""
        ...
