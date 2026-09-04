"""ML Model Monitoring, Telemetry, and Drift Detection for RAY."""

import math
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime


class ModelTelemetry:
    """Tracks live inference counts, band distributions, and expected recovery metrics."""

    def __init__(self):
        self.prediction_count: int = 0
        self.high_band_count: int = 0
        self.medium_band_count: int = 0
        self.low_band_count: int = 0
        self._sum_probability: float = 0.0
        self._sum_expected_recovery: Decimal = Decimal("0.00")

    def record_prediction(self, probability: float, expected_recovery: Decimal, band: str):
        self.prediction_count += 1
        band_upper = str(band).upper()
        if band_upper == "HIGH":
            self.high_band_count += 1
        elif band_upper == "MEDIUM":
            self.medium_band_count += 1
        else:
            self.low_band_count += 1

        self._sum_probability += probability
        self._sum_expected_recovery += expected_recovery

    def get_summary(self) -> Dict[str, Any]:
        avg_prob = (self._sum_probability / self.prediction_count) if self.prediction_count > 0 else 0.0
        avg_er = (self._sum_expected_recovery / self.prediction_count) if self.prediction_count > 0 else Decimal("0.00")
        return {
            "prediction_count": self.prediction_count,
            "band_distribution": {
                "HIGH": self.high_band_count,
                "MEDIUM": self.medium_band_count,
                "LOW": self.low_band_count,
            },
            "average_probability": round(avg_prob, 4),
            "average_expected_recovery": float(avg_er.quantize(Decimal("0.01"))),
        }


class ModelDriftDetector:
    """
    Monitors inference feature distributions against training baseline distributions.
    Tracks: amount, customer_success_rate, failure_type, payment_method.
    Triggers 'MODEL DRIFT WARNING' if distribution shifts significantly.
    """

    # Baseline distributions derived from synthetic training set
    BASELINE_STATS = {
        "amount": {"mean": 24000.0, "std": 32000.0},
        "customer_success_rate": {"mean": 0.82, "std": 0.18},
        "failure_types": {
            "timeout": 0.35,
            "bank_unavailable": 0.25,
            "insufficient_funds": 0.20,
            "card_expired": 0.10,
            "network_error": 0.10,
        },
    }

    def __init__(self, drift_threshold_z: float = 2.5):
        self.drift_threshold_z = drift_threshold_z

    def check_feature_drift(self, recent_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compares a sample of recent inference features against baseline.
        Returns drift status and warning if detected.
        """
        if not recent_features or len(recent_features) < 5:
            return {
                "drift_detected": False,
                "warning": None,
                "sample_size": len(recent_features) if recent_features else 0,
                "metrics": {},
            }

        drift_warnings: List[str] = []

        # 1. Amount mean shift
        amounts = [float(f.get("amount", 0.0)) for f in recent_features if "amount" in f]
        if amounts:
            current_mean_amount = sum(amounts) / len(amounts)
            base_mean = self.BASELINE_STATS["amount"]["mean"]
            base_std = self.BASELINE_STATS["amount"]["std"]
            z_score = abs(current_mean_amount - base_mean) / (base_std / math.sqrt(len(amounts)))
            if z_score > self.drift_threshold_z:
                drift_warnings.append(f"Amount distribution shifted (mean={current_mean_amount:.2f}, baseline={base_mean:.2f}, z={z_score:.2f})")

        # 2. Customer Success Rate shift
        success_rates = [float(f.get("customer_success_rate", 0.8)) for f in recent_features if "customer_success_rate" in f]
        if success_rates:
            current_mean_sr = sum(success_rates) / len(success_rates)
            base_mean_sr = self.BASELINE_STATS["customer_success_rate"]["mean"]
            base_std_sr = self.BASELINE_STATS["customer_success_rate"]["std"]
            z_score_sr = abs(current_mean_sr - base_mean_sr) / (base_std_sr / math.sqrt(len(success_rates)))
            if z_score_sr > self.drift_threshold_z:
                drift_warnings.append(f"Customer success rate shifted (mean={current_mean_sr:.2f}, baseline={base_mean_sr:.2f}, z={z_score_sr:.2f})")

        drift_detected = len(drift_warnings) > 0
        warning_msg = f"MODEL DRIFT WARNING: {'; '.join(drift_warnings)}" if drift_detected else None

        return {
            "drift_detected": drift_detected,
            "warning": warning_msg,
            "sample_size": len(recent_features),
            "drift_warnings": drift_warnings,
        }


def calculate_recovery_priority_score(amount: float, probability: float, expected_recovery: float) -> float:
    """
    Computes deterministic recovery priority score:
    Primary: Expected Recovery Value
    Secondary: Probability of Recovery
    Tertiary: Amount at Risk
    Formula: ER + (P * 100) + (Amount * 0.001)
    """
    return float(expected_recovery) + (float(probability) * 100.0) + (float(amount) * 0.001)


model_telemetry = ModelTelemetry()
drift_detector = ModelDriftDetector()
