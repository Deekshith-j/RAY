"""Tests for /api/v1/recovery/{case_id}/provenance endpoint."""

import pytest
import uuid
from app.database import async_session_factory
from app.models.entities import (
    RecoveryCase,
    Customer,
    RecoveryState,
    RecoveryDecision,
    ExecutionRecord,
    VerificationRecord,
    RecoveryPredictionRecord,
)
from app.api.v1.recovery import get_case_provenance


@pytest.mark.asyncio
async def test_get_case_provenance_full_chain():
    async with async_session_factory() as session:
        cid = f"cust_prov_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="prov@test.com", name="Prov Cust", phone="9999999999")
        session.add(cust)

        case_id = f"prov_case_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=24999.00,
            failure_type="timeout",
            failure_reason="Gateway timeout on payment processing",
            state=RecoveryState.RECOVERED,
            recovered_amount=24999.00,
        )
        session.add(case)

        # 1. Prediction Record
        pred = RecoveryPredictionRecord(
            case_id=case_id,
            model_version="v1.0",
            feature_schema_version="v1.0",
            probability=0.88,
            expected_recovery=21999.12,
            recoverability_band="HIGH",
            features_json={},
            correlation_id="corr_test",
        )
        session.add(pred)
        await session.flush()

        # 2. Decision Record
        dec_id = f"dec_{uuid.uuid4().hex[:8]}"
        dec = RecoveryDecision(
            id=dec_id,
            case_id=case_id,
            prediction_id=pred.id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.88,
            expected_recovery=21999.12,
            rationale="Prov test rationale",
            policy_result="ALLOW",
            authorization_status="AUTHORIZED",
            correlation_id="corr_test",
        )
        session.add(dec)

        # 3. Execution Record
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        exec_rec = ExecutionRecord(
            id=exec_id,
            case_id=case_id,
            decision_id=dec_id,
            tool_name="payments",
            operation="retry_payment",
            request_id="req_test",
            idempotency_key=f"ray:{case_id}:RETRY:1",
            provider_reference="pay_mock_123",
            execution_status="SUCCESS",
            provider_response_hash="hash123",
            correlation_id="corr_test",
        )
        session.add(exec_rec)

        # 4. Verification Record
        verif_id = f"verif_{uuid.uuid4().hex[:8]}"
        verif = VerificationRecord(
            id=verif_id,
            case_id=case_id,
            execution_id=exec_id,
            webhook_confirmed=True,
            api_state_confirmed=True,
            provider_status="captured",
            verified_amount=24999.00,
            verification_status="VERIFIED",
            evidence_hash="sha256_mock",
            correlation_id="corr_test",
        )
        session.add(verif)
        await session.commit()

        # Call endpoint logic
        res = await get_case_provenance(case_id, session)

        assert res["case_id"] == case_id
        assert res["prediction"]["probability"] == 0.88
        assert res["decision"]["recommended_strategy"] == "RETRY"
        assert res["execution"]["operation"] == "retry_payment"
        assert res["verification"]["verification_status"] == "VERIFIED"
        assert res["provenance_chain_valid"] is True
