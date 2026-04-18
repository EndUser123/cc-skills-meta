"""Hook: Validate format of GTO output artifacts.

This hook validates that GTO output artifacts follow the expected format.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def validate_artifact_format(artifact_path: Path) -> bool:
    """Validate artifact has expected format.

    Args:
        artifact_path: Path to artifact file

    Returns:
        True if valid, False otherwise
    """
    if not artifact_path.exists():
        print(f"ERROR: Artifact not found: {artifact_path}", file=sys.stderr)
        return False

    # JSON artifacts must be valid JSON
    if artifact_path.suffix == ".json":
        try:
            with open(artifact_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {artifact_path}: {e}", file=sys.stderr)
            return False

    # Markdown artifacts must have required sections
    if artifact_path.suffix == ".md":
        content = artifact_path.read_text()

        # Check for required headers
        required_sections = ["#", "##"]
        for section in required_sections:
            if section not in content:
                print(f"WARNING: Missing section {section} in {artifact_path}", file=sys.stderr)

    return True


if __name__ == "__main__":
    # Validate artifact path from command line
    if len(sys.argv) < 2:
        print("Usage: validate_format.py <artifact_path>", file=sys.stderr)
        sys.exit(1)

    artifact_path = Path(sys.argv[1])
    valid = validate_artifact_format(artifact_path)
    sys.exit(0 if valid else 1)
