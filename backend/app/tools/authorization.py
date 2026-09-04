"""Tool Gateway Authorization Enforcement."""

from typing import Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import RecoveryCase, RecoveryDecision
from app.tools.schemas import ToolCallRequest
from app.tools.idempotency import validate_idempotency_key_format


async def authorize_tool_call(
    session: AsyncSession,
    request: ToolCallRequest,
) -> Tuple[bool, Optional[str], Optional[RecoveryCase], Optional[RecoveryDecision]]:
    """
    Strictly authorize a tool call against the deterministic policy boundary.
    Returns (authorized, reason, case, decision).
    """
    # 1. Format check
    if not validate_idempotency_key_format(request.idempotency_key):
        return False, f"Malformed idempotency key '{request.idempotency_key}'", None, None

    # 2. Case exists
    case_stmt = select(RecoveryCase).where(RecoveryCase.id == request.case_id)
    case_res = await session.execute(case_stmt)
    case = case_res.scalar_one_or_none()
    if not case:
        return False, f"RecoveryCase '{request.case_id}' does not exist", None, None

    # 3. Decision exists
    dec_stmt = select(RecoveryDecision).where(RecoveryDecision.id == request.decision_id)
    dec_res = await session.execute(dec_stmt)
    decision = dec_res.scalar_one_or_none()
    if not decision:
        return False, f"RecoveryDecision '{request.decision_id}' does not exist", case, None

    # 4. Decision belongs to case
    if decision.case_id != case.id:
        return False, f"Decision '{decision.id}' does not belong to Case '{case.id}'", case, decision

    # 5. Policy check
    if decision.policy_result == "DENY":
        return False, f"Policy Engine denied strategy '{decision.recommended_strategy}'", case, decision

    if decision.authorization_required and decision.authorization_status != "AUTHORIZED":
        return False, f"High-value recovery (₹{case.amount_at_risk:,.2f}) requires human approval. Current status: {decision.authorization_status}", case, decision

    # 6. Strategy match
    op_lower = request.operation.lower()
    strat_upper = decision.recommended_strategy.upper()
    if "retry" in op_lower and strat_upper != "RETRY":
        return False, f"Operation '{request.operation}' does not match authorized strategy '{strat_upper}'", case, decision
    if ("link" in op_lower or "plink" in op_lower) and strat_upper != "PAYMENT_LINK":
        return False, f"Operation '{request.operation}' does not match authorized strategy '{strat_upper}'", case, decision
    if ("subscription" in op_lower or "charge" in op_lower) and strat_upper != "SUBSCRIPTION_RECOVERY":
        return False, f"Operation '{request.operation}' does not match authorized strategy '{strat_upper}'", case, decision

    return True, None, case, decision
