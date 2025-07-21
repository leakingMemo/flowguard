"""FlowGuard MCP Server implementation."""

import json
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

from flowguard.engine import StateMachine
from flowguard.parser import WorkflowParser
from flowguard.persistence import WorkflowPersistence
from flowguard.exceptions import StateNotFoundError, TransitionNotAllowedError


class WorkflowStatusArgs(BaseModel):
    """Arguments for checking workflow status."""
    instance_id: Optional[str] = Field(None, description="Workflow instance ID. If not provided, shows all active instances.")


class TransitionWorkflowArgs(BaseModel):
    """Arguments for transitioning workflow state."""
    instance_id: str = Field(..., description="Workflow instance ID")
    action: str = Field(..., description="Action to perform")
    context_update: Optional[Dict[str, Any]] = Field(None, description="Optional context data to update")


class GetWorkflowContextArgs(BaseModel):
    """Arguments for getting workflow context."""
    instance_id: str = Field(..., description="Workflow instance ID")


class CreateWorkflowArgs(BaseModel):
    """Arguments for creating a new workflow instance."""
    workflow_name: str = Field(..., description="Name of the workflow to instantiate")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Initial context data")


class ListWorkflowsArgs(BaseModel):
    """Arguments for listing available workflows."""
    pass


class FlowGuardMCPServer:
    """MCP Server for FlowGuard workflow management."""
    
    def __init__(self):
        self.server = Server("flowguard")
        self.parser = WorkflowParser()
        self.persistence = WorkflowPersistence()
        self.active_machines: Dict[str, StateMachine] = {}
        self.workflow_dir = Path(os.environ.get("FLOWGUARD_WORKFLOWS_DIR", "~/.flowguard/workflows")).expanduser()
        
        # Register tools
        self._register_tools()
        
    def _register_tools(self):
        """Register all FlowGuard tools with the MCP server."""
        
        @self.server.tool()
        async def check_workflow_status(arguments: WorkflowStatusArgs) -> List[TextContent]:
            """Check the status of workflow instances."""
            if arguments.instance_id:
                # Get specific instance
                if arguments.instance_id not in self.active_machines:
                    return [TextContent(
                        type="text",
                        text=f"Workflow instance '{arguments.instance_id}' not found."
                    )]
                
                machine = self.active_machines[arguments.instance_id]
                summary = machine.get_instance_summary()
                
                return [TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2)
                )]
            else:
                # List all instances
                if not self.active_machines:
                    return [TextContent(
                        type="text",
                        text="No active workflow instances."
                    )]
                
                summaries = []
                for instance_id, machine in self.active_machines.items():
                    summary = machine.get_instance_summary()
                    summaries.append(summary)
                
                return [TextContent(
                    type="text",
                    text=json.dumps(summaries, indent=2)
                )]
        
        @self.server.tool()
        async def transition_workflow(arguments: TransitionWorkflowArgs) -> List[TextContent]:
            """Transition a workflow to a new state."""
            if arguments.instance_id not in self.active_machines:
                return [TextContent(
                    type="text",
                    text=f"Workflow instance '{arguments.instance_id}' not found."
                )]
            
            machine = self.active_machines[arguments.instance_id]
            
            try:
                new_state = machine.transition(
                    arguments.action,
                    arguments.context_update
                )
                
                # Save instance state
                self.persistence.save_instance(machine.instance)
                
                return [TextContent(
                    type="text",
                    text=f"Successfully transitioned to state '{new_state.name}' via action '{arguments.action}'."
                )]
            except TransitionNotAllowedError as e:
                return [TextContent(
                    type="text",
                    text=f"Transition failed: {str(e)}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error during transition: {str(e)}"
                )]
        
        @self.server.tool()
        async def get_workflow_context(arguments: GetWorkflowContextArgs) -> List[TextContent]:
            """Get the context injection for a workflow instance."""
            if arguments.instance_id not in self.active_machines:
                return [TextContent(
                    type="text",
                    text=f"Workflow instance '{arguments.instance_id}' not found."
                )]
            
            machine = self.active_machines[arguments.instance_id]
            context = machine.get_context_for_injection()
            
            return [TextContent(
                type="text",
                text=context
            )]
        
        @self.server.tool()
        async def create_workflow_instance(arguments: CreateWorkflowArgs) -> List[TextContent]:
            """Create a new workflow instance."""
            # Look for workflow file
            workflow_files = [
                self.workflow_dir / f"{arguments.workflow_name}.yaml",
                self.workflow_dir / f"{arguments.workflow_name}.yml",
                Path(f"{arguments.workflow_name}.yaml"),
                Path(f"{arguments.workflow_name}.yml"),
            ]
            
            workflow_file = None
            for file in workflow_files:
                if file.exists():
                    workflow_file = file
                    break
            
            if not workflow_file:
                return [TextContent(
                    type="text",
                    text=f"Workflow '{arguments.workflow_name}' not found in any of: {[str(f) for f in workflow_files]}"
                )]
            
            try:
                # Parse workflow
                workflow = self.parser.parse_file(str(workflow_file))
                
                # Create state machine
                machine = StateMachine(workflow)
                
                # Update context if provided
                if arguments.context_data:
                    machine.instance.context_data.update(arguments.context_data)
                
                # Save instance
                self.persistence.save_instance(machine.instance)
                
                # Store in active machines
                self.active_machines[machine.instance.id] = machine
                
                return [TextContent(
                    type="text",
                    text=f"Created workflow instance '{machine.instance.id}' for workflow '{arguments.workflow_name}'.\n"
                         f"Initial state: {machine.current_state.name}"
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error creating workflow instance: {str(e)}"
                )]
        
        @self.server.tool()
        async def list_available_workflows(arguments: ListWorkflowsArgs) -> List[TextContent]:
            """List all available workflow definitions."""
            workflows = []
            
            # Check workflow directory
            if self.workflow_dir.exists():
                for file in self.workflow_dir.glob("*.yaml"):
                    workflows.append(file.stem)
                for file in self.workflow_dir.glob("*.yml"):
                    workflows.append(file.stem)
            
            # Check current directory
            for file in Path(".").glob("*.yaml"):
                if file.stem not in workflows:
                    workflows.append(file.stem)
            for file in Path(".").glob("*.yml"):
                if file.stem not in workflows:
                    workflows.append(file.stem)
            
            if not workflows:
                return [TextContent(
                    type="text",
                    text="No workflow definitions found."
                )]
            
            return [TextContent(
                type="text",
                text=f"Available workflows:\n" + "\n".join(f"- {w}" for w in sorted(set(workflows)))
            )]
        
        # Store tool definitions for listing
        self.tools = [
            Tool(
                name="check_workflow_status",
                description="Check the status of workflow instances",
                inputSchema=WorkflowStatusArgs.model_json_schema()
            ),
            Tool(
                name="transition_workflow",
                description="Transition a workflow to a new state",
                inputSchema=TransitionWorkflowArgs.model_json_schema()
            ),
            Tool(
                name="get_workflow_context",
                description="Get the context injection for a workflow instance",
                inputSchema=GetWorkflowContextArgs.model_json_schema()
            ),
            Tool(
                name="create_workflow_instance",
                description="Create a new workflow instance",
                inputSchema=CreateWorkflowArgs.model_json_schema()
            ),
            Tool(
                name="list_available_workflows",
                description="List all available workflow definitions",
                inputSchema=ListWorkflowsArgs.model_json_schema()
            )
        ]
    
    def load_active_instances(self):
        """Load all active workflow instances from persistence."""
        instances = self.persistence.list_instances()
        
        for instance in instances:
            # Load the workflow definition
            workflow_file = None
            workflow_files = [
                self.workflow_dir / f"{instance.workflow_name}.yaml",
                self.workflow_dir / f"{instance.workflow_name}.yml",
                Path(f"{instance.workflow_name}.yaml"),
                Path(f"{instance.workflow_name}.yml"),
            ]
            
            for file in workflow_files:
                if file.exists():
                    workflow_file = file
                    break
            
            if workflow_file:
                try:
                    workflow = self.parser.parse_file(str(workflow_file))
                    machine = StateMachine(workflow, instance)
                    self.active_machines[instance.id] = machine
                except Exception as e:
                    print(f"Error loading instance {instance.id}: {e}", file=sys.stderr)
    
    async def run(self):
        """Run the MCP server."""
        # Load active instances
        self.load_active_instances()
        
        # Start the server
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


def main():
    """Main entry point for the MCP server."""
    import asyncio
    
    server = FlowGuardMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()