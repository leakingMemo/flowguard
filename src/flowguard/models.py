"""Core models for FlowGuard workflow system."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Transition(BaseModel):
    """Represents a state transition."""
    action: str = Field(..., description="Action that triggers this transition")
    target_state: str = Field(..., description="State to transition to")
    prerequisites: List[str] = Field(default_factory=list, description="Required conditions")
    
    
class State(BaseModel):
    """Represents a workflow state."""
    id: str = Field(..., description="Unique state identifier")
    name: str = Field(..., description="Human-readable state name")
    description: Optional[str] = Field(None, description="State description")
    required_context: str = Field(..., description="Context to inject for this state")
    transitions: Dict[str, str] = Field(default_factory=dict, description="Action -> target state mapping")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites to enter this state")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional state data")
    

class Workflow(BaseModel):
    """Represents a complete workflow definition."""
    name: str = Field(..., description="Workflow name")
    version: str = Field(default="1.0", description="Workflow version")
    description: Optional[str] = Field(None, description="Workflow description")
    initial_state: str = Field(..., description="Starting state ID")
    states: List[State] = Field(..., description="All states in the workflow")
    global_context: Optional[str] = Field(None, description="Context always injected")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow data")
    
    def get_state(self, state_id: str) -> Optional[State]:
        """Get a state by ID."""
        for state in self.states:
            if state.id == state_id:
                return state
        return None
        

class WorkflowInstance(BaseModel):
    """Represents an active workflow instance."""
    id: str = Field(..., description="Instance ID")
    workflow_name: str = Field(..., description="Name of the workflow")
    current_state: str = Field(..., description="Current state ID")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Instance-specific data")
    history: List[Dict[str, Any]] = Field(default_factory=list, description="State transition history")
    
    def add_history_entry(self, from_state: str, to_state: str, action: str, metadata: Optional[Dict] = None):
        """Add a transition to history."""
        entry = {
            "from_state": from_state,
            "to_state": to_state,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.history.append(entry)
        self.updated_at = datetime.now()