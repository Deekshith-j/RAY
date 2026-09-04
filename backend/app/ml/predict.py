"""Inference pipeline for RAY Recoverability ML.

Predicts P(successful_recovery | context).
Strictly uses Decimal arithmetic for stored monetary outputs.
Provides deterministic, feature-derived explainability.
ML output NEVER directly triggers or authorizes financial actions.
"""

import sys
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.ml.config import ml_config
from app.ml.schemas import (
    RecoverabilityPrediction,
    RecoverabilityBand,
    FeatureExplanation,
    calculate_expected_recovery,
)
from app.ml.features import extract_features_from_case
from app.ml.registry import registry


def get_recoverability_band(prob: float) -> RecoverabilityBand:
    """Determine recoverability band based on configurable thresholds."""
    if prob >= ml_config.BAND_HIGH_THRESHOLD:
        return RecoverabilityBand.HIGH
    elif prob >= ml_config.BAND_MEDIUM_THRESHOLD:
        return RecoverabilityBand.MEDIUM
    else:
        return RecoverabilityBand.LOW


def generate_feature_explanations(features: Dict[str, Any], prob: float) -> List[FeatureExplanation]:
    """
    Derive deterministic feature-level explanations from actual input values.
    Zero fabricated or unsupported claims.
    """
    explanations = []

    # 1. Failure type diagnosis
    ft = features.get("failure_type", "")
    if ft in ("network_error", "timeout", "bank_unavailable"):
        explanations.append(FeatureExplanation(
            feature_name="failure_type",
            feature_value=ft,
            impact="positive",
            description=f"Failure type '{ft}' is transient and historically exhibits high recovery potential.",
        ))
    elif ft in ("fraud_flagged", "card_declined_permanent"):
        explanations.append(FeatureExplanation(
            feature_name="failure_type",
            feature_value=ft,
            impact="negative",
            description=f"Failure type '{ft}' indicates permanent decline or security block.",
        ))
    elif ft == "abandonment":
        explanations.append(FeatureExplanation(
            feature_name="failure_type",
            feature_value=ft,
            impact="neutral",
            description="Checkout abandonment requires customer re-engagement via payment link.",
        ))

    # 2. Customer historical success rate
    succ_rate = features.get("customer_success_rate", 0.0)
    attempts = features.get("previous_payment_count", 0)
    if attempts >= 3:
        if succ_rate >= 0.75:
            explanations.append(FeatureExplanation(
                feature_name="customer_success_rate",
                feature_value=f"{succ_rate * 100:.1f}%",
                impact="positive",
                description=f"Strong customer track record: {succ_rate * 100:.1f}% success rate across {attempts} transactions.",
            ))
        elif succ_rate < 0.30:
            explanations.append(FeatureExplanation(
                feature_name="customer_success_rate",
                feature_value=f"{succ_rate * 100:.1f}%",
                impact="negative",
                description=f"Low historical payment reliability ({succ_rate * 100:.1f}% success rate).",
            ))

    # 3. Retry count fatigue
    retries = features.get("retry_count", 0)
    if retries >= 1:
        explanations.append(FeatureExplanation(
            feature_name="retry_count",
            feature_value=retries,
            impact="negative" if retries >= 2 else "neutral",
            description=f"{retries} automated retry already attempted. Diminishing marginal returns on repeated retries.",
        ))

    # 4. Transaction amount risk
    amt = features.get("amount", 0.0)
    if amt >= 50000.0:
        explanations.append(FeatureExplanation(
            feature_name="amount",
            feature_value=f"₹{amt:,.2f}",
            impact="neutral",
            description="High-value transaction: requires human policy verification prior to execution.",
        ))

    return explanations[:4]


class RecoverabilityPredictor:
    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.metadata = None
        self._load_if_available()

    def _load_if_available(self):
        if registry.has_artifacts():
            self.model, self.preprocessor, self.metadata = registry.load_artifacts()

    def predict(
        self,
        case_dict: Dict[str, Any],
        customer_history: Optional[Dict[str, Any]] = None,
    ) -> RecoverabilityPrediction:
        """Predict recovery probability for a single case."""
        if self.model is None or self.preprocessor is None:
            self._load_if_available()
        if self.model is None or self.preprocessor is None:
            raise RuntimeError("Model artifacts not loaded. Please train a model first using 'python -m app.ml.train'.")

        case_id = case_dict.get("id", f"case_anon_{datetime.utcnow().timestamp()}")
        amount = float(case_dict.get("amount_at_risk", 0.0))

        # Extract features
        feat_dict = extract_features_from_case(case_dict, customer_history)
        df = pd.DataFrame([feat_dict])

        # Preprocess & Predict
        X_proc = self.preprocessor.transform(df)
        prob = float(self.model.predict_proba(X_proc)[0, 1])
        prob = max(0.0, min(1.0, prob))  # Ensure strictly bounded in [0, 1]

        # Calculate Decimal Expected Recovery
        expected_rec = calculate_expected_recovery(amount, prob)
        band = get_recoverability_band(prob)
        explanations = generate_feature_explanations(feat_dict, prob)

        return RecoverabilityPrediction(
            case_id=case_id,
            probability=prob,
            amount_at_risk=Decimal(str(round(amount, 2))),
            expected_recovery=expected_rec,
            model_version=self.metadata.model_version if self.metadata else "unknown",
            prediction_timestamp=datetime.utcnow(),
            recoverability_band=band,
            top_features=explanations,
        )

    def predict_batch(
        self,
        cases: List[Dict[str, Any]],
        customer_history_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[RecoverabilityPrediction]:
        """Batch predict recovery probabilities for multiple cases."""
        predictions = []
        hist_map = customer_history_map or {}
        for c in cases:
            cid = c.get("customer_id", "")
            hist = hist_map.get(cid)
            pred = self.predict(c, hist)
            predictions.append(pred)
        return predictions


predictor = RecoverabilityPredictor()


def run_predict_cli():
    """CLI tool for single case prediction."""
    parser = argparse.ArgumentParser(description="Predict recoverability for a case.")
    parser.add_argument("--case-id", type=str, default="case_demo_001", help="Case ID to predict")
    parser.add_argument("--amount", type=float, default=9999.0, help="Amount at risk in INR")
    parser.add_argument("--failure-type", type=str, default="network_error", help="Failure type")
    args = parser.parse_args()

    sample_case = {
        "id": args.case_id,
        "amount_at_risk": args.amount,
        "failure_type": args.failure_type,
        "customer_id": "cust_demo",
        "entity_type": "PAYMENT",
        "retry_count": 0,
    }

    pred = predictor.predict(sample_case)
    print("=" * 60)
    print("RAY RECOVERABILITY PREDICTION")
    print("=" * 60)
    print(f"Case ID:             {pred.case_id}")
    print(f"Model Version:       {pred.model_version}")
    print(f"Calibrated P(Rec):   {pred.probability * 100:.2f}%")
    print(f"Amount at Risk:      ₹{pred.amount_at_risk}")
    print(f"Expected Recovery:   ₹{pred.expected_recovery}")
    print(f"Recoverability Band: {pred.recoverability_band.value}")
    print("\nFeature Evidence:")
    for f in pred.top_features:
        print(f"  - [{f.impact.upper()}] {f.feature_name} = {f.feature_value}: {f.description}")
    print("=" * 60)


if __name__ == "__main__":
    run_predict_cli()
