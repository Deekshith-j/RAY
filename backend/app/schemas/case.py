from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from app.models.entities import RecoveryState, RecoveryStrategy


class AuditLogSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_id: str
    case_id: str
    event_id: Optional[str] = None
    agent: str
    action: str
    reason: str
    evidence: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    policy_result: Optional[str] = None
    approval_required: bool = False
    approved_by: Optional[str] = None
    execution_result: Optional[str] = None
    verification_result: Optional[str] = None
    timestamp: datetime


class RecoveryCaseBase(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    customer_id: str
    amount_at_risk: float
    recoverability_score: float
    expected_recovery_value: float
    recovered_amount: float
    failure_reason: str
    failure_type: str
    state: RecoveryState
    recommended_action: Optional[RecoveryStrategy] = None
    authorized_action: Optional[RecoveryStrategy] = None
    executed_action: Optional[RecoveryStrategy] = None
    retry_count: int = 0
    ai_diagnosis: Optional[str] = None
    ai_confidence: Optional[float] = None
    policy_check_result: Optional[Dict[str, Any]] = None
    human_approved: Optional[bool] = None
    human_approved_by: Optional[str] = None
    verification_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class RecoveryCaseResponse(RecoveryCaseBase):
    model_config = ConfigDict(from_attributes=True)

    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class RecoveryCaseDetailResponse(RecoveryCaseResponse):
    audit_logs: List[AuditLogSchema] = []


class ApprovalRequest(BaseModel):
    case_id: str
    approved: bool
    reviewer_name: str
    notes: Optional[str] = None
