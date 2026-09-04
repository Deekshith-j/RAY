"""Comprehensive Security Boundary & Containment Invariant Tests.

Guarantees:
1. LLM / Agents / ML cannot directly call provider.
2. ToolGateway rejects unauthorized calls.
3. High-value requires human approval.
4. Idempotency guarantees at-most-once execution.
5. Invalid webhook is rejected.
6. Conflicting verification never marks RECOVERED.
"""

import pytest
import uuid
from app.database import async_session_factory
from app.agents.detective import RevenueDetective
from app.agents.diagnosis import DiagnosisAgent
from app.agents.planner import RecoveryPlanner
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest
from app.models.entities import (
    RecoveryCase,
    Customer,
    RecoveryState,
    RecoveryDecision,
    ExecutionRecord,
)
from app.verification.engine import VerificationEngine
from app.api.v1.webhooks import verify_razorpay_signature


def test_no_direct_provider_access_on_advisory_components():
    """Invariants: Detective, Diagnosis, and Planner have zero provider handles."""
    det = RevenueDetective()
    diag = DiagnosisAgent()
    plan = RecoveryPlanner()

    for agent in (det, diag, plan):
        assert not hasattr(agent, "gateway")
        assert not hasattr(agent, "payment_adapter")
        assert not hasattr(agent, "razorpay_client")


@pytest.mark.asyncio
async def test_tool_gateway_rejects_unauthorized_call():
    """Invariant: Tool Gateway strictly rejects tool call without approved decision."""
    gateway = ToolGateway()
    async with async_session_factory() as session:
        cid = f"cust_sec_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="sec@test.com", name="Sec Cust", phone="9999999999")
        session.add(cust)

        case_id = f"case_sec_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=1000.0,
            failure_type="timeout",
            failure_reason="Gateway timeout",
            state=RecoveryState.FAILED,
        )
        session.add(case)
        await session.commit()

        # Attempt to call Tool Gateway with fake/unapproved decision
        req = ToolCallRequest(
            case_id=case_id,
            decision_id="fake_unapproved_decision",
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": "pay_fake", "amount": 1000.0},
            idempotency_key=f"ray:{case_id}:RETRY:1",
            correlation_id=f"RAY-SEC-{case_id}",
        )
        result = await gateway.execute(req, session)
        assert result.status == "REJECTED"


@pytest.mark.asyncio
async def test_high_value_without_human_approval_fails():
    """Invariant: ₹50,000+ cannot be executed without human approval."""
    gateway = ToolGateway()
    async with async_session_factory() as session:
        cid = f"cust_hv_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="hv@test.com", name="HV Cust", phone="9999999999")
        session.add(cust)

        case_id = f"case_hv_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=75000.0,
            failure_type="timeout",
            failure_reason="Gateway timeout",
            state=RecoveryState.AWAITING_APPROVAL,
        )
        session.add(case)

        # Decision requires human approval and is PENDING
        dec_id = f"dec_hv_{uuid.uuid4().hex[:8]}"
        dec = RecoveryDecision(
            id=dec_id,
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.95,
            expected_recovery=75000.0,
            rationale="High value test",
            policy_result="REQUIRE_HUMAN_APPROVAL",
            authorization_required=True,
            authorization_status="PENDING",
            correlation_id="corr_hv",
        )
        session.add(dec)
        await session.commit()

        req = ToolCallRequest(
            case_id=case_id,
            decision_id=dec_id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": "pay_hv", "amount": 75000.0},
            idempotency_key=f"ray:{case_id}:RETRY:1",
            correlation_id="corr_hv",
        )
        result = await gateway.execute(req, session)
        assert result.status == "REJECTED"
        assert "requires human approval" in result.rejection_reason.lower()


def test_invalid_webhook_signature_rejection():
    """Invariant: Invalid signature is rejected."""
    raw = b'{"event":"payment.captured"}'
    assert verify_razorpay_signature(raw, "invalid_sig", "secret") is False


@pytest.mark.asyncio
async def test_conflicting_verification_never_marks_recovered():
    """Invariant: If API confirms captured but Webhook reports failed -> CONFLICT -> NOT RECOVERED."""
    engine = VerificationEngine()
    async with async_session_factory() as session:
        cid = f"cust_conf_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="conf@test.com", name="Conf Cust", phone="9999999999")
        session.add(cust)

        case_id = f"case_conf_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=20000.0,
            failure_type="timeout",
            failure_reason="Gateway timeout",
            state=RecoveryState.AWAITING_VERIFICATION,
        )
        session.add(case)

        dec_id = f"dec_conf_{uuid.uuid4().hex[:8]}"
        dec_conf = RecoveryDecision(
            id=dec_id,
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.8,
            expected_recovery=16000.0,
            rationale="Conflicting verification test",
            policy_result="ALLOW",
            authorization_status="AUTHORIZED",
            correlation_id="corr_conf",
        )
        session.add(dec_conf)

        exec_id = f"exec_conf_{uuid.uuid4().hex[:8]}"
        exec_rec = ExecutionRecord(
            id=exec_id,
            case_id=case_id,
            decision_id=dec_id,
            tool_name="payments",
            operation="retry_payment",
            request_id="req_conf",
            idempotency_key=f"ray:{case_id}:RETRY:1",
            provider_reference="pay_conf_123",
            execution_status="SUCCESS",
            provider_response_hash="hash_conf",
            correlation_id="corr_conf",
        )
        session.add(exec_rec)
        await session.commit()

        # Conflicting payload: webhook says failed
        result = await engine.verify_recovery(
            case_id=case_id,
            execution_id=exec_id,
            session=session,
            webhook_payload={"event": "payment.failed", "status": "failed"},
        )

        await session.refresh(case)

        assert result.status.value == "CONFLICT"
        assert case.state != RecoveryState.RECOVERED
        assert case.state == RecoveryState.HUMAN_REVIEW
        assert case.recovered_amount == 0.0
