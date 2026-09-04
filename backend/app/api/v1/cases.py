from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.entities import RecoveryCase, Customer, AuditLog, RecoveryState, RecoveryStrategy
from app.schemas.case import (
    RecoveryCaseResponse,
    RecoveryCaseDetailResponse,
    AuditLogSchema,
    ApprovalRequest,
)
from app.core.audit import log_audit_entry
from app.core.state_machine import validate_transition

router = APIRouter(prefix="/cases", tags=["Recovery Cases"])


@router.get("", response_model=List[RecoveryCaseResponse])
async def list_cases(
    db: AsyncSession = Depends(get_db),
    state: Optional[str] = Query(None, description="Filter by case state"),
    failure_type: Optional[str] = Query(None, description="Filter by failure type"),
    requires_approval: Optional[bool] = Query(None, description="Filter cases awaiting approval"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List recovery cases with optional filtering, sorted by expected recovery value descending."""
    query = (
        select(RecoveryCase)
        .join(Customer, RecoveryCase.customer_id == Customer.id)
        .options(selectinload(RecoveryCase.customer))
        .order_by(desc(RecoveryCase.expected_recovery_value))
    )

    if state:
        query = query.where(RecoveryCase.state == state)
    if failure_type:
        query = query.where(RecoveryCase.failure_type == failure_type)
    if requires_approval is True:
        query = query.where(RecoveryCase.state == RecoveryState.AWAITING_APPROVAL)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    cases = result.scalars().all()

    response = []
    for c in cases:
        item = RecoveryCaseResponse.model_validate(c)
        if c.customer:
            item.customer_name = c.customer.name
            item.customer_email = c.customer.email
        response.append(item)

    return response


@router.get("/{case_id}", response_model=RecoveryCaseDetailResponse)
async def get_case_detail(case_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch complete recovery case details including full immutable audit log trail."""
    query = (
        select(RecoveryCase)
        .where(RecoveryCase.id == case_id)
        .options(
            selectinload(RecoveryCase.customer),
            selectinload(RecoveryCase.audit_logs),
        )
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail=f"Recovery case '{case_id}' not found.")

    response = RecoveryCaseDetailResponse.model_validate(case)
    if case.customer:
        response.customer_name = case.customer.name
        response.customer_email = case.customer.email

    response.audit_logs = [
        AuditLogSchema.model_validate(log)
        for log in sorted(case.audit_logs, key=lambda l: l.timestamp)
    ]
    return response


@router.post("/{case_id}/approve", response_model=RecoveryCaseResponse)
async def approve_or_reject_case(
    case_id: str,
    payload: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Human-in-the-loop authorization endpoint.
    Approves or rejects recovery action for high-value cases or policy escalations.
    """
    query = select(RecoveryCase).where(RecoveryCase.id == case_id).options(selectinload(RecoveryCase.customer))
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    if case.state not in (RecoveryState.AWAITING_APPROVAL, RecoveryState.HUMAN_REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"Case {case_id} is in state '{case.state}', which cannot be approved/rejected.",
        )

    if payload.approved:
        validate_transition(case.state, RecoveryState.EXECUTING)
        case.state = RecoveryState.EXECUTING
        case.human_approved = True
        case.human_approved_by = payload.reviewer_name
        case.authorized_action = case.recommended_action or RecoveryStrategy.PAYMENT_LINK

        await log_audit_entry(
            db=db,
            case_id=case.id,
            agent="Human Reviewer",
            action="APPROVE_RECOVERY",
            reason=payload.notes or f"Action approved by {payload.reviewer_name} for ₹{case.amount_at_risk:,.2f}",
            approval_required=True,
            approved_by=payload.reviewer_name,
            policy_result="PASSED_HUMAN_APPROVAL",
        )
    else:
        validate_transition(case.state, RecoveryState.STOPPED)
        case.state = RecoveryState.STOPPED
        case.human_approved = False
        case.human_approved_by = payload.reviewer_name

        await log_audit_entry(
            db=db,
            case_id=case.id,
            agent="Human Reviewer",
            action="REJECT_RECOVERY",
            reason=payload.notes or f"Action rejected by {payload.reviewer_name}",
            approval_required=True,
            approved_by=payload.reviewer_name,
            policy_result="REJECTED_BY_HUMAN",
        )

    await db.commit()
    await db.refresh(case)

    resp = RecoveryCaseResponse.model_validate(case)
    if case.customer:
        resp.customer_name = case.customer.name
        resp.customer_email = case.customer.email
    return resp


@router.get("/{case_id}/events", summary="SSE stream of recovery lifecycle events (alias)")
async def stream_case_events_alias(case_id: str, request: Request):
    """Server-Sent Events stream for real-time frontend timeline updates."""
    import asyncio
    import json
    from fastapi.responses import StreamingResponse
    from app.agents.orchestrator import orchestrator

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
