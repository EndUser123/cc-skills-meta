"""Minimal test to isolate the workflow_path issue."""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflow_state import workflow_state


def test_workflow_path_minimal():
    """Minimal test - just the workflow path logic."""
    # Reset state
    workflow_state.current_skill = None
    workflow_state.stack = []

    # Enter two skills
    result1 = workflow_state.enter_skill("/analyze")
    print(f"DEBUG: After /analyze: current={workflow_state.current_skill}, stack={workflow_state.stack}, result={result1}")

    result2 = workflow_state.enter_skill("/nse")
    print(f"DEBUG: After /nse: current={workflow_state.current_skill}, stack={workflow_state.stack}, result={result2}")

    # Get path
    path = workflow_state.get_workflow_path()
    print(f"DEBUG: path={path}")

    # Assertions
    assert result1 is True, "First enter_skill should succeed"
    assert result2 is True, "Second enter_skill should succeed"
    assert "/analyze" in path, f"/analyze should be in path, got {path}"
    assert "/nse" in path, f"/nse should be in path, got {path}"


if __name__ == "__main__":
    test_workflow_path_minimal()
    print("All tests passed!")
