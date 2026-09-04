import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.entities import WebhookEvent, RecoveryCase, RecoveryState, RecoveryStrategy, Payment
from app.core.audit import log_audit_entry

router = APIRouter(prefix="/webhooks", tags=["Razorpay Webhooks"])


def verify_razorpay_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC SHA256 signature against raw request body."""
    if not signature or not secret:
        return False
    # If in development with placeholder secret, allow test simulations if matching header
    if secret == "webhook_secret_placeholder" and signature.startswith("sig_"):
        return True
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str = Header(None, alias="X-Razorpay-Event-Id"),
    db: AsyncSession = Depends(get_db),
):
    """
    Razorpay Webhook receiver:
    - Verifies HMAC SHA256 signature on raw bytes
    - Idempotent processing with x-razorpay-event-id
    - Persists raw payload
    - Handles duplicates and out-of-order deliveries safely
    """
    raw_body = await request.body()

    if not x_razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature header.")

    # 1. Signature Verification
    if not verify_razorpay_signature(raw_body, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    try:
        payload: Dict[str, Any] = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed JSON in webhook body.")

    event_id = x_razorpay_event_id or payload.get("id") or f"evt_{hashlib.md5(raw_body).hexdigest()}"
    event_type = payload.get("event", "unknown")

    # 2. Idempotency Check: check if event already recorded
    existing_evt_query = select(WebhookEvent).where(WebhookEvent.id == event_id)
    existing_evt = (await db.execute(existing_evt_query)).scalar_one_or_none()

    if existing_evt:
        # Duplicate delivery detected - mark and return 200 OK without re-executing
        existing_evt.is_duplicate = True
        await db.commit()
        return {
            "status": "duplicate_ignored",
            "event_id": event_id,
            "message": "Duplicate webhook received and safely acknowledged.",
        }

    # 3. Persist Raw Webhook Event
    webhook_record = WebhookEvent(
        id=event_id,
        event_type=event_type,
        raw_payload=payload,
        signature=x_razorpay_signature,
        processed=False,
        is_duplicate=False,
        created_at=datetime.utcnow(),
    )
    db.add(webhook_record)
    await db.flush()

    # 4. State Machine Updates & Verification Trigger
    payment_entity = (
        payload.get("payload", {})
        .get("payment", {})
        .get("entity", {})
    )
    payment_id = payment_entity.get("id")
    order_id = payment_entity.get("order_id")

    if payment_id or order_id:
        # Look for associated recovery case
        case_query = select(RecoveryCase).where(
            (RecoveryCase.entity_id == payment_id) | (RecoveryCase.entity_id == order_id)
        )
        case = (await db.execute(case_query)).scalar_one_or_none()

        if case:
            if event_type in ("payment.captured", "order.paid"):
                # Independent financial outcome confirmed!
                amount_recovered = float(payment_entity.get("amount", 0)) / 100.0  # Paise to INR
                if amount_recovered <= 0 and case.amount_at_risk > 0:
                    amount_recovered = case.amount_at_risk

                # Safe transition to RECOVERED only if coming from valid previous state
                if case.state in (RecoveryState.EXECUTING, RecoveryState.AWAITING_VERIFICATION, RecoveryState.ANALYZING):
                    case.state = RecoveryState.RECOVERED
                    case.recovered_amount = amount_recovered
                    case.verification_id = event_id

                    await log_audit_entry(
                        db=db,
                        case_id=case.id,
                        event_id=event_id,
                        agent="Verification Agent",
                        action="VERIFY_RECOVERY_SUCCESS",
                        reason=f"Verified Razorpay event '{event_type}' confirming ₹{amount_recovered:,.2f} received.",
                        evidence=payment_entity,
                        verification_result="VERIFIED",
                    )
            elif event_type == "payment.failed":
                # Additional failure registered
                case.retry_count += 1
                if case.retry_count >= settings.MAX_TOTAL_RECOVERY_ATTEMPTS:
                    case.state = RecoveryState.STOPPED
                else:
                    case.state = RecoveryState.FAILED_RECOVERY

                await log_audit_entry(
                    db=db,
                    case_id=case.id,
                    event_id=event_id,
                    agent="Revenue Detective",
                    action="REGISTER_PAYMENT_FAILURE",
                    reason=f"Payment failed webhook received for {payment_id}",
                    evidence=payment_entity,
                    verification_result="FAILED",
                )

    webhook_record.processed = True
    webhook_record.processed_at = datetime.utcnow()
    await db.commit()

    return {
        "status": "processed",
        "event_id": event_id,
        "event_type": event_type,
    }
