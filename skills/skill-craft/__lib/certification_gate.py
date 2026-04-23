"""
certification_gate — Phase 5 GATING component for skill-craft.

Validates a skill's SKILL.md: required frontmatter fields, body size,
and trigger-to-usage fidelity (listed triggers actually cause the skill to fire).

Usage:
    from certification_gate import certification_gate
    result = certification_gate.check(skill_path="P:/.claude/skills/gto")
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .craft_state import CertGateResult

REQUIRED_FIELDS = ["name", "description"]
MAX_BODY_LINES = 500


def check(skill_path: str | Path) -> CertGateResult:
    """
    Validate a skill's SKILL.md for certification readiness.

    Checks:
    - name + description present in frontmatter
    - SKILL.md body < MAX_BODY_LINES lines
    - triggers listed in frontmatter are referenced in body text

    Args:
        skill_path: Path to the skill directory (must contain SKILL.md)

    Returns:
        CertGateResult with passed flag, errors list, and warnings list.

    Raises:
        FileNotFoundError: If skill_path/SKILL.md not found
    """
    skill_path = Path(skill_path)
    skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")

    content = skill_md.read_text()
    frontmatter = _parse_frontmatter(content)
    body_lines = _count_body_lines(content)
    body_text = _extract_body(content)

    errors = []
    warnings = []

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in frontmatter or not frontmatter[field]:
            errors.append(f"Missing required frontmatter field: {field}")

    # Context size
    if body_lines > MAX_BODY_LINES:
        errors.append(
            f"SKILL.md body is {body_lines} lines (max {MAX_BODY_LINES}). "
            f"Apply progressive disclosure."
        )

    # Trigger-usage fidelity
    triggers = frontmatter.get("triggers", [])
    if triggers:
        hallucinated = _find_hallucinated_triggers(triggers, body_text)
        if hallucinated:
            warnings.append(
                f"Trigger(s) listed but not referenced in body: {', '.join(hallucinated)}"
            )

    return CertGateResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings if warnings else [],
    )


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from SKILL.md content."""
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        end_idx = 1
        while end_idx < len(lines) and lines[end_idx].strip() != "---":
            end_idx += 1
        fm_lines = lines[1:end_idx]
        fm = {}
        for line in fm_lines:
            if ":" in line:
                key, _, val = line.partition(":")
                fm[key.strip()] = val.strip().strip('"').strip("'")
        return fm
    return {}


def _count_body_lines(content: str) -> int:
    """Count non-empty lines after frontmatter delimiter."""
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        end_idx = 1
        while end_idx < len(lines) and lines[end_idx].strip() != "---":
            end_idx += 1
        body_lines = [l for l in lines[end_idx + 1 :] if l.strip()]
        return len(body_lines)
    return len([l for l in lines if l.strip()])


def _extract_body(content: str) -> str:
    """Extract text content after frontmatter, stripped of markdown."""
    lines = content.splitlines()
    if lines and lines[0].strip() == "---":
        end_idx = 1
        while end_idx < len(lines) and lines[end_idx].strip() != "---":
            end_idx += 1
        body_lines = lines[end_idx + 1 :]
    else:
        body_lines = lines

    text = " ".join(body_lines)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"#+ ", " ", text)
    text = re.sub(r"\|.+\|", " ", text)
    return text.lower()


def _find_hallucinated_triggers(triggers: list[str], body_text: str) -> list[str]:
    """
    Return triggers that appear in frontmatter but are not found in body text.
    Uses substring matching after normalization.
    """
    hallucinated = []
    for t in triggers:
        normalized = t.lower().strip().lstrip("/")
        if normalized not in body_text and t.lower() not in body_text:
            hallucinated.append(t)
    return hallucinated
