# RAY — Final Implementation Report
## Revenue Autonomy Engine (Razorpay AI Buildathon)

---

## 1. Architecture Overview

RAY is an enterprise-grade, bounded agentic revenue recovery system designed to autonomously identify, diagnose, recover, and verify failed transactions.

The core architectural invariant is:
$$\text{PREDICTION} \neq \text{RECOMMENDATION} \neq \text{AUTHORIZATION} \neq \text{EXECUTION} \neq \text{VERIFICATION} \neq \text{VERIFIED REVENUE}$$

```
                ┌─────────────────────────┐
                │  Payment Failure Event  │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  Revenue Detective      │  (Advisory / Read-Only)
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  Recoverability ML      │  P(recovery) Calibrated
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  Diagnosis Agent        │  Root Cause Classification
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │  Recovery Planner       │  Candidate Strategy & EV
                └────────────┬────────────┘
                             │
                             ▼
                ╔═════════════════════════╗
                ║  Policy Engine Gate     ║  Deterministic Python Authority
                ╚════════════╤════════════╝
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
        DENY / STOP                 ALLOW / APPROVAL
                                           │
                                ┌──────────┴──────────┐
                                ▼                     ▼
                        Human Approval          Tool Gateway
                                │                     │
                                └──────────┬──────────┘
                                           │
                                           ▼
                                ┌─────────────────────┐
                                │ Razorpay Adapter    │ (Mock / Test Mode)
                                └──────────┬──────────┘
                                           │
                                           ▼
                                ┌─────────────────────┐
                                │ Execution Record    │
                                └──────────┬──────────┘
                                           │
                                           ▼
                                ╔═════════════════════╗
                                ║ Verification Engine ║
                                ╚══════════╤══════════╝
                                           │
                                ┌──────────┴──────────┐
                                ▼                     ▼
                           API Polling           HMAC Webhook
                                │                     │
                                └──────────┬──────────┘
                                           │
                                ┌──────────┴──────────┐
                                ▼                     ▼
                              AGREE                CONFLICT
                                │                     │
                                ▼                     ▼
                            RECOVERED            HUMAN_REVIEW
```

---

## 2. Core Components

1. **State Machine (`app.core.state_machine`)**:
   - Manages strict transitions: `CREATED` $\rightarrow$ `ATTEMPTED` $\rightarrow$ `FAILED` $\rightarrow$ `ANALYZING` $\rightarrow$ `RECOVERY_PLANNED` $\rightarrow$ `AWAITING_APPROVAL` $\rightarrow$ `EXECUTING` $\rightarrow$ `AWAITING_VERIFICATION` $\rightarrow$ `RECOVERED` or `HUMAN_REVIEW`.
   - Direct transitions from unverified states to `RECOVERED` raise `InvalidStateTransitionError`.
2. **Policy Engine (`app.core.policy_engine`)**:
   - Deterministic rule set (Rules 1–10).
   - Enforces automatic retry limits ($\le 1$), amount ceilings ($\le$ ₹10,000 auto-retry, $\ge$ ₹50,000 human approval), fraud denial, opt-out denial, and permanent decline blocks.
3. **Tool Gateway (`app.tools.gateway`)**:
   - Single execution choke point.
   - Enforces canonical idempotency (`ray:{case_id}:{strategy}:{attempt_number}`), decision verification, and human authorization checks.
4. **Razorpay Adapters (`app.integrations.razorpay`)**:
   - `MockPaymentAdapter`: Deterministic execution for offline testing and CI/CD.
   - `RazorpayTestModeAdapter`: Direct integration with Razorpay Test Mode APIs.
5. **Verification Engine (`app.verification.engine`)**:
   - Requires dual-signal confirmation: Signal A (provider API polling) + Signal B (HMAC-SHA256 authenticated webhook).
   - Confirms matching amounts and hashes before granting `VERIFIED`.
6. **Provenance Chain (`app.models.entities`)**:
   - Cryptographic chain linking `RecoveryPredictionRecord` $\rightarrow$ `RecoveryDecision` $\rightarrow$ `HumanApprovalRecord` $\rightarrow$ `ExecutionRecord` $\rightarrow$ `VerificationRecord` $\rightarrow$ `VerifiedRevenue`.

---

## 3. Security Boundaries & Invariants

- **Zero LLM Authorization**: Advisory LLMs can propose plans, but have zero access to keys, execution tools, or state transitions.
- **Prompt Injection Defense**: All customer notes and failure reasons are wrapped in `<UNTRUSTED_DATA>` tags.
- **Secret Redaction**: `rzp_test_*`, `rzp_live_*`, and Bearer tokens are scrubbed across logs, traces, and SSE payloads.
- **Decimal Precision**: All currency calculations use `Decimal` with exact paise quantization (`ROUND_HALF_UP`).

---

## 4. Agent Responsibilities

