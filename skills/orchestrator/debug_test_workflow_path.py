"""Debug script to exactly mimic test_workflow_path test."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflow_state import workflow_state

print("=== Debugging test_workflow_path ===")
print()

# Save state
print(f"Initial state: current_skill={workflow_state.current_skill}, stack={workflow_state.stack}")
old_current = workflow_state.current_skill
old_stack = workflow_state.stack.copy()

workflow_state.current_skill = None
workflow_state.stack = []
print(f"After reset: current_skill={workflow_state.current_skill}, stack={workflow_state.stack}")

# Enter first skill
print()
print("Calling enter_skill('/analyze')...")
result1 = workflow_state.enter_skill("/analyze")
print(f"Result: {result1}")
print(f"State after: current_skill={workflow_state.current_skill}, stack={workflow_state.stack}")

# Enter second skill
print()
print("Calling enter_skill('/nse')...")
result2 = workflow_state.enter_skill("/nse")
print(f"Result: {result2}")
print(f"State after: current_skill={workflow_state.current_skill}, stack={workflow_state.stack}")

# Get workflow path
print()
print("Calling get_workflow_path()...")
path = workflow_state.get_workflow_path()
print(f"Path returned: {path}")
print()

# Test assertions
print("Testing assertions:")
print(f"  '/analyze' in path: {'/analyze' in path}")
print(f"  '/nse' in path: {'/nse' in path}")
print()

# Restore state
workflow_state.current_skill = old_current
workflow_state.stack = old_stack
print(f"Restored state: current_skill={workflow_state.current_skill}, stack={workflow_state.stack}")
