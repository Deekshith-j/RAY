import pytest
from app.core.policy_engine import PolicyEngine
from app.models.entities import RecoveryCase, Customer, RecoveryStrategy, RecoveryState


def test_customer_opt_out():
    engine = PolicyEngine()
    customer = Customer(id="c1", name="Test User", email="test@example.com", opt_out=True)
    case = RecoveryCase(
        id="case1",
        entity_type="PAYMENT",
        entity_id="pay_1",
        customer_id="c1",
        amount_at_risk=2000.0,
        failure_type="network_error",
        failure_reason="Timeout",
        retry_count=0,
    )

    decision = engine.evaluate(case, RecoveryStrategy.RETRY, customer=customer)
    assert decision.allowed is False
    assert decision.rule_code == "CUSTOMER_OPT_OUT"


def test_high_value_requires_human_approval():
    engine = PolicyEngine(human_approval_threshold=50000.0)
    case = RecoveryCase(
        id="case_high",
        entity_type="PAYMENT",
        entity_id="pay_high",
        customer_id="c2",
        amount_at_risk=75000.0,
        failure_type="timeout",
        failure_reason="Network Timeout",
        retry_count=0,
    )

    decision = engine.evaluate(case, RecoveryStrategy.PAYMENT_LINK)
    assert decision.allowed is True
    assert decision.requires_human_approval is True
    assert decision.rule_code == "HUMAN_APPROVAL_REQUIRED"


def test_auto_retry_policy_constraints():
    engine = PolicyEngine(
        auto_retry_max_amount=10000.0,
        max_retry_attempts=1,
        allowed_retry_failure_types=["network_error", "timeout"],
    )

    # Eligible retry
    valid_case = RecoveryCase(
        id="case_v",
        entity_type="PAYMENT",
        entity_id="pay_v",
        customer_id="c3",
        amount_at_risk=4999.0,
        failure_type="network_error",
        failure_reason="Gateway timeout",
        retry_count=0,
    )
    d1 = engine.evaluate(valid_case, RecoveryStrategy.RETRY)
    assert d1.allowed is True
    assert d1.requires_human_approval is False
    assert d1.rule_code == "RETRY_POLICY_PASSED"

    # Exceeding amount limit (e.g. ₹15,000 > ₹10,000)
    over_limit_case = RecoveryCase(
        id="case_ol",
        entity_type="PAYMENT",
        entity_id="pay_ol",
        customer_id="c3",
        amount_at_risk=15000.0,
        failure_type="network_error",
        failure_reason="Gateway timeout",
        retry_count=0,
    )
    d2 = engine.evaluate(over_limit_case, RecoveryStrategy.RETRY)
    assert d2.allowed is False
    assert d2.rule_code == "AMOUNT_EXCEEDS_RETRY_LIMIT"
    assert d2.fallback_strategy == RecoveryStrategy.PAYMENT_LINK

    # Disallowed failure type (e.g. permanent card decline)
    declined_case = RecoveryCase(
        id="case_dec",
        entity_type="PAYMENT",
        entity_id="pay_dec",
        customer_id="c3",
        amount_at_risk=1000.0,
        failure_type="card_declined_permanent",
        failure_reason="Card reported stolen",
        retry_count=0,
    )
    d3 = engine.evaluate(declined_case, RecoveryStrategy.RETRY)
    assert d3.allowed is False
    assert d3.rule_code == "DISALLOWED_RETRY_FAILURE_TYPE"
