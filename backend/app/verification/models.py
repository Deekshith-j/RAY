"""Schemas for Verification Engine."""

import enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


class VerificationResult(BaseModel):
    verification_id: str
    case_id: str
    execution_id: str
    status: VerificationStatus
    webhook_confirmed: bool
    api_state_confirmed: bool
    provider_status: str
    verified_amount: float
    evidence_hash: str
    evidence_json: Dict[str, Any] = Field(default_factory=dict)
    rejection_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
