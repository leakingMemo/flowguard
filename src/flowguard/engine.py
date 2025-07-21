"""State machine engine for FlowGuard."""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from .models import Workflow, WorkflowInstance, State
from .exceptions import (
    StateNotFoundError, 
    TransitionNotAllowedError,
    PrerequisiteNotMetError
)


class StateMachine:
    """Manages workflow state transitions and enforcement."""
    
    def __init__(self, workflow: Workflow, instance: Optional[WorkflowInstance] = None):
        """Initialize state machine with a workflow."""
        self.workflow = workflow
        self.instance = instance or self._create_instance()
        self.prerequisite_checkers: Dict[str, Callable] = {}
        
    def _create_instance(self) -> WorkflowInstance:
        """Create a new workflow instance."""
        import uuid
        return WorkflowInstance(
            id=str(uuid.uuid4()),
            workflow_name=self.workflow.name,
            current_state=self.workflow.initial_state
        )
    
    @property
    def current_state(self) -> State:
        """Get the current state object."""
        state = self.workflow.get_state(self.instance.current_state)
        if not state:
            raise StateNotFoundError(f"State '{self.instance.current_state}' not found")
        return state
    
    def register_prerequisite_checker(self, name: str, checker: Callable[[WorkflowInstance], bool]):
        """Register a function to check prerequisites."""
        self.prerequisite_checkers[name] = checker
    
    def can_transition(self, action: str) -> bool:
        """Check if a transition is allowed from current state."""
        return action in self.current_state.transitions
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions from current state."""
        return list(self.current_state.transitions.keys())
    
    def check_prerequisites(self, target_state_id: str) -> List[str]:
        """Check prerequisites for entering a state. Returns list of unmet prerequisites."""
        target_state = self.workflow.get_state(target_state_id)
        if not target_state:
            raise StateNotFoundError(f"State '{target_state_id}' not found")
        
        unmet = []
        for prereq in target_state.prerequisites:
            # Check if we have a registered checker for this prerequisite
            if prereq in self.prerequisite_checkers:
                if not self.prerequisite_checkers[prereq](self.instance):
                    unmet.append(prereq)
            else:
                # If no checker registered, check context data
                if prereq not in self.instance.context_data:
                    unmet.append(prereq)
                    
        return unmet
    
    def transition(self, action: str, context_update: Optional[Dict[str, Any]] = None) -> State:
        """Execute a state transition."""
        # Check if action is valid
        if not self.can_transition(action):
            raise TransitionNotAllowedError(
                f"Action '{action}' not allowed from state '{self.instance.current_state}'. "
                f"Available actions: {self.get_available_actions()}"
            )
        
        # Get target state
        target_state_id = self.current_state.transitions[action]
        
        # Check prerequisites
        unmet_prereqs = self.check_prerequisites(target_state_id)
        if unmet_prereqs:
            raise PrerequisiteNotMetError(
                f"Cannot transition to '{target_state_id}'. "
                f"Unmet prerequisites: {unmet_prereqs}"
            )
        
        # Update context if provided
        if context_update:
            self.instance.context_data.update(context_update)
        
        # Record transition in history
        self.instance.add_history_entry(
            from_state=self.instance.current_state,
            to_state=target_state_id,
            action=action,
            metadata=context_update
        )
        
        # Update current state
        self.instance.current_state = target_state_id
        
        return self.current_state
    
    def get_context_for_injection(self) -> str:
        """Generate context string for injection into AI conversation."""
        contexts = []
        
        # Add global context if present
        if self.workflow.global_context:
            contexts.append(self.workflow.global_context)
        
        # Add current state context
        state_context = self.current_state.required_context
        
        # Replace placeholders with actual values from context_data
        for key, value in self.instance.context_data.items():
            placeholder = f"{{{key}}}"
            state_context = state_context.replace(placeholder, str(value))
        
        contexts.append(f"Current workflow state: {self.current_state.name}")
        contexts.append(state_context)
        
        # Add available actions
        actions = self.get_available_actions()
        if actions:
            contexts.append(f"Available actions: {', '.join(actions)}")
        
        # Add any unmet prerequisites for next states
        next_states_info = []
        for action, target_state_id in self.current_state.transitions.items():
            unmet = self.check_prerequisites(target_state_id)
            if unmet:
                next_states_info.append(f"To {action}: requires {', '.join(unmet)}")
        
        if next_states_info:
            contexts.append("Prerequisites needed: " + "; ".join(next_states_info))
        
        return "\\n".join(contexts)
    
    def get_instance_summary(self) -> Dict[str, Any]:
        """Get a summary of the current instance state."""
        return {
            "id": self.instance.id,
            "workflow": self.workflow.name,
            "current_state": self.current_state.name,
            "current_state_id": self.instance.current_state,
            "available_actions": self.get_available_actions(),
            "context_data": self.instance.context_data,
            "created_at": self.instance.created_at.isoformat(),
            "updated_at": self.instance.updated_at.isoformat(),
            "history_length": len(self.instance.history)
        }