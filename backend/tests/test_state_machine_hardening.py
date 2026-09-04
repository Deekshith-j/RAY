"""State Machine Hardening Tests.

Verifies Section 26 invariants:
- Impossible transitions remain impossible.
- Forbidden:
    FAILED -> RECOVERED
    EXECUTING -> RECOVERED
    CREATED -> RECOVERED
    ANALYZING -> RECOVERED
    RECOVERY_PLANNED -> RECOVERED
- A case MUST pass through AWAITING_VERIFICATION before RECOVERED.
- Terminal state RECOVERED cannot transition out.
- Dual-signal conflict triggers AWAITING_VERIFICATION -> HUMAN_REVIEW.
"""

import pytest
from app.models.entities import RecoveryState
from app.core.state_machine import (
    can_transition,
    validate_transition,
    InvalidStateTransitionError,
)


def test_forbidden_direct_to_recovered_transitions():
    """Verify that NO state can transition directly to RECOVERED except AWAITING_VERIFICATION (and ATTEMPTED)."""
    forbidden_sources = [
        RecoveryState.CREATED,
        RecoveryState.FAILED,
        RecoveryState.ANALYZING,
        RecoveryState.RECOVERY_PLANNED,
        RecoveryState.AWAITING_APPROVAL,
        RecoveryState.EXECUTING,
        RecoveryState.FAILED_RECOVERY,
        RecoveryState.STOPPED,
        RecoveryState.HUMAN_REVIEW,
    ]

    for source in forbidden_sources:
        assert not can_transition(source, RecoveryState.RECOVERED), (
            f"State machine allowed forbidden direct jump from {source.value} to RECOVERED!"
        )
        with pytest.raises(InvalidStateTransitionError):
            validate_transition(source, RecoveryState.RECOVERED)


def test_valid_low_value_recovery_lifecycle():
    """Verify the standard valid sequence for low-value automatic recovery."""
    # FAILED -> ANALYZING -> RECOVERY_PLANNED -> EXECUTING -> AWAITING_VERIFICATION -> RECOVERED
    state = RecoveryState.FAILED

    validate_transition(state, RecoveryState.ANALYZING)
    state = RecoveryState.ANALYZING

    validate_transition(state, RecoveryState.RECOVERY_PLANNED)
    state = RecoveryState.RECOVERY_PLANNED

    validate_transition(state, RecoveryState.EXECUTING)
    state = RecoveryState.EXECUTING

    validate_transition(state, RecoveryState.AWAITING_VERIFICATION)
    state = RecoveryState.AWAITING_VERIFICATION

    validate_transition(state, RecoveryState.RECOVERED)
    state = RecoveryState.RECOVERED

    assert state == RecoveryState.RECOVERED


def test_valid_high_value_recovery_lifecycle():
    """Verify the standard valid sequence for high-value gated recovery."""
    # FAILED -> ANALYZING -> RECOVERY_PLANNED -> AWAITING_APPROVAL -> EXECUTING -> AWAITING_VERIFICATION -> RECOVERED
    state = RecoveryState.FAILED

    validate_transition(state, RecoveryState.ANALYZING)
    state = RecoveryState.ANALYZING

    validate_transition(state, RecoveryState.RECOVERY_PLANNED)
    state = RecoveryState.RECOVERY_PLANNED

    validate_transition(state, RecoveryState.AWAITING_APPROVAL)
    state = RecoveryState.AWAITING_APPROVAL

    validate_transition(state, RecoveryState.EXECUTING)
    state = RecoveryState.EXECUTING

    validate_transition(state, RecoveryState.AWAITING_VERIFICATION)
    state = RecoveryState.AWAITING_VERIFICATION

    validate_transition(state, RecoveryState.RECOVERED)
    state = RecoveryState.RECOVERED

    assert state == RecoveryState.RECOVERED


def test_verification_conflict_escalation():
    """Verify that a verification conflict safely escalates to HUMAN_REVIEW."""
    state = RecoveryState.AWAITING_VERIFICATION
    assert can_transition(state, RecoveryState.HUMAN_REVIEW)
    validate_transition(state, RecoveryState.HUMAN_REVIEW)


def test_recovered_is_strictly_terminal():
    """Once RECOVERED, no automatic transition can un-recover or modify state."""
    assert not can_transition(RecoveryState.RECOVERED, RecoveryState.FAILED)
    assert not can_transition(RecoveryState.RECOVERED, RecoveryState.ANALYZING)
    assert not can_transition(RecoveryState.RECOVERED, RecoveryState.EXECUTING)
