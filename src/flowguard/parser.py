"""YAML workflow parser for FlowGuard."""

import yaml
from pathlib import Path
from typing import Dict, Any, Union
from .models import Workflow, State


class WorkflowParser:
    """Parses YAML workflow definitions into Workflow objects."""
    
    @staticmethod
    def parse_file(filepath: Union[str, Path]) -> Workflow:
        """Parse a workflow from a YAML file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Workflow file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            
        return WorkflowParser.parse_dict(data)
    
    @staticmethod
    def parse_string(yaml_string: str) -> Workflow:
        """Parse a workflow from a YAML string."""
        data = yaml.safe_load(yaml_string)
        return WorkflowParser.parse_dict(data)
    
    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> Workflow:
        """Parse a workflow from a dictionary."""
        # Parse states
        states = []
        for state_data in data.get('states', []):
            state = State(
                id=state_data['id'],
                name=state_data.get('name', state_data['id']),
                description=state_data.get('description'),
                required_context=state_data.get('required_context', ''),
                transitions=state_data.get('transitions', {}),
                prerequisites=state_data.get('prerequisites', []),
                metadata=state_data.get('metadata', {})
            )
            states.append(state)
        
        # Create workflow
        workflow = Workflow(
            name=data['name'],
            version=data.get('version', '1.0'),
            description=data.get('description'),
            initial_state=data.get('initial_state', states[0].id if states else ''),
            states=states,
            global_context=data.get('global_context'),
            metadata=data.get('metadata', {})
        )
        
        # Validate workflow
        WorkflowParser._validate_workflow(workflow)
        
        return workflow
    
    @staticmethod
    def _validate_workflow(workflow: Workflow) -> None:
        """Validate workflow integrity."""
        state_ids = {state.id for state in workflow.states}
        
        # Check initial state exists
        if workflow.initial_state not in state_ids:
            raise ValueError(f"Initial state '{workflow.initial_state}' not found in workflow")
        
        # Check all transitions point to valid states
        for state in workflow.states:
            for action, target_state in state.transitions.items():
                if target_state not in state_ids:
                    raise ValueError(
                        f"State '{state.id}' has transition '{action}' to "
                        f"non-existent state '{target_state}'"
                    )
    
    @staticmethod
    def workflow_to_yaml(workflow: Workflow) -> str:
        """Convert a Workflow object back to YAML."""
        data = {
            'name': workflow.name,
            'version': workflow.version,
            'description': workflow.description,
            'initial_state': workflow.initial_state,
            'states': []
        }
        
        if workflow.global_context:
            data['global_context'] = workflow.global_context
            
        if workflow.metadata:
            data['metadata'] = workflow.metadata
        
        for state in workflow.states:
            state_data = {
                'id': state.id,
                'name': state.name,
                'required_context': state.required_context,
            }
            
            if state.description:
                state_data['description'] = state.description
            if state.transitions:
                state_data['transitions'] = state.transitions
            if state.prerequisites:
                state_data['prerequisites'] = state.prerequisites
            if state.metadata:
                state_data['metadata'] = state.metadata
                
            data['states'].append(state_data)
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False)