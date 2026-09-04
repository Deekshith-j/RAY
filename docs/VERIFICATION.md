# Independent Verification Engine

## 1. The Core Principle

A payment provider API returning an HTTP 200 or an agent claiming success **never** marks revenue as recovered. Revenue is only marked as recovered when independently proven by the **Verification Engine**.

---

## 2. Dual-Signal Corroboration

Verification requires two independent signals:

1. **Signal A: Provider API Polling**
   - Direct query to the payment gateway (or mock adapter) verifying payment state.
   - Requirement: `status == "captured"`.
2. **Signal B: Asynchronous Webhook Event**
   - Webhook delivered to `/api/v1/webhooks/razorpay` verified with HMAC-SHA256.
   - Requirement: `event == "payment.captured"` and `payload.payment.entity.id == provider_reference`.

---

## 3. Decision Matrix

| Signal A (API) | Signal B (Webhook) | Amount Match | Verification Status | Case Final State | Verified Revenue |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `captured` | `captured` | Yes | `VERIFIED` | `RECOVERED` | INR Amount |
| `captured` | `failed` | N/A | `CONFLICT` | `HUMAN_REVIEW` | ₹0.00 |
| `failed` | `captured` | N/A | `CONFLICT` | `HUMAN_REVIEW` | ₹0.00 |
| `failed` | `failed` | N/A | `FAILED` | `FAILED_RECOVERY` | ₹0.00 |
| Pending | Pending | N/A | `PENDING` | `AWAITING_VERIFICATION` | ₹0.00 |

---

## 4. Cryptographic Evidence Hashing

For auditable provenance, canonical evidence JSON is hashed using SHA-256:

```python
evidence = {
    "case_id": case_id,
    "execution_id": execution_id,
    "provider_reference": provider_ref,
    "api_confirmed": True,
    "webhook_confirmed": True,
    "verified_amount": float(verified_amount),
    "timestamp": now.isoformat(),
}
evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
```

The resulting hash is stored in `VerificationRecord.evidence_hash` and exposed in the provenance chain UI. Secrets are never hashed or logged.
