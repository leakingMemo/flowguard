#!/bin/bash
# FlowGuard-Claude Integration Installation Script
#
# This script installs the claude-with-workflow wrapper by creating
# a symlink in ~/.local/bin/ (or another directory in your PATH).
#
# Usage:
#   ./install-claude-wrapper.sh [--target-dir <dir>] [--force]
#
# Options:
#   --target-dir <dir>  Install to a custom directory (default: ~/.local/bin)
#   --force            Overwrite existing installation
#   --uninstall        Remove the installed wrapper
#   --help             Show this help message

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TARGET_DIR="$HOME/.local/bin"
FORCE=false
UNINSTALL=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_SCRIPT="$SCRIPT_DIR/claude-with-workflow"
WRAPPER_NAME="claude-with-workflow"

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to show usage
show_help() {
    echo "FlowGuard-Claude Integration Installation Script"
    echo ""
    echo "This script installs the claude-with-workflow wrapper by creating"
    echo "a symlink in ~/.local/bin/ (or another directory in your PATH)."
    echo ""
    echo "Usage:"
    echo "  $0 [--target-dir <dir>] [--force] [--uninstall]"
    echo ""
    echo "Options:"
    echo "  --target-dir <dir>  Install to a custom directory (default: ~/.local/bin)"
    echo "  --force            Overwrite existing installation"
    echo "  --uninstall        Remove the installed wrapper"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Install to default location"
    echo "  $0"
    echo ""
    echo "  # Install to custom location"
    echo "  $0 --target-dir /usr/local/bin"
    echo ""
    echo "  # Force reinstall"
    echo "  $0 --force"
    echo ""
    echo "  # Uninstall"
    echo "  $0 --uninstall"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target-dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_color $RED "Error: Unknown option $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
done

# Function to check if claude CLI is installed
check_claude_cli() {
    if ! command -v claude &> /dev/null; then
        print_color $YELLOW "Warning: 'claude' command not found in PATH"
        print_color $YELLOW "Make sure to install Claude CLI before using the wrapper"
        echo ""
    fi
}

# Function to check if directory is in PATH
check_in_path() {
    local dir="$1"
    if [[ ":$PATH:" == *":$dir:"* ]]; then
        return 0
    else
        return 1
    fi
}

# Uninstall function
uninstall_wrapper() {
    local target_path="$TARGET_DIR/$WRAPPER_NAME"
    
    if [[ -L "$target_path" ]]; then
        print_color $BLUE "Removing symlink: $target_path"
        rm "$target_path"
        print_color $GREEN "✓ FlowGuard-Claude wrapper uninstalled successfully"
    elif [[ -f "$target_path" ]]; then
        print_color $YELLOW "Warning: $target_path is not a symlink"
        read -p "Remove it anyway? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm "$target_path"
            print_color $GREEN "✓ File removed"
        else
            print_color $BLUE "Uninstall cancelled"
        fi
    else
        print_color $YELLOW "No installation found at $target_path"
    fi
}

# Install function
install_wrapper() {
    # Check if wrapper script exists
    if [[ ! -f "$WRAPPER_SCRIPT" ]]; then
        print_color $RED "Error: Wrapper script not found at $WRAPPER_SCRIPT"
        exit 1
    fi
    
    # Create target directory if it doesn't exist
    if [[ ! -d "$TARGET_DIR" ]]; then
        print_color $BLUE "Creating directory: $TARGET_DIR"
        mkdir -p "$TARGET_DIR"
    fi
    
    local target_path="$TARGET_DIR/$WRAPPER_NAME"
    
    # Check if target already exists
    if [[ -e "$target_path" ]] && [[ "$FORCE" != true ]]; then
        print_color $YELLOW "Warning: $target_path already exists"
        echo "Use --force to overwrite or --uninstall to remove first"
        exit 1
    fi
    
    # Remove existing file/link if force is true
    if [[ -e "$target_path" ]] && [[ "$FORCE" == true ]]; then
        print_color $BLUE "Removing existing installation..."
        rm -f "$target_path"
    fi
    
    # Create symlink
    print_color $BLUE "Creating symlink: $target_path -> $WRAPPER_SCRIPT"
    ln -s "$WRAPPER_SCRIPT" "$target_path"
    
    # Check if target directory is in PATH
    if ! check_in_path "$TARGET_DIR"; then
        print_color $YELLOW ""
        print_color $YELLOW "⚠️  Warning: $TARGET_DIR is not in your PATH"
        print_color $YELLOW "Add it to your PATH by adding this line to your shell config:"
        print_color $BLUE "    export PATH=\"$TARGET_DIR:\$PATH\""
        print_color $YELLOW ""
    fi
    
    print_color $GREEN "✓ FlowGuard-Claude wrapper installed successfully!"
    print_color $GREEN ""
    print_color $GREEN "You can now use: $WRAPPER_NAME [claude-arguments]"
    print_color $GREEN ""
    print_color $BLUE "Tips:"
    print_color $BLUE "  • Use '$WRAPPER_NAME --help-wrapper' to see wrapper-specific help"
    print_color $BLUE "  • The wrapper will automatically detect active FlowGuard workflows"
    print_color $BLUE "  • Use '$WRAPPER_NAME -v' for verbose output"
}

# Main execution
print_color $BLUE "FlowGuard-Claude Integration Installer"
print_color $BLUE "====================================="
echo ""

# Check for Claude CLI
check_claude_cli

if [[ "$UNINSTALL" == true ]]; then
    uninstall_wrapper
else
    install_wrapper
fi