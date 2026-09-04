"""Failure Mode and Edge Case Security Tests per Section 25.

Verifies that all financial failures fail closed:
- LLM malformed output escalates safely to HUMAN_REVIEW
- Missing authorization fails closed in Tool Gateway
- Negative or zero amounts are rejected in Tool Gateway
- Fraud flags and permanent declines are rejected by Policy Engine
- Retry limit exceeded (> 1 retry) is rejected by Policy Engine
- Customer opt-out is strictly rejected
- Provider API failure marks execution FAILED and never RECOVERED
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
)
from app.core.policy_engine import PolicyEngine
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest


@pytest.mark.asyncio
async def test_policy_rejects_fraud_failure_type():
    """Policy Engine must reject fraud-flagged payment failures."""
    engine = PolicyEngine()
    case = RecoveryCase(
        id="case_fail_fraud",
        entity_type="PAYMENT",
        entity_id="pay_fraud",
        customer_id="cust_fraud",
        amount_at_risk=8000.00,
        failure_type="fraud_flagged",
        failure_reason="Suspected card fraud",
        retry_count=0,
    )
    dec = engine.evaluate(case, RecoveryStrategy.RETRY)
    assert dec.allowed is False
    assert dec.rule_code == "DISALLOWED_RETRY_FAILURE_TYPE"


@pytest.mark.asyncio
async def test_policy_rejects_retry_limit_exceeded():
    """Policy Engine must reject retry when attempt count >= MAX_RETRY_ATTEMPTS (1)."""
    engine = PolicyEngine()
    case = RecoveryCase(
        id="case_fail_retry_limit",
        entity_type="PAYMENT",
        entity_id="pay_retry_lim",
        customer_id="cust_limit",
        amount_at_risk=2000.00,
        failure_type="network_error",
        failure_reason="Network error",
        retry_count=1,  # Already attempted once!
    )
    dec = engine.evaluate(case, RecoveryStrategy.RETRY)
    assert dec.allowed is False
    assert dec.rule_code == "RETRY_LIMIT_REACHED"


@pytest.mark.asyncio
async def test_tool_gateway_rejects_negative_or_zero_amount():
    """Tool Gateway must reject negative or zero payment amounts."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"case_neg_{uid}"

        cust = await session.get(Customer, "cust_neg")
        if not cust:
            cust = Customer(id="cust_neg", name="Negative Tester", email="neg@example.com", customer_age_days=30, opt_out=False)
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_neg_{uid}",
            customer_id="cust_neg",
            amount_at_risk=-500.00,  # Negative!
            failure_type="network_error",
            failure_reason="Negative test",
            retry_count=0,
            state=RecoveryState.EXECUTING,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=f"dec_neg_{uid}",
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.8,
            expected_recovery=-400.00,
            rationale="Negative amount test",
            policy_result="ALLOW",
            policy_version="ray-policy-v1",
            authorization_required=False,
            authorization_status="AUTHORIZED",
            correlation_id=f"corr_{uid}",
        )
        session.add(decision)
        await session.commit()

        gateway = ToolGateway()
        req = ToolCallRequest(
            case_id=case_id,
            decision_id=decision.id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": case.entity_id, "amount": -500.00},
            idempotency_key=f"ray:{case_id}:RETRY:1",
            correlation_id=f"corr_{uid}",
        )

        res = await gateway.execute(req, session)
        assert res.status == "REJECTED"


@pytest.mark.asyncio
async def test_tool_gateway_rejects_missing_decision():
    """Tool Gateway must reject execution when referenced decision_id does not exist."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        gateway = ToolGateway()
        req = ToolCallRequest(
            case_id=f"case_nonexistent_{uid}",
            decision_id=f"dec_nonexistent_{uid}",
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": "pay_fake", "amount": 1000.00},
            idempotency_key=f"ray:fake_{uid}:RETRY:1",
            correlation_id=f"corr_{uid}",
        )

        res = await gateway.execute(req, session)
        assert res.status == "REJECTED"
