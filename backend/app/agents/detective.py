"""Agent 1 — Revenue Detective: Identifies and quantifies financial recovery opportunities."""

from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.base import BaseAgent, PromptInjectionDefense
from app.models.entities import RecoveryCase, Customer
from app.ml.predict import predictor, get_recoverability_band
from app.ml.schemas import calculate_expected_recovery


class RevenueOpportunity(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    case_id: str
    entity_type: str
    amount: Decimal
    failure_type: str
    customer_context: Dict[str, Any]
    recoverability_probability: float
    expected_recovery: Decimal
    recoverability_band: str
    opportunity_summary: str


class RevenueDetective(BaseAgent):
    """
    Agent 1: Reads case and historical ledger data, invokes the ML Recoverability
    Pipeline, and quantifies expected recovery using exact Decimal arithmetic.
    CANNOT authorize or execute.
    """

    def __init__(self):
        super().__init__(name="RevenueDetective")

    async def analyze_opportunity(
        self,
        case_id: str,
        session: AsyncSession,
        correlation_id: str = "",
    ) -> RevenueOpportunity:
        self.increment_step()

        # 1. Fetch Recovery Case
        stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
        res = await session.execute(stmt)
        case = res.scalar_one_or_none()
        if not case:
            raise ValueError(f"RecoveryCase '{case_id}' not found")

        # 2. Fetch Customer Context if available
        customer_ctx = {}
        if case.customer_id:
            c_stmt = select(Customer).where(Customer.id == case.customer_id)
            c_res = await session.execute(c_stmt)
            cust = c_res.scalar_one_or_none()
            if cust:
                customer_ctx = {
                    "customer_id": cust.id,
                    "customer_age_days": cust.customer_age_days,
                    "opted_out": cust.opt_out,
                    "email": PromptInjectionDefense.sanitize_untrusted_data(cust.email),
                }

        # 3. Call ML Predictor
        amount_float = float(case.amount_at_risk)
        case_dict = {
            "id": case.id,
            "amount_at_risk": amount_float,
            "failure_type": case.failure_type,
            "entity_type": case.entity_type,
            "retry_count": case.retry_count,
        }
        prediction = predictor.predict(case_dict, customer_history=customer_ctx)

        amount_decimal = Decimal(str(amount_float)).quantize(Decimal("0.01"))
        expected_recovery_dec = calculate_expected_recovery(amount_float, prediction.probability)
        band = get_recoverability_band(prediction.probability)

        summary = (
            f"Case {case.id} represents INR {amount_decimal:,.2f} at risk from {case.failure_type}. "
            f"Estimated recovery probability is {prediction.probability * 100:.1f}% ({band.value} band) "
            f"with expected recovery value of INR {expected_recovery_dec:,.2f}."
        )

        return RevenueOpportunity(
            case_id=case.id,
            entity_type=case.entity_type,
            amount=amount_decimal,
            failure_type=case.failure_type,
            customer_context=customer_ctx,
            recoverability_probability=prediction.probability,
            expected_recovery=expected_recovery_dec,
            recoverability_band=band.value,
            opportunity_summary=summary,
        )
