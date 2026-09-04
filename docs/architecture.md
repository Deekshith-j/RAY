# RAY System Architecture

## 1. Core Architectural Principle

The central invariant of RAY is:

$$\text{PREDICTION} \neq \text{RECOMMENDATION} \neq \text{POLICY AUTHORIZATION} \neq \text{EXECUTION} \neq \text{INDEPENDENT VERIFICATION} \neq \text{VERIFIED REVENUE}$$

Every layer has a strictly bounded responsibility. Advisory components cannot authorize or execute; execution components cannot verify; only independent verification can mark revenue as recovered.

---

## 2. Conceptual Workflow Diagram

```mermaid
flowchart TD
    A[Payment Failure / Event] --> B[Revenue Detective]
    B --> C[Recoverability ML Model]
    C --> D[Diagnosis Agent]
    D --> E[Recovery Planner]
    E --> F[DETERMINISTIC POLICY ENGINE]
    
    F -->|Requires Approval| G[HUMAN APPROVAL GATE]
    G -->|Approved by Operator| H[Tool Gateway]
    G -->|Rejected / Pending| I[STOPPED / HUMAN_REVIEW]
    
    F -->|Allowed| H[Tool Gateway]
    F -->|Denied| I
    
    H --> J[Razorpay Adapter Protocol]
    J --> K[Execution via Provider]
    K --> L[VERIFICATION ENGINE]
    
    L --> M[Signal A: Provider API State]
    L --> N[Signal B: Webhook HMAC Payload]
    
    M & N --> O{Signals Agree & Amount Matches?}
    O -->|YES: Dual Verified| P[RECOVERED State & Verified Revenue > 0]
    O -->|NO: Conflict| Q[HUMAN_REVIEW State & Verified Revenue = 0]
```

---

## 3. Subsystem Breakdown

### 3.1 Advisory Multi-Agent Layer
- **Revenue Detective:** Extracts features, queries ML model for $P(\text{recovery})$, computes expected recovery in Python `Decimal`.
- **Diagnosis Agent:** Identifies failure category (`TRANSIENT`, `TIMEOUT`, `BANK_UNAVAILABLE`, `PERMANENT`, `ABANDONMENT`, etc.) and structured evidence.
- **Recovery Planner:** Ranks candidate recovery strategies by Expected Value:
  $$EV = P(\text{success} \mid \text{action}) \times \text{amount} - \text{cost} - \text{penalty}$$
  Outputs an advisory proposal (does not authorize or execute).
- **Execution Agent:** Converts approved decisions into strongly-typed `ToolCallRequest` schemas for the Tool Gateway.

### 3.2 Deterministic Governance & Policy Engine
- Absolute authority over all recovery actions.
- Rules:
  - `MAX_RETRY_ATTEMPTS = 1`
  - Auto-retry ceiling: ₹10,000
  - High-value human gate: $\ge \text{₹}50,000$
  - Customer opt-outs strictly honored.
- Rejection or human gating cannot be overridden by any agent or prompt injection.

### 3.3 Tool Gateway & Idempotency
- Single entry point for financial execution.
- Canonical idempotency key: `ray:{case_id}:{strategy}:{attempt_number}`.
- Replays return cached results with zero duplicate provider calls.

### 3.4 Verification Engine & Cryptographic Evidence
- Requires two independent signals:
  1. API Polling: `status == 'captured'`
  2. Webhook: HMAC-SHA256 signature verification + event payload match
- Generates SHA-256 evidence hash from canonical JSON payload.
- In case of disagreement, case escalates to `HUMAN_REVIEW` with `verified_amount = 0.00`.
