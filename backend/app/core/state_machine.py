from typing import Set, Dict
from app.models.entities import RecoveryState


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal state transition is attempted."""
    pass


# Strict transition graph for financial recovery state machine
VALID_TRANSITIONS: Dict[RecoveryState, Set[RecoveryState]] = {
    RecoveryState.CREATED: {
        RecoveryState.ATTEMPTED,
        RecoveryState.FAILED,
        RecoveryState.ANALYZING,
        RecoveryState.STOPPED,
    },
    RecoveryState.ATTEMPTED: {
        RecoveryState.FAILED,
        RecoveryState.RECOVERED,
        RecoveryState.ANALYZING,
    },
    RecoveryState.FAILED: {
        RecoveryState.ANALYZING,
        RecoveryState.STOPPED,
        RecoveryState.HUMAN_REVIEW,
    },
    RecoveryState.ANALYZING: {
        RecoveryState.RECOVERY_PLANNED,
        RecoveryState.STOPPED,
        RecoveryState.HUMAN_REVIEW,
    },
    RecoveryState.RECOVERY_PLANNED: {
        RecoveryState.AWAITING_APPROVAL,
        RecoveryState.EXECUTING,
        RecoveryState.STOPPED,
        RecoveryState.HUMAN_REVIEW,
    },
    RecoveryState.AWAITING_APPROVAL: {
        RecoveryState.EXECUTING,       # Approved by human
        RecoveryState.STOPPED,         # Rejected by human
        RecoveryState.HUMAN_REVIEW,    # Escalated
    },
    RecoveryState.EXECUTING: {
        RecoveryState.AWAITING_VERIFICATION,
        RecoveryState.FAILED_RECOVERY,
        RecoveryState.HUMAN_REVIEW,
    },
    RecoveryState.AWAITING_VERIFICATION: {
        RecoveryState.RECOVERED,       # Independently verified success!
        RecoveryState.FAILED_RECOVERY, # Verification determined failure
        RecoveryState.HUMAN_REVIEW,    # Mismatch or suspicious outcome
    },
    # Terminal or escalation states
    RecoveryState.RECOVERED: set(),  # Terminal state
    RecoveryState.FAILED_RECOVERY: {
        RecoveryState.ANALYZING,      # Can re-analyze if within max attempt limit
        RecoveryState.HUMAN_REVIEW,
        RecoveryState.STOPPED,
    },
    RecoveryState.STOPPED: {
        RecoveryState.HUMAN_REVIEW,   # Reopen by human if needed
    },
    RecoveryState.HUMAN_REVIEW: {
        RecoveryState.RECOVERY_PLANNED,
        RecoveryState.EXECUTING,
        RecoveryState.STOPPED,
    },
}


def can_transition(current_state: RecoveryState, target_state: RecoveryState) -> bool:
    """Return True if current_state can transition to target_state."""
    allowed = VALID_TRANSITIONS.get(current_state, set())
    return target_state in allowed


def validate_transition(current_state: RecoveryState, target_state: RecoveryState) -> None:
    """Raise InvalidStateTransitionError if the transition is illegal."""
    if not can_transition(current_state, target_state):
        raise InvalidStateTransitionError(
            f"Invalid recovery state transition: cannot move from {current_state.value} to {target_state.value}. "
            f"Allowed next states: {[s.value for s in VALID_TRANSITIONS.get(current_state, set())]}"
        )
