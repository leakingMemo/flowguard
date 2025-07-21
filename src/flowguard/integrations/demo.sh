#!/bin/bash
# Demo script showing the Claude-FlowGuard integration

echo "FlowGuard-Claude Integration Demo"
echo "================================="
echo ""

# Check if wrapper is installed
if command -v claude-with-workflow &> /dev/null; then
    echo "✓ claude-with-workflow is installed"
else
    echo "⚠️  claude-with-workflow not found in PATH"
    echo "   Run ./install-claude-wrapper.sh to install"
    exit 1
fi

echo ""
echo "The wrapper works transparently with all Claude CLI options:"
echo ""

# Show some example commands
echo "Examples:"
echo "---------"
echo "# Start a conversation with workflow context:"
echo "$ claude-with-workflow"
echo ""
echo "# Ask a specific question:"
echo '$ claude-with-workflow "How do I complete the current workflow state?"'
echo ""
echo "# Use with specific model:"
echo '$ claude-with-workflow --model claude-3-opus "Explain the workflow transitions"'
echo ""
echo "# Get verbose output:"
echo "$ claude-with-workflow -v"
echo ""
echo "# Get wrapper-specific help:"
echo "$ claude-with-workflow --help-wrapper"
echo ""

# Check for active workflow
echo "Current Status:"
echo "--------------"
if command -v flowguard &> /dev/null; then
    echo "Checking for active FlowGuard workflow..."
    flowguard status 2>/dev/null || echo "No active workflow found"
else
    echo "FlowGuard CLI not found - install FlowGuard to use workflow features"
fi