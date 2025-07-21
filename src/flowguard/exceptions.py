"""Custom exceptions for FlowGuard."""


class FlowGuardError(Exception):
    """Base exception for FlowGuard."""
    pass


class StateNotFoundError(FlowGuardError):
    """Raised when a state cannot be found in the workflow."""
    pass


class TransitionNotAllowedError(FlowGuardError):
    """Raised when attempting an invalid state transition."""
    pass


class PrerequisiteNotMetError(FlowGuardError):
    """Raised when prerequisites for a state transition are not met."""
    pass


class PersistenceError(FlowGuardError):
    """Raised when there's an error with state persistence."""
    pass


class WorkflowNotFoundError(FlowGuardError):
    """Raised when a workflow cannot be found."""
    pass