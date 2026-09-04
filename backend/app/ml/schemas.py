import enum
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class RecoverabilityBand(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def calculate_expected_recovery(amount: float, probability: float) -> Decimal:
    """
    Calculate expected recovery using full-precision probability,
    then quantize the final monetary INR amount to Decimal('0.01') using ROUND_HALF_UP.
    Never uses floating-point arithmetic for stored financial currency.
    """
    dec_amount = Decimal(str(amount))
    dec_prob = Decimal(str(probability))
    expected = dec_amount * dec_prob
    # Quantize to 2 decimal places (paise precision)
    return expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class FeatureExplanation(BaseModel):
    feature_name: str
    feature_value: Any
    impact: str  # 'positive', 'negative', 'neutral'
    description: str


class RecoverabilityPrediction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_id: str
    probability: float = Field(..., ge=0.0, le=1.0, description="Full precision calibrated probability")
    amount_at_risk: Decimal
    expected_recovery: Decimal
    model_version: str
    prediction_timestamp: datetime
    recoverability_band: RecoverabilityBand
    top_features: List[FeatureExplanation] = []


class BatchPredictionRequest(BaseModel):
    case_ids: List[str]


class BatchPredictionResponse(BaseModel):
    model_version: str
    total_cases: int
    predictions: List[RecoverabilityPrediction]


class EvaluationMetrics(BaseModel):
    roc_auc: float
    pr_auc: float
    precision: float  # Case-level precision
    recall: float     # Case-level recall
    f1: float
    brier_score: float
    log_loss: float
    confusion_matrix: List[List[int]]
    operating_thresholds: Dict[str, Dict[str, float]] = {}

    # Financial & Revenue-Weighted Telemetry
    revenue_weighted_recall: Optional[float] = None
    revenue_at_risk: Optional[float] = None
    recovered_revenue: Optional[float] = None
    revenue_recovery_rate: Optional[float] = None
    expected_recovery: Optional[float] = None
    average_recovery_amount: Optional[float] = None


class ModelComparisonEntry(BaseModel):
    model_type: str
    validation_pr_auc: float
    validation_roc_auc: float
    validation_f1: float
    validation_brier_score: float
    calibrated_brier_score: float
    selected_for_production: bool = False


class ModelMetadata(BaseModel):
    model_version: str
    model_type: str
    is_calibrated: bool
    calibration_method: str
    training_timestamp: str
    training_seed: int
    dataset_version: str
    dataset_hash: str
    feature_list: List[str]
    train_size: int
    validation_size: int
    test_size: int
    validation_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]
    library_versions: Dict[str, str]
