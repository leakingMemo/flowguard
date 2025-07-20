# FlowGuard 🛡️

**Deterministic workflow enforcement for AI agents through context injection**

FlowGuard ensures AI agents follow predefined workflows by managing state and injecting context at the optimal point in the conversation flow.

## The Problem

AI agents (like Claude) can "forget" workflow requirements because:
- Instructions in system prompts get diluted by distance in the context window
- No enforcement mechanism exists for multi-step processes
- State isn't persisted between actions

## The Solution

FlowGuard acts as a **workflow state machine** that:
1. Tracks the current state of any workflow
2. Injects relevant context/rules at the end of the AI's context window
3. Enforces prerequisites before allowing certain actions
4. Maintains persistence across sessions

## Key Features

- 🔄 **State Machine Engine** - Define workflows as state transitions
- 💉 **Smart Context Injection** - Right context at the right time
- 🚦 **Prerequisite Enforcement** - Can't skip steps
- 📝 **Workflow Templates** - Common patterns ready to use
- 🔍 **State Inspection** - Know exactly where you are in a process

## Quick Start

```bash
# Install FlowGuard
./install.sh

# Start a GitHub feature workflow
flowguard start github-feature "Add new authentication method"

# Check current state
flowguard status

# Transition to next state (if prerequisites met)
flowguard next
```

## Example Workflow

```yaml
name: github-feature
states:
  - id: need_issue
    required_context: "Must create GitHub issue first"
    transitions:
      create_issue: has_issue
      
  - id: has_issue
    required_context: "Issue #{issue_number} created"
    transitions:
      create_branch: on_branch
      
  - id: on_branch
    required_context: "Working on branch: {branch_name}"
    transitions:
      make_changes: changes_made
```

## How It Works

1. **Define** your workflow in YAML
2. **Start** the workflow with `flowguard start`
3. **FlowGuard** tracks state and injects context
4. **AI agents** see the context and follow the workflow
5. **Transitions** happen only when prerequisites are met

Built with ❤️ for developers who want predictable AI agent behavior.