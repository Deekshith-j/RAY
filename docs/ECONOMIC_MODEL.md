# RAY — Economic Model & Revenue Decision Framework

> [!IMPORTANT]
> **SYNTHETIC SIMULATION NOTICE**: All benchmark metrics, simulation rates, and test cases discussed in this document are derived from controlled, deterministic synthetic datasets. They illustrate algorithmic characteristics and do NOT represent actual Razorpay live production revenue.

---

## 1. Expected Value (EV) Formulation

In naive systems, recovery strategies are applied indiscriminately or through arbitrary heuristics, leading to customer fatigue, unnecessary gateway fees, and high false-intervention rates.

RAY optimizes recovery by evaluating the net Expected Value for candidate actions:

$$\text{EV}(\text{action}) = P(\text{success} \mid \text{action}, \text{context}) \times \text{Amount} - C_{\text{action}} - R_{\text{penalty}}$$

Where:
- $P(\text{success} \mid \text{action}, \text{context})$: Calibrated probability produced by the Recoverability ML model and adjusted by the Recovery Planner.
- $\text{Amount}$: Ground-truth transaction amount at risk (`Decimal`).
- $C_{\text{action}}$: Direct operational and gateway cost incurred by dispatching the recovery tool.
- $R_{\text{penalty}}$: Risk adjustment accounting for customer churn, contact frequency, or failure severity.

---

## 2. Parameter Specifications

### Direct Action Costs ($C_{\text{action}}$)

| Strategy | Direct Cost ($C$) | Description |
| :--- | :--- | :--- |
| `RETRY` | ₹1.50 | Server-to-server gateway retry fee and network overhead |
| `PAYMENT_LINK` | ₹3.00 | SMS/WhatsApp dispatch gateway and payment gateway link hosting |
| `SUBSCRIPTION_RECOVERY` | ₹2.00 | Recurring mandate re-trigger and dunning cycle check |
| `CUSTOMER_NOTIFICATION` | ₹0.50 | Automated email/push alert notification |
| `NO_ACTION` | ₹0.00 | Case dropped or left alone (zero financial cost) |
| `HUMAN_REVIEW` | ₹15.00 | Estimated operator review cost |

### Risk Penalties ($R_{\text{penalty}}$)

| Scenario / Risk Category | Penalty ($R$) | Rationale |
| :--- | :--- | :--- |
| High churn customer tier | ₹25.00 | Prevents irritating customers who have signaled cancellation intent |
| Medium churn customer tier | ₹5.00 | Mild dampening of aggressive contact strategies |
| Opted-out customer | $\infty$ | Hard policy veto (EV negative infinity) |
| Fraudulent transaction | $\infty$ | Hard policy veto (EV negative infinity) |

---

## 3. Evaluation Metrics

### 1. Revenue-Weighted Recall (RWR)
Standard unweighted recall treats a ₹100 failure equally with a ₹75,000 failure. RAY computes revenue-weighted recall to reflect true financial capture:

$$\text{Revenue-Weighted Recall} = \frac{\sum_{i \in \text{Recovered}} \text{Amount}_i}{\sum_{j \in \text{Ground-Truth Recoverable}} \text{Amount}_j}$$

In our held-out test evaluation:
- Unweighted Case Recall: **87.09%**
- Revenue-Weighted Recall: **95.00% – 95.18%**
*(The ML model prioritizes high-value recoverable opportunities, capturing significantly more value than unweighted accuracy suggests).*

### 2. False Intervention Rate (FIR)
Measures the proportion of interventions wasted on permanently dead payments:

$$\text{FIR} = \frac{\text{Interventions on Non-Recoverable Cases}}{\text{Total Actions Attempted}}$$

### 3. Net Economic Value (NEV)
The true bottom-line recovery figure after operational overhead:

$$\text{NEV} = \text{Verified Recovered Revenue} - \sum C_{\text{action}} - \sum R_{\text{penalty}}$$

---

## 4. Benchmark Performance Comparison (Synthetic 1,000-Case Cohort)

| Metric | Mode A: Naive Retry | Mode B: Rule-Based RAY | Mode C: ML-Assisted RAY |
| :--- | :--- | :--- | :--- |
| **Actions Attempted** | 1,000 | 788 | 763 |
| **Successful Recoveries** | 116 | 711 | 702 |
| **Recovery Rate** | 11.60% | 71.10% | 70.20% |
| **Wasted Interventions** | 735 | 195 | 180 |
| **False Intervention Rate** | 73.50% | 24.75% | **23.59%** |
| **Action Costs Incurred** | ₹1,500.00 | ₹1,182.00 | ₹1,144.50 |
| **Wasted Cost Reduction** | Baseline | -73.5% | **-75.5%** |

**Key Takeaway**: ML-Assisted RAY matches rule-based yield while eliminating 25 additional wasted interventions, reducing unnecessary payment retries on hopeless transactions and protecting merchant reputation.
