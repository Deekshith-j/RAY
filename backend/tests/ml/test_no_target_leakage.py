import pytest
from app.ml.features import (
    FORBIDDEN_LEAKAGE_COLUMNS,
    extract_features_from_case,
    extract_dataset_features,
)
from app.simulator.generator import SyntheticDataGenerator


def test_no_forbidden_columns_in_feature_extraction():
    """
    Strict Leakage Audit:
    Ensure that no future or post-action information can enter the feature set.
    """
    sample_case = {
        "id": "case_test_001",
        "customer_id": "cust_001",
        "amount_at_risk": 4999.0,
        "failure_type": "network_error",
        "entity_type": "PAYMENT",
        "retry_count": 0,
        # Ground truth / post-action fields that must NEVER leak into features
        "recovered_amount": 4999.0,
        "best_action": "RETRY",
        "actual_outcome": "recovered",
        "state": "RECOVERED",
        "verification_id": "evt_verified_123",
    }

    features = extract_features_from_case(sample_case)

    for forbidden in FORBIDDEN_LEAKAGE_COLUMNS:
        assert forbidden not in features, f"Target leakage: '{forbidden}' found in extracted features!"


def test_full_dataset_leakage_audit():
    """Verify that dataset feature matrix X contains zero post-action leakage columns."""
    gen = SyntheticDataGenerator(seed=42)
    dataset = gen.generate_dataset(total_events=200)

    X, y, customer_ids = extract_dataset_features(dataset)

    assert "is_recoverable" not in X.columns
    assert "recovered_amount" not in X.columns
    assert "best_action" not in X.columns
    assert "actual_outcome" not in X.columns
    assert "state" not in X.columns

    # Check intersection
    leaked = set(X.columns).intersection(FORBIDDEN_LEAKAGE_COLUMNS)
    assert len(leaked) == 0, f"Leaked columns found: {leaked}"
