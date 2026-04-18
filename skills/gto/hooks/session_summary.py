"""Hook: Generate session summary for GTO analysis.

This hook generates a concise summary of the current session's findings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def generate_session_summary(artifacts_dir: Path) -> str:
    """Generate session summary from analysis artifacts.

    Args:
        artifacts_dir: Path to artifacts directory

    Returns:
        Markdown summary string
    """
    summary_lines = ["# GTO Session Summary\n"]

    # Find all JSON artifacts
    json_files = list(artifacts_dir.glob("*.json"))

    if not json_files:
        summary_lines.append("No artifacts found.\n")
        return "\n".join(summary_lines)

    # Aggregate findings from all artifacts
    total_gaps = 0
    total_unfinished = 0

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)

            if "gaps" in data:
                total_gaps += len(data["gaps"])
            if "unfinished" in data:
                total_unfinished += len(data["unfinished"])
        except (OSError, json.JSONDecodeError):
            pass

    summary_lines.append(f"**Gaps Detected**: {total_gaps}")
    summary_lines.append(f"**Unfinished Items**: {total_unfinished}")
    summary_lines.append(f"**Artifacts Generated**: {len(json_files)}")

    return "\n".join(summary_lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: session_summary.py <artifacts_dir>", file=sys.stderr)
        sys.exit(1)

    artifacts_dir = Path(sys.argv[1])
    summary = generate_session_summary(artifacts_dir)
    print(summary)
