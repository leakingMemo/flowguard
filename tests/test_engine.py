"""Tests for the state machine engine."""

import pytest
from flowguard.models import State, Workflow
from flowguard.engine import StateMachine
from flowguard.exceptions import TransitionNotAllowedError, PrerequisiteNotMetError


def create_test_workflow():
    """Create a simple test workflow."""
    states = [
        State(
            id="start",
            name="Start",
            required_context="Starting state",
            transitions={"go": "middle"}
        ),
        State(
            id="middle",
            name="Middle",
            required_context="Middle state with {data}",
            transitions={"finish": "end"},
            prerequisites=["data"]
        ),
        State(
            id="end",
            name="End",
            required_context="End state",
            transitions={}
        )
    ]
    
    return Workflow(
        name="test_workflow",
        initial_state="start",
        states=states
    )


def test_state_machine_initialization():
    """Test state machine initialization."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    assert sm.current_state.id == "start"
    assert sm.instance.workflow_name == "test_workflow"


def test_available_actions():
    """Test getting available actions."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    actions = sm.get_available_actions()
    assert actions == ["go"]


def test_valid_transition():
    """Test a valid state transition."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    # Add required data for middle state
    sm.instance.context_data["data"] = "test_value"
    
    # Transition to middle
    new_state = sm.transition("go")
    assert new_state.id == "middle"
    assert sm.current_state.id == "middle"


def test_invalid_transition():
    """Test invalid transition raises error."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    with pytest.raises(TransitionNotAllowedError):
        sm.transition("invalid_action")


def test_prerequisite_checking():
    """Test prerequisite enforcement."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    # Try to transition without required data
    with pytest.raises(PrerequisiteNotMetError):
        sm.transition("go")
    
    # Add required data and retry
    sm.instance.context_data["data"] = "test_value"
    new_state = sm.transition("go")
    assert new_state.id == "middle"


def test_context_injection():
    """Test context generation for injection."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    context = sm.get_context_for_injection()
    assert "Starting state" in context
    assert "Current workflow state: Start" in context
    assert "Available actions: go" in context


def test_context_with_placeholders():
    """Test context with placeholder replacement."""
    workflow = create_test_workflow()
    sm = StateMachine(workflow)
    
    # Transition to middle with data
    sm.instance.context_data["data"] = "important_info"
    sm.transition("go")
    
    context = sm.get_context_for_injection()
    assert "Middle state with important_info" in context