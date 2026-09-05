# RAY — Pitch Deck & Demonstration Narrative
## Revenue Autonomy Engine (Razorpay AI Buildathon)

---

## Slide 1: Title Slide

# RAY — Revenue Autonomy Engine
### Controlled Agentic Autonomy Over Payment Recovery & Verification
**Track:** AI Revenue Recovery &bull; Razorpay AI Buildathon  
**Tagline:** *"AI is capable enough to recommend. The system is constrained enough to trust."*

---

## Slide 2: The Multi-Billion Dollar Problem

### Failed Payments Leak Revenue & Erode Trust
- **The Scale:** 5% to 15% of digital payment transactions fail globally due to transient network glitches, bank downtime, expired instruments, or user drop-off.
- **The Failure of Naive Retries:** Simple automated retries spam customer cards, incur gateway fees, trigger bank velocity blocks, and yield only **11.6% recovery** with **73.5% wasted attempts**.
- **The Danger of Unconstrained AI:** Letting LLMs directly invoke payment APIs creates catastrophic financial liabilities: prompt injection vulnerabilities, hallucinated authorizations, and unverified recoveries.

---

## Slide 3: The Non-Negotiable System Invariant

```
                 PREDICTION (ML)
                       ≠
             RECOMMENDATION (LLM)
                       ≠
             AUTHORIZATION (Policy)
                       ≠
               EXECUTION (Gateway)
                       ≠
             VERIFICATION (Dual-Signal)
                       ≠
              VERIFIED REVENUE (Ledger)
```

> **The Core Thesis:**  
> **RAY does NOT give AI control of payments. It gives AI controlled autonomy over revenue recovery.**  
> The ML model and LLM agents are strictly advisory. The deterministic Policy Engine is the sole financial authority.

---

## Slide 4: Bounded Multi-Agent Architecture

```
                    ┌───────────────────────┐
                    │ Payment Failure Event │
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │   Revenue Detective   │  Read-Only Exposure Evaluator
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │   Recoverability ML   │  Calibrated P(recovery) = 91.4%
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │    Diagnosis Agent    │  Root Cause Telemetry
                    └───────────┬───────────┘
                                ↓
                    ┌───────────────────────┐
                    │   Recovery Planner    │  Expected Value Optimization
                    └───────────┬───────────┘
                                ↓
                    ╔═══════════════════════╗
                    ║ DETERMINISTIC POLICY  ║  Sole Authorization Authority
                    ║ ENGINE                ║  (Hardcoded Python Rules)
                    ╚═══════════╤═══════════╝
                                │
                    ┌───────────┴───────────┐
                    │                       │
              DENY / STOP             ALLOW / APPROVAL
                    │                       │
                    │               ┌───────┴────────┐
                    │               │                │
                    │          Human Approval    Tool Gateway
                    │          (≥ ₹50,000)      (Canonical Idempotency)
                    │               │                │
                    └───────────────┴────────────────┘
                                    ↓
                         ┌─────────────────────┐
                         │  Razorpay Adapter   │  Test Mode / Mock Isolation
                         └──────────┬──────────┘
                                    ↓
                         ╔═════════════════════╗
                         ║ Verification Engine ║  Independent Dual-Signal
                         ╚══════════╤══════════╝
                                    ↓
                           ┌────────┴────────┐
                           │                 │
                         AGREE            CONFLICT
                           │                 │
                           ↓                 ↓
                       RECOVERED       HUMAN_REVIEW
                     (₹ Verified)       (₹0.00 Held)
```

---

## Slide 5: The 3-Minute Killer Demo Flow

### Moment 1: Autonomous Low-Value Recovery (₹24,999)
- Transaction fails with issuer timeout.
- ML estimates **$P(\text{recovery}) = 91.42\%$** (Band: HIGH, Expected: ₹22,855.16).
- Advisory Planner proposes `RETRY`.
- Policy Engine verifies amount $\le$ ₹10,000 auto-limit, retry count $\le 1$ $\rightarrow$ **AUTHORIZED**.
- Tool Gateway executes with idempotency key `ray:PAY_DEMO_001:RETRY:1`.
- Verification Engine polls Razorpay API (`captured`) + verifies HMAC webhook signature (`captured`) + hashes match $\rightarrow$ **₹24,999.00 VERIFIED REVENUE**.

### Moment 2: The High-Value Attack on Our Own System (₹75,000)
```
AI → RETRY
      ↓
POLICY ENGINE
      ↓
⚠ ₹75,000 (Exceeds ₹50,000 ceiling)
      ↓
HUMAN APPROVAL REQUIRED
      ↓
TOOL GATEWAY BLOCKED
      ↓
0 EXECUTIONS
```
- **The Contrast:** Even though ML predicts 87% recoverability and AI urges `RETRY`, the Policy Engine deterministically freezes execution in `AWAITING_APPROVAL`.
- Only after Risk Lead signs an immutable `HumanApprovalRecord` does the Tool Gateway permit provider dispatch.

### Moment 3: The Verification Conflict Guard (₹15,000)
- Razorpay API reports `captured` (Signal A).
- Webhook reports `failed` (Signal B).
- Naive systems mark this as recovered; **RAY escalates to `HUMAN_REVIEW` and holds verified revenue strictly at ₹0.00**.

---

## Slide 6: Real ML Evaluation & Unit Economics

| Benchmark Dimension | Mode A: Naive Retry | Mode B: Rule-Based RAY | Mode C: ML-Assisted RAY |
| :--- | :--- | :--- | :--- |
| **Actions Attempted** | 1,896 | 1,330 | 1,281 |
| **Successful Recoveries**| 503 | 1,002 | 978 |
| **Revenue Recovered** | ₹4,387,269 | ₹26,893,292 | ₹26,533,316 |
| **Revenue / Action** | **₹2,314** | **₹20,221** | **₹20,713** *(+₹492.45 / attempt)* |
| **Wasted Interventions**| 1,393 | 328 | **303** *(25 fewer wasted actions)* |
| **False Intervention Rate**| 73.5% | 24.7% | **23.6%** |
| **Revenue-Weighted Recall**| 15.7% | 96.2% | **95.0%** |

### Why ML Matters Here
1. **Capital Efficiency:** Generates **+INR 492.45 more revenue per action attempted**.
2. **Brand & Reputation Protection:** Eliminates **25 hopeless retry attempts (-7.62% waste)** on customers with expired cards or permanent declines.
3. **Calibrated Probabilities:** Sigmoid-calibrated Logistic Regression achieves a **Brier Score of 0.1372** and **PR-AUC of 0.8602** with strict customer-group isolation.

---

## Slide 7: Enterprise Safety & Defense-in-Depth

- [x] **Zero Direct Provider Access:** LLMs and ML agents have zero network access to Razorpay credentials.
- [x] **Deterministic Policy Authority:** Python code rules are immutable to prompt injection.
- [x] **Canonical Idempotency:** Replay attempts return cached responses with at-most-once financial execution.
- [x] **Cryptographic Webhook Ingestion:** HMAC-SHA256 signature verification protects against forgery.
- [x] **Prompt Injection Containment:** Customer free-text is isolated in `<UNTRUSTED_DATA>` blocks.
- [x] **Centralized Secret Redaction:** API keys, secrets, and auth headers are scrubbed from logs and SSE streams.
- [x] **Decimal Currency Engine:** Precision to the exact paise (`ROUND_HALF_UP`), eliminating floating-point drift.

---

## Slide 8: The Conclusion & Judge Takeaway

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   RAY does not replace financial judgment with AI.      │
│                                                         │
│   RAY uses AI to detect and diagnose opportunities,     │
│   while deterministic financial controls guarantee      │
│   that unauthorized execution is mathematically         │
│   impossible.                                           │
│                                                         │
│   "AI is capable enough to recommend.                   │
│    The system is constrained enough to trust."          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Live Demonstration Command:**
```bash
python scripts/demo.py
```
**Automated Verification:**
```bash
python -m pytest backend/tests -v   # 101 passed in 9.5s
```
