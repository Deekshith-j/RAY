"""Canonical financial calculations, verified revenue aggregation, and precision utilities."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.entities import (
    RecoveryCase,
    VerificationRecord,
    ExecutionRecord,
    RecoveryDecision,
)


def to_decimal(val: Any) -> Decimal:
    """Safely convert any numeric/string value to exact Decimal without float binary inaccuracies."""
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def quantize_inr(val: Any) -> Decimal:
    """Quantize to exact Indian Rupee paise (2 decimal places) using standard commercial rounding."""
    return to_decimal(val).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def calculate_verified_revenue(session: AsyncSession) -> Decimal:
    """
    CANONICAL FUNCTION: Calculates strictly verified financial revenue recovered.
    CRITICAL INVARIANT:
    - Only counts records where verification_status == 'VERIFIED'
    - Only counts verified_amount > 0
    - NEVER counts predicted revenue, expected recovery, planned recovery, or unverified provider execution.
    """
    stmt = (
        select(func.coalesce(func.sum(VerificationRecord.verified_amount), 0.0))
        .where(
            VerificationRecord.verification_status == "VERIFIED",
            VerificationRecord.verified_amount > 0,
        )
    )
    res = await session.execute(stmt)
    total_float = res.scalar_one_or_none() or 0.0
    return quantize_inr(total_float)


async def get_financial_breakdown(session: AsyncSession) -> Dict[str, Decimal]:
    """
    Returns the four strictly separated financial telemetry quantities:
    1. Revenue At Risk: Total value of payment failures / abandonments detected.
    2. Expected Recovery: Sum of (Amount * Calibrated Probability) across all cases.
    3. Executed Amount: Total value dispatched through Tool Gateway.
    4. Verified Revenue: Independently proven recovered revenue confirmed by dual-signals.
    """
    # 1. Revenue at Risk
    stmt_risk = select(func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0.0))
    res_risk = await session.execute(stmt_risk)
    risk_dec = quantize_inr(res_risk.scalar_one_or_none() or 0.0)

    # 2. Expected Recovery
    stmt_exp = select(func.coalesce(func.sum(RecoveryCase.expected_recovery_value), 0.0))
    res_exp = await session.execute(stmt_exp)
    exp_dec = quantize_inr(res_exp.scalar_one_or_none() or 0.0)

    # 3. Executed Amount
    # Sum amount of cases that reached EXECUTING or completed ToolGateway execution
    stmt_exec = (
        select(func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0.0))
        .join(ExecutionRecord, ExecutionRecord.case_id == RecoveryCase.id)
        .where(ExecutionRecord.execution_status == "SUCCESS")
    )
    res_exec = await session.execute(stmt_exec)
    exec_dec = quantize_inr(res_exec.scalar_one_or_none() or 0.0)

    # 4. Verified Revenue (Canonical)
    verified_dec = await calculate_verified_revenue(session)

    return {
        "revenue_at_risk": risk_dec,
        "expected_recovery": exp_dec,
        "executed_amount": exec_dec,
        "verified_revenue": verified_dec,
    }
