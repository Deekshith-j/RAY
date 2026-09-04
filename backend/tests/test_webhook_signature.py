"""Tests for Razorpay Webhook signature verification and security."""

import hmac
import hashlib
import json
import pytest
from app.api.v1.webhooks import verify_razorpay_signature


def test_valid_webhook_signature():
    secret = "test_webhook_secret_key_123"
    raw_payload = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_123"}}}}'
    valid_sig = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()

    assert verify_razorpay_signature(raw_payload, valid_sig, secret) is True


def test_invalid_webhook_signature_rejected():
    secret = "test_webhook_secret_key_123"
    raw_payload = b'{"event":"payment.captured"}'
    invalid_sig = "fake_tampered_signature_hex_code"

    assert verify_razorpay_signature(raw_payload, invalid_sig, secret) is False


def test_missing_signature_or_secret():
    raw_payload = b'{"event":"payment.captured"}'
    assert verify_razorpay_signature(raw_payload, "", "secret") is False
    assert verify_razorpay_signature(raw_payload, "sig", "") is False
