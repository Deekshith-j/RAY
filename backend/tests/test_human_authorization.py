"""Tests for Human Authorization records and validation."""

import pytest
import uuid
from datetime import datetime
from app.database import async_session_factory
from app.models.entities import HumanApprovalRecord, RecoveryCase, RecoveryDecision, Customer


@pytest.mark.asyncio
async def test_human_authorization_record_creation():
    async with async_session_factory() as session:
        cid = f"cust_auth_{uuid.uuid4().hex[:8]}"
        cust = Customer(id=cid, email="auth@test.com", name="Auth Cust", phone="9876543210")
        session.add(cust)

        case_id = f"case_auth_{uuid.uuid4().hex[:8]}"
        case = RecoveryCase(
            id=case_id,
            customer_id=cid,
            entity_type="PAYMENT",
            entity_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount_at_risk=75000.00,
            failure_type="timeout",
            failure_reason="Gateway timeout on payment processing",
        )
        session.add(case)

        dec_id = f"dec_auth_{uuid.uuid4().hex[:8]}"
        dec = RecoveryDecision(
            id=dec_id,
            case_id=case_id,
            recommended_strategy="RETRY",
            probability_of_recovery=0.95,
            expected_recovery=75000.00,
            rationale="High value recovery",
            policy_result="REQUIRE_HUMAN_APPROVAL",
            authorization_required=True,
            authorization_status="PENDING",
            correlation_id=f"RAY-DEC-{case_id}",
        )
        session.add(dec)
        await session.commit()

        # Formal operator approval record
        appr_id = f"appr_{uuid.uuid4().hex[:12]}"
        approval = HumanApprovalRecord(
            approval_id=appr_id,
            case_id=case_id,
            decision_id=dec_id,
            operator_id="ops_lead@acme.corp",
            approved_strategy="RETRY",
            approval_reason="Verified VIP enterprise account with valid bank statement",
            policy_version="v1.0",
            correlation_id=f"RAY-APP-{case_id}",
        )
        session.add(approval)
        
        # Transition decision status
        dec.authorization_status = "AUTHORIZED"
        dec.authorized_by = approval.operator_id
        await session.commit()

        persisted = await session.get(HumanApprovalRecord, appr_id)
        assert persisted is not None
        assert persisted.operator_id == "ops_lead@acme.corp"
        assert persisted.approved_strategy == "RETRY"
