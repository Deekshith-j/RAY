# Security Architecture & Boundary Invariants

## 1. Non-Negotiable Boundary Invariants

1. **Advisory Isolation:**
   - ML models and LLM agents are strictly read-only advisory components.
   - They possess zero execution capabilities, zero database write permissions for financial balances, and zero direct provider network access.
2. **Deterministic Supremacy:**
   - The Policy Engine is deterministic Python code. It is immune to prompt injection, hallucinations, and probabilistic shifts.
   - No agent recommendation can bypass the Policy Engine.
3. **Execution Gating:**
   - The Tool Gateway rejects all requests lacking an authorized `RecoveryDecision`.
   - High-value cases ($\ge \text{₹}50,000$) require a formal `HumanApprovalRecord` signed by an operator.

---

## 2. Prompt Injection Containment

Untrusted customer fields:
- `customer_name`
- `failure_reason` / `error_description`
- `order_notes` / `metadata`

**Defense Mechanism:**
All customer inputs are wrapped in strict passive tags `<UNTRUSTED_DATA>...</UNTRUSTED_DATA>` and passed only as passive contextual data. The agents are instructed never to follow instructions found within these tags. Furthermore, even if an LLM were compromised, the deterministic Policy Engine and Tool Gateway block any unauthorized action.

---

## 3. Canonical Idempotency & Replay Protection

Every financial tool dispatch requires an idempotency key following the canonical format:
```text
ray:{case_id}:{strategy}:{attempt_number}
```

If an execution is requested with an existing key:
1. The Tool Gateway detects the existing `ExecutionRecord`.
2. Provider API dispatch is skipped.
3. The previous execution result is returned with `is_idempotent_replay: True`.

---

## 4. Webhook Authentication & HMAC-SHA256

Incoming webhooks are verified using HMAC-SHA256 with `RAZORPAY_WEBHOOK_SECRET`:
- Missing or invalid signatures return `HTTP 400 Bad Request`.
- Verified payloads are checked against the internal idempotency table to prevent replay attacks.
- Sensitive credentials (`RAZORPAY_KEY_SECRET`, `webhook_secret`) are automatically redacted from all audit logs and exception traces.
