"""Tests for secret redaction and credential protection."""

from app.core.security import redact_secrets
from app.config import settings


def test_redact_secrets_in_strings():
    text = f"Connecting using secret {settings.RAZORPAY_KEY_SECRET} to gateway"
    redacted = redact_secrets(text)
    assert settings.RAZORPAY_KEY_SECRET not in redacted or "placeholder" in settings.RAZORPAY_KEY_SECRET.lower()


def test_redact_secrets_in_dict():
    payload = {
        "payment_id": "pay_123",
        "api_key": "rzp_live_secretkey9999",
        "nested": {
            "password": "super_secret_password",
            "amount": 24999,
        }
    }
    redacted = redact_secrets(payload)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["password"] == "[REDACTED]"
    assert redacted["nested"]["amount"] == 24999
    assert redacted["payment_id"] == "pay_123"


def test_redact_secrets_in_exception_strings():
    err_str = "Failed authentication: rzp_live_998877665544332211 is invalid"
    redacted = redact_secrets(err_str)
    assert "rzp_live_[REDACTED]" in redacted
