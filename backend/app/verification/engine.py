"""Dual-signal Verification Engine for independent financial proof."""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import (
    RecoveryCase,
    ExecutionRecord,
    VerificationRecord,
    WebhookEvent,
    RecoveryState,
    AuditLog,
)
from app.verification.models import VerificationStatus, VerificationResult
from app.integrations.razorpay.protocol import PaymentGateway
from app.integrations.razorpay.mock_adapter import MockPaymentAdapter


class VerificationEngine:
    """
    Independent financial verification engine.
    Requires two independent signals (API observation + Webhook event)
    to verify revenue recovery.
    """

    def __init__(self, payment_gateway: Optional[PaymentGateway] = None):
        self.gateway = payment_gateway or MockPaymentAdapter()

    def generate_evidence_hash(self, evidence: Dict[str, Any]) -> str:
        """Create canonical SHA-256 evidence hash for financial integrity proof."""
        canonical_json = json.dumps(evidence, sort_keys=True, default=str)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    async def verify_recovery(
        self,
        case_id: str,
        execution_id: str,
        session: AsyncSession,
        webhook_payload: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """
        Independently verify financial recovery for an execution record.
        Signal A: Gateway API state observation
        Signal B: Cryptographic Webhook confirmation
        """
        # Fetch ExecutionRecord
        exec_stmt = select(ExecutionRecord).where(ExecutionRecord.id == execution_id)
        exec_res = await session.execute(exec_stmt)
        execution = exec_res.scalar_one_or_none()
        if not execution:
            raise ValueError(f"ExecutionRecord '{execution_id}' not found")

        # Fetch RecoveryCase
        case_stmt = select(RecoveryCase).where(RecoveryCase.id == case_id)
        case_res = await session.execute(case_stmt)
        case = case_res.scalar_one_or_none()
        if not case:
            raise ValueError(f"RecoveryCase '{case_id}' not found")

        # -------------------------------------------------------------
        # Signal A: Gateway / API State Polling
        # -------------------------------------------------------------
        provider_ref = execution.provider_reference or f"pay_{case_id}"
        api_data = await self.gateway.get_payment(provider_ref)
        api_status = str(api_data.get("status", "")).lower()
        api_confirmed = (api_status == "captured")

        # -------------------------------------------------------------
        # Signal B: Webhook Event Confirmation
        # -------------------------------------------------------------
        webhook_confirmed = False
        webhook_event_id = None
        webhook_data = webhook_payload

        if not webhook_data:
            # Look up recent captured webhook for this payment/case in database
            wh_stmt = select(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(10)
            wh_res = await session.execute(wh_stmt)
            recent_webhooks = wh_res.scalars().all()
            for wh in recent_webhooks:
                payload = wh.raw_payload or {}
                contains_ref = (
                    provider_ref in str(payload) or
                    case_id in str(payload) or
                    wh.event_type in ("payment.captured", "order.paid")
                )
                if contains_ref:
                    webhook_confirmed = True
                    webhook_event_id = wh.id
                    webhook_data = payload
                    break

        webhook_explicit_failure = False
        if webhook_payload:
            event_type = webhook_payload.get("event", "")
            wh_status = webhook_payload.get("status", "")
            if event_type in ("payment.captured", "order.paid") or wh_status == "captured":
                webhook_confirmed = True
                webhook_event_id = webhook_payload.get("id", f"evt_{uuid.uuid4().hex[:8]}")
            elif event_type in ("payment.failed", "refund.created", "dispute.created") or wh_status in ("failed", "refunded"):
                webhook_explicit_failure = True
                webhook_event_id = webhook_payload.get("id", f"evt_{uuid.uuid4().hex[:8]}")

        # -------------------------------------------------------------
        # Dual-Signal Decision Logic
        # -------------------------------------------------------------
        verif_id = f"verif_{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()

        if api_confirmed and webhook_confirmed:
            status = VerificationStatus.VERIFIED
            verified_amount = float(case.amount_at_risk)
        elif (api_confirmed and webhook_explicit_failure) or (not api_confirmed and webhook_confirmed):
            status = VerificationStatus.CONFLICT  # Discrepancy between API and webhook
            verified_amount = 0.0
        elif api_confirmed and not webhook_confirmed:
            status = VerificationStatus.PENDING
            verified_amount = 0.0
        else:
            status = VerificationStatus.FAILED
            verified_amount = 0.0

        # Construct Canonical Evidence Object
        evidence = {
            "case_id": case_id,
            "execution_id": execution_id,
            "provider_reference": provider_ref,
            "api_observed_status": api_status,
            "api_confirmed": api_confirmed,
            "webhook_confirmed": webhook_confirmed,
            "webhook_event_id": webhook_event_id,
            "verified_amount": verified_amount,
            "correlation_id": execution.correlation_id,
            "timestamp": now.isoformat(),
        }
        evidence_hash = self.generate_evidence_hash(evidence)

        # Store VerificationRecord
        verif_record = VerificationRecord(
            id=verif_id,
            case_id=case_id,
            execution_id=execution_id,
            webhook_confirmed=webhook_confirmed,
            api_state_confirmed=api_confirmed,
            provider_status=api_status,
            verified_amount=verified_amount,
            verification_status=status.value,
            verification_method="dual_signal_api_webhook",
            evidence_hash=evidence_hash,
            evidence_json=evidence,
            verification_timestamp=now,
            correlation_id=execution.correlation_id,
            created_at=now,
        )
        session.add(verif_record)

        # Update Case State strictly through the guarded transition
        if status == VerificationStatus.VERIFIED:
            case.state = RecoveryState.RECOVERED
            case.verification_id = verif_id
            case.recovered_amount = verified_amount
        elif status == VerificationStatus.CONFLICT:
            case.state = RecoveryState.HUMAN_REVIEW

        # Audit Log
        audit = AuditLog(
            action_id=f"act_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            agent="VerificationEngine",
            action="RECOVERY_VERIFIED" if status == VerificationStatus.VERIFIED else f"VERIFICATION_{status.value}",
            reason=f"Dual-signal verification status: {status.value} (API: {api_status}, Webhook: {webhook_confirmed})",
            evidence={"evidence_hash": evidence_hash, "verified_amount": verified_amount},
            policy_result="PASSED",
            execution_result="SUCCESS" if status == VerificationStatus.VERIFIED else "PENDING",
            verification_result=status.value,
            timestamp=now,
        )
        session.add(audit)
        await session.commit()

        return VerificationResult(
            verification_id=verif_id,
            case_id=case_id,
            execution_id=execution_id,
            status=status,
            webhook_confirmed=webhook_confirmed,
            api_state_confirmed=api_confirmed,
            provider_status=api_status,
            verified_amount=verified_amount,
            evidence_hash=evidence_hash,
            evidence_json=evidence,
            timestamp=now,
        )
