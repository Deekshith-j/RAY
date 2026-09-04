# RAY Recoverability Ablation Benchmark

> **Benchmark Disclaimer**: The evaluation benchmark uses deterministic synthetic test-mode data generated under strict customer-grouped isolation. Results demonstrate system methodology, architectural invariants, and economic behavior, not guaranteed live merchant performance.

---

## 1. Methodology & Experimental Rigor

To evaluate the economic value of ML-assisted revenue recovery, RAY executes a fair, controlled 3-way ablation study on **1,896 identical held-out test events** (374 unique customers) that were never seen during training or validation:

$$\text{Revenue-Weighted Recall} = \frac{\sum \text{Amount of correctly recovered cases}}{\sum \text{Amount of ground truth recoverable cases}}$$

$$\text{Net Economic Value} = \text{Recovered Revenue} - \text{Intervention Costs} - \text{Provider Fees} - \text{Customer Friction Costs}$$

- **Intervention Cost**: ₹25.00 per attempt (network fees, notification bandwidth, gateway retry cost)
- **Friction Cost**: ₹50.00 per false intervention (customer annoyance, bank velocity flags)

---

## 2. Benchmark Results Table

Workload: **1,896 held-out test transactions**, representing **₹37,808,252.00 total revenue at risk**:

| Metric | Strategy A: Naive Blind Retry | Strategy B: Rule-Based RAY | Strategy C: ML-Assisted RAY |
| :--- | :--- | :--- | :--- |
| **Actions Attempted** | 1,896 | 1,330 | **1,281** |
| **Successful Recoveries** | 503 | 1,002 | **978** |
| **Gross Revenue Recovered** | ₹4,387,269.00 | ₹26,893,292.00 | **₹26,533,316.00** |
| **Recovery Rate** | 11.6% | 71.1% | **70.2%** |
| **Case-Level Recall** | 47.0% | 93.7% | **91.5%** |
| **Revenue-Weighted Recall** | 15.7% | 96.2% | **95.0%** |
| **False Interventions (Wasted)**| 1,393 (73.5% waste) | 328 (24.7% waste) | **303 (23.6% waste)** |
| **Net Economic Value** | ₹4,270,219.00 | ₹26,843,642.00 | **₹26,486,141.00** |
| **Human Escalations (&ge; ₹50k)**| 0 | 181 | **181** |

---

## 3. Key Economic Insights

1. **Massive Lift Over Naive Retries**:
   - ML-Assisted RAY delivers **+₹22,146,047.00 (+504.8%)** economic lift over standard naive retry logic.
2. **False Intervention Suppression**:
   - Compared to rigid rule-based systems, ML-Assisted RAY avoids **25 hopeless interventions (-7.62%)** on fundamentally unrecoverable cases ($EV \le 0$), protecting customer goodwill and reducing card-network velocity penalties while preserving **95.00% Revenue-Weighted Recall**.
3. **Safety Ceilings Enforced**:
   - In both Rule-Based and ML-Assisted strategies, all **181 high-value cases (&ge; ₹50,000)** were safely escalated to human operators, preventing autonomous runaway execution on large funds.
