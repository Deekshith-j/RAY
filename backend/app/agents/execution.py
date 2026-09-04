"""Agent 5 — Execution Agent: Dispatches authorized recovery operations strictly through Tool Gateway."""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import BaseAgent
from app.models.entities import RecoveryDecision, RecoveryCase
from app.tools.gateway import ToolGateway
from app.tools.schemas import ToolCallRequest, ToolCallResult
from app.tools.idempotency import generate_idempotency_key


class ExecutionAgent(BaseAgent):
    """
    Agent 5: Dispatches authorized actions.
    MUST NOT interact with Razorpay directly.
    Can ONLY submit requests to Tool Gateway.
    """

    def __init__(self, tool_gateway: Optional[ToolGateway] = None):
        super().__init__(name="ExecutionAgent")
        self.gateway = tool_gateway or ToolGateway()

    async def execute_decision(
        self,
        decision: RecoveryDecision,
        case: RecoveryCase,
        session: AsyncSession,
        attempt_number: int = 1,
    ) -> ToolCallResult:
        self.increment_step()

        # Map strategy to tool operation
        strategy = decision.recommended_strategy.upper()
        if strategy == "RETRY":
            tool_name = "payments"
            operation = "retry_payment"
            parameters = {"payment_id": f"pay_{case.id}"}
        elif strategy == "PAYMENT_LINK":
            tool_name = "payment_links"
            operation = "create_payment_link"
            parameters = {
                "amount": float(case.amount_at_risk),
                "description": f"Recovery for Case {case.id}",
            }
        elif strategy == "SUBSCRIPTION_RECOVERY":
            tool_name = "subscriptions"
            operation = "recover_subscription"
            parameters = {"subscription_id": f"sub_{case.id}"}
        else:
            raise ValueError(f"Strategy '{strategy}' does not support automated execution")

        # Canonical idempotency key: ray:{case_id}:{strategy}:{attempt_number}
        idempotency_key = generate_idempotency_key(
            case_id=case.id,
            strategy=strategy,
            attempt_number=attempt_number,
        )

        request = ToolCallRequest(
            tool_name=tool_name,
            operation=operation,
            case_id=case.id,
            decision_id=decision.id,
            parameters=parameters,
            idempotency_key=idempotency_key,
            correlation_id=decision.correlation_id,
        )

        # Dispatch exclusively through Tool Gateway
        return await self.gateway.execute(request, session)
