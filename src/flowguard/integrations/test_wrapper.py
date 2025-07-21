#!/usr/bin/env python3
"""
Test script for the Claude-FlowGuard wrapper.

This script tests the wrapper's ability to detect and format workflow context.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path to import the wrapper functions
sys.path.insert(0, str(Path(__file__).parent))

# Import from the wrapper (treating it as a module)
# We need to extract just the functions, not execute the main code
wrapper_path = Path(__file__).parent / 'claude-with-workflow'
wrapper_code = wrapper_path.read_text()

# Extract the code up to the main() execution
code_lines = wrapper_code.split('\n')
filtered_lines = []
for line in code_lines:
    if line.strip() == "if __name__ == '__main__':":
        break
    filtered_lines.append(line)

exec('\n'.join(filtered_lines))


def test_context_formatting():
    """Test the context formatting function."""
    print("Testing context formatting...")
    
    # Create a sample context
    sample_context = {
        'workflow_name': 'Test Workflow',
        'workflow_description': 'A test workflow for development',
        'current_state': 'development',
        'instance_id': 'test-123',
        'current_instructions': 'Write and test new features',
        'variables': {
            'project': 'flowguard',
            'feature': 'claude-integration'
        },
        'available_transitions': [
            {
                'name': 'complete',
                'to_state': 'review',
                'condition': 'tests_pass == true'
            },
            {
                'name': 'abandon',
                'to_state': 'cancelled',
                'condition': None
            }
        ]
    }
    
    # Format the context
    formatted = format_context_for_claude(sample_context)
    
    print("\nFormatted context:")
    print("-" * 60)
    print(formatted)
    print("-" * 60)
    
    # Verify key elements are present
    assert "FlowGuard Workflow Context" in formatted
    assert "Test Workflow" in formatted
    assert "development" in formatted
    assert "tests_pass == true" in formatted
    
    print("\n✓ Context formatting test passed!")


def test_flowguard_detection():
    """Test FlowGuard context detection."""
    print("\nTesting FlowGuard detection...")
    
    try:
        context = get_flowguard_context()
        if context:
            print(f"✓ Found active workflow: {context['workflow_name']}")
            print(f"  Current state: {context['current_state']}")
            print(f"  Instance ID: {context['instance_id']}")
        else:
            print("ℹ️  No active workflow found (this is normal if not in a workflow)")
    except Exception as e:
        print(f"⚠️  Error during detection: {e}")
        print("  (This is expected if FlowGuard is not in the Python path)")


def main():
    """Run all tests."""
    print("FlowGuard-Claude Wrapper Test Suite")
    print("=" * 60)
    
    test_context_formatting()
    test_flowguard_detection()
    
    print("\n✓ All tests completed!")


if __name__ == '__main__':
    main()