"""Hook: Checklist gate for GTO analysis.

This hook ensures all pre-flight checklist items are satisfied before analysis.
"""

from __future__ import annotations

import sys
from pathlib import Path


def run_checklist_gate(checklist_path: Path) -> bool:
    """Run checklist gate validation.

    Args:
        checklist_path: Path to checklist file

    Returns:
        True if all items checked, False otherwise
    """
    if not checklist_path.exists():
        print(f"WARNING: Checklist not found: {checklist_path}", file=sys.stderr)
        return True  # Pass if checklist doesn't exist

    content = checklist_path.read_text()

    # Check for unchecked items
    unchecked = [line for line in content.split("\n") if "- [ ]" in line]

    if unchecked:
        print(f"ERROR: {len(unchecked)} unchecked items in checklist:", file=sys.stderr)
        for item in unchecked[:5]:  # Show first 5
            print(f"  - {item.strip()}", file=sys.stderr)
        if len(unchecked) > 5:
            print(f"  ... and {len(unchecked) - 5} more", file=sys.stderr)
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: checklist_gate.py <checklist_path>", file=sys.stderr)
        sys.exit(1)

    checklist_path = Path(sys.argv[1])
    passed = run_checklist_gate(checklist_path)
    sys.exit(0 if passed else 1)
