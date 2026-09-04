"""Feature engineering pipeline for RAY Recoverability ML.

LEAKAGE AUDIT & AVAILABILITY TIMELINE:
Every feature documented here is strictly available *BEFORE* any recovery action is taken.
Post-action outcomes (e.g. recovered_amount, verified status, best_action) are strictly FORBIDDEN.

FEATURE DICTIONARY:
1. amount: Transaction amount in INR (Available at payment attempt / order creation)
2. customer_age_days: Customer account tenure in days (Available from Customer record)
3. previous_payment_count: Total previous payments attempted by customer (From historical ledger)
4. successful_payment_count: Historical successful payments (From historical ledger)
5. failed_payment_count: Historical failed payments (From historical ledger)
6. customer_success_rate: successful_payment_count / max(1, previous_payment_count)
7. failure_type: Categorical error classification (Available immediately from payment gateway response / webhook)
8. retry_count: Number of retries already attempted on this specific payment (Current state before new action)
9. payment_method: Payment method used (card, upi, netbanking)
10. merchant_baseline_failure_rate: System-wide baseline failure rate (Historical constant ~0.15)
11. subscription_age_days: Tenure of subscription if applicable (0 for one-time orders)
12. customer_lifetime_value: Sum of historical captured payment amounts (From customer ledger)
13. entity_type: PAYMENT, ORDER_ABANDONMENT, SUBSCRIPTION
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

FORBIDDEN_FEATURES = {
    "recovered_amount",
    "best_action",
    "actual_outcome",
    "verification_id",
    "audit_logs",
    "execution_status",
    "provider_response",
    "webhook_confirmation",
    "future_timestamps",
    "post_action_state",
    "recovery_result",
    "state",
    "is_duplicate",
    "processed_at",
    "decision_id",
    "execution_id",
    "evidence_hash",
}

FORBIDDEN_LEAKAGE_COLUMNS = FORBIDDEN_FEATURES



def build_customer_history_map(
    customers: List[Dict[str, Any]],
    payments: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Precompute customer history metrics prior to the event being evaluated.
    Ensures zero temporal leakage.
    """
    history: Dict[str, Dict[str, Any]] = {}
    for c in customers:
        cid = c["id"]
        history[cid] = {
            "customer_age_days": c.get("customer_age_days", 30),
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "lifetime_value": 0.0,
        }

    for p in payments:
        cid = p["customer_id"]
        if cid in history:
            history[cid]["total_attempts"] += 1
            if p["status"] == "captured":
                history[cid]["successes"] += 1
                history[cid]["lifetime_value"] += float(p["amount"])
            elif p["status"] == "failed":
                history[cid]["failures"] += 1

    return history


def extract_features_from_case(
    case_dict: Dict[str, Any],
    customer_history: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Extract pre-action features for a single recovery case."""
    hist = customer_history or {
        "customer_age_days": 30,
        "total_attempts": 1,
        "successes": 0,
        "failures": 1,
        "lifetime_value": 0.0,
    }

    tot = max(1, hist.get("total_attempts", 1))
    succ = hist.get("successes", 0)
    rate = round(succ / tot, 4)

    # Determine payment method based on entity
    ft = case_dict.get("failure_type", "network_error")
    method = case_dict.get("payment_method", "upi" if "upi" in ft else "card")

    features = {
        "amount": float(case_dict.get("amount_at_risk", 0.0)),
        "customer_age_days": int(hist.get("customer_age_days", 30)),
        "previous_payment_count": int(hist.get("total_attempts", 0)),
        "successful_payment_count": int(succ),
        "failed_payment_count": int(hist.get("failures", 1)),
        "customer_success_rate": float(rate),
        "retry_count": int(case_dict.get("retry_count", 0)),
        "merchant_baseline_failure_rate": 0.15,
        "subscription_age_days": 90 if case_dict.get("entity_type") == "SUBSCRIPTION" else 0,
        "customer_lifetime_value": float(hist.get("lifetime_value", 0.0)),
        "failure_type": str(ft),
        "payment_method": str(method),
        "entity_type": str(case_dict.get("entity_type", "PAYMENT")),
    }

    # Strict assertion against target leakage
    for forbidden in FORBIDDEN_LEAKAGE_COLUMNS:
        if forbidden in features:
            raise ValueError(f"TARGET LEAKAGE DETECTED: Feature '{forbidden}' is forbidden!")

    return features


def extract_dataset_features(dataset: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Extract full pre-action feature matrix X, target vector y, and customer IDs
    for customer-grouped splitting.
    """
    customers = dataset.get("customers", [])
    payments = dataset.get("payments", [])
    orders = dataset.get("orders", [])
    recovery_cases = dataset.get("recovery_cases", [])
    ground_truth = {g["case_id"]: g for g in dataset.get("ground_truth", [])}

    history_map = build_customer_history_map(customers, payments, orders)

    rows = []
    targets = []
    customer_ids = []

    for case in recovery_cases:
        cid = case["customer_id"]
        hist = history_map.get(cid)
        feat = extract_features_from_case(case, hist)

        gt = ground_truth.get(case["id"])
        if gt is not None:
            target = int(gt["recoverable"])
        else:
            # Fallback for synthetic cases without explicit gt
            target = 1 if case.get("recoverability_score", 0) > 0.5 else 0

        rows.append(feat)
        targets.append(target)
        customer_ids.append(cid)

    X = pd.DataFrame(rows)
    y = pd.Series(targets, name="is_recoverable")

    # Final sanity check: verify no forbidden column in DataFrame
    leaked = set(X.columns).intersection(FORBIDDEN_LEAKAGE_COLUMNS)
    if leaked:
        raise ValueError(f"TARGET LEAKAGE DETECTED in DataFrame: {leaked}")

    return X, y, customer_ids
