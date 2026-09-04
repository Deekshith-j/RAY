import enum
from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RecoveryState(str, enum.Enum):
    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    FAILED = "FAILED"
    ANALYZING = "ANALYZING"
    RECOVERY_PLANNED = "RECOVERY_PLANNED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    RECOVERED = "RECOVERED"
    FAILED_RECOVERY = "FAILED_RECOVERY"
    STOPPED = "STOPPED"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class RecoveryStrategy(str, enum.Enum):
    RETRY = "RETRY"
    PAYMENT_LINK = "PAYMENT_LINK"
    SUBSCRIPTION_RECOVERY = "SUBSCRIPTION_RECOVERY"
    CUSTOMER_NOTIFICATION = "CUSTOMER_NOTIFICATION"
    NO_ACTION = "NO_ACTION"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    customer_age_days: Mapped[int] = mapped_column(Integer, default=30)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    cases = relationship("RecoveryCase", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # in INR
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="created")  # created, attempted, paid, expired
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    payments = relationship("Payment", back_populates="order")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("orders.id"), nullable=True, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # in INR
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(32), default="failed", index=True)  # failed, captured, authorized, refunded
    method: Mapped[str] = mapped_column(String(32), default="card")  # card, upi, netbanking, wallet
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    order = relationship("Order", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    attempts = relationship("PaymentAttempt", back_populates="payment")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payment_id: Mapped[str] = mapped_column(String(64), ForeignKey("payments.id"), nullable=False, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    error_type: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="attempts")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    plan_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)  # active, halted, paused, cancelled
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    current_period_end: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="subscription")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subscription_id: Mapped[str] = mapped_column(String(64), ForeignKey("subscriptions.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="unpaid")  # unpaid, paid, expired
    due_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="invoices")


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # PAYMENT, ORDER_ABANDONMENT, SUBSCRIPTION
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.id"), nullable=False, index=True)

    amount_at_risk: Mapped[float] = mapped_column(Float, nullable=False)  # in INR
    recoverability_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 to 1.0
    expected_recovery_value: Mapped[float] = mapped_column(Float, default=0.0)  # amount * score
    recovered_amount: Mapped[float] = mapped_column(Float, default=0.0)  # ONLY > 0 AFTER VERIFIED

    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    failure_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    state: Mapped[RecoveryState] = mapped_column(
        SQLEnum(RecoveryState, native_enum=False),
        default=RecoveryState.CREATED,
        index=True,
    )
    recommended_action: Mapped[Optional[RecoveryStrategy]] = mapped_column(
        SQLEnum(RecoveryStrategy, native_enum=False),
        nullable=True,
    )
    authorized_action: Mapped[Optional[RecoveryStrategy]] = mapped_column(
        SQLEnum(RecoveryStrategy, native_enum=False),
        nullable=True,
    )
    executed_action: Mapped[Optional[RecoveryStrategy]] = mapped_column(
        SQLEnum(RecoveryStrategy, native_enum=False),
        nullable=True,
    )

    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    policy_check_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    human_approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    human_approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    verification_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="cases")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    event_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    agent: Mapped[str] = mapped_column(String(64), nullable=False)  # Detective, Diagnosis, Planner, Policy, Execution, Verification
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Audit Event Metadata per Section 8
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    input_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    output_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    policy_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    policy_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # PASSED, REJECTED, APPROVAL_REQUIRED
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    execution_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # SUCCESS, FAILED, PENDING
    verification_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # VERIFIED, UNVERIFIED, NOT_APPLICABLE
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    case = relationship("RecoveryCase", back_populates="audit_logs")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # x-razorpay-event-id
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    signature: Mapped[str] = mapped_column(String(255), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RecoveryPredictionRecord(Base):
    __tablename__ = "recovery_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature_schema_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_recovery: Mapped[float] = mapped_column(Float, nullable=False)  # Stored as exact INR float
    recoverability_band: Mapped[str] = mapped_column(String(16), nullable=False)  # HIGH, MEDIUM, LOW
    features_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class RecoveryDecision(Base):
    """
    Represents an advisory recommendation and policy assessment.
    Does NOT represent execution.
    """
    __tablename__ = "recovery_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    prediction_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("recovery_predictions.id"), nullable=True)
    agent_run_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    probability_of_recovery: Mapped[float] = mapped_column(Float, nullable=False)
    expected_recovery: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    policy_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    policy_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    policy_result: Mapped[str] = mapped_column(String(32), nullable=False)  # ALLOW, REQUIRE_HUMAN_APPROVAL, DENY
    policy_version: Mapped[str] = mapped_column(String(32), default="ray-policy-v1")
    authorization_required: Mapped[bool] = mapped_column(Boolean, default=False)
    authorization_status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING, AUTHORIZED, REJECTED
    authorized_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ExecutionRecord(Base):
    """
    Represents an attempted financial recovery operation via ToolGateway.
    """
    __tablename__ = "execution_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    decision_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_decisions.id"), nullable=False, index=True)
    strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    authorization_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    execution_status: Mapped[str] = mapped_column(String(32), nullable=False)  # SUCCESS, FAILED, PENDING
    provider_response_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class VerificationRecord(Base):
    """
    Represents independent financial outcome proof required before RECOVERED state.
    """
    __tablename__ = "verification_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(String(64), ForeignKey("execution_records.id"), nullable=False, index=True)
    api_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    signals_agree: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    api_state_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    provider_status: Mapped[str] = mapped_column(String(32), nullable=False)
    verified_amount: Mapped[float] = mapped_column(Float, default=0.0)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False)  # PENDING, VERIFIED, CONFLICT, FAILED
    verification_method: Mapped[str] = mapped_column(String(64), default="dual_signal_api_webhook")
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    api_evidence_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    webhook_evidence_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    evidence_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    verification_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class HumanApprovalRecord(Base):
    """
    Formal human authorization record required before executing high-value or policy-gated recoveries.
    Validates operator identity, policy version, and specific approved strategy.
    """
    __tablename__ = "human_approval_records"

    approval_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_cases.id"), nullable=False, index=True)
    decision_id: Mapped[str] = mapped_column(String(64), ForeignKey("recovery_decisions.id"), nullable=False, index=True)
    operator_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    approved_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    approval_reason: Mapped[str] = mapped_column(Text, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)



