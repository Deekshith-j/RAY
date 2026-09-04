"""RAY ML Recoverability Package.

Predicts P(successful_recovery | payment/customer/context).
Outputs expected recovery values to inform downstream recovery strategies.
ML predictions NEVER directly authorize or execute financial actions.
"""

__version__ = "0.1.0"

from app.ml.monitoring import model_telemetry, drift_detector, calculate_recovery_priority_score

__all__ = [
    "model_telemetry",
    "drift_detector",
    "calculate_recovery_priority_score",
]
