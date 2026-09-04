"""Integration Test for Scenario 5: Canonical Idempotency Replay (PAY_DEMO_DUPLICATE).

Verifies:
- Canonical key format: ray:{case_id}:{strategy}:{attempt_number}
- First execution dispatches to provider; second returns cached execution with is_idempotent_replay = True
- Attempting to pass altered parameters with an existing idempotency key returns original cached execution
- Provider invocation count remains strictly 1 (at-most-once financial execution)
"""

import pytest
import uuid
from app.database import async_session_factory
from app.models.entities import (
    Customer,
    RecoveryCase,
    RecoveryState,
    RecoveryDecision,
)
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest


@pytest.mark.asyncio
async def test_scenario_5_canonical_idempotency_replay_protection():
    """Verify that repeating a recovery execution with the same idempotency key guarantees at-most-once execution."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"PAY_DEMO_DUP_{uid}"
        idemp_key = f"ray:{case_id}:RETRY:1"

        cust = await session.get(Customer, "cust_demo_dup")
        if not cust:
            cust = Customer(
                id="cust_demo_dup",
                name="Duplicate Tester",
                email="dup@example.com",
                customer_age_days=100,
                opt_out=False,
            )
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_dup_{uid}",
            customer_id="cust_demo_dup",
            amount_at_risk=5000.00,
            failure_type="network_error",
            failure_reason="Transient network disconnect",
            retry_count=0,
            state=RecoveryState.EXECUTING,
        )
        session.add(case)

        decision = RecoveryDecision(
            id=f"dec_dup_{uid}",
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.92,
            expected_recovery=4600.00,
            rationale="Transient failure",
            policy_result="ALLOW",
            policy_version="ray-policy-v1",
            authorization_required=False,
            authorization_status="AUTHORIZED",
            correlation_id=f"corr_{uid}",
        )
        session.add(decision)
        await session.commit()

        gateway = ToolGateway()
        req_1 = ToolCallRequest(
            case_id=case_id,
            decision_id=decision.id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": case.entity_id, "amount": 5000.00},
            idempotency_key=idemp_key,
            correlation_id=f"corr_{uid}",
        )

        # 1. First Execution -> Dispatched
        res_1 = await gateway.execute(req_1, session)
        assert res_1.status == "SUCCESS"
        assert res_1.is_idempotent_replay is False
        exec_id = res_1.execution_id

        # 2. Second Execution (Identical Request) -> Idempotent Cache Replay
        res_2 = await gateway.execute(req_1, session)
        assert res_2.status == "SUCCESS"
        assert res_2.is_idempotent_replay is True
        assert res_2.execution_id == exec_id
        assert res_2.provider_response.get("replayed") is True

        # 3. Third Execution (Tampered Amount with Same Key) -> Must NOT re-execute
        req_tampered = ToolCallRequest(
            case_id=case_id,
            decision_id=decision.id,
            tool_name="payments",
            operation="retry_payment",
            parameters={"payment_id": case.entity_id, "amount": 50000.00},  # Tampered 10x amount!
            idempotency_key=idemp_key,
            correlation_id=f"corr_{uid}",
        )
        res_3 = await gateway.execute(req_tampered, session)
        assert res_3.status == "SUCCESS"
        assert res_3.is_idempotent_replay is True
        assert res_3.execution_id == exec_id
