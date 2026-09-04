"""Recovery Lifecycle & Multi-Agent REST API Endpoints."""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.entities import (
    RecoveryCase,
    RecoveryDecision,
    ExecutionRecord,
    VerificationRecord,
    RecoveryPredictionRecord,
    RecoveryState,
    RecoveryStrategy,
)
from app.config import settings
from app.agents.orchestrator import orchestrator
from app.agents.detective import RevenueDetective
from app.agents.diagnosis import DiagnosisAgent
from app.agents.planner import RecoveryPlanner
from app.agents.execution import ExecutionAgent
from app.core.policy_engine import PolicyEngine
from app.tools.gateway import ToolGateway
from app.verification.engine import VerificationEngine
from app.verification.models import VerificationStatus

router = APIRouter(prefix="/recovery", tags=["Agentic Recovery"])


@router.post("/{case_id}/run-full", summary="Run full autonomous recovery flow")
async def run_full_recovery_flow(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Executes the full Detective -> Diagnosis -> Planner -> Policy -> Execution -> Verification flow."""
    try:
        result = await orchestrator.run_full_recovery_flow(case_id, db)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/analyze", summary="Step 1 & 2: Revenue Detective & Diagnosis")
async def analyze_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Performs pre-action feature extraction, ML probability estimation, and failure diagnosis."""
    detective = RevenueDetective()
    diagnosis_agent = DiagnosisAgent()

    try:
        opportunity = await detective.analyze_opportunity(case_id, db)
        diagnosis = await diagnosis_agent.diagnose(opportunity)

        # Transition case to ANALYZING
        stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
        res = await db.execute(stmt)
        case = res.scalar_one_or_none()
        if case and case.state == RecoveryState.FAILED:
            case.state = RecoveryState.ANALYZING
            await db.commit()

        return {
            "case_id": case_id,
            "opportunity": opportunity.model_dump(),
            "diagnosis": diagnosis.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/plan", summary="Step 3 & 4: Recovery Planner & Policy Evaluation")
async def plan_recovery(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Proposes candidate strategy and submits to deterministic Policy Engine. Persists RecoveryDecision."""
    detective = RevenueDetective()
    diagnosis_agent = DiagnosisAgent()
    planner = RecoveryPlanner()
    policy_engine = PolicyEngine()

    try:
        opportunity = await detective.analyze_opportunity(case_id, db)
        diagnosis = await diagnosis_agent.diagnose(opportunity)
        plan = await planner.plan_recovery(opportunity, diagnosis)

        stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
        res = await db.execute(stmt)
        case = res.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        # Evaluate deterministic policy
        strat_enum = RecoveryStrategy(plan.recommended_strategy) if plan.recommended_strategy in [s.value for s in RecoveryStrategy] else RecoveryStrategy.NO_ACTION
        policy_eval = policy_engine.evaluate(case, strat_enum)

        decision_id = f"dec_{case_id}_{int(asyncio.get_event_loop().time())}"
        auth_req = policy_eval.requires_human_approval
        auth_status = "PENDING" if auth_req else ("AUTHORIZED" if policy_eval.allowed else "REJECTED")

        decision = RecoveryDecision(
            id=decision_id,
            case_id=case_id,
            recommended_strategy=plan.recommended_strategy,
            probability_of_recovery=opportunity.recoverability_probability,
            expected_recovery=float(opportunity.expected_recovery),
            rationale=plan.rationale,
            policy_result="REQUIRE_HUMAN_APPROVAL" if auth_req else ("ALLOW" if policy_eval.allowed else "DENY"),
            policy_version="v1.0",
            authorization_required=auth_req,
            authorization_status=auth_status,
            correlation_id=f"RAY-{case_id}",
        )
        db.add(decision)

        if auth_req:
            case.state = RecoveryState.AWAITING_APPROVAL
        elif policy_eval.allowed:
            case.state = RecoveryState.RECOVERY_PLANNED
        else:
            case.state = RecoveryState.STOPPED

        await db.commit()

        return {
            "case_id": case_id,
            "decision_id": decision_id,
            "recommended_strategy": plan.recommended_strategy,
            "expected_recovery": plan.expected_recovery,
            "policy_result": decision.policy_result,
            "authorization_required": auth_req,
            "authorization_status": auth_status,
            "case_state": case.state.value,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/execute", summary="Step 5: Execution via Tool Gateway")
async def execute_recovery(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Dispatches execution strictly through Tool Gateway.
    Fails if Policy Engine has not authorized the decision.
    """
    stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
    case_res = await db.execute(stmt)
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    dec_stmt = select(RecoveryDecision).where(RecoveryDecision.case_id == case_id).order_by(RecoveryDecision.created_at.desc())
    dec_res = await db.execute(dec_stmt)
    decision = dec_res.scalars().first()
    if not decision:
        raise HTTPException(status_code=400, detail="No RecoveryDecision found for case. Run /plan first.")

    execution_agent = ExecutionAgent()
    case.state = RecoveryState.EXECUTING
    await db.commit()

    tool_result = await execution_agent.execute_decision(decision, case, db, attempt_number=case.retry_count + 1)

    if tool_result.status == "SUCCESS":
        case.state = RecoveryState.AWAITING_VERIFICATION
        case.retry_count += 1
        await db.commit()
        return {
            "status": "SUCCESS",
            "execution_id": tool_result.execution_id,
            "provider_reference": tool_result.provider_reference,
            "idempotency_key": tool_result.idempotency_key,
            "case_state": case.state.value,
        }
    else:
        case.state = RecoveryState.FAILED
        await db.commit()
        raise HTTPException(status_code=400, detail=f"Execution rejected by Tool Gateway: {tool_result.rejection_reason}")


@router.post("/{case_id}/verify", summary="Step 6: Dual-Signal Verification")
async def verify_recovery(
    case_id: str,
    execution_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Performs dual-signal verification (API polling + Webhook proof)."""
    if not execution_id:
        exec_stmt = select(ExecutionRecord).where(ExecutionRecord.case_id == case_id).order_by(ExecutionRecord.created_at.desc())
        exec_res = await db.execute(exec_stmt)
        exec_rec = exec_res.scalars().first()
        if not exec_rec:
            raise HTTPException(status_code=400, detail="No ExecutionRecord found for case. Run /execute first.")
        execution_id = exec_rec.id

    verification_engine = VerificationEngine()
    verif_res = await verification_engine.verify_recovery(case_id, execution_id, db)

    return {
        "verification_id": verif_res.verification_id,
        "status": verif_res.status.value,
        "webhook_confirmed": verif_res.webhook_confirmed,
        "api_state_confirmed": verif_res.api_state_confirmed,
        "verified_amount": verif_res.verified_amount,
        "evidence_hash": verif_res.evidence_hash,
    }


@router.get("/{case_id}/decision", summary="Get RecoveryDecision record")
async def get_case_decision(case_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RecoveryDecision).where(RecoveryDecision.case_id == case_id).order_by(RecoveryDecision.created_at.desc())
    res = await db.execute(stmt)
    decision = res.scalars().first()
    if not decision:
        raise HTTPException(status_code=404, detail="No decision found")
    return {
        "id": decision.id,
        "case_id": decision.case_id,
        "recommended_strategy": decision.recommended_strategy,
        "probability_of_recovery": decision.probability_of_recovery,
        "expected_recovery": decision.expected_recovery,
        "rationale": decision.rationale,
        "policy_result": decision.policy_result,
        "authorization_required": decision.authorization_required,
        "authorization_status": decision.authorization_status,
        "created_at": decision.created_at.isoformat(),
    }


@router.get("/{case_id}/execution", summary="Get ExecutionRecord")
async def get_case_execution(case_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ExecutionRecord).where(ExecutionRecord.case_id == case_id).order_by(ExecutionRecord.created_at.desc())
    res = await db.execute(stmt)
    rec = res.scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="No execution record found")
    return {
        "id": rec.id,
        "case_id": rec.case_id,
        "decision_id": rec.decision_id,
        "tool_name": rec.tool_name,
        "operation": rec.operation,
        "idempotency_key": rec.idempotency_key,
        "provider_reference": rec.provider_reference,
        "execution_status": rec.execution_status,
        "provider_response_hash": rec.provider_response_hash,
        "created_at": rec.created_at.isoformat(),
    }


@router.get("/{case_id}/verification", summary="Get VerificationRecord")
async def get_case_verification(case_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(VerificationRecord).where(VerificationRecord.case_id == case_id).order_by(VerificationRecord.created_at.desc())
    res = await db.execute(stmt)
    verif = res.scalars().first()
    if not verif:
        raise HTTPException(status_code=404, detail="No verification record found")
    return {
        "id": verif.id,
        "case_id": verif.case_id,
        "execution_id": verif.execution_id,
        "webhook_confirmed": verif.webhook_confirmed,
        "api_state_confirmed": verif.api_state_confirmed,
        "provider_status": verif.provider_status,
        "verified_amount": verif.verified_amount,
        "verification_status": verif.verification_status,
        "evidence_hash": verif.evidence_hash,
        "verification_timestamp": verif.verification_timestamp.isoformat(),
    }


@router.get("/{case_id}/timeline", summary="Get chronological agent timeline")
async def get_case_timeline(case_id: str):
    events = orchestrator.get_timeline(case_id)
    return {"case_id": case_id, "events": events}


@router.get("/{case_id}/events", summary="SSE stream of recovery lifecycle events")
async def stream_case_events(case_id: str, request: Request):
    """Server-Sent Events stream for real-time frontend timeline updates."""
    async def event_generator():
        last_count = 0
        while True:
            if await request.is_disconnected():
                break

            events = orchestrator.get_timeline(case_id)
            if len(events) > last_count:
                for new_event in events[last_count:]:
                    yield f"data: {json.dumps(new_event)}\n\n"
                last_count = len(events)

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/{case_id}/provenance", summary="Get complete cryptographic financial provenance chain")
async def get_case_provenance(case_id: str, db: AsyncSession = Depends(get_db)):
    """Returns the end-to-end provenance chain for a case: Prediction -> Decision -> Execution -> Verification."""
    case_stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
    case = (await db.execute(case_stmt)).scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    pred_stmt = select(RecoveryPredictionRecord).where(RecoveryPredictionRecord.case_id == case_id).order_by(RecoveryPredictionRecord.created_at.desc())
    pred = (await db.execute(pred_stmt)).scalars().first()

    dec_stmt = select(RecoveryDecision).where(RecoveryDecision.case_id == case_id).order_by(RecoveryDecision.created_at.desc())
    dec = (await db.execute(dec_stmt)).scalars().first()

    exec_stmt = select(ExecutionRecord).where(ExecutionRecord.case_id == case_id).order_by(ExecutionRecord.created_at.desc())
    exec_rec = (await db.execute(exec_stmt)).scalars().first()

    verif_stmt = select(VerificationRecord).where(VerificationRecord.case_id == case_id).order_by(VerificationRecord.created_at.desc())
    verif = (await db.execute(verif_stmt)).scalars().first()

    is_valid_chain = bool(dec and exec_rec and verif and verif.verification_status == "VERIFIED")

    return {
        "case_id": case_id,
        "amount_at_risk": case.amount_at_risk,
        "recovered_amount": case.recovered_amount,
        "state": case.state.value,
        "prediction": {
            "id": pred.id,
            "probability": getattr(pred, "probability", getattr(pred, "probability_of_recovery", 0.0)),
            "recoverability_band": pred.recoverability_band,
            "expected_recovery": pred.expected_recovery,
            "model_version": pred.model_version,
            "created_at": pred.created_at.isoformat(),
        } if pred else None,
        "decision": {
            "id": dec.id,
            "recommended_strategy": dec.recommended_strategy,
            "policy_result": dec.policy_result,
            "authorization_status": dec.authorization_status,
            "rationale": dec.rationale,
            "created_at": dec.created_at.isoformat(),
        } if dec else None,
        "execution": {
            "id": exec_rec.id,
            "operation": exec_rec.operation,
            "idempotency_key": exec_rec.idempotency_key,
            "provider_reference": exec_rec.provider_reference,
            "execution_status": exec_rec.execution_status,
            "provider_response_hash": exec_rec.provider_response_hash,
            "created_at": exec_rec.created_at.isoformat(),
        } if exec_rec else None,
        "verification": {
            "id": verif.id,
            "verification_status": verif.verification_status,
            "webhook_confirmed": verif.webhook_confirmed,
            "api_state_confirmed": verif.api_state_confirmed,
            "verified_amount": verif.verified_amount,
            "evidence_hash": verif.evidence_hash,
            "verification_timestamp": verif.verification_timestamp.isoformat(),
        } if verif else None,
        "provenance_chain_valid": is_valid_chain,
    }


@router.post("/demo/reset", summary="Reset demo cases and provenance for clean demonstration")
async def reset_demo_data(db: AsyncSession = Depends(get_db)):
    """Resets only demonstration test cases (e.g. PAY_DEMO_*) when DEMO_MODE is active."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo reset is disabled when DEMO_MODE is False.")

    from sqlalchemy import delete
    from app.models.entities import AuditLog

    demo_prefixes = ["PAY_DEMO_", "prov_test_", "gate_case_", "idem_case_"]
    
    # Clean timeline in memory
    for cid in list(orchestrator._timeline_events.keys()):
        if any(cid.startswith(p) for p in demo_prefixes):
            del orchestrator._timeline_events[cid]

    # Delete records matching demo prefix
    for table, col in [
        (VerificationRecord, VerificationRecord.case_id),
        (ExecutionRecord, ExecutionRecord.case_id),
        (RecoveryDecision, RecoveryDecision.case_id),
        (RecoveryPredictionRecord, RecoveryPredictionRecord.case_id),
        (AuditLog, AuditLog.case_id),
        (RecoveryCase, RecoveryCase.id),
    ]:
        for prefix in demo_prefixes:
            await db.execute(delete(table).where(col.startswith(prefix)))

    await db.commit()
    return {"status": "success", "message": "Demo cases reset successfully."}

