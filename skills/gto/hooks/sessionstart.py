#!/usr/bin/env python3
"""GTO SessionStart hook — restore state and show prior diagnosis.

Claude Code hook protocol: reads JSON from stdin, outputs JSON to stdout.

If GTO state exists for this terminal, shows a brief summary of the
last run's findings so the user can pick up where they left off.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .common import is_gto_active, read_state, write_hook_output


def _count_findings_in_artifact(artifact_path: str) -> int:
    """Count findings in an artifact JSON file. Returns 0 on any failure."""
    try:
        data = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        return len(data.get("findings", []))
    except (json.JSONDecodeError, OSError, ValueError):
        return 0


def run(data: dict) -> dict | None:
    """In-process hook entry point. Returns None to allow, dict to modify."""
    if not is_gto_active():
        return None

    state = read_state()
    if not state:
        return None

    phase = state.get("phase", "")
    target = state.get("current_target", "unknown")

    # Count actual findings from the artifact, not artifact paths
    findings_count = sum(
        _count_findings_in_artifact(p)
        for p in state.get("expected_artifacts", [])
    )

    if phase == "completed":
        msg = f"GTO: prior run completed for '{target}'. {findings_count} findings available."
    elif phase in ("initialized", "running"):
        msg = f"GTO: prior run was '{phase}' for '{target}'. Consider re-running /gto."
    else:
        return None

    return {"decision": "allow", "reason": msg}


def main() -> None:
    """CLI entry point for Claude Code hook protocol."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        data = {}

    result = run(data)
    if result is not None:
        write_hook_output(result)
    else:
        write_hook_output({"decision": "allow"})
    sys.exit(0)


if __name__ == "__main__":
    main()
