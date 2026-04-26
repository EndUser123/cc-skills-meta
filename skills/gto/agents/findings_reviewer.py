from __future__ import annotations

"""
Findings Reviewer Agent — spawned via Claude Code Agent tool.

Reviews and validates findings from deterministic detectors and domain analyzers.
Removes duplicates, adjusts severities, and ensures evidence quality.
"""
from pathlib import Path
import json

from . import parse_agent_result
from ..models import Finding, AgentResult


def write_handoff(path: Path, findings: list[Finding]) -> None:
    """Write findings for the reviewer agent to evaluate."""
    handoff = {
        "role": "findings_reviewer",
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "findings_reviewer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the reviewer result from its output file."""
    return parse_agent_result(path, "findings_reviewer")
