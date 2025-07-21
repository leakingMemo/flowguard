# FlowGuard Integrations

This directory contains integration scripts and tools that help FlowGuard work with external applications.

## Claude CLI Integration

The `claude-with-workflow` script provides seamless integration between FlowGuard and the Claude CLI.

### Features

- Automatically detects active FlowGuard workflows in the current directory
- Injects workflow context into Claude conversations via system prompts
- Falls back gracefully to regular Claude when no workflow is active
- Preserves all original Claude CLI functionality and arguments

### Installation

Run the installation script to create a symlink in your PATH:

```bash
./install-claude-wrapper.sh
```

Options:
- `--target-dir <dir>`: Install to a custom directory (default: ~/.local/bin)
- `--force`: Overwrite existing installation
- `--uninstall`: Remove the installed wrapper
- `--help`: Show help message

### Usage

Once installed, use `claude-with-workflow` exactly like the regular `claude` command:

```bash
# Start a conversation with workflow context
claude-with-workflow

# Pass any Claude CLI arguments
claude-with-workflow --model claude-3-opus --temperature 0.7

# Get wrapper-specific help
claude-with-workflow --help-wrapper
```

### How It Works

1. The wrapper checks for an active FlowGuard workflow in the current directory
2. If found, it extracts the workflow context including:
   - Workflow name and description
   - Current state and instructions
   - Workflow variables
   - Available transitions
3. This context is formatted and passed to Claude via `--append-system-prompt`
4. Claude receives the context and can provide workflow-aware assistance

### Troubleshooting

If the wrapper isn't working:

1. Ensure FlowGuard is properly installed and in your Python path
2. Check that you have an active workflow (`flowguard status`)
3. Verify the Claude CLI is installed and working
4. Run with verbose flag for debugging: `claude-with-workflow -v`

### Development

To modify the integration:

1. Edit `claude-with-workflow` directly
2. Test your changes
3. Re-run the installer if needed: `./install-claude-wrapper.sh --force`