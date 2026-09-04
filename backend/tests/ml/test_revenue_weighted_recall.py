"""Revenue-Weighted Recall Edge Case Tests per Section 7 & 24.

Formula:
Revenue Recall = sum(amount for correctly recovered recoverable cases) / sum(amount for all recoverable cases)

Verifies:
- Division-by-zero protection when total recoverable revenue is zero
- 100% revenue recall when all recoverable cases are captured
- 0% revenue recall when all recoverable cases are missed
- Proper separation from unrecoverable transactions
"""

import pytest
import numpy as np
from app.ml.evaluate import calculate_metrics


def test_revenue_weighted_recall_zero_recoverable_cases():
    """Verify division-by-zero safety when no cases in evaluation set are recoverable."""
    amounts = np.array([5000.0, 10000.0, 15000.0])
    y_true = np.array([0, 0, 0])  # None are recoverable!
    y_prob = np.array([0.1, 0.2, 0.3])

    metrics = calculate_metrics(y_true, y_prob, threshold=0.5, amounts=amounts)

    assert metrics.revenue_weighted_recall == 0.0
    assert metrics.recovered_revenue == 0.0
    assert metrics.revenue_at_risk == 30000.0


def test_revenue_weighted_recall_perfect_capture():
    """Verify 100% revenue recall when all high-value recoverable cases are captured."""
    amounts = np.array([50000.0, 75000.0, 25000.0, 5000.0])
    y_true = np.array([1, 1, 1, 0])
    y_prob = np.array([0.95, 0.90, 0.85, 0.10])

    metrics = calculate_metrics(y_true, y_prob, threshold=0.5, amounts=amounts)

    assert metrics.revenue_weighted_recall == 1.0
    assert metrics.recovered_revenue == 150000.0
    assert metrics.revenue_at_risk == 155000.0


def test_revenue_weighted_recall_zero_capture():
    """Verify 0% revenue recall when all recoverable cases are missed."""
    amounts = np.array([50000.0, 75000.0, 25000.0])
    y_true = np.array([1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3])  # All below threshold 0.5

    metrics = calculate_metrics(y_true, y_prob, threshold=0.5, amounts=amounts)

    assert metrics.revenue_weighted_recall == 0.0
    assert metrics.recovered_revenue == 0.0
