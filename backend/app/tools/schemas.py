"""Strict schemas for Tool Gateway interactions."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    """Execution request submitted by the Execution Agent to the Tool Gateway."""

    tool_name: str = Field(..., description="Tool namespace (e.g. 'payments', 'payment_links', 'subscriptions')")
    operation: str = Field(..., description="Operation to perform (e.g. 'retry', 'create_link', 'charge_now')")
    case_id: str
    decision_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(..., description="Format: ray:{case_id}:{strategy}:{attempt_number}")
    correlation_id: str


class ToolCallResult(BaseModel):
    """Result returned by the Tool Gateway after policy and authorization checks."""

    execution_id: Optional[str] = None
    case_id: str
    decision_id: str
    status: str  # SUCCESS, REJECTED, FAILED
    idempotency_key: str
    provider_reference: Optional[str] = None
    provider_response: Dict[str, Any] = Field(default_factory=dict)
    provider_response_hash: str = ""
    rejection_reason: Optional[str] = None
    is_idempotent_replay: bool = False
