import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import AuditLog


async def log_audit_entry(
    db: AsyncSession,
    case_id: str,
    agent: str,
    action: str,
    reason: str,
    evidence: Optional[Dict[str, Any]] = None,
    confidence: Optional[float] = None,
    policy_result: Optional[str] = None,
    approval_required: bool = False,
    approved_by: Optional[str] = None,
    execution_result: Optional[str] = None,
    verification_result: Optional[str] = None,
    event_id: Optional[str] = None,
) -> AuditLog:
    """Create and persist an immutable audit record."""
    action_id = f"act_{uuid.uuid4().hex[:12]}"
    log = AuditLog(
        action_id=action_id,
        case_id=case_id,
        event_id=event_id,
        agent=agent,
        action=action,
        reason=reason,
        evidence=evidence or {},
        confidence=confidence,
        policy_result=policy_result,
        approval_required=approval_required,
        approved_by=approved_by,
        execution_result=execution_result,
        verification_result=verification_result,
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.flush()
    return log
