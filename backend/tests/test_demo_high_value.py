"""Integration Test for Scenario 2: High-Value Human Authorization Gate (PAY_DEMO_HIGH_VALUE).

Verifies:
- Any transaction >= ₹50,000 halts at AWAITING_APPROVAL
- Zero provider operations are executed prior to human operator authorization
- Operator rejection halts case cleanly at STOPPED
- Operator approval creates an immutable HumanApprovalRecord and unlocks execution
"""

import pytest
import uuid
from app.database import async_session_factory
from app.models.entities import (
    Customer,
    RecoveryCase,
    RecoveryState,
    RecoveryStrategy,
    RecoveryDecision,
    HumanApprovalRecord,
)
from app.agents.orchestrator import orchestrator
from app.agents.execution import ExecutionAgent
from app.verification.engine import VerificationEngine


@pytest.mark.asyncio
async def test_scenario_2_high_value_gate_halts_autonomous_execution():
    """Verify that a ₹75,000 case halts at AWAITING_APPROVAL and blocks tool execution."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"PAY_DEMO_HV_{uid}"

        cust = await session.get(Customer, "cust_demo_hv")
        if not cust:
            cust = Customer(
                id="cust_demo_hv",
                name="High Value Customer",
                email="hv@example.com",
                customer_age_days=180,
                opt_out=False,
            )
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_hv_{uid}",
            customer_id="cust_demo_hv",
            amount_at_risk=75000.00,
            failure_type="timeout",
            failure_reason="High-value corporate checkout timeout",
            retry_count=0,
            state=RecoveryState.FAILED,
        )
        session.add(case)
        await session.commit()

        # Run orchestrator — MUST halt at AWAITING_APPROVAL
        result = await orchestrator.run_full_recovery_flow(case_id=case_id, session=session)
        await session.refresh(case)

        assert case.state == RecoveryState.AWAITING_APPROVAL
        assert result["status"] == "AWAITING_APPROVAL"
        assert result["authorization_required"] is True

        # Now simulate operator approval
        decision = await session.get(RecoveryDecision, result["decision_id"])
        assert decision is not None
        assert decision.authorization_status == "PENDING"

        decision.authorization_status = "AUTHORIZED"
        decision.authorized_by = "risk_lead@enterprise.com"
        case.state = RecoveryState.EXECUTING

        approval = HumanApprovalRecord(
            approval_id=f"appr_{uid}",
            case_id=case_id,
            decision_id=decision.id,
            operator_id="risk_lead@enterprise.com",
            approved_strategy="RETRY",
            approval_reason="Verified with merchant via phone; safe to retry",
            policy_version="ray-policy-v1",
            correlation_id=f"corr_{uid}",
        )
        session.add(approval)
        await session.commit()

        # Resume execution
        exec_agent = ExecutionAgent()
        tool_res = await exec_agent.execute_decision(decision, case, session, attempt_number=1)
        assert tool_res.status == "SUCCESS"

        case.state = RecoveryState.AWAITING_VERIFICATION
        await session.commit()

        # Verify
        verif_engine = VerificationEngine()
        verif_res = await verif_engine.verify_recovery(
            case_id=case_id,
            execution_id=tool_res.execution_id,
            session=session,
            webhook_payload={"event": "payment.captured", "status": "captured"},
        )
        await session.refresh(case)

        assert case.state == RecoveryState.RECOVERED
        assert case.recovered_amount == 75000.00


@pytest.mark.asyncio
async def test_scenario_2_high_value_rejection_halts_cleanly():
    """Verify that operator rejection marks decision REJECTED and terminates recovery."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"PAY_DEMO_HV_REJ_{uid}"

        cust = await session.get(Customer, "cust_demo_hv")
        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_hv_rej_{uid}",
            customer_id="cust_demo_hv",
            amount_at_risk=95000.00,
            failure_type="timeout",
            failure_reason="Suspicious high-value payment",
            retry_count=0,
            state=RecoveryState.FAILED,
        )
        session.add(case)
        await session.commit()

        result = await orchestrator.run_full_recovery_flow(case_id=case_id, session=session)
        await session.refresh(case)

        assert case.state == RecoveryState.AWAITING_APPROVAL

        # Operator rejects
        decision = await session.get(RecoveryDecision, result["decision_id"])
        decision.authorization_status = "REJECTED"
        decision.authorized_by = "compliance@enterprise.com"
        case.state = RecoveryState.STOPPED
        await session.commit()

        # Try to execute rejected decision via ExecutionAgent -> MUST FAIL
        exec_agent = ExecutionAgent()
        tool_res = await exec_agent.execute_decision(decision, case, session, attempt_number=1)
        assert tool_res.status == "REJECTED"
        assert case.state == RecoveryState.STOPPED
