# Machine Learning Pipeline & Recoverability Modeling

## 1. Objective

The ML subsystem estimates $P(\text{recovery} \mid \text{pre-action context})$. It informs opportunity prioritization and expected value optimization. It never authorizes or executes actions directly.

---

## 2. Customer Group Isolation

To prevent data leakage caused by customer-level correlations, dataset splitting strictly partitions unique `customer_id` sets:
$$\text{TRAIN} \cap \text{VALIDATION} = \emptyset, \quad \text{TRAIN} \cap \text{TEST} = \emptyset, \quad \text{VALIDATION} \cap \text{TEST} = \emptyset$$

- **Train Set:** 70% of customer groups (8,784 samples, 1,740 customers)
- **Validation Set:** 15% of customer groups (1,820 samples, 372 customers)
- **Test Set:** 15% of customer groups (1,896 samples, 374 customers)

Verified via automated test: `backend/tests/ml/test_customer_group_isolation.py`.

---

## 3. Strict Feature Leakage Prevention

The feature extractor enforces a strict prohibition against post-action and target-correlated features:

```python
FORBIDDEN_FEATURES = {
    "recovered_amount",
    "best_action",
    "actual_outcome",
    "verification_id",
    "verification_status",
    "audit_logs",
    "execution_status",
    "execution_id",
    "post_action_state",
    "future_timestamp",
}
```

Only pre-action observations (e.g. `amount`, `customer_age_days`, `previous_payment_count`, `failure_type`, `payment_method`, `retry_count`) are allowed. Verified via `backend/tests/ml/test_no_target_leakage.py`.

---

## 4. Financial Precision

All expected recovery and monetary aggregations strictly use Python `Decimal` with commercial `ROUND_HALF_UP` paise quantization:

```python
from decimal import Decimal, ROUND_HALF_UP

expected_recovery = (
    Decimal(str(amount)) * Decimal(str(probability))
).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

Probabilities are never rounded prematurely before multiplication.

---

## 5. Recoverability Bands

Thresholds are centralized in `app/ml/config.py`:
- **HIGH:** $\ge 0.85$
- **MEDIUM:** $\ge 0.60$ and $< 0.85$
- **LOW:** $< 0.60$

Deterministic logic assigns bands; LLMs are never permitted to define bands.

---

## 6. Revenue-Weighted Evaluation Metrics

In financial recovery, recovering a ₹50,000 transaction is 100x more valuable than recovering a ₹500 transaction. RAY calculates Revenue-Weighted Recall alongside ordinary case-level metrics:

$$\text{Revenue Recall} = \frac{\sum \text{amount of correctly recovered recoverable cases}}{\sum \text{amount of all recoverable cases}}$$

### Test Set Performance:
- **PR-AUC:** 0.8602
- **ROC-AUC:** 0.8682
- **Brier Score:** 0.1372 (Platt Sigmoid calibrated)
- **Case Precision:** 80.19%
- **Case Recall:** 87.09%
- **F1-Score:** 0.8350
- **Revenue Recall:** 95.0% - 95.18%
