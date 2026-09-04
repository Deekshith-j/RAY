"""Tests for ML Model Monitoring, Telemetry, and Drift Warning."""

from decimal import Decimal
from app.ml.monitoring import ModelDriftDetector, ModelTelemetry, calculate_recovery_priority_score


def test_model_telemetry_tracking():
    telemetry = ModelTelemetry()
    telemetry.record_prediction(0.88, Decimal("1000.00"), "HIGH")
    telemetry.record_prediction(0.70, Decimal("500.00"), "MEDIUM")
    telemetry.record_prediction(0.40, Decimal("200.00"), "LOW")

    summary = telemetry.get_summary()
    assert summary["prediction_count"] == 3
    assert summary["band_distribution"]["HIGH"] == 1
    assert summary["band_distribution"]["MEDIUM"] == 1
    assert summary["band_distribution"]["LOW"] == 1
    assert summary["average_probability"] > 0.60


def test_model_drift_detection_warning():
    detector = ModelDriftDetector(drift_threshold_z=2.0)

    # Normal baseline distribution features
    normal_batch = [
        {"amount": 25000.0, "customer_success_rate": 0.82} for _ in range(10)
    ]
    res_normal = detector.check_feature_drift(normal_batch)
    assert res_normal["drift_detected"] is False
    assert res_normal["warning"] is None

    # Severely shifted distribution features (10x amount, low success rate)
    drifted_batch = [
        {"amount": 500000.0, "customer_success_rate": 0.15} for _ in range(20)
    ]
    res_drift = detector.check_feature_drift(drifted_batch)
    assert res_drift["drift_detected"] is True
    assert "MODEL DRIFT WARNING" in res_drift["warning"]


def test_recovery_priority_scoring():
    # Case A: High expected recovery
    score_a = calculate_recovery_priority_score(amount=50000, probability=0.9, expected_recovery=45000)
    # Case B: Low expected recovery
    score_b = calculate_recovery_priority_score(amount=50000, probability=0.2, expected_recovery=10000)

    assert score_a > score_b
