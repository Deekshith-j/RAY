"""Model training and selection pipeline for RAY Recoverability ML.

Trains:
1. Logistic Regression (Transparent baseline)
2. Random Forest Classifier
3. XGBoost Classifier (with sklearn GradientBoosting fallback)

CRITICAL RULES:
- Preprocessor fitted strictly on Train.
- Calibration fitted strictly on Train via internal cross-validation.
- Best model selected strictly using Validation PR-AUC.
- Held-out Test set evaluated only once for final verification.
"""

import sys
import os
import platform
from datetime import datetime
from typing import Dict, Any, Tuple, List
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Check XGBoost availability
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except Exception:
    from sklearn.ensemble import GradientBoostingClassifier
    HAS_XGBOOST = False

from app.ml.config import ml_config
from app.ml.dataset import build_reproducible_dataset, DatasetSplits
from app.ml.preprocessing import RecoverabilityPreprocessor
from app.ml.evaluate import calculate_metrics
from app.ml.calibration import train_calibrated_model, evaluate_calibration_quality
from app.ml.registry import registry
from app.ml.schemas import ModelMetadata, ModelComparisonEntry


def train_and_select_model(
    splits: DatasetSplits,
    seed: int = ml_config.SEED,
) -> Tuple[Any, RecoverabilityPreprocessor, ModelMetadata, List[ModelComparisonEntry]]:
    """
    Train candidate models, calibrate probabilities, evaluate on validation set,
    select best model by validation PR-AUC, and perform held-out test evaluation.
    """
    # 1. Fit Preprocessor EXCLUSIVELY on Train
    preprocessor = RecoverabilityPreprocessor()
    X_train_proc = preprocessor.fit_transform(splits.X_train)
    X_val_proc = preprocessor.transform(splits.X_val)
    X_test_proc = preprocessor.transform(splits.X_test)

    y_train = splits.y_train.values
    y_val = splits.y_val.values
    y_test = splits.y_test.values

    # 2. Instantiate Candidate Estimators
    candidates = {}

    # Model 1: Logistic Regression
    candidates["Logistic Regression"] = LogisticRegression(
        C=1.0,
        max_iter=1000,
        random_state=seed,
        class_weight="balanced",
    )

    # Model 2: Random Forest
    candidates["Random Forest"] = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        random_state=seed,
        n_jobs=-1,
        class_weight="balanced",
    )

    # Model 3: XGBoost (or fallback)
    if HAS_XGBOOST:
        candidates["XGBoost"] = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.08,
            random_state=seed,
            eval_metric="logloss",
        )
    else:
        candidates["Gradient Boosting (Fallback)"] = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.08,
            random_state=seed,
        )

    # 3. Train & Evaluate Candidates on Validation Set
    comparison_entries: List[ModelComparisonEntry] = []
    trained_calibrated_models: Dict[str, Any] = {}
    val_metrics_map: Dict[str, Any] = {}

    best_model_name = ""
    best_val_pr_auc = -1.0
    best_calibrated_model = None

    for name, estimator in candidates.items():
        # Fit base estimator on training data
        estimator.fit(X_train_proc, y_train)

        # Fit calibrated classifier strictly on training data via internal CV
        calibrated_model = train_calibrated_model(
            base_estimator=estimator,
            X_train=X_train_proc,
            y_train=y_train,
            method=ml_config.CALIBRATION_METHOD,
            cv=ml_config.CALIBRATION_CV,
        )
        trained_calibrated_models[name] = calibrated_model

        # Evaluate on Validation set (NEVER on test set during selection)
        val_probs_uncal = estimator.predict_proba(X_val_proc)[:, 1]
        val_probs_cal = calibrated_model.predict_proba(X_val_proc)[:, 1]

        uncal_metrics = calculate_metrics(y_val, val_probs_uncal)
        cal_metrics = calculate_metrics(y_val, val_probs_cal)

        val_metrics_map[name] = cal_metrics

        entry = ModelComparisonEntry(
            model_type=name,
            validation_pr_auc=cal_metrics.pr_auc,
            validation_roc_auc=cal_metrics.roc_auc,
            validation_f1=cal_metrics.f1,
            validation_brier_score=uncal_metrics.brier_score,
            calibrated_brier_score=cal_metrics.brier_score,
            selected_for_production=False,
        )
        comparison_entries.append(entry)

        # Selection criterion: highest validation PR-AUC
        if cal_metrics.pr_auc > best_val_pr_auc:
            best_val_pr_auc = cal_metrics.pr_auc
            best_model_name = name
            best_calibrated_model = calibrated_model

    # Mark winning model in comparison
    for entry in comparison_entries:
        if entry.model_type == best_model_name:
            entry.selected_for_production = True

    # 4. Final Evaluation on Held-Out Test Set (Used ONLY once)
    test_probs = best_calibrated_model.predict_proba(X_test_proc)[:, 1]
    test_metrics = calculate_metrics(y_test, test_probs)

    # 5. Compile Metadata
    model_version = f"ray-recov-v1-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    metadata = ModelMetadata(
        model_version=model_version,
        model_type=f"{best_model_name} + {ml_config.CALIBRATION_METHOD.capitalize()} Calibration",
        is_calibrated=True,
        calibration_method=ml_config.CALIBRATION_METHOD,
        training_timestamp=datetime.utcnow().isoformat(),
        training_seed=seed,
        dataset_version="synthetic-50k-v1",
        dataset_hash=splits.dataset_hash,
        feature_list=preprocessor.numeric_features + preprocessor.categorical_features,
        train_size=len(splits.X_train),
        validation_size=len(splits.X_val),
        test_size=len(splits.X_test),
        validation_metrics=val_metrics_map[best_model_name].model_dump(),
        test_metrics=test_metrics.model_dump(),
        library_versions={
            "python": platform.python_version(),
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "xgboost": sys.modules.get("xgboost").__version__ if HAS_XGBOOST else "not_installed",
        },
    )

    # 6. Save Artifacts to Registry
    registry.save_artifacts(
        model=best_calibrated_model,
        preprocessor=preprocessor,
        metadata=metadata,
    )

    return best_calibrated_model, preprocessor, metadata, comparison_entries


