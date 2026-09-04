# Bounded Multi-Agent Architecture

## 1. Architectural Philosophy

RAY implements **bounded agents**. Agents reason, analyze, and propose actions, but they are architecturally barred from direct financial execution.

```text
Revenue Detective
       ↓
Diagnosis Agent
       ↓
Recovery Planner
       ↓
Deterministic Policy Engine
       ↓
[Human Approval if >= ₹50,000]
       ↓
Execution Agent
       ↓
Tool Gateway
```

---

## 2. Agent Responsibilities

### Agent 1: Revenue Detective
- **Role:** Opportunity Identification & Valuation.
- **Inputs:** Case ID, Payment/Order/Subscription metadata, Customer history.
- **Outputs:** `RevenueOpportunity` schema (amount at risk, ML probability, expected recovery in `Decimal`, recoverability band).
- **Boundary:** Cannot authorize, modify amounts, or invoke external tools.

### Agent 2: Diagnosis Agent
- **Role:** Root-Cause Analysis.
- **Inputs:** `RevenueOpportunity`, failure description, provider error code.
- **Outputs:** `DiagnosisOutput` (failure class: `TRANSIENT`, `TIMEOUT`, `BANK_UNAVAILABLE`, `PERMANENT`, `ABANDONMENT`, confidence score, structured evidence list).
- **Boundary:** Purely advisory. Disallowed from making decisions.

### Agent 3: Recovery Planner
- **Role:** Strategy Optimization.
- **Candidate Strategies:** `RETRY`, `PAYMENT_LINK`, `SUBSCRIPTION_RECOVERY`, `CUSTOMER_NOTIFICATION`, `NO_ACTION`, `HUMAN_REVIEW`.
- **Logic:** Evaluates Expected Economic Value $EV = (P \times \text{amount}) - \text{cost} - \text{penalty}$.
- **Outputs:** `RecoveryPlanOutput` (recommended strategy, rationale, expected recovery).
- **Boundary:** Proposes only. Passes recommendation to the Policy Engine for deterministic authorization.

### Agent 4: Execution Agent
- **Role:** Tool Request Construction.
- **Inputs:** Authorized `RecoveryDecision` and case details.
- **Outputs:** `ToolCallRequest` targeted exclusively to `ToolGateway`.
- **Boundary:** Does not import or communicate with payment provider SDKs directly.

---

## 3. Execution Safety Controls

- **Step Limit:** Enforces `MAX_AGENT_STEPS = 12`. The orchestrator terminates if step limits are reached to eliminate infinite loops or circular delegations.
- **Structured Pydantic Validation:** All agent outputs are parsed into strict Pydantic schemas. Malformed or hallucinated strategies are rejected immediately and escalated to `HUMAN_REVIEW`.
- **LLM Provider Abstraction:**
  - `MockLLMProvider`: Deterministic offline execution for automated testing and CI/CD.
  - `OllamaLLMProvider`: Local open-weight LLM execution via Ollama (e.g. Llama 3 / Mistral).
