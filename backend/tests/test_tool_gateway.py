import pytest
from datetime import datetime
from app.database import async_session_factory
from app.models.entities import Customer, RecoveryCase, RecoveryDecision, RecoveryState
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest


@pytest.mark.asyncio
async def test_tool_gateway_rejects_unauthorized_high_value():
    """Verify Tool Gateway strictly blocks execution when high-value approval is pending."""
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_gate")
        if not cust:
            cust = Customer(id="cust_test_gate", name="Gate Customer", email="gate@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        import uuid
        uid1 = uuid.uuid4().hex[:8]
        case_id_1 = f"gate_case_high_{uid1}"
        dec_id_1 = f"gate_dec_high_{uid1}"

        case = RecoveryCase(
            id=case_id_1,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid1}",
            customer_id="cust_test_gate",
            amount_at_risk=75000.0,
            failure_type="timeout",
            failure_reason="Timeout",
            state=RecoveryState.AWAITING_APPROVAL,
            retry_count=0,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=dec_id_1,
            case_id=case_id_1,
            recommended_strategy="PAYMENT_LINK",
            probability_of_recovery=0.95,
            expected_recovery=71250.0,
            rationale="High value timeout",
            policy_result="REQUIRE_HUMAN_APPROVAL",
            authorization_required=True,
            authorization_status="PENDING",  # Not yet approved
            correlation_id="RAY-test-high",
        )
        session.add(decision)
        await session.commit()

        gateway = ToolGateway()
        req = ToolCallRequest(
            tool_name="payment_links",
            operation="create_payment_link",
            case_id=case_id_1,
            decision_id=dec_id_1,
            idempotency_key=f"ray:{case_id_1}:PAYMENT_LINK:1",
            correlation_id="RAY-test-high",
        )

        res = await gateway.execute(req, session)
        assert res.status == "REJECTED"
        assert "requires human approval" in res.rejection_reason.lower()


@pytest.mark.asyncio
async def test_tool_gateway_rejects_mismatched_strategy():
    """Verify Tool Gateway blocks tool operations that do not match the authorized strategy."""
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_gate")
        if not cust:
            cust = Customer(id="cust_test_gate", name="Gate Customer", email="gate@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        import uuid
        uid2 = uuid.uuid4().hex[:8]
        case_id_2 = f"gate_case_strat_{uid2}"
        dec_id_2 = f"gate_dec_strat_{uid2}"

        case = RecoveryCase(
            id=case_id_2,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid2}",
            customer_id="cust_test_gate",
            amount_at_risk=2000.0,
            failure_type="timeout",
            failure_reason="Timeout",
            state=RecoveryState.RECOVERY_PLANNED,
            retry_count=0,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=dec_id_2,
            case_id=case_id_2,
            recommended_strategy="RETRY",
            probability_of_recovery=0.88,
            expected_recovery=1760.0,
            rationale="Timeout retry",
            policy_result="ALLOW",
            authorization_required=False,
            authorization_status="AUTHORIZED",
            correlation_id="RAY-test-strat",
        )
        session.add(decision)
        await session.commit()

        gateway = ToolGateway()
        # Requesting create_payment_link when strategy is RETRY
        req = ToolCallRequest(
            tool_name="payment_links",
            operation="create_payment_link",
            case_id=case_id_2,
            decision_id=dec_id_2,
            idempotency_key=f"ray:{case_id_2}:PAYMENT_LINK:1",
            correlation_id="RAY-test-strat",
        )

        res = await gateway.execute(req, session)
        assert res.status == "REJECTED"
        assert "does not match authorized strategy" in res.rejection_reason.lower()
