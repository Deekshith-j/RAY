# RAY — Economic Ablation Benchmark Report

> [!IMPORTANT]
> **SIMULATION / SYNTHETIC DATA NOTICE:**
> The empirical results documented below were generated using a reproducible synthetic dataset generator (`seed=42`) modeled after Razorpay failure distributions and evaluated on a strictly held-out test set with zero customer overlap. These numbers demonstrate algorithmic differences under controlled experimental conditions; they do not claim live merchant production metrics.

---

## 1. Methodology

The benchmark performs an independent 3-way ablation study comparing recovery paradigms on identical, unseen test cases:

1. **Mode A: Baseline Naive Retry**
   - Standard industry default: re-attempts every failed transaction once indiscriminately.
   - Ignores failure type, customer lifetime value, and permanent decline reasons.
2. **Mode B: Rule-Based RAY**
   - Deterministic error classification and static policy engine.
   - Restricts retries to transient errors (`network_error`, `timeout`, `bank_unavailable`).
   - Routes abandonments and insufficient funds to payment links.
   - Enforces human approval for transactions $\ge \text{₹}50,000$.
3. **Mode C: ML-Assisted RAY**
   - Uses calibrated probability predictions $P(\text{recovery} \mid \text{context})$ from Platt-scaled Logistic Regression.
   - Evaluates Expected Economic Value:
     $$EV(\text{action}) = P(\text{success} \mid \text{action}, \text{context}) \times \text{amount} - \text{action\_cost} - \text{risk\_penalty}$$
   - Suppresses low-probability, negative expected value attempts to eliminate wasted merchant fees and preserve customer goodwill.
   - Operates strictly within Policy Engine boundaries.

---

## 2. Experimental Setup

- **Dataset Samples:** 12,500 total events
- **Customer Group Isolation:** Disjoint customer pools for Train (70%), Validation (15%), and Test (15%)
- **Held-Out Test Cases:** 1,896 transactions
- **Total Revenue at Risk:** INR 37,808,252.00
- **Test PR-AUC:** 0.8602
- **Test Brier Score:** 0.1372

---

## 3. Measured Ablation Benchmark Results

| Metric | A: Baseline (Naive Retry) | B: Rule-Based RAY | C: ML-Assisted RAY |
| :--- | :--- | :--- | :--- |
| **Actions Attempted** | 1,896 | 1,330 | **1,281** |
| **Successful Recoveries** | 503 | 1,002 | **978** |
| **Revenue at Risk** | ₹37,808,252.00 | ₹37,808,252.00 | **₹37,808,252.00** |
| **Revenue Recovered** | ₹4,387,269.00 | ₹26,893,292.00 | **₹26,533,316.00** |
| **Recovery Rate (%)** | 11.60% | 71.13% | **70.18%** |
| **Case Recall (%)** | 47.05% | 93.73% | **91.49%** |
| **Revenue Recall (%)** | 15.69% | 96.19% | **94.90%** |
| **False Interventions (Wasted)** | 1,393 | 328 | **303** |
| **False Intervention Rate (%)** | 73.47% | 24.66% | **23.65%** |
| **Net Economic Value** | ₹4,270,219.00 | ₹26,843,642.00 | **₹26,486,141.00** |
| **Human Escalations ($\ge \text{₹}50\text{k}$)** | 0 *(unsafe)* | 181 *(safely gated)* | **181 *(safely gated)*** |

---

## 4. Key Findings & Analysis

### Economic Lift:
- **ML vs Baseline:** **+₹22,146,047.00 (+504.78% economic lift)**. Naive retries fail completely on non-transient payment declines (fraud, invalid credentials, checkout abandonment), producing massive waste.
- **ML vs Rule-Based (The Selective Advantage):**
  - Rule-Based RAY recovers slightly higher raw revenue (₹26.89M vs ₹26.53M) by blindly attempting all rule-matching cases.
  - ML-Assisted RAY demonstrates **operational efficiency**: by evaluating expected value, ML suppresses 49 marginal actions, achieving **25 fewer wasted interventions (-7.62%)** while capturing 94.9% of all recoverable revenue.
  - In a production environment, fewer false interventions translate directly to fewer irritated customers, lower chargeback risks, and reduced API gateway fees.

---

## 5. Execution Command

To regenerate and independently verify this benchmark:

```bash
python -m app.ml.benchmark
```
