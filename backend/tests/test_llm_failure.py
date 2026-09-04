"""Tests for LLM failure modes and safe escalation to HUMAN_REVIEW."""

import pytest
import uuid
from app.database import async_session_factory
from app.agents.orchestrator import AgentOrchestrator
from app.models.entities import RecoveryCase, Customer, RecoveryState


@pytest.mark.asyncio
async def test_llm_unsupported_strategy_escalates_to_human_review(monkeypatch):
    orchestrator = AgentOrchestrator()

    # Mock planner to simulate LLM hallucination / unsupported strategy
    async def mock_hallucinated_plan(opportunity, diagnosis):
        from app.agents.planner import RecoveryPlanOutput
        return RecoveryPlanOutput(
            recommended_strategy="ARBITRARY_CRYPTO_REVERSAL",
            rationale="Hallucinated LLM response",
            expected_recovery="100.00",
        )

    monkeypatch.setattr(orchestrator.planner, "plan_recovery", mock_hallucinated_plan)

    async with async_session_factory() as session:
        cid = f"cust_llm_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="llm@fail.com", name="Fail Cust", phone="1234567890")
        session.add(cust)

        case_id = f"case_llm_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=2000.0,
            failure_type="timeout",
            failure_reason="Gateway timeout on payment processing",
            state=RecoveryState.FAILED,
        )
        session.add(case)
        await session.commit()

        res = await orchestrator.run_full_recovery_flow(case_id, session)

        # Invariant check: MUST STOP and escalate to HUMAN_REVIEW
        assert res["case_state"] == "HUMAN_REVIEW"
        assert "unsupported or hallucinated" in res["error"]
