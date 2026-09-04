"""Probability calibration for RAY Recoverability Models.

CRITICAL INSTRUCTION:
Calibration must happen without validation/test leakage.
CalibratedClassifierCV uses internal K-Fold Cross-Validation STRICTLY on the training set.
"""

from typing import Tuple, Dict, Any
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss

from app.ml.config import ml_config


def train_calibrated_model(
    base_estimator,
    X_train: np.ndarray,
    y_train: np.ndarray,
    method: str = ml_config.CALIBRATION_METHOD,
    cv: int = ml_config.CALIBRATION_CV,
) -> CalibratedClassifierCV:
    """
    Fit calibrated classifier using strictly internal K-fold cross-validation
    on the training set only.
    Zero leakage into validation or test sets.
    """
    calibrated = CalibratedClassifierCV(
        estimator=base_estimator,
        method=method,
        cv=cv,
    )
    calibrated.fit(X_train, y_train)
    return calibrated


def evaluate_calibration_quality(
    y_true: np.ndarray,
    y_prob_uncalibrated: np.ndarray,
    y_prob_calibrated: np.ndarray,
    n_bins: int = 10,
) -> Dict[str, Any]:
    """
    Compare uncalibrated vs calibrated probabilities:
    - Brier score reduction
    - Reliability curve bin points
    """
    brier_uncal = float(brier_score_loss(y_true, y_prob_uncalibrated))
    brier_cal = float(brier_score_loss(y_true, y_prob_calibrated))
    brier_improvement = round(brier_uncal - brier_cal, 4)

    prob_true_uncal, prob_pred_uncal = calibration_curve(y_true, y_prob_uncalibrated, n_bins=n_bins, strategy="uniform")
    prob_true_cal, prob_pred_cal = calibration_curve(y_true, y_prob_calibrated, n_bins=n_bins, strategy="uniform")

    return {
        "brier_uncalibrated": round(brier_uncal, 4),
        "brier_calibrated": round(brier_cal, 4),
        "brier_improvement": brier_improvement,
        "is_improved": brier_cal <= brier_uncal,
        "uncalibrated_curve": {
            "mean_predicted_prob": [round(float(p), 4) for p in prob_pred_uncal],
            "fraction_of_positives": [round(float(p), 4) for p in prob_true_uncal],
        },
        "calibrated_curve": {
            "mean_predicted_prob": [round(float(p), 4) for p in prob_pred_cal],
            "fraction_of_positives": [round(float(p), 4) for p in prob_true_cal],
        },
    }
