"""Command-line interface for FlowGuard."""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from .parser import WorkflowParser
from .engine import StateMachine
from .persistence import StateStore
from .exceptions import FlowGuardError

console = Console()


@click.group()
def cli():
    """FlowGuard - Deterministic workflow enforcement for AI agents."""
    pass


@cli.command()
@click.argument('workflow_name')
@click.argument('description', required=False)
@click.option('--workflow-file', '-f', type=click.Path(exists=True), 
              help='Path to workflow YAML file')
def start(workflow_name: str, description: str = None, workflow_file: str = None):
    """Start a new workflow instance."""
    try:
        # Load workflow
        if workflow_file:
            workflow = WorkflowParser.parse_file(workflow_file)
        else:
            # Look for workflow in standard location
            workflow_path = Path("workflows") / f"{workflow_name}.yaml"
            if not workflow_path.exists():
                console.print(f"[red]Workflow '{workflow_name}' not found[/red]")
                console.print(f"Looked in: {workflow_path}")
                sys.exit(1)
            workflow = WorkflowParser.parse_file(workflow_path)
        
        # Create state machine and persist
        sm = StateMachine(workflow)
        if description:
            sm.instance.context_data['description'] = description
            
        store = StateStore()
        store.save(sm.instance)
        
        # Display initial state
        console.print(Panel(
            f"Started workflow: [bold]{workflow.name}[/bold]\\n"
            f"Instance ID: {sm.instance.id}\\n"
            f"Initial state: [cyan]{sm.current_state.name}[/cyan]",
            title="Workflow Started",
            border_style="green"
        ))
        
        # Show context
        context = sm.get_context_for_injection()
        console.print("\\n[bold]Context for AI:[/bold]")
        console.print(Panel(context, border_style="blue"))
        
    except FlowGuardError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--instance-id', '-i', help='Specific instance ID')
@click.option('--workflow', '-w', help='Show status for specific workflow')
def status(instance_id: str = None, workflow: str = None):
    """Show current workflow status."""
    try:
        store = StateStore()
        
        if instance_id:
            # Load specific instance
            instance = store.load(instance_id)
            if not instance:
                console.print(f"[red]Instance '{instance_id}' not found[/red]")
                sys.exit(1)
            instances = [instance]
        elif workflow:
            # Get active instance for workflow
            instance = store.get_active_instance(workflow)
            if not instance:
                console.print(f"[red]No active instance for workflow '{workflow}'[/red]")
                sys.exit(1)
            instances = [instance]
        else:
            # Show all instances
            instance_list = store.list_instances()
            if not instance_list:
                console.print("[yellow]No active workflow instances[/yellow]")
                return
                
            # Create table
            table = Table(title="Active Workflow Instances")
            table.add_column("ID", style="cyan", width=36)
            table.add_column("Workflow", style="green")
            table.add_column("Current State", style="yellow")
            table.add_column("Updated", style="magenta")
            
            for info in instance_list[:10]:  # Show max 10
                table.add_row(
                    info["id"],
                    info["workflow_name"],
                    info["current_state"],
                    info["updated_at"]
                )
            
            console.print(table)
            return
        
        # Show detailed status for single instance
        for instance in instances:
            # Load the workflow
            workflow_path = Path("workflows") / f"{instance.workflow_name}.yaml"
            if workflow_path.exists():
                workflow = WorkflowParser.parse_file(workflow_path)
                sm = StateMachine(workflow, instance)
                
                console.print(Panel(
                    f"Instance ID: {instance.id}\\n"
                    f"Workflow: [bold]{instance.workflow_name}[/bold]\\n"
                    f"Current state: [cyan]{sm.current_state.name}[/cyan]\\n"
                    f"Available actions: {', '.join(sm.get_available_actions())}\\n"
                    f"Updated: {instance.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                    title="Workflow Status",
                    border_style="blue"
                ))
                
                # Show context
                context = sm.get_context_for_injection()
                console.print("\\n[bold]Current Context:[/bold]")
                console.print(Panel(context, border_style="green"))
                
    except FlowGuardError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('action')
@click.option('--instance-id', '-i', help='Specific instance ID')
@click.option('--workflow', '-w', help='Workflow name')
@click.option('--data', '-d', multiple=True, help='Context data as key=value')
def transition(action: str, instance_id: str = None, workflow: str = None, data: tuple = None):
    """Transition to the next workflow state."""
    try:
        store = StateStore()
        
        # Get instance
        if instance_id:
            instance = store.load(instance_id)
        elif workflow:
            instance = store.get_active_instance(workflow)
        else:
            console.print("[red]Specify either --instance-id or --workflow[/red]")
            sys.exit(1)
            
        if not instance:
            console.print("[red]Instance not found[/red]")
            sys.exit(1)
        
        # Load workflow and create state machine
        workflow_path = Path("workflows") / f"{instance.workflow_name}.yaml"
        workflow_obj = WorkflowParser.parse_file(workflow_path)
        sm = StateMachine(workflow_obj, instance)
        
        # Parse context data
        context_update = {}
        if data:
            for item in data:
                if '=' in item:
                    key, value = item.split('=', 1)
                    context_update[key] = value
        
        # Attempt transition
        old_state = sm.current_state.name
        new_state = sm.transition(action, context_update)
        
        # Save updated instance
        store.save(sm.instance)
        
        console.print(Panel(
            f"Transition successful!\\n"
            f"[yellow]{old_state}[/yellow] → [green]{new_state.name}[/green]\\n"
            f"Action: [cyan]{action}[/cyan]",
            title="State Transition",
            border_style="green"
        ))
        
        # Show new context
        context = sm.get_context_for_injection()
        console.print("\\n[bold]New Context:[/bold]")
        console.print(Panel(context, border_style="blue"))
        
    except FlowGuardError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--days', '-d', default=30, help='Delete instances older than N days')
def cleanup(days: int):
    """Clean up old workflow instances."""
    try:
        store = StateStore()
        deleted = store.cleanup_old_instances(days)
        console.print(f"[green]Deleted {deleted} old instances[/green]")
    except FlowGuardError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('workflow_file', type=click.Path(exists=True))
def validate(workflow_file: str):
    """Validate a workflow YAML file."""
    try:
        workflow = WorkflowParser.parse_file(workflow_file)
        console.print(f"[green]✓ Workflow '{workflow.name}' is valid[/green]")
        
        # Show workflow structure
        console.print(f"\\nWorkflow: [bold]{workflow.name}[/bold]")
        console.print(f"Version: {workflow.version}")
        console.print(f"States: {len(workflow.states)}")
        console.print(f"Initial state: {workflow.initial_state}")
        
        # Show states
        console.print("\\n[bold]States:[/bold]")
        for state in workflow.states:
            console.print(f"  - {state.id} ({state.name})")
            for action, target in state.transitions.items():
                console.print(f"    → {action}: {target}")
                
    except Exception as e:
        console.print(f"[red]Invalid workflow: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()