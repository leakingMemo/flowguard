"""Tests for FlowGuard models."""

import pytest
from flowguard.models import State, Workflow, WorkflowInstance, Transition


def test_state_creation():
    """Test creating a state."""
    state = State(
        id="test_state",
        name="Test State",
        description="A test state",
        required_context="This is a test",
        transitions={"action": "next_state"}
    )
    
    assert state.id == "test_state"
    assert state.name == "Test State"
    assert state.transitions["action"] == "next_state"


def test_workflow_creation():
    """Test creating a workflow."""
    states = [
        State(id="start", name="Start", required_context="Starting"),
        State(id="end", name="End", required_context="Ending")
    ]
    
    workflow = Workflow(
        name="test_workflow",
        initial_state="start",
        states=states
    )
    
    assert workflow.name == "test_workflow"
    assert workflow.initial_state == "start"
    assert len(workflow.states) == 2


def test_workflow_get_state():
    """Test getting a state from workflow."""
    states = [
        State(id="start", name="Start", required_context="Starting"),
        State(id="end", name="End", required_context="Ending")
    ]
    
    workflow = Workflow(
        name="test_workflow",
        initial_state="start",
        states=states
    )
    
    start_state = workflow.get_state("start")
    assert start_state is not None
    assert start_state.name == "Start"
    
    missing_state = workflow.get_state("missing")
    assert missing_state is None


def test_workflow_instance_history():
    """Test workflow instance history tracking."""
    instance = WorkflowInstance(
        id="test_instance",
        workflow_name="test_workflow",
        current_state="start"
    )
    
    instance.add_history_entry(
        from_state="start",
        to_state="middle",
        action="proceed",
        metadata={"user": "test"}
    )
    
    assert len(instance.history) == 1
    assert instance.history[0]["from_state"] == "start"
    assert instance.history[0]["to_state"] == "middle"
    assert instance.history[0]["action"] == "proceed"
    assert instance.history[0]["metadata"]["user"] == "test"