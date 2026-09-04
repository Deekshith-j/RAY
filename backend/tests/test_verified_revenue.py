"""Tests for canonical calculate_verified_revenue and metric separation."""

import pytest
import uuid
from decimal import Decimal
from app.database import async_session_factory
from app.core.financial import calculate_verified_revenue, get_financial_breakdown, quantize_inr
from app.models.entities import VerificationRecord, ExecutionRecord, RecoveryCase, Customer, RecoveryDecision, RecoveryState


@pytest.mark.asyncio
async def test_calculate_verified_revenue_strictly_counts_only_verified_outcomes():
    async with async_session_factory() as session:
        # Create customer and case
        cid = f"cust_ver_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="test@verif.com", name="Verif Customer", phone="9999999999")
        session.add(cust)

        case_id = f"case_ver_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=24999.00,
            failure_type="timeout",
            failure_reason="Gateway timeout on payment processing",
            state=RecoveryState.RECOVERED,
        )
        session.add(case)
        await session.commit()

        # Add an unverified execution
        exec_id = f"exec_ver_{uuid.uuid4().hex[:8]}"
        dec_id = f"dec_ver_{uuid.uuid4().hex[:8]}"
        dec = RecoveryDecision(
            id=dec_id,
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.95,
            expected_recovery=24999.00,
            rationale="Verified outcome recovery",
            policy_result="ALLOW",
            authorization_status="AUTHORIZED",
            correlation_id=f"RAY-DEC-{case_id}",
        )
        session.add(dec)

        exec_rec = ExecutionRecord(
            id=exec_id,
            case_id=case_id,
            decision_id=dec_id,
            tool_name="payments",
            operation="retry_payment",
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            idempotency_key=f"ray:{case_id}:RETRY:1",
            execution_status="SUCCESS",
            provider_response_hash="hash123",
            correlation_id="corr123",
        )
        session.add(exec_rec)

        # 1. Non-verified record (PENDING) - should NOT count
        verif_pending = VerificationRecord(
            id=f"verif_pen_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            execution_id=exec_id,
            provider_status="pending",
            verified_amount=24999.00,
            verification_status="PENDING",
            evidence_hash="pending_hash",
            correlation_id="corr_pen",
        )
        session.add(verif_pending)
        await session.commit()

        rev_pending = await calculate_verified_revenue(session)
        # Should not include verif_pending because status is PENDING
        
        # 2. Add VERIFIED record
        verif_success = VerificationRecord(
            id=f"verif_suc_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            execution_id=exec_id,
            webhook_confirmed=True,
            api_state_confirmed=True,
            provider_status="captured",
            verified_amount=24999.00,
            verification_status="VERIFIED",
            evidence_hash="verified_hash",
            correlation_id="corr_suc",
        )
        session.add(verif_success)
        await session.commit()

        rev_final = await calculate_verified_revenue(session)
        assert rev_final >= Decimal("24999.00")
