"""Tests for Policy Engine decision object and policy versioning."""

from app.core.policy_engine import PolicyEngine, PolicyDecision
from app.models.entities import RecoveryCase, RecoveryStrategy, Customer


def test_policy_decision_version_and_explicit_fields():
    engine = PolicyEngine()
    case = RecoveryCase(
        id="case_pol_test",
        customer_id="cust_test",
        amount_at_risk=24999.00,
        failure_type="timeout",
        retry_count=0,
    )

    decision = engine.evaluate(case, RecoveryStrategy.RETRY)

    assert isinstance(decision, PolicyDecision)
    assert decision.policy_version == "v1.0"
    assert decision.decision in ("ALLOW", "DENY", "REQUIRE_HUMAN_APPROVAL")
    assert decision.allowed is True
    assert decision.requires_human_approval is False
    assert decision.rule_code == "RETRY_POLICY_PASSED"
    assert decision.correlation_id.startswith("pol_")


def test_high_value_policy_explicit_requirement():
    engine = PolicyEngine()
    case = RecoveryCase(
        id="case_high_val",
        customer_id="cust_test",
        amount_at_risk=75000.00,
        failure_type="timeout",
        retry_count=0,
    )

    decision = engine.evaluate(case, RecoveryStrategy.RETRY)

    assert decision.requires_human_approval is True
    assert decision.rule_code == "HUMAN_APPROVAL_REQUIRED"
    assert "₹50,000" in decision.reason
