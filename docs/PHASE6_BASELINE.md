# Phase 6 Baseline & Repository Audit Report

**Project:** RAY — Revenue Autonomy Engine  
**Audit Date:** September 2026  
**Status:** Phase 5 Hardened & Phase 6 Bounded Agentic Architecture

---

## 1. Baseline Test Suite Summary

- **Total Automated Tests:** 81
- **Passed:** 81 (100%)
- **Failed:** 0
- **Warnings:** 0
- **Test Categories:**
  - Machine Learning & Feature Leakage: 12 tests
  - Customer Group Isolation: 3 tests
  - Financial Precision (Decimal & Paise Quantization): 7 tests
  - Policy Engine & Governance: 7 tests
  - Security Boundary & Advisory Isolation: 6 tests
  - Tool Gateway & Canonical Idempotency: 4 tests
  - Verification Engine & Dual-Signal Agreement: 4 tests
  - State Machine & Hardening Transitions: 6 tests
  - Prompt Injection Defense: 2 tests
  - Provenance Chain & Telemetry: 3 tests
  - Webhooks (HMAC SHA-256 & Idempotency): 4 tests
  - Simulator & Synthetic Data Integrity: 3 tests

---

## 2. Existing System Architecture

RAY is an AI-native financial recovery orchestration system designed around Razorpay payment failures, checkout abandonments, and subscription recovery.

The central architectural invariant is:
```text
PREDICTION != RECOMMENDATION != AUTHORIZATION != EXECUTION != VERIFICATION
```

### Core Subsystems:
1. **Advisory Multi-Agent Reasoning Plane:**
   - `RevenueDetective`: Identifies financial opportunity, requests calibrated recoverability score, computes expected recovery using Python `Decimal`.
   - `DiagnosisAgent`: Categorizes root causes (`TRANSIENT`, `TIMEOUT`, `BANK_UNAVAILABLE`, `PERMANENT`, `ABANDONMENT`, etc.) using structured evidence.
   - `RecoveryPlanner`: Computes expected value $EV = (P \times \text{amount}) - \text{cost} - \text{risk}$ and recommends candidate recovery strategies.
   - `ExecutionAgent`: Converts authorized decisions into strict `ToolCallRequest` instances directed exclusively to the Tool Gateway.
2. **Deterministic Governance & Authorization Plane:**
   - `PolicyEngine`: Absolute deterministic authority over execution. Enforces:
     - `MAX_RETRY_ATTEMPTS = 1`
     - Auto-retry ceiling: ₹10,000
     - High-value human gate: $\ge \text{₹}50,000$
     - Customer opt-out compliance
   - `HumanApprovalRecord`: Immutable audit records capturing operator approvals.
3. **Bounded Tool Gateway:**
   - Enforces pre-execution validation: case existence, decision existence, authorization status, parameter bounds, and canonical idempotency key check.
   - Canonical idempotency format: `ray:{case_id}:{strategy}:{attempt_number}`.
4. **Independent Verification Plane:**
   - `VerificationEngine`: Dual-signal corroboration:
     - Signal A: Provider API status polling (`status == 'captured'`)
     - Signal B: Webhook HMAC-SHA256 signature payload confirmation
   - Cryptographic evidence hashing via SHA-256 canonical JSON.
   - Conflict escalation: Mismatched signals transition case to `HUMAN_REVIEW` with ₹0.00 verified revenue.

---

## 3. Existing API Endpoints

### Recovery Lifecycle & Control:
- `POST /api/v1/recovery/{case_id}/analyze`: Run Revenue Detective & Diagnosis Agent.
- `POST /api/v1/recovery/{case_id}/plan`: Generate candidate strategy proposal via Recovery Planner.
- `POST /api/v1/recovery/{case_id}/execute`: Dispatch authorized action through Tool Gateway.
- `POST /api/v1/recovery/{case_id}/verify`: Verify financial outcome via Dual-Signal Engine.

### Financial Provenance & Audit:
- `GET /api/v1/recovery/{case_id}/timeline`: Retrieve chronological audit and agent step timeline.
- `GET /api/v1/recovery/{case_id}/decision`: Retrieve advisory recommendation and policy assessment.
- `GET /api/v1/recovery/{case_id}/execution`: Retrieve Tool Gateway execution record and provider hash.
- `GET /api/v1/recovery/{case_id}/verification`: Retrieve dual-signal verification proof and evidence hash.
- `GET /api/v1/cases/{case_id}/events`: Server-Sent Events (SSE) live streaming timeline.

### Analytics & Simulation:
- `GET /api/v1/analytics/overview`: Financial summary (revenue at risk, expected recovery, verified recovered).
- `POST /api/v1/simulator/run`: Execute 3-way ablation simulation (`Baseline`, `Rule RAY`, `ML RAY`).
- `POST /api/v1/webhooks/razorpay`: Razorpay webhook ingestion with HMAC-SHA256 validation.

---

## 4. Existing ML Model Metrics (Held-Out Test Set)

Evaluated on 1,896 unseen test transactions across 374 isolated customer groups:

- **Primary Ranking (PR-AUC):** 0.8602
- **Discrimination (ROC-AUC):** 0.8682
- **Calibration (Brier Score):** 0.1372 (Platt Sigmoid scaling)
- **Log Loss:** 0.4307
- **Case Precision:** 80.19%
- **Case Recall:** 87.09%
- **F1-Score:** 0.8350
- **Revenue-Weighted Recall:** 95.0% - 95.18%

---

## 5. Existing Simulator & Benchmark Metrics

Comparison across 1,896 held-out test cases (₹37,808,252 at risk):

| Mode | Attempted | Recovered (INR) | Recovery Rate | False Interventions | Net Economic Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline (Naive Always-Retry)** | 1,896 | ₹4,387,269 | 11.6% | 1,393 (73.5% waste) | ₹4,270,219 |
| **Rule-Based RAY** | 1,330 | ₹26,893,292 | 71.1% | 328 (24.7% waste) | ₹26,843,642 |
| **ML-Assisted RAY** | 1,281 | ₹26,533,316 | 70.2% | 303 (23.6% waste) | ₹26,486,141 |

---

## 6. Known Limitations & Constraints

1. **Synthetic Training Data:**
   - Training and validation datasets were synthesized using probabilistic behavioral distributions modeled after typical Indian merchant payment gateways.
2. **Test Mode Integration:**
   - Live provider interactions are restricted to Razorpay Test Mode keys (`rzp_test_...`). Real bank settlement and production card networks are not processed.
3. **Local LLM Fallback:**
   - In environments without an active Ollama instance, the system seamlessly defaults to `MockLLMProvider`, preserving deterministic evaluation.
