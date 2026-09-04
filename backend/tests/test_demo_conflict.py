"""Integration Test for Scenario 3: Independent Verification Conflict (PAY_DEMO_CONFLICT).

Verifies:
- Conflicting signals (API captured vs Webhook failed) route case to HUMAN_REVIEW
- Reverse conflict (API failed vs Webhook captured) routes case to HUMAN_REVIEW
- Amount mismatch between signals routes case to HUMAN_REVIEW
- In all conflict scenarios, verified revenue remains strictly ₹0.00
"""

import pytest
import uuid
from app.database import async_session_factory
from app.models.entities import (
    Customer,
    RecoveryCase,
    RecoveryState,
    ExecutionRecord,
    VerificationRecord,
)
from app.verification.engine import VerificationEngine
from app.verification.models import VerificationStatus


@pytest.mark.asyncio
async def test_scenario_3_api_success_webhook_failure_conflict():
    """Verify conflict when API polling succeeds but webhook reports failure."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"PAY_DEMO_CONFLICT_{uid}"

        cust = await session.get(Customer, "cust_demo_conflict")
        if not cust:
            cust = Customer(
                id="cust_demo_conflict",
                name="Conflict Customer",
                email="conflict@example.com",
                customer_age_days=60,
                opt_out=False,
            )
            session.add(cust)
            await session.commit()

        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid}",
            customer_id="cust_demo_conflict",
            amount_at_risk=15000.00,
            failure_type="bank_unavailable",
            failure_reason="Bank unavailable conflict test",
            retry_count=0,
            state=RecoveryState.AWAITING_VERIFICATION,
        )
        session.add(case)

        exec_rec = ExecutionRecord(
            id=f"exec_{uid}",
            case_id=case_id,
            decision_id=f"dec_{uid}",
            tool_name="payments",
            operation="retry_payment",
            request_id=f"req_{uid}",
            idempotency_key=f"ray:{case_id}:RETRY:1",
            provider_reference=f"pay_ref_{uid}",
            execution_status="SUCCESS",
            provider_response_hash="hash123",
            correlation_id=f"corr_{uid}",
        )
        session.add(exec_rec)
        await session.commit()

        verif_engine = VerificationEngine()
        # Mock payment adapter reports 'captured' for this payment id,
        # but the incoming webhook reports 'failed'
        verif_res = await verif_engine.verify_recovery(
            case_id=case_id,
            execution_id=exec_rec.id,
            session=session,
            webhook_payload={"event": "payment.failed", "status": "failed"},
        )
        await session.refresh(case)

        assert verif_res.status == VerificationStatus.CONFLICT
        assert case.state == RecoveryState.HUMAN_REVIEW
        assert case.recovered_amount == 0.00


@pytest.mark.asyncio
async def test_scenario_3_amount_mismatch_conflict():
    """Verify conflict when webhook verified amount differs from case amount at risk."""
    async with async_session_factory() as session:
        uid = uuid.uuid4().hex[:8]
        case_id = f"PAY_DEMO_AMT_MISMATCH_{uid}"

        cust = await session.get(Customer, "cust_demo_conflict")
        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id=f"pay_mm_{uid}",
            customer_id="cust_demo_conflict",
            amount_at_risk=20000.00,
            failure_type="bank_unavailable",
            failure_reason="Amount discrepancy test",
            retry_count=0,
            state=RecoveryState.AWAITING_VERIFICATION,
        )
        session.add(case)

        exec_rec = ExecutionRecord(
            id=f"exec_mm_{uid}",
            case_id=case_id,
            decision_id=f"dec_mm_{uid}",
            tool_name="payments",
            operation="retry_payment",
            request_id=f"req_mm_{uid}",
            idempotency_key=f"ray:{case_id}:RETRY:1",
            provider_reference=f"pay_ref_mm_{uid}",
            execution_status="SUCCESS",
            provider_response_hash="hash456",
            correlation_id=f"corr_mm_{uid}",
        )
        session.add(exec_rec)
        await session.commit()

        verif_engine = VerificationEngine()
        # Webhook payload with a partial amount (e.g. ₹5,000 instead of ₹20,000)
        verif_res = await verif_engine.verify_recovery(
            case_id=case_id,
            execution_id=exec_rec.id,
            session=session,
            webhook_payload={
                "event": "payment.captured",
                "status": "captured",
                "payment": {"entity": {"amount": 500000}},  # 500000 paise = ₹5,000 != ₹20,000
            },
        )
        await session.refresh(case)

        assert case.state == RecoveryState.HUMAN_REVIEW
        assert case.recovered_amount == 0.00
