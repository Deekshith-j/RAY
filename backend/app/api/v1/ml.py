from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.entities import RecoveryCase, Customer, Payment, RecoveryPredictionRecord
from app.ml.predict import predictor
from app.ml.registry import registry
from app.ml.schemas import (
    RecoverabilityPrediction,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ModelMetadata,
)

router = APIRouter(prefix="/ml", tags=["Recoverability ML"])


class PredictRequest(BaseModel):
    case_id: str


@router.post("/predict", response_model=RecoverabilityPrediction)
async def predict_case_recoverability(
    payload: PredictRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Predict recoverability probability for a recovery case.
    Strictly read/predict-only; never triggers financial actions.
    Persists an immutable prediction record for auditability.
    """
    # Fetch case and customer details
    query = (
        select(RecoveryCase)
        .where(RecoveryCase.id == payload.case_id)
        .options(selectinload(RecoveryCase.customer))
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail=f"Recovery case '{payload.case_id}' not found.")

    # Build customer history from database
    cust = case.customer
    customer_history = None
    if cust:
        # Query customer payments
        q_pay = select(Payment).where(Payment.customer_id == cust.id)
        pays = (await db.execute(q_pay)).scalars().all()
        total_p = len(pays)
        succ_p = sum(1 for p in pays if p.status == "captured")
        fail_p = sum(1 for p in pays if p.status == "failed")
        ltv = sum(float(p.amount) for p in pays if p.status == "captured")

        customer_history = {
            "customer_age_days": cust.customer_age_days,
            "total_attempts": max(1, total_p),
            "successes": succ_p,
            "failures": fail_p,
            "lifetime_value": ltv,
        }

    case_dict = {
        "id": case.id,
        "customer_id": case.customer_id,
        "amount_at_risk": case.amount_at_risk,
        "failure_type": case.failure_type,
        "entity_type": case.entity_type,
        "retry_count": case.retry_count,
    }

    prediction = predictor.predict(case_dict, customer_history)

    # Persist prediction record in database
    rec = RecoveryPredictionRecord(
        case_id=case.id,
        model_version=prediction.model_version,
        probability=prediction.probability,
        expected_recovery=float(prediction.expected_recovery),
        recoverability_band=prediction.recoverability_band.value,
        features_json={
            "amount_at_risk": float(prediction.amount_at_risk),
            "top_features": [f.model_dump() for f in prediction.top_features],
        },
    )
    db.add(rec)
    await db.commit()

    return prediction


@router.post("/batch-predict", response_model=BatchPredictionResponse)
async def batch_predict_recoverability(
    payload: BatchPredictionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Batch predict recoverability for multiple cases."""
    predictions: List[RecoverabilityPrediction] = []

    for cid in payload.case_ids:
        query = select(RecoveryCase).where(RecoveryCase.id == cid)
        case = (await db.execute(query)).scalar_one_or_none()
        if case:
            case_dict = {
                "id": case.id,
                "customer_id": case.customer_id,
                "amount_at_risk": case.amount_at_risk,
                "failure_type": case.failure_type,
                "entity_type": case.entity_type,
                "retry_count": case.retry_count,
            }
            pred = predictor.predict(case_dict)
            predictions.append(pred)

    version = predictor.metadata.model_version if predictor.metadata else "unknown"
    return BatchPredictionResponse(
        model_version=version,
        total_cases=len(predictions),
        predictions=predictions,
    )


@router.get("/model", response_model=ModelMetadata)
async def get_model_metadata():
    """Retrieve production model metadata, version, and training provenance."""
    if not registry.has_artifacts():
        raise HTTPException(
            status_code=503,
            detail="Model artifacts have not been trained yet. Please run training pipeline.",
        )
    _, _, metadata = registry.load_artifacts()
    return metadata


@router.get("/metrics")
async def get_model_metrics():
    """Retrieve held-out test and validation metrics for the current production model."""
    if not registry.has_artifacts():
        raise HTTPException(status_code=503, detail="Model artifacts not found.")
    _, _, metadata = registry.load_artifacts()
    return {
        "model_version": metadata.model_version,
        "model_type": metadata.model_type,
        "validation_metrics": metadata.validation_metrics,
        "test_metrics": metadata.test_metrics,
        "is_calibrated": metadata.is_calibrated,
        "calibration_method": metadata.calibration_method,
    }