| Agent | Responsibility | Permitted Actions | Prohibited Actions |
| :--- | :--- | :--- | :--- |
| **Revenue Detective** | Evaluate financial exposure & extract features | Read database records, call ML inference | Trigger payments, modify case states |
| **Diagnosis Agent** | Classify failure root cause | Parse failure telemetry into structured enum | Execute retries, bypass policy |
| **Recovery Planner** | Compute EV for recovery strategies | Rank candidate actions | Authorize execution, dispatch tools |
| **Execution Agent** | Bridge to Tool Gateway | Submit authorized requests to Tool Gateway | Direct provider API access, bypass gateway |

---

## 5. Machine Learning Methodology

- **Algorithm**: Logistic Regression with Sigmoid Probability Calibration (`CalibratedClassifierCV`).
- **Isolation**: `GroupKFold` splitting on `customer_id` ensuring zero customer-group data leakage.
- **Held-Out Test Metrics**:
  - **PR-AUC**: `0.8602`
  - **ROC-AUC**: `0.8682`
  - **Brier Score**: `0.1372`
  - **Case Precision**: `80.19%`
  - **Case Recall**: `87.09%`
  - **Revenue-Weighted Recall**: `95.00% – 95.18%`

---

## 6. Economic Benchmark (Synthetic 1,000-Case Evaluation)

> [!NOTE]
> All benchmark results are generated on deterministic synthetic datasets and do not represent actual live Razorpay merchant volumes.

- **Baseline Naive Retry**:
  - Actions Attempted: 1,000
  - Recoveries: 116 (11.60%)
  - Wasted Interventions: 735 (73.50%)
- **Rule-Based RAY**:
  - Actions Attempted: 788
  - Recoveries: 711 (71.10%)
  - Wasted Interventions: 195 (24.75%)
- **ML-Assisted RAY**:
  - Actions Attempted: 763
  - Recoveries: 702 (70.20%)
  - Wasted Interventions: 180 (**23.59%**)
  - **Result**: 25 fewer wasted interventions with high revenue yield, preserving merchant brand reputation.

---

## 7. Automated Test Suite

- Total Tests: **101 passed**
- Failures / Errors: **0**
- Test Coverage:
  - Unit & Schema tests
  - State machine hardening
  - Customer group isolation
  - Decimal financial precision
  - Revenue-weighted recall
  - Policy engine boundary
  - High-value human approval
  - Tool Gateway & canonical idempotency
  - Dual-signal verification & conflict resolution
  - Secret redaction
  - Adversarial prompt injection containment
  - Full end-to-end demo lifecycles

---

## 8. Demonstration Scenarios

1. **Scenario 1 (Autonomous Recovery)**: `PAY_DEMO_001` (₹24,999.00) completes full lifecycle $\rightarrow$ `RECOVERED` with ₹24,999.00 verified revenue.
2. **Scenario 2 (High-Value Gate)**: `PAY_DEMO_HIGH_VALUE` (₹75,000.00) halts in `AWAITING_APPROVAL` until signed operator authorization is provided.
3. **Scenario 3 (Verification Conflict)**: `PAY_DEMO_CONFLICT` (₹15,000.00) triggers discrepancy between API and Webhook $\rightarrow$ `HUMAN_REVIEW` with verified revenue held at ₹0.00.
4. **Scenario 4 (Prompt Injection Defense)**: `PAY_DEMO_INJECTION` contains adversarial prompt in customer notes; system isolates data and enforces hard ceiling.
5. **Scenario 5 (Canonical Idempotency)**: `PAY_DEMO_DUPLICATE` repeats execution; Tool Gateway returns cached execution with strictly 1 provider call.

---

## 9. Known Limitations

1. **Synthetic Training Corpus**: Current models are trained on realistic synthetic transaction datasets. Fine-tuning on live production cohorts will further refine domain calibration.
2. **Multi-Currency**: Current implementation is tailored for INR (₹) with paise precision; international multi-currency conversion is scheduled for future milestones.
3. **Async Webhook Latency**: In live environments, provider webhook delivery may experience variable delays; the dual-signal verification engine accommodates this via background polling.

---

## 10. Razorpay Integration

- Implemented in `app/integrations/razorpay/`:
  - `PaymentGateway` protocol.
  - `MockPaymentAdapter`: Full offline deterministic simulation.
  - `RazorpayTestModeAdapter`: Direct client interacting with Razorpay Orders, Payments, and Payment Links API.
  - Webhook router verifying `x-razorpay-signature` using HMAC-SHA256.

---

## 11. Deployment Instructions

### Local Development (Free / Zero-Cost Setup)
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# 2. Run backend
cd backend
python -m uvicorn app.main:app --port 8000

# 3. Run frontend
cd frontend
npm run dev
```

### Docker Compose
```bash
docker-compose up --build
```

---

## 12. Buildathon Judge Walkthrough

To replicate the complete demonstration in under 60 seconds:
```bash
python scripts/demo.py
```
This executes all 5 demonstration scenarios, validates all cryptographic hashes, and outputs the final safety summary.
