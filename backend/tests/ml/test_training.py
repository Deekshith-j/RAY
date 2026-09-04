import pytest
from app.ml.dataset import build_reproducible_dataset
from app.ml.train import train_and_select_model


def test_model_training_and_metrics_validity():
    # Train on a small fast batch for testing
    splits = build_reproducible_dataset(total_events=600, seed=42)

    best_model, preprocessor, meta, comparison = train_and_select_model(splits, seed=42)

    assert best_model is not None
    assert preprocessor.is_fitted is True
    assert len(comparison) >= 2  # At least Logistic Regression and Random Forest

    # Verify that PR-AUC and ROC-AUC are valid probabilities within [0, 1]
    for c in comparison:
        assert 0.0 <= c.validation_pr_auc <= 1.0
        assert 0.0 <= c.validation_roc_auc <= 1.0
        assert 0.0 <= c.validation_brier_score <= 1.0
        assert 0.0 <= c.calibrated_brier_score <= 1.0

    # Verify that the selected model has the highest validation PR-AUC
    selected = [c for c in comparison if c.selected_for_production]
    assert len(selected) == 1

    max_pr_auc = max(c.validation_pr_auc for c in comparison)
    assert selected[0].validation_pr_auc == max_pr_auc

    # Verify metadata fields
    assert meta.train_size > 0
    assert meta.validation_size > 0
    assert meta.test_size > 0
    assert "pr_auc" in meta.test_metrics
    assert 0.0 <= meta.test_metrics["pr_auc"] <= 1.0
