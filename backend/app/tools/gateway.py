"""Tool Gateway enforcing strict authorization and idempotency for all financial operations."""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import ExecutionRecord, AuditLog
from app.tools.schemas import ToolCallRequest, ToolCallResult
from app.tools.idempotency import check_idempotency
from app.tools.authorization import authorize_tool_call
from app.integrations.razorpay.protocol import PaymentGateway
from app.integrations.razorpay.mock_adapter import MockPaymentAdapter
from app.core.security import redact_secrets


class ToolGateway:
    """
    Central authorization and execution gateway.
    The Execution Agent MUST interact through this gateway.
    Never allows direct provider access.
    """

    def __init__(self, payment_gateway: Optional[PaymentGateway] = None):
        self.gateway = payment_gateway or MockPaymentAdapter()

    async def execute(
        self,
        request: ToolCallRequest,
        session: AsyncSession,
    ) -> ToolCallResult:
        """
        Execute an authorized financial recovery operation.
        Strictly enforces:
        1. Idempotency check
        2. Policy authorization check
        3. Parameter boundary validation
        4. Provider execution
        5. Audit logging
        """
        # 1. Idempotency Check
        existing_exec = await check_idempotency(session, request.idempotency_key)
        if existing_exec:
            return ToolCallResult(
                execution_id=existing_exec.id,
                case_id=existing_exec.case_id,
                decision_id=existing_exec.decision_id,
                status=existing_exec.execution_status,
                idempotency_key=existing_exec.idempotency_key,
                provider_reference=existing_exec.provider_reference,
                provider_response={"replayed": True, "cached_at": existing_exec.created_at.isoformat()},
                provider_response_hash=existing_exec.provider_response_hash,
                is_idempotent_replay=True,
            )

        # 2. Authorization Check
        authorized, reason, case, decision = await authorize_tool_call(session, request)
        if not authorized:
            # Write rejection audit log
            audit = AuditLog(
                action_id=f"act_{uuid.uuid4().hex[:12]}",
                case_id=request.case_id,
                agent="ToolGateway",
                action="TOOL_CALL_REJECTED",
                reason=reason or "Unauthorized tool call",
                evidence={"tool_name": request.tool_name, "operation": request.operation, "parameters": request.parameters},
                policy_result="REJECTED",
                execution_result="REJECTED",
                timestamp=datetime.utcnow(),
            )
            session.add(audit)
            await session.commit()

            return ToolCallResult(
                case_id=request.case_id,
                decision_id=request.decision_id,
                status="REJECTED",
                idempotency_key=request.idempotency_key,
                rejection_reason=reason,
            )

        # 3. Provider Execution via Isolated Adapter
        exec_id = f"exec_{uuid.uuid4().hex[:16]}"
        provider_resp = {}
        provider_ref = None
        op_lower = request.operation.lower()

        try:
            if "retry" in op_lower:
                provider_resp = await self.gateway.retry_payment(
                    payment_id=request.parameters.get("payment_id", f"pay_{request.case_id}"),
                    amount=float(case.amount_at_risk),
                    idempotency_key=request.idempotency_key,
                )
                provider_ref = provider_resp.get("id")
            elif "link" in op_lower or "plink" in op_lower:
                provider_resp = await self.gateway.create_payment_link(
                    case_id=request.case_id,
                    amount=float(case.amount_at_risk),
                    description=request.parameters.get("description", f"Recovery for Case {request.case_id}"),
                    idempotency_key=request.idempotency_key,
                )
                provider_ref = provider_resp.get("id")
            elif "subscription" in op_lower or "charge" in op_lower:
                provider_resp = await self.gateway.recover_subscription(
                    subscription_id=request.parameters.get("subscription_id", f"sub_{request.case_id}"),
                    idempotency_key=request.idempotency_key,
                )
                provider_ref = provider_resp.get("id")
            else:
                return ToolCallResult(
                    case_id=request.case_id,
                    decision_id=request.decision_id,
                    status="REJECTED",
                    idempotency_key=request.idempotency_key,
                    rejection_reason=f"Unknown tool operation '{request.operation}'",
                )

            # Response integrity hash
            resp_canonical = json.dumps(provider_resp, sort_keys=True)
            resp_hash = hashlib.sha256(resp_canonical.encode()).hexdigest()

            # 4. Record Execution
            exec_record = ExecutionRecord(
                id=exec_id,
                case_id=request.case_id,
                decision_id=request.decision_id,
                tool_name=request.tool_name,
                operation=request.operation,
                request_id=f"req_{uuid.uuid4().hex[:12]}",
                idempotency_key=request.idempotency_key,
                provider_reference=provider_ref,
                execution_status="SUCCESS",
                provider_response_hash=resp_hash,
                correlation_id=request.correlation_id,
                created_at=datetime.utcnow(),
            )
            session.add(exec_record)

            # Write AuditLog
            audit = AuditLog(
                action_id=f"act_{uuid.uuid4().hex[:12]}",
                case_id=request.case_id,
                agent="ToolGateway",
                action="TOOL_CALL_EXECUTED",
                reason=f"Operation '{request.operation}' executed via Tool Gateway",
                evidence={"provider_ref": provider_ref, "idempotency_key": request.idempotency_key},
                policy_result="PASSED",
                execution_result="SUCCESS",
                timestamp=datetime.utcnow(),
            )
            session.add(audit)
            await session.commit()

            return ToolCallResult(
                execution_id=exec_id,
                case_id=request.case_id,
                decision_id=request.decision_id,
                status="SUCCESS",
                idempotency_key=request.idempotency_key,
                provider_reference=provider_ref,
                provider_response=provider_resp,
                provider_response_hash=resp_hash,
            )

        except Exception as e:
            await session.rollback()
            # Log failure
            safe_err = redact_secrets(str(e))
            audit = AuditLog(
                action_id=f"act_{uuid.uuid4().hex[:12]}",
                case_id=request.case_id,
                agent="ToolGateway",
                action="TOOL_CALL_FAILED",
                reason=f"Provider execution failed: {safe_err}",
                policy_result="PASSED",
                execution_result="FAILED",
                timestamp=datetime.utcnow(),
            )
            session.add(audit)
            await session.commit()

            return ToolCallResult(
                case_id=request.case_id,
                decision_id=request.decision_id,
                status="FAILED",
                idempotency_key=request.idempotency_key,
                rejection_reason=f"Provider execution exception: {safe_err}",
            )
