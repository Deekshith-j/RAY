import pytest
from datetime import datetime
from app.database import async_session_factory, init_db
from app.models.entities import (
    Customer,
    RecoveryCase,
    RecoveryPredictionRecord,
    RecoveryDecision,
    ExecutionRecord,
    VerificationRecord,
    RecoveryState,
)


@pytest.mark.asyncio
async def test_financial_provenance_lineage():
    """
    Verify complete financial provenance chain:
    Prediction -> Decision -> Execution -> Verification
    """
    await init_db()
    async with async_session_factory() as session:
        cust = await session.get(Customer, "cust_test_prov")
        if not cust:
            cust = Customer(id="cust_test_prov", name="Prov Customer", email="prov@example.com", phone="+919999999999", customer_age_days=120, opt_out=False)
            session.add(cust)
            await session.commit()

        case_id = f"prov_test_{int(datetime.utcnow().timestamp())}"
        case = RecoveryCase(
            id=case_id,
            entity_type="PAYMENT",
            entity_id="pay_prov_1",
            customer_id="cust_test_prov",
            amount_at_risk=15000.0,
            failure_type="timeout",
            failure_reason="Gateway timeout",
            state=RecoveryState.FAILED,
            retry_count=0,
        )
        session.add(case)
        await session.commit()

        # 1. Prediction Record
        pred = RecoveryPredictionRecord(
            case_id=case_id,
            model_version="ray-recov-v1-production",
            probability=0.91,
            expected_recovery=13650.0,
            recoverability_band="HIGH",
            features_json={"amount": 15000.0, "failure_type": "timeout"},
            correlation_id=f"RAY-{case_id}",
        )
        session.add(pred)
        await session.commit()
        await session.refresh(pred)

        # 2. Decision Record
        dec = RecoveryDecision(
            id=f"dec_{case_id}",
            case_id=case_id,
            prediction_id=pred.id,
            recommended_strategy="RETRY",
            probability_of_recovery=pred.probability,
            expected_recovery=pred.expected_recovery,
            rationale="Transient timeout with high recoverability",
            policy_result="ALLOW",
            policy_version="v1.0",
            authorization_required=False,
            authorization_status="AUTHORIZED",
            correlation_id=f"RAY-{case_id}",
        )
        session.add(dec)
        await session.commit()

        # 3. Execution Record
        exec_rec = ExecutionRecord(
            id=f"exec_{case_id}",
            case_id=case_id,
            decision_id=dec.id,
            tool_name="payments",
            operation="retry_payment",
            request_id="req_123",
            idempotency_key=f"ray:{case_id}:RETRY:1",
            provider_reference="pay_mock_123",
            execution_status="SUCCESS",
            provider_response_hash="hash123",
            correlation_id=f"RAY-{case_id}",
        )
        session.add(exec_rec)
        await session.commit()

        # 4. Verification Record
        verif = VerificationRecord(
            id=f"verif_{case_id}",
            case_id=case_id,
            execution_id=exec_rec.id,
            webhook_confirmed=True,
            api_state_confirmed=True,
            provider_status="captured",
            verified_amount=15000.0,
            verification_status="VERIFIED",
            evidence_hash="ev_hash_123",
            correlation_id=f"RAY-{case_id}",
        )
        session.add(verif)
        case.state = RecoveryState.RECOVERED
        case.recovered_amount = 15000.0
        case.verification_id = verif.id
        await session.commit()

        # Verify Linkage Integrity
        assert dec.prediction_id == pred.id
        assert exec_rec.decision_id == dec.id
        assert verif.execution_id == exec_rec.id
        assert case.verification_id == verif.id
        assert case.state == RecoveryState.RECOVERED
