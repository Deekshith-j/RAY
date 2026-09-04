from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    auc,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    log_loss,
    confusion_matrix,
)
from app.ml.schemas import EvaluationMetrics


def calculate_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5,
    amounts: Optional[np.ndarray] = None,
) -> EvaluationMetrics:
    """
    Calculate comprehensive binary classification and calibration metrics.
    Emphasizes PR-AUC, Brier score, and Revenue-Weighted Recall.
    Distinguishes CASE RECALL from REVENUE-WEIGHTED RECALL.
    """
    y_pred = (y_prob >= threshold).astype(int)

    # 1. ROC-AUC
    try:
        roc = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        roc = 0.5

    # 2. PR-AUC
    precisions, recalls, _ = precision_recall_curve(y_true, y_prob)
    pr_auc_val = float(auc(recalls, precisions))

    # 3. Precision, Recall, F1 at threshold (CASE LEVEL)
    p = float(precision_score(y_true, y_pred, zero_division=0))
    r = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # 4. Calibration & Loss metrics
    brier = float(brier_score_loss(y_true, y_prob))
    try:
        lloss = float(log_loss(y_true, clipped_probs, labels=[0, 1]))
    except Exception:
        lloss = 0.5

    # 5. Confusion Matrix
    cm = confusion_matrix(y_true, y_pred).tolist()

    # 6. Operating Thresholds Analysis (e.g. 0.60, 0.75, 0.85)
    operating_thresholds = {}
    for thresh in [0.50, 0.60, 0.75, 0.85]:
        pred_t = (y_prob >= thresh).astype(int)
        operating_thresholds[str(thresh)] = {
            "precision": round(float(precision_score(y_true, pred_t, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, pred_t, zero_division=0)), 4),
            "f1": round(float(f1_score(y_true, pred_t, zero_division=0)), 4),
            "predicted_positive_rate": round(float(pred_t.mean()), 4),
        }

    # 7. Revenue-Weighted Financial Telemetry
    rev_weighted_recall = None
    rev_at_risk = None
    recovered_rev = None
    rev_recovery_rate = None
    exp_recovery = None
    avg_recovery_amt = None

    if amounts is not None and len(amounts) == len(y_true):
        amt_arr = np.asarray(amounts, dtype=float)
        total_recoverable_rev = float(np.sum(amt_arr[y_true == 1]))
        correctly_recovered_rev = float(np.sum(amt_arr[(y_true == 1) & (y_pred == 1)]))

        rev_weighted_recall = round(
            float(correctly_recovered_rev / max(1.0, total_recoverable_rev)), 4
        ) if total_recoverable_rev > 0 else 0.0

        rev_at_risk = round(float(np.sum(amt_arr)), 2)
        recovered_rev = round(correctly_recovered_rev, 2)
        rev_recovery_rate = round(float(recovered_rev / max(1.0, rev_at_risk) * 100.0), 2)
        exp_recovery = round(float(np.sum(amt_arr * y_prob)), 2)
        avg_recovery_amt = round(float(np.mean(amt_arr[y_pred == 1])), 2) if np.sum(y_pred == 1) > 0 else 0.0

    return EvaluationMetrics(
        roc_auc=round(roc, 4),
        pr_auc=round(pr_auc_val, 4),
        precision=round(p, 4),
        recall=round(r, 4),
        f1=round(f1, 4),
        brier_score=round(brier, 4),
        log_loss=round(lloss, 4),
        confusion_matrix=cm,
        operating_thresholds=operating_thresholds,
        revenue_weighted_recall=rev_weighted_recall,
        revenue_at_risk=rev_at_risk,
        recovered_revenue=recovered_rev,
        revenue_recovery_rate=rev_recovery_rate,
        expected_recovery=exp_recovery,
        average_recovery_amount=avg_recovery_amt,
    )


def run_evaluate_cli():
    """CLI evaluation of current production model on held-out test data."""
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    from app.ml.registry import registry
    from app.ml.dataset import build_reproducible_dataset

    if not registry.has_artifacts():
        print("Error: No trained model found. Run 'python -m app.ml.train' first.")
        return

    model, preprocessor, meta = registry.load_artifacts()
    splits = build_reproducible_dataset()

    X_test_proc = preprocessor.transform(splits.X_test)
    probs = model.predict_proba(X_test_proc)[:, 1]
    metrics = calculate_metrics(splits.y_test.values, probs, amounts=splits.X_test["amount"].values)

    print("=" * 65)
    print("RAY RECOVERABILITY MODEL EVALUATION (HELD-OUT TEST SET)")
    print("=" * 65)
    print(f"Model:                 {meta.model_type}")
    print(f"Version:               {meta.model_version}")
    print(f"Test Cases:            {len(splits.X_test):,}")
    print("-" * 65)
    print(f"PR-AUC:                {metrics.pr_auc:.4f}")
    print(f"ROC-AUC:               {metrics.roc_auc:.4f}")
    print(f"Case Precision:        {metrics.precision:.4f}")
    print(f"Case Recall:           {metrics.recall:.4f}")
    print(f"Revenue-Weighted Recall: {metrics.revenue_weighted_recall:.4f}")
    print(f"F1-Score:              {metrics.f1:.4f}")
    print(f"Brier Score:           {metrics.brier_score:.4f}")
    print(f"Log Loss:              {metrics.log_loss:.4f}")
    print("-" * 65)
    print(f"Revenue at Risk:       INR {metrics.revenue_at_risk:,.2f}")
    print(f"Recovered Revenue:     INR {metrics.recovered_revenue:,.2f}")
    print(f"Recovery Rate:         {metrics.revenue_recovery_rate:.1f}%")
    print("-" * 65)
    print("Operating Thresholds (Case-Level):")
    for thresh, vals in metrics.operating_thresholds.items():
        print(f"  Threshold >= {thresh}: Precision={vals['precision']:.2f}, Recall={vals['recall']:.2f}, F1={vals['f1']:.2f}")
    print("=" * 65)


if __name__ == "__main__":
    run_evaluate_cli()
