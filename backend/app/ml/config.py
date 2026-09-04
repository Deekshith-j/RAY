from pathlib import Path
from typing import List
from pydantic import BaseModel


class MLConfig(BaseModel):
    # Reproducibility
    SEED: int = 42

    # Split ratios (Customer-grouped split takes priority)
    TRAIN_RATIO: float = 0.70
    VAL_RATIO: float = 0.15
    TEST_RATIO: float = 0.15

    # Storage paths
    ARTIFACTS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "models"

    # Recoverability band thresholds
    BAND_HIGH_THRESHOLD: float = 0.85
    BAND_MEDIUM_THRESHOLD: float = 0.60

    # Model parameters
    CALIBRATION_METHOD: str = "sigmoid"  # 'sigmoid' (Platt scaling) or 'isotonic'
    CALIBRATION_CV: int = 3  # strictly internal cross-validation on train set only

    # Pre-action features (strictly available BEFORE any recovery action)
    NUMERIC_FEATURES: List[str] = [
        "amount",
        "customer_age_days",
        "previous_payment_count",
        "successful_payment_count",
        "failed_payment_count",
        "customer_success_rate",
        "retry_count",
        "merchant_baseline_failure_rate",
        "subscription_age_days",
        "customer_lifetime_value",
    ]

    CATEGORICAL_FEATURES: List[str] = [
        "failure_type",
        "payment_method",
        "entity_type",
    ]

    TARGET_COLUMN: str = "is_recoverable"


ml_config = MLConfig()
