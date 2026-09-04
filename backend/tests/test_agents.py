import pytest
from decimal import Decimal
from app.database import async_session_factory
from app.models.entities import Customer, RecoveryCase, RecoveryState
from app.agents.base import BaseAgent
from app.agents.detective import RevenueDetective, RevenueOpportunity
from app.agents.diagnosis import DiagnosisAgent, DiagnosisOutput
from app.agents.planner import RecoveryPlanner, RecoveryPlanOutput
from app.agents.execution import ExecutionAgent


def test_agent_step_limit_enforcement():
    """Verify agent cannot exceed configured maximum steps (MAX_AGENT_STEPS=12)."""
    agent = BaseAgent(name="TestStepAgent", max_steps=3)
    agent.increment_step()  # 1
    agent.increment_step()  # 2
    agent.increment_step()  # 3

    with pytest.raises(RuntimeError, match="exceeded maximum allowed execution steps"):
        agent.increment_step()  # 4 -> Must raise and escalate to HUMAN_REVIEW


@pytest.mark.asyncio
async def test_revenue_detective_and_diagnosis_flow():
    """Verify Revenue Detective and Diagnosis Agent pipeline."""
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_agents")
        if not cust:
            cust = Customer(id="cust_test_agents", name="Agent Customer", email="agent@example.com", phone="+919999999999", customer_age_days=150, opt_out=False)
            session.add(cust)
            await session.commit()

        import uuid
        case_id = f"agent_test_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_{case_id}",
            customer_id="cust_test_agents",
            amount_at_risk=24999.0,
            failure_type="timeout",
            failure_reason="Issuer timeout",
            state=RecoveryState.FAILED,
            retry_count=0,
        )
        session.add(case)
        await session.commit()

        # Step 1: Detective
        detective = RevenueDetective()
        opp = await detective.analyze_opportunity(case_id, session)
        assert isinstance(opp.amount, Decimal)
        assert opp.amount == Decimal("24999.00")
        assert opp.recoverability_probability > 0.0
        assert opp.recoverability_band in ["HIGH", "MEDIUM", "LOW"]

        # Step 2: Diagnosis
        diagnosis_agent = DiagnosisAgent()
        diag = await diagnosis_agent.diagnose(opp)
        assert isinstance(diag, DiagnosisOutput)
        assert diag.diagnosis == "TRANSIENT_FAILURE"
        assert diag.recommended_recovery_family == "RETRY"

        # Step 3: Planner
        planner = RecoveryPlanner()
        plan = await planner.plan_recovery(opp, diag)
        assert isinstance(plan, RecoveryPlanOutput)
        assert plan.recommended_strategy == "RETRY"
        assert len(plan.alternatives) > 0
