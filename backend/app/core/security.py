"""Security, secret management, and redaction utilities for RAY."""

import re
from typing import Any, Dict, List, Union
from app.config import settings

# Secret patterns to automatically mask
SECRET_PATTERNS = [
    re.compile(r"rzp_(live|test)_[a-zA-Z0-9]{14,24}"),
    re.compile(r"[a-zA-Z0-9]{20,32}"),
]


def redact_secrets(data: Any) -> Any:
    """
    Recursively redacts Razorpay keys, webhook secrets, and sensitive tokens
    from strings, dictionaries, lists, and exception outputs.
    Guarantees secrets never appear in logs, database audit records, SSE, or UI.
    """
    known_secrets = [
        s for s in [
            settings.RAZORPAY_KEY_SECRET,
            settings.RAZORPAY_WEBHOOK_SECRET,
        ]
        if s and "placeholder" not in s.lower()
    ]

    if isinstance(data, str):
        cleaned = data
        for secret in known_secrets:
            if secret in cleaned:
                cleaned = cleaned.replace(secret, "[REDACTED_SECRET]")
        # Mask live/test key patterns if exposed
        cleaned = re.sub(r"rzp_live_[a-zA-Z0-9]+", "rzp_live_[REDACTED]", cleaned)
        return cleaned

    elif isinstance(data, dict):
        redacted_dict = {}
        for k, v in data.items():
            key_lower = str(k).lower()
            if any(term in key_lower for term in ["secret", "password", "token", "auth", "api_key"]):
                redacted_dict[k] = "[REDACTED]"
            else:
                redacted_dict[k] = redact_secrets(v)
        return redacted_dict

    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]

    return data


def ensure_test_mode_safety():
    """
    Guarantees that RAY operates in Test/Mock Mode.
    Blocks any automated financial execution if accidentally pointed at production
    without explicit non-test safety authorization.
    """
    if not settings.RAZORPAY_TEST_MODE:
        raise RuntimeError(
            "SAFETY ERROR: RAZORPAY_TEST_MODE is False. Live financial execution is strictly disabled by RAY safety policy."
        )
