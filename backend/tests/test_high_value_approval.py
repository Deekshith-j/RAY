"""High-Value Transaction Human Authorization Tests.

Invariants:
- Transactions >= ₹50,000 MUST require human authorization.
- Autonomous orchestrator must halt at AWAITING_APPROVAL.
- Tool Gateway strictly rejects unauthorized execution of high-value cases.
- Formal HumanApprovalRecord must be persisted upon operator approval.
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
from app.core.policy_engine import PolicyEngine
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest


@pytest.mark.asyncio
async def test_high_value_threshold_triggers_human_approval():
    """Verify that cases >= ₹50,000 trigger REQUIRE_HUMAN_APPROVAL regardless of failure type."""
    engine = PolicyEngine()
    case_75k = RecoveryCase(
        id="case_75k",
        entity_type="PAYMENT",
        entity_id="pay_75k",
        customer_id="cust_high",
        amount_at_risk=75000.00,
        failure_type="network_error",
        failure_reason="Network error during checkout",
        retry_count=0,
        state=RecoveryState.RECOVERY_PLANNED,
    )

    decision = engine.evaluate(case_75k, RecoveryStrategy.RETRY)

    assert decision.requires_human_approval is True
    assert decision.allowed is True
    assert "human authorization required" in decision.reason.lower()


@pytest.mark.asyncio
async def test_high_value_unauthorized_tool_call_rejected():
    """Tool Gateway must reject high-value case if authorization status is PENDING."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"case_hv_unauth_{uid}"
        dec_id = f"dec_hv_pending_{uid}"

        cust = await session.get(Customer, "cust_test_hva")
        if not cust:
            cust = Customer(id="cust_test_hva", name="HVA Customer", email="hva@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_hv_{uid}",
            customer_id="cust_test_hva",
            amount_at_risk=60000.00,
            failure_type="network_error",
            failure_reason="Transient network error",
            retry_count=0,
            state=RecoveryState.AWAITING_APPROVAL,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=dec_id,
            case_id=case.id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.88,
            expected_recovery=52800.00,
            rationale="Transient failure on high value account",
            policy_result="REQUIRE_HUMAN_APPROVAL",
            policy_version="ray-policy-v1",
            authorization_required=True,
            authorization_status="PENDING",
            correlation_id=f"corr_{uid}",
        )
        session.add(decision)
        await session.commit()

        gateway = ToolGateway()
        request = ToolCallRequest(
            case_id=case.id,
            decision_id=decision.id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": case.entity_id, "amount": 60000.00},
            idempotency_key=f"ray:{case.id}:RETRY:1",
            correlation_id=f"corr_{uid}",
        )

        result = await gateway.execute(request, session)

        assert result.status == "REJECTED"
        assert "requires human approval" in result.rejection_reason.lower() or "not yet authorized" in result.rejection_reason.lower()


@pytest.mark.asyncio
async def test_high_value_authorized_tool_call_succeeds():
    """Tool Gateway succeeds when operator approves and creates formal HumanApprovalRecord."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"case_hv_auth_{uid}"
        dec_id = f"dec_hv_auth_{uid}"

        cust = await session.get(Customer, "cust_test_hva")
        if not cust:
            cust = Customer(id="cust_test_hva", name="HVA Customer", email="hva@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_hv_{uid}",
            customer_id="cust_test_hva",
            amount_at_risk=75000.00,
            failure_type="network_error",
            failure_reason="Transient network error",
            retry_count=0,
            state=RecoveryState.EXECUTING,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=dec_id,
            case_id=case.id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.91,
            expected_recovery=68250.00,
            rationale="Transient network issue",
            policy_result="REQUIRE_HUMAN_APPROVAL",
            policy_version="ray-policy-v1",
            authorization_required=True,
            authorization_status="AUTHORIZED",
            authorized_by="lead_risk_officer@corp.internal",
            correlation_id=f"corr_{uid}",
        )
        session.add(decision)

        approval_record = HumanApprovalRecord(
            approval_id=f"appr_{uid}",
            case_id=case.id,
            decision_id=decision.id,
            operator_id="lead_risk_officer@corp.internal",
            approved_strategy="RETRY",
            approval_reason="Verified with merchant via phone; safe to retry",
            policy_version="ray-policy-v1",
            correlation_id=f"corr_{uid}",
        )
        session.add(approval_record)
        await session.commit()

        gateway = ToolGateway()
        request = ToolCallRequest(
            case_id=case.id,
            decision_id=decision.id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": case.entity_id, "amount": 75000.00},
            idempotency_key=f"ray:{case.id}:RETRY:1",
            correlation_id=f"corr_{uid}",
        )

        result = await gateway.execute(request, session)

        assert result.status == "SUCCESS"
        assert result.provider_reference is not None
        assert result.execution_id is not None