def run_training_cli(total_events: int = 50000, seed: int = ml_config.SEED):
    """CLI execution for model training."""
    print("=" * 60)
    print("RAY RECOVERABILITY MODEL TRAINING PIPELINE")
    print("=" * 60)
    print(f"Generating reproducible dataset with seed {seed}...")
    splits = build_reproducible_dataset(total_events=total_events, seed=seed)
    print(f"Total dataset samples: {splits.total_samples:,}")
    print(f"Train samples: {len(splits.X_train):,} ({len(splits.train_customers):,} unique customers)")
    print(f"Val samples:   {len(splits.X_val):,} ({len(splits.val_customers):,} unique customers)")
    print(f"Test samples:  {len(splits.X_test):,} ({len(splits.test_customers):,} unique customers)")
    print(f"Dataset hash:  {splits.dataset_hash}")
    print("-" * 60)
    print("Training candidate models and calibrating...")
    best_model, preprocessor, meta, comparison = train_and_select_model(splits, seed=seed)

    print("\nMODEL SELECTION COMPARISON (VALIDATION SET):")
    print(f"{'Model':<30} | {'PR-AUC':<8} | {'ROC-AUC':<8} | {'Brier':<8} | {'Cal Brier':<10} | {'Selected'}")
    print("-" * 80)
    for c in comparison:
        sel = "[SELECTED]" if c.selected_for_production else "   No    "
        print(f"{c.model_type:<30} | {c.validation_pr_auc:<8.4f} | {c.validation_roc_auc:<8.4f} | {c.validation_brier_score:<8.4f} | {c.calibrated_brier_score:<10.4f} | {sel}")

    print("-" * 80)
    print(f"\nSELECTED PRODUCTION MODEL: {meta.model_type}")
    print(f"Model Version: {meta.model_version}")
    print(f"Validation PR-AUC: {meta.validation_metrics['pr_auc']:.4f}")
    print(f"Validation Brier Score: {meta.validation_metrics['brier_score']:.4f}")
    print(f"\nHELD-OUT TEST SET EVALUATION (Unseen Data):")
    print(f"Test PR-AUC:     {meta.test_metrics['pr_auc']:.4f}")
    print(f"Test ROC-AUC:    {meta.test_metrics['roc_auc']:.4f}")
    print(f"Test Precision:  {meta.test_metrics['precision']:.4f}")
    print(f"Test Recall:     {meta.test_metrics['recall']:.4f}")
    print(f"Test F1:         {meta.test_metrics['f1']:.4f}")
    print(f"Test Brier:      {meta.test_metrics['brier_score']:.4f}")
    print("\nArtifacts successfully persisted to backend/models/")
    print("=" * 60)
    return meta


if __name__ == "__main__":
    run_training_cli()
