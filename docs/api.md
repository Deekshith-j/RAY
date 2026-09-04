# RAY REST API Reference

All endpoints return JSON responses with standard HTTP status codes.

---

## 1. System & Health

### `GET /health`
Inspects subsystem operational health without exposing secrets or credentials.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "app": "RAY — Autonomous Revenue Recovery & Verification Engine",
  "environment": "development",
  "database": "healthy",
  "redis": "healthy",
  "ml_model": "loaded",
  "payment_provider": "razorpay_test_mode",
  "llm_provider": "mock",
  "verification_engine": "healthy"
}
```

---

## 2. Recovery Orchestration

### `POST /api/v1/recovery/{case_id}/run-full`
Executes complete end-to-end bounded recovery cycle:
Detective $\rightarrow$ Diagnosis $\rightarrow$ Planner $\rightarrow$ Policy $\rightarrow$ ToolGateway $\rightarrow$ Verification.

**Response (200 OK):**
```json
{
  "case_id": "PAY_DEMO_001",
  "case_state": "RECOVERED",
  "recovered_amount": 24999.00,
  "verified_amount": 24999.00,
  "opportunity": { ... },
  "diagnosis": { "diagnosis": "TRANSIENT_FAILURE", "confidence": 0.92 },
  "plan": { "recommended_strategy": "RETRY", "expected_recovery": 21999.12 },
  "policy": { "decision": "ALLOW", "policy_version": "v1.0" },
  "execution": { "execution_id": "exec_6099f4e120ca", "status": "SUCCESS" },
  "verification": { "verification_id": "verif_38dca47e", "status": "VERIFIED", "evidence_hash": "1a793836..." }
}
```

### `GET /api/v1/recovery/{case_id}/provenance`
Returns the cryptographic financial provenance chain:
Prediction $\rightarrow$ Decision $\rightarrow$ Execution $\rightarrow$ Verification.

**Response (200 OK):**
```json
{
  "case_id": "PAY_DEMO_001",
  "amount_at_risk": 24999.00,
  "recovered_amount": 24999.00,
  "state": "RECOVERED",
  "prediction": { "id": 1, "probability": 0.88, "recoverability_band": "HIGH" },
  "decision": { "id": "dec_...", "recommended_strategy": "RETRY", "policy_result": "ALLOW" },
  "execution": { "id": "exec_...", "operation": "retry_payment", "idempotency_key": "ray:PAY_DEMO_001:RETRY:1" },
  "verification": { "id": "verif_...", "verification_status": "VERIFIED", "evidence_hash": "1a793836..." },
  "provenance_chain_valid": true
}
```

### `GET /api/v1/recovery/{case_id}/timeline`
Returns chronological audit events and agent reasoning steps for real-time SSE feeds.

---

## 3. Human Authorization

### `POST /api/v1/cases/{case_id}/approve`
Records formal human operator authorization required for cases $\ge$ ₹50,000.

**Request Body:**
```json
{
  "case_id": "PAY_DEMO_HIGH_VALUE",
  "approved": true,
  "reviewer_name": "Ops Lead",
  "notes": "Verified enterprise bank transfer statement"
}
```

---

## 4. Webhook Ingestion

### `POST /webhooks/razorpay` (or `/api/v1/webhooks/razorpay`)
Accepts raw Razorpay webhook payloads. Enforces HMAC-SHA256 signature verification and idempotency duplicate rejection.

**Headers:**
- `x-razorpay-signature`: HMAC-SHA256 signature
- `x-razorpay-event-id`: Unique Razorpay event identifier

---

## 5. Machine Learning

### `POST /api/v1/ml/predict`
Advisory predict endpoint for transaction recoverability.

**Request Body:**
```json
{
  "amount": 24999.00,
  "failure_type": "timeout",
  "entity_type": "PAYMENT",
  "customer_id": "cust_123"
}
```

**Response (200 OK):**
```json
{
  "probability": 0.88,
  "recoverability_band": "HIGH",
  "expected_recovery": 21999.12,
  "model_version": "ray-recov-v1-production",
  "top_factors": [
    { "factor": "transient_timeout", "impact": "+0.32" }
  ]
}
```

---

## 6. Demo Environment Reset

### `POST /api/v1/demo/reset`
Purges temporary demonstration cases while preserving production ledger data. Active only when `DEMO_MODE=true`.

**Response (200 OK):**
```json
{
  "status": "success",
  "deleted_demo_cases": 5,
  "message": "Demo data reset successfully."
}
```
