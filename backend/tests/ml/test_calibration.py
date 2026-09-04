import pytest
import numpy as np
from sklearn.linear_model import LogisticRegression
from app.ml.calibration import train_calibrated_model, evaluate_calibration_quality


def test_calibration_zero_leakage():
    # Synthetic training data
    np.random.seed(42)
    X_train = np.random.randn(200, 5)
    y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(int)

    base = LogisticRegression()

    # Train calibrated model strictly on X_train, y_train
    calibrated = train_calibrated_model(base, X_train, y_train, method="sigmoid", cv=3)

    # Test that predictions are strictly bounded probabilities
    probs = calibrated.predict_proba(X_train)[:, 1]
    assert np.all(probs >= 0.0)
    assert np.all(probs <= 1.0)

    # Evaluate calibration curve
    eval_result = evaluate_calibration_quality(y_train, probs, probs)
    assert "brier_uncalibrated" in eval_result
    assert "brier_calibrated" in eval_result
    assert eval_result["brier_calibrated"] >= 0.0
