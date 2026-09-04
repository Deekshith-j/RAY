# RAY System Limitations & Scope Disclosures

In accordance with competition engineering ethics, this document explicitly discloses the current boundaries, constraints, and assumptions of RAY.

---

## 1. Razorpay Credentials & Live Sandbox
- **Implementation Status**: The `RazorpayTestModeAdapter` implements the official Razorpay REST protocol (`/v1/payments`, `/v1/orders`, `/v1/payment_links`, `/v1/subscriptions`) and includes strict test-mode safety guards (`ensure_test_mode_safety()`).
- **Disclosure**: In local evaluation environments where live merchant sandbox API keys (`rzp_test_...`) are not configured in `.env`, the system defaults to the deterministic `MockPaymentAdapter`. Real external network sandbox roundtrips require merchant-supplied credentials.

---

## 2. Dataset & Benchmark Synthetics
- **Disclosure**: The benchmark evaluation uses deterministic synthetic transaction events generated from Razorpay failure distribution profiles. While customer-grouped 70/15/15 isolation guarantees zero leakage and proves mathematical methodology, results demonstrate algorithmic behavior rather than historical merchant production data.

---

## 3. LLM Provider Execution
- **Disclosure**: To guarantee instant, deterministic, zero-cost, and zero-token-leakage test runs during automated CI/CD and judge demos, the default `LLM_PROVIDER` runs in deterministic mock mode. The orchestrator is fully architected with prompt injection containment and structured JSON schema validation for live Ollama or OpenAI-compatible backends.

---

## 4. Bounded Action Families
- **Current Scope**: RAY currently supports 5 bounded recovery action families:
  1. `RETRY`: Automated payment retry via gateway.
  2. `PAYMENT_LINK`: Generating a customized Razorpay Payment Link with SMS/Email notifications.
  3. `SUBSCRIPTION_RECOVERY`: Invoicing and dunning flow updates for recurring billing.
  4. `CUSTOMER_NOTIFICATION`: Passive nudges for customer-facing balance or authentication issues.
  5. `NO_ACTION`: Explicit suppression of hopeless interventions ($EV \le 0$ or customer opt-out).
- **Out of Scope**: Multi-currency cross-border FX conversions, automated crypto settlements, and direct bank account debit overrides are strictly unsupported.
