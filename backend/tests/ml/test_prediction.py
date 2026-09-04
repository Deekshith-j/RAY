import pytest
from decimal import Decimal
from app.ml.schemas import (
    calculate_expected_recovery,
    RecoverabilityBand,
    RecoverabilityPrediction,
)
from app.ml.predict import get_recoverability_band, generate_feature_explanations


def test_decimal_expected_recovery_calculation():
    amount = 10000.0
    full_precision_prob = 0.823456789

    expected = calculate_expected_recovery(amount, full_precision_prob)

    assert isinstance(expected, Decimal)
    # Expected: 10000 * 0.823456789 = 8234.56789 -> 8234.57 quantized
    assert expected == Decimal("8234.57")
    # Expected recovery must never exceed amount at risk
    assert expected <= Decimal(str(amount))


def test_recoverability_band_classification():
    assert get_recoverability_band(0.92) == RecoverabilityBand.HIGH
    assert get_recoverability_band(0.85) == RecoverabilityBand.HIGH
    assert get_recoverability_band(0.84) == RecoverabilityBand.MEDIUM
    assert get_recoverability_band(0.60) == RecoverabilityBand.MEDIUM
    assert get_recoverability_band(0.59) == RecoverabilityBand.LOW
    assert get_recoverability_band(0.12) == RecoverabilityBand.LOW


def test_deterministic_feature_explanations():
    features = {
        "failure_type": "network_error",
        "customer_success_rate": 0.95,
        "previous_payment_count": 10,
        "retry_count": 0,
        "amount": 2500.0,
    }

    explanations = generate_feature_explanations(features, 0.92)
    assert len(explanations) >= 1
    # Check that network error is flagged as positive transient
    ft_exp = [e for e in explanations if e.feature_name == "failure_type"]
    assert len(ft_exp) == 1
    assert ft_exp[0].impact == "positive"
