#!/bin/bash
# Installation script for FlowGuard MCP Server

set -e

echo "Installing FlowGuard MCP Server..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_SERVER_PATH="${SCRIPT_DIR}/flowguard-mcp-server"

# Create workflows directory
WORKFLOWS_DIR="${HOME}/.flowguard/workflows"
mkdir -p "$WORKFLOWS_DIR"

# Copy sample workflows if they don't exist
REPO_ROOT="${SCRIPT_DIR}/../../../.."
if [ -d "${REPO_ROOT}/workflows" ]; then
    echo "Copying sample workflows to $WORKFLOWS_DIR..."
    for workflow in "${REPO_ROOT}/workflows"/*.yaml; do
        if [ -f "$workflow" ]; then
            basename_workflow=$(basename "$workflow")
            if [ ! -f "$WORKFLOWS_DIR/$basename_workflow" ]; then
                cp "$workflow" "$WORKFLOWS_DIR/"
                echo "  - Copied $basename_workflow"
            fi
        fi
    done
fi

# Install to /usr/local/bin
INSTALL_PATH="/usr/local/bin/flowguard-mcp"
echo "Installing MCP server to $INSTALL_PATH..."

# Create wrapper script that sets up the Python path correctly
cat > /tmp/flowguard-mcp-wrapper << 'EOF'
#!/bin/bash
# FlowGuard MCP Server wrapper

# Get the real path of this script
SCRIPT_PATH="$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")"

# Determine the FlowGuard installation directory
if [[ "$SCRIPT_PATH" == "/usr/local/bin/flowguard-mcp" ]]; then
    # Installed via install script - find the source
    FLOWGUARD_SRC=""
    
    # Check common locations
    for dir in "$HOME/git/flowguard" "$HOME/projects/flowguard" "$HOME/flowguard" "/opt/flowguard"; do
        if [ -f "$dir/src/flowguard/integrations/mcp/server.py" ]; then
            FLOWGUARD_SRC="$dir/src"
            break
        fi
    done
    
    if [ -z "$FLOWGUARD_SRC" ]; then
        echo "Error: Could not find FlowGuard source directory" >&2
        echo "Please set FLOWGUARD_SRC environment variable" >&2
        exit 1
    fi
else
    # Running from source
    FLOWGUARD_SRC="$(cd "$(dirname "$SCRIPT_PATH")/../../../../src" && pwd)"
fi

# Set Python path and run the server
export PYTHONPATH="$FLOWGUARD_SRC:$PYTHONPATH"
exec python3 -m flowguard.integrations.mcp.server "$@"
EOF

# Install the wrapper
sudo mv /tmp/flowguard-mcp-wrapper "$INSTALL_PATH"
sudo chmod +x "$INSTALL_PATH"

# Create MCP configuration for Claude Desktop
CLAUDE_CONFIG_DIR="${HOME}/Library/Application Support/Claude"
if [ -d "$CLAUDE_CONFIG_DIR" ]; then
    CLAUDE_CONFIG_FILE="${CLAUDE_CONFIG_DIR}/claude_desktop_config.json"
    
    echo
    echo "Detected Claude Desktop configuration directory."
    echo
    echo "To configure Claude Desktop to use the FlowGuard MCP server,"
    echo "add the following to your $CLAUDE_CONFIG_FILE:"
    echo
    echo '  "mcpServers": {'
    echo '    "flowguard": {'
    echo '      "command": "/usr/local/bin/flowguard-mcp",'
    echo '      "args": [],'
    echo '      "env": {'
    echo '        "FLOWGUARD_WORKFLOWS_DIR": "'$WORKFLOWS_DIR'",'
    echo "        \"FLOWGUARD_SRC\": \"${SCRIPT_DIR}/../../../../src\""
    echo '      }'
    echo '    }'
    echo '  }'
    echo
    echo "Note: Make sure to add this within the existing JSON structure,"
    echo "not as a standalone block."
else
    echo
    echo "Claude Desktop configuration directory not found."
    echo "Please refer to the documentation for manual configuration."
fi

echo
echo "FlowGuard MCP Server installed successfully!"
echo "Server executable: $INSTALL_PATH"
echo "Workflows directory: $WORKFLOWS_DIR"
echo
echo "To test the server, run:"
echo "  $INSTALL_PATH"
echo