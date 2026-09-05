
import pytest
import numpy as np
from app.ml.evaluate import calculate_metrics


def test_revenue_weighted_recall_distinction_from_case_recall():
    """
    Verify mathematical distinction between Case Recall and Revenue-Weighted Recall.
    Scenario:
    Case 1: ₹100,000 (Ground Truth Recoverable) -> Correctly predicted recoverable (True Positive)
    Case 2: ₹10,000  (Ground Truth Recoverable) -> Missed (False Negative)
    Case 3: ₹10,000  (Ground Truth Non-recoverable) -> Correctly predicted non-recoverable (True Negative)

    Case Recall = 1 / 2 = 50.0%
    Revenue-Weighted Recall = 100,000 / (100,000 + 10,000) = 100,000 / 110,000 = 90.91%
    """
    amounts = np.array([100000.0, 10000.0, 10000.0])
    y_true = np.array([1, 1, 0])
    y_prob = np.array([0.90, 0.20, 0.10])

    metrics = calculate_metrics(y_true, y_prob, threshold=0.5, amounts=amounts)

    # 1. Case-Level Recall
    assert metrics.recall == 0.50

    # 2. Revenue-Weighted Recall
    assert metrics.revenue_weighted_recall == 0.9091

    # Clearly distinguish that they are NOT equal
    assert metrics.revenue_weighted_recall > metrics.recall

    # Financial totals
    assert metrics.revenue_at_risk == 120000.0
    assert metrics.recovered_revenue == 100000.0
    assert metrics.revenue_recovery_rate == 83.33
