"""Test Policy Engine and Agent Safety Boundary.

Enforces Non-Negotiable Invariants:
PREDICTION != RECOMMENDATION != POLICY AUTHORIZATION != EXECUTION != INDEPENDENT VERIFICATION

- Agents cannot authorize financial actions.
- Agents cannot directly call payment gateways.
- Deterministic Policy Engine has absolute authority to veto any LLM recommendation.
- Tool Gateway strictly refuses unauthorized or overridden recommendations.
"""

import pytest
import uuid
from app.database import async_session_factory
from app.models.entities import (
    RecoveryCase,
    RecoveryState,
    RecoveryStrategy,
    RecoveryDecision,
    Customer,
)
from app.core.policy_engine import PolicyEngine
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest


@pytest.mark.asyncio
async def test_policy_engine_vetoes_agent_recommendation_on_permanent_failure():
    """Policy Engine must veto an advisory agent recommending RETRY on permanent failure."""
    engine = PolicyEngine()
    case = RecoveryCase(
        id="case_perm_failure",
        entity_type="PAYMENT",
        entity_id="pay_perm",
        customer_id="cust_perm",
        amount_at_risk=2500.00,
        failure_type="fraud_flagged",
        failure_reason="Permanent fraud rejection by card network",
        retry_count=0,
        state=RecoveryState.RECOVERY_PLANNED,
    )

    # Advisory agent recommends RETRY (hallucinated or reckless recommendation)
    advisory_recommendation = RecoveryStrategy.RETRY

    # Deterministic Policy Engine evaluation
    decision = engine.evaluate(case, advisory_recommendation)

    assert not decision.allowed, "Policy Engine MUST reject retry on fraud_flagged!"
    assert decision.rule_code == "DISALLOWED_RETRY_FAILURE_TYPE"
    assert decision.fallback_strategy == RecoveryStrategy.PAYMENT_LINK


@pytest.mark.asyncio
async def test_policy_engine_vetoes_agent_on_opted_out_customer():
    """Policy Engine must strictly enforce customer opt-out, overriding any agent plan."""
    engine = PolicyEngine()
    customer = Customer(
        id="cust_opt_out",
        email="optout@domain.com",
        name="Opted Out User",
        opt_out=True,
    )
    case = RecoveryCase(
        id="case_optout",
        entity_type="PAYMENT",
        entity_id="pay_optout",
        customer_id=customer.id,
        amount_at_risk=1000.00,
        failure_type="network_error",
        failure_reason="Network error",
        retry_count=0,
        state=RecoveryState.RECOVERY_PLANNED,
    )

    # Advisory agent recommends RETRY
    decision = engine.evaluate(case, RecoveryStrategy.RETRY, customer=customer)

    assert not decision.allowed
    assert decision.rule_code == "CUSTOMER_OPT_OUT"


@pytest.mark.asyncio
async def test_tool_gateway_rejects_agent_attempt_without_authorized_policy():
    """Tool Gateway must reject any execution where policy did not authorize the action."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"case_unauth_{uid}"
        dec_id = f"dec_unauth_{uid}"

        cust = await session.get(Customer, "cust_test_pab")
        if not cust:
            cust = Customer(id="cust_test_pab", name="PAB Customer", email="pab@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid}",
            customer_id="cust_test_pab",
            amount_at_risk=15000.00,  # Exceeds ₹10,000 auto-retry
            failure_type="network_error",
            failure_reason="Network timeout",
            retry_count=0,
            state=RecoveryState.RECOVERY_PLANNED,
        )
        session.add(case)

        # Agent records a DENIED decision
        denied_decision = RecoveryDecision(
            id=dec_id,
            case_id=case.id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.95,
            expected_recovery=14250.00,
            rationale="Agent wants to retry anyway",
            policy_result="DENY",
            policy_version="ray-policy-v1",
            authorization_required=False,
            authorization_status="REJECTED",
            correlation_id=f"corr_{uid}",
        )
        session.add(denied_decision)
        await session.commit()

        gateway = ToolGateway()
        request = ToolCallRequest(
            case_id=case.id,
            decision_id=denied_decision.id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": case.entity_id, "amount": 15000.00},
            idempotency_key=f"ray:{case.id}:RETRY:1",
            correlation_id=f"corr_{uid}",
        )

        result = await gateway.execute(request, session)

        assert result.status == "REJECTED"
        assert any(term in result.rejection_reason.lower() for term in ["denied", "rejected", "not authorized"])
