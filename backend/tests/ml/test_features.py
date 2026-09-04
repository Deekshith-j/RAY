import pytest
from app.ml.features import extract_features_from_case, build_customer_history_map


def test_feature_extraction_types_and_defaults():
    case = {
        "id": "c1",
        "customer_id": "cust_123",
        "amount_at_risk": 15000.0,
        "failure_type": "timeout",
        "entity_type": "PAYMENT",
        "retry_count": 1,
    }

    features = extract_features_from_case(case)

    assert isinstance(features["amount"], float)
    assert features["amount"] == 15000.0
    assert features["failure_type"] == "timeout"
    assert features["retry_count"] == 1
    assert features["merchant_baseline_failure_rate"] == 0.15
    assert features["customer_success_rate"] >= 0.0


def test_customer_history_mapping():
    customers = [{"id": "cust_1", "customer_age_days": 120}]
    payments = [
        {"id": "p1", "customer_id": "cust_1", "amount": 1000.0, "status": "captured"},
        {"id": "p2", "customer_id": "cust_1", "amount": 2000.0, "status": "failed"},
    ]
    orders = []

    history = build_customer_history_map(customers, payments, orders)

    assert "cust_1" in history
    assert history["cust_1"]["total_attempts"] == 2
    assert history["cust_1"]["successes"] == 1
    assert history["cust_1"]["failures"] == 1
    assert history["cust_1"]["lifetime_value"] == 1000.0
