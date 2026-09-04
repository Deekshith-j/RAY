import pytest
from app.database import async_session_factory
from app.models.entities import Customer, RecoveryCase, RecoveryDecision, RecoveryState
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest
from app.tools.idempotency import generate_idempotency_key, validate_idempotency_key_format


def test_idempotency_key_generation_and_validation():
    key = generate_idempotency_key("case_123", "RETRY", 1)
    assert key == "ray:case_123:RETRY:1"
    assert validate_idempotency_key_format(key) is True

    # Malformed keys
    assert validate_idempotency_key_format("invalid_key") is False
    assert validate_idempotency_key_format("ray:case:RETRY") is False


@pytest.mark.asyncio
async def test_idempotent_replay_prevents_duplicate_execution():
    """Verify that repeating a tool call with the same idempotency key returns the cached execution."""
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_idem")
        if not cust:
            cust = Customer(id="cust_test_idem", name="Idem Customer", email="idem@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        import uuid
        uid = uuid.uuid4().hex[:8]
        case_id = f"idem_case_{uid}"
        dec_id = f"idem_dec_{uid}"
        idem_key = f"ray:{case_id}:RETRY:1"

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid}",
            customer_id="cust_test_idem",
            amount_at_risk=3000.0,
            failure_type="timeout",
            failure_reason="Timeout",
            state=RecoveryState.RECOVERY_PLANNED,
            retry_count=0,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=dec_id,
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.90,
            expected_recovery=2700.0,
            rationale="Retry timeout",
            policy_result="ALLOW",
            authorization_required=False,
            authorization_status="AUTHORIZED",
            correlation_id="RAY-idem-test",
        )
        session.add(decision)
        await session.commit()

        gateway = ToolGateway()
        req = ToolCallRequest(
            tool_name="payments",
            operation="retry_payment",
            case_id=case_id,
            decision_id=dec_id,
            idempotency_key=idem_key,
            correlation_id="RAY-idem-test",
        )

        # First execution
        res1 = await gateway.execute(req, session)
        assert res1.status == "SUCCESS"
        assert res1.is_idempotent_replay is False

        # Duplicate execution (e.g. browser refresh or network retry)
        res2 = await gateway.execute(req, session)
        assert res2.status == "SUCCESS"
        assert res2.is_idempotent_replay is True
        assert res2.execution_id == res1.execution_id
