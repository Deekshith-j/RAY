import pytest
from app.database import async_session_factory
from app.models.entities import Customer, RecoveryCase, ExecutionRecord, RecoveryState
from app.verification.engine import VerificationEngine
from app.verification.models import VerificationStatus
from app.integrations.razorpay.mock_adapter import MockPaymentAdapter


@pytest.mark.asyncio
async def test_dual_signal_verification_agreement():
    """Verify agreement between API and webhook marks case RECOVERED."""
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_verif")
        if not cust:
            cust = Customer(id="cust_test_verif", name="Verif Customer", email="verif@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        import uuid
        uid1 = uuid.uuid4().hex[:8]
        case_id_1 = f"verif_case_agree_{uid1}"
        exec_id_1 = f"exec_agree_{uid1}"

        case = RecoveryCase(
            id=case_id_1,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid1}",
            customer_id="cust_test_verif",
            amount_at_risk=4999.0,
            failure_type="timeout",
            failure_reason="Timeout",
            state=RecoveryState.AWAITING_VERIFICATION,
            retry_count=1,
        )
        session.add(case)

        exec_rec = ExecutionRecord(
            id=exec_id_1,
            case_id=case_id_1,
            decision_id=f"dec_{uid1}",
            tool_name="payments",
            operation="retry_payment",
            request_id=f"req_{uid1}",
            idempotency_key=f"ray:{case_id_1}:RETRY:1",
            provider_reference="pay_agree_123",
            execution_status="SUCCESS",
            provider_response_hash="hash_agree",
            correlation_id="RAY-agree",
        )
        session.add(exec_rec)
        await session.commit()

        # Gateway reports captured
        mock_gateway = MockPaymentAdapter(default_status="captured")
        engine = VerificationEngine(payment_gateway=mock_gateway)

        # Webhook payload confirms captured
        result = await engine.verify_recovery(
            case_id=case_id_1,
            execution_id=exec_id_1,
            session=session,
            webhook_payload={"event": "payment.captured", "status": "captured"},
        )

        assert result.status == VerificationStatus.VERIFIED
        assert result.verified_amount == 4999.0
        assert len(result.evidence_hash) == 64  # SHA-256

        await session.refresh(case)
        assert case.state == RecoveryState.RECOVERED
        assert case.recovered_amount == 4999.0


@pytest.mark.asyncio
async def test_dual_signal_conflict_escalates_to_human_review():
    """Verify that conflicting signals (API failed vs Webhook captured) escalate to HUMAN_REVIEW."""
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_verif")
        if not cust:
            cust = Customer(id="cust_test_verif", name="Verif Customer", email="verif@example.com", phone="+919999999999", customer_age_days=100, opt_out=False)
            session.add(cust)
            await session.commit()

        import uuid
        uid2 = uuid.uuid4().hex[:8]
        case_id_2 = f"verif_case_conflict_{uid2}"
        exec_id_2 = f"exec_conf_{uid2}"

        case = RecoveryCase(
            id=case_id_2,
            entity_type="PAYMENT",
            entity_id=f"pay_{uid2}",
            customer_id="cust_test_verif",
            amount_at_risk=10000.0,
            failure_type="timeout",
            failure_reason="Timeout",
            state=RecoveryState.AWAITING_VERIFICATION,
            retry_count=1,
        )
        session.add(case)

        exec_rec = ExecutionRecord(
            id=exec_id_2,
            case_id=case_id_2,
            decision_id=f"dec_{uid2}",
            tool_name="payments",
            operation="retry_payment",
            request_id=f"req_{uid2}",
            idempotency_key=f"ray:{case_id_2}:RETRY:1",
            provider_reference="pay_conf_123",
            execution_status="SUCCESS",
            provider_response_hash="hash_conf",
            correlation_id="RAY-conf",
        )
        session.add(exec_rec)
        await session.commit()

        # Gateway API reports failed
        mock_gateway = MockPaymentAdapter(default_status="failed")
        engine = VerificationEngine(payment_gateway=mock_gateway)

        # Webhook says captured (Discrepancy)
        result = await engine.verify_recovery(
            case_id=case_id_2,
            execution_id=exec_id_2,
            session=session,
            webhook_payload={"event": "payment.captured", "status": "captured"},
        )

        assert result.status == VerificationStatus.CONFLICT
        assert result.verified_amount == 0.0  # Unverified money NOT counted

        await session.refresh(case)
        assert case.state == RecoveryState.HUMAN_REVIEW
        assert case.recovered_amount == 0.0
