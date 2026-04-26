from __future__ import annotations

"""
Domain Analyzer Agent — spawned via Claude Code Agent tool.

This module provides the agent specification and handoff contract
for the domain analyzer subagent. The actual execution happens via
Agent(subagent_type="general-purpose", prompt=...) in Claude Code.

The agent reads a handoff JSON file, performs analysis, and writes
results back to a designated output file.
"""
from pathlib import Path
import json

from . import parse_agent_result
from ..models import Finding, AgentResult


def write_handoff(path: Path, target: str, root: str, domains: list[str] | None = None) -> None:
    """Write the handoff JSON for the domain analyzer agent."""
    handoff = {
        "role": "domain_analyzer",
        "target": target,
        "root": root,
        "domains": domains or ["quality", "tests", "docs", "security", "performance"],
        "output_path": str(path.parent / "domain_analyzer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the domain analyzer result from its output file."""
    return parse_agent_result(path, "domain_analyzer")
