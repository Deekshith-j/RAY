from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.config import settings
from app.models.entities import RecoveryStrategy, RecoveryCase, Customer


from datetime import datetime
import uuid

class PolicyDecision(BaseModel):
    allowed: bool
    requires_human_approval: bool
    reason: str
    rule_code: str
    fallback_strategy: Optional[RecoveryStrategy] = None
    
    # Phase 7 Explicit Fields
    decision: str = "ALLOW"  # "ALLOW", "DENY", "REQUIRE_HUMAN_APPROVAL"
    reason_codes: List[str] = []
    policy_version: str = "v1.0"
    authorization_required: bool = False
    constraints_checked: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: str = Field(default_factory=lambda: f"pol_{uuid.uuid4().hex[:12]}")


class PolicyEngine:
    def __init__(
        self,
        max_retry_attempts: int = settings.MAX_RETRY_ATTEMPTS,
        auto_retry_enabled: bool = settings.AUTO_RETRY_ENABLED,
        auto_retry_max_amount: float = settings.AUTO_RETRY_MAX_AMOUNT,
        allowed_retry_failure_types: Optional[List[str]] = None,
        payment_link_enabled: bool = settings.PAYMENT_LINK_ENABLED,
        payment_link_max_amount: float = settings.PAYMENT_LINK_MAX_AMOUNT,
        human_approval_threshold: float = settings.HUMAN_APPROVAL_THRESHOLD,
        max_total_recovery_attempts: int = settings.MAX_TOTAL_RECOVERY_ATTEMPTS,
    ):
        self.max_retry_attempts = max_retry_attempts
        self.auto_retry_enabled = auto_retry_enabled
        self.auto_retry_max_amount = auto_retry_max_amount
        self.allowed_retry_failure_types = (
            allowed_retry_failure_types or settings.ALLOWED_RETRY_FAILURE_TYPES
        )
        self.payment_link_enabled = payment_link_enabled
        self.payment_link_max_amount = payment_link_max_amount
        self.human_approval_threshold = human_approval_threshold
        self.max_total_recovery_attempts = max_total_recovery_attempts

    def evaluate(
        self,
        case: RecoveryCase,
        proposed_strategy: RecoveryStrategy,
        customer: Optional[Customer] = None,
    ) -> PolicyDecision:
        """
        Deterministically evaluates whether the proposed recovery strategy is permitted.
        The LLM proposes; the Policy Engine decides.
        """
        # Rule 1: Customer Opt-Out Check
        if customer and customer.opt_out:
            return PolicyDecision(
                allowed=False,
                requires_human_approval=False,
                reason="Customer has opted out of automated recovery interactions.",
                rule_code="CUSTOMER_OPT_OUT",
                fallback_strategy=RecoveryStrategy.STOPPED if hasattr(RecoveryStrategy, 'STOPPED') else RecoveryStrategy.NO_ACTION,
            )

        # Rule 2: Maximum Overall Recovery Attempts
        if case.retry_count >= self.max_total_recovery_attempts:
            return PolicyDecision(
                allowed=False,
                requires_human_approval=False,
                reason=f"Exceeded maximum recovery attempts ({self.max_total_recovery_attempts}). Stopping further automated attempts.",
                rule_code="MAX_ATTEMPTS_EXCEEDED",
                fallback_strategy=RecoveryStrategy.HUMAN_REVIEW,
            )

        # Rule 3: High-Value Human Approval Threshold
        if case.amount_at_risk >= self.human_approval_threshold:
            # High-value actions require human approval before execution
            return PolicyDecision(
                allowed=True,
                requires_human_approval=True,
                reason=f"Amount (₹{case.amount_at_risk:,.2f}) meets or exceeds human approval threshold (₹{self.human_approval_threshold:,.2f}). Human authorization required.",
                rule_code="HUMAN_APPROVAL_REQUIRED",
            )

        # Rule 4: Strategy-Specific Policies
        if proposed_strategy == RecoveryStrategy.RETRY:
            if not self.auto_retry_enabled:
                return PolicyDecision(
                    allowed=False,
                    requires_human_approval=False,
                    reason="Automated retries are disabled by policy.",
                    rule_code="AUTO_RETRY_DISABLED",
                    fallback_strategy=RecoveryStrategy.PAYMENT_LINK,
                )

            if case.retry_count >= self.max_retry_attempts:
                return PolicyDecision(
                    allowed=False,
                    requires_human_approval=False,
                    reason=f"Retry limit reached ({case.retry_count}/{self.max_retry_attempts}). Falling back to alternative recovery strategy.",
                    rule_code="RETRY_LIMIT_REACHED",
                    fallback_strategy=RecoveryStrategy.PAYMENT_LINK,
                )

            if case.amount_at_risk > self.auto_retry_max_amount:
                return PolicyDecision(
                    allowed=False,
                    requires_human_approval=False,
                    reason=f"Amount (₹{case.amount_at_risk:,.2f}) exceeds auto-retry ceiling (₹{self.auto_retry_max_amount:,.2f}). Use payment link instead.",
                    rule_code="AMOUNT_EXCEEDS_RETRY_LIMIT",
                    fallback_strategy=RecoveryStrategy.PAYMENT_LINK,
                )

            if case.failure_type not in self.allowed_retry_failure_types:
                return PolicyDecision(
                    allowed=False,
                    requires_human_approval=False,
                    reason=f"Failure type '{case.failure_type}' is not eligible for automated retry. Allowed types: {self.allowed_retry_failure_types}.",
                    rule_code="DISALLOWED_RETRY_FAILURE_TYPE",
                    fallback_strategy=RecoveryStrategy.PAYMENT_LINK,
                )

            return PolicyDecision(
                allowed=True,
                requires_human_approval=False,
                reason="Auto-retry policy checks passed. Eligible for safe bounded retry.",
                rule_code="RETRY_POLICY_PASSED",
            )

        elif proposed_strategy == RecoveryStrategy.PAYMENT_LINK:
            if not self.payment_link_enabled:
                return PolicyDecision(
                    allowed=False,
                    requires_human_approval=False,
                    reason="Payment link creation is disabled by policy.",
                    rule_code="PAYMENT_LINK_DISABLED",
                    fallback_strategy=RecoveryStrategy.HUMAN_REVIEW,
                )

            if case.amount_at_risk > self.payment_link_max_amount:
                return PolicyDecision(
                    allowed=True,
                    requires_human_approval=True,
                    reason=f"Payment link amount (₹{case.amount_at_risk:,.2f}) exceeds limit (₹{self.payment_link_max_amount:,.2f}). Requires approval.",
                    rule_code="PAYMENT_LINK_APPROVAL_REQUIRED",
                )

            return PolicyDecision(
                allowed=True,
                requires_human_approval=False,
                reason="Payment link policy checks passed.",
                rule_code="PAYMENT_LINK_PASSED",
            )

        elif proposed_strategy == RecoveryStrategy.SUBSCRIPTION_RECOVERY:
            if case.entity_type != "SUBSCRIPTION":
                return PolicyDecision(
                    allowed=False,
                    requires_human_approval=False,
                    reason=f"Subscription recovery cannot be applied to non-subscription entity type '{case.entity_type}'.",
                    rule_code="INVALID_SUBSCRIPTION_ENTITY",
                    fallback_strategy=RecoveryStrategy.PAYMENT_LINK,
                )

            return PolicyDecision(
                allowed=True,
                requires_human_approval=False,
                reason="Subscription recovery policy checks passed.",
                rule_code="SUBSCRIPTION_RECOVERY_PASSED",
            )

        elif proposed_strategy in (RecoveryStrategy.CUSTOMER_NOTIFICATION, RecoveryStrategy.NO_ACTION):
            return PolicyDecision(
                allowed=True,
                requires_human_approval=False,
                reason=f"Strategy '{proposed_strategy.value}' accepted by policy.",
                rule_code="PASSIVE_STRATEGY_PASSED",
            )

        elif proposed_strategy == RecoveryStrategy.HUMAN_REVIEW:
            return PolicyDecision(
                allowed=True,
                requires_human_approval=True,
                reason="Action escalated to human review as requested.",
                rule_code="ESCALATED_TO_HUMAN",
            )

        return PolicyDecision(
            allowed=False,
            requires_human_approval=False,
            reason=f"Unknown recovery strategy '{proposed_strategy}'.",
            rule_code="UNKNOWN_STRATEGY",
            fallback_strategy=RecoveryStrategy.HUMAN_REVIEW,
        )


policy_engine = PolicyEngine()
