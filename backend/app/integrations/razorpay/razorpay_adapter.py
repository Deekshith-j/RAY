"""Razorpay Test Mode API adapter."""

import os
import hashlib
from typing import Dict, Any, Optional
import httpx
from app.config import settings
from app.core.security import ensure_test_mode_safety
from app.integrations.razorpay.mock_adapter import MockPaymentAdapter


class RazorpayTestModeAdapter:
    """
    Adapter communicating with Razorpay Test Mode REST API.
    Uses basic auth with KEY_ID and KEY_SECRET.
    Never exposes or logs credentials.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
    ):
        ensure_test_mode_safety()
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.base_url = "https://api.razorpay.com/v1"
        self._fallback_mock = MockPaymentAdapter()

    def _is_placeholder(self) -> bool:
        """Return True if real Razorpay test credentials are not provided."""
        return not self.key_id or "placeholder" in self.key_id.lower() or not self.key_secret or "placeholder" in self.key_secret.lower()

    async def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment status from Razorpay."""
        if self._is_placeholder():
            return await self._fallback_mock.get_payment(payment_id)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/payments/{payment_id}",
                auth=(self.key_id, self.key_secret),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def retry_payment(
        self,
        payment_id: str,
        amount: float,
        currency: str = "INR",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Attempt retry or status refresh."""
        if self._is_placeholder():
            return await self._fallback_mock.retry_payment(
                payment_id=payment_id,
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
            )

        headers = {}
        if idempotency_key:
            headers["X-Razorpay-Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/payments/{payment_id}/retry",
                auth=(self.key_id, self.key_secret),
                headers=headers,
                json={"amount": int(amount * 100), "currency": currency},
                timeout=10.0,
            )
            if resp.status_code == 404:
                # Razorpay retry endpoint may not be active for all payment types; fall back to state query
                return await self.get_payment(payment_id)
            resp.raise_for_status()
            return resp.json()

    async def create_payment_link(
        self,
        case_id: str,
        amount: float,
        currency: str = "INR",
        description: str = "",
        customer: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a hosted payment link in Razorpay Test Mode."""
        if self._is_placeholder():
            return await self._fallback_mock.create_payment_link(
                case_id=case_id,
                amount=amount,
                currency=currency,
                description=description,
                customer=customer,
                idempotency_key=idempotency_key,
            )

        headers = {}
        if idempotency_key:
            headers["X-Razorpay-Idempotency-Key"] = idempotency_key

        payload = {
            "amount": int(amount * 100),
            "currency": currency,
            "description": description or f"Recovery for Case {case_id}",
            "reference_id": case_id,
        }
        if customer:
            payload["customer"] = customer

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/payment_links",
                auth=(self.key_id, self.key_secret),
                headers=headers,
                json=payload,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Fetch subscription details."""
        if self._is_placeholder():
            return await self._fallback_mock.get_subscription(subscription_id)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/subscriptions/{subscription_id}",
                auth=(self.key_id, self.key_secret),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def recover_subscription(
        self,
        subscription_id: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Attempt subscription charge recovery."""
        if self._is_placeholder():
            return await self._fallback_mock.recover_subscription(
                subscription_id=subscription_id,
                idempotency_key=idempotency_key,
            )

        headers = {}
        if idempotency_key:
            headers["X-Razorpay-Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/subscriptions/{subscription_id}/charge_now",
                auth=(self.key_id, self.key_secret),
                headers=headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_payment_link(self, link_id: str) -> Dict[str, Any]:
        """Fetch payment link details."""
        if self._is_placeholder():
            return await self._fallback_mock.get_payment_link(link_id)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/payment_links/{link_id}",
                auth=(self.key_id, self.key_secret),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Fetch order details."""
        if self._is_placeholder():
            return await self._fallback_mock.get_order(order_id)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/orders/{order_id}",
                auth=(self.key_id, self.key_secret),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Quick status check for payment verification."""
        payment = await self.get_payment(payment_id)
        return {
            "payment_id": payment_id,
            "status": payment.get("status", "unknown"),
            "captured": payment.get("captured", payment.get("status") == "captured"),
            "amount": payment.get("amount", 0),
        }
