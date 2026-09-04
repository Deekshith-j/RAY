import pytest
from app.models.entities import RecoveryState
from app.core.state_machine import can_transition, validate_transition, InvalidStateTransitionError


def test_valid_state_transitions():
    # Flow: CREATED -> ANALYZING -> RECOVERY_PLANNED -> EXECUTING -> AWAITING_VERIFICATION -> RECOVERED
    assert can_transition(RecoveryState.CREATED, RecoveryState.ANALYZING) is True
    assert can_transition(RecoveryState.ANALYZING, RecoveryState.RECOVERY_PLANNED) is True
    assert can_transition(RecoveryState.RECOVERY_PLANNED, RecoveryState.EXECUTING) is True
    assert can_transition(RecoveryState.EXECUTING, RecoveryState.AWAITING_VERIFICATION) is True
    assert can_transition(RecoveryState.AWAITING_VERIFICATION, RecoveryState.RECOVERED) is True


def test_human_approval_flow():
    assert can_transition(RecoveryState.RECOVERY_PLANNED, RecoveryState.AWAITING_APPROVAL) is True
    assert can_transition(RecoveryState.AWAITING_APPROVAL, RecoveryState.EXECUTING) is True
    assert can_transition(RecoveryState.AWAITING_APPROVAL, RecoveryState.STOPPED) is True


def test_invalid_transitions_rejected():
    # Direct jump from CREATED to RECOVERED is forbidden (must be verified!)
    assert can_transition(RecoveryState.CREATED, RecoveryState.RECOVERED) is False
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(RecoveryState.CREATED, RecoveryState.RECOVERED)

    # RECOVERED is terminal
    assert can_transition(RecoveryState.RECOVERED, RecoveryState.EXECUTING) is False
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(RecoveryState.RECOVERED, RecoveryState.EXECUTING)

    # Cannot jump from ANALYZING to EXECUTING without planning
    assert can_transition(RecoveryState.ANALYZING, RecoveryState.EXECUTING) is False
