from __future__ import annotations

"""
Action Normalizer Agent — spawned via Claude Code Agent tool.

Normalizes findings: ensures valid domains, severities, actions, priorities,
and adds effort estimates for findings that lack them.
"""
from pathlib import Path
import json

from . import parse_agent_result
from ..models import Finding, AgentResult


def write_handoff(path: Path, findings: list[Finding]) -> None:
    """Write findings for the normalizer agent to process."""
    handoff = {
        "role": "action_normalizer",
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "action_normalizer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the normalizer result from its output file."""
    return parse_agent_result(path, "action_normalizer")
