"""
certification_gate — Phase 5 GATING component for skill-craft.

Validates a skill's SKILL.md: required frontmatter fields, body size,
and trigger-to-usage fidelity (listed triggers actually cause the skill to fire).

Usage:
    from certification_gate import check
    result = check(skill_path="P:/.claude/skills/gto")
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from craft_state import CertGateResult

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

    # craft_lens: imperative form check — triggers should be actionable (start with / or be imperative verbs)
    if triggers:
        non_imperative = _find_non_imperative_triggers(triggers)
        if non_imperative:
            warnings.append(
                f"Trigger(s) may not be in imperative form: {', '.join(non_imperative)}"
            )

    # craft_lens: progressive disclosure — large sections with heavy references should be summarized
    large_sections = _find_large_reference_sections(content)
    if large_sections:
        warnings.append(
            f"Large reference sections may need summarization: {', '.join(large_sections)}"
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


def _find_non_imperative_triggers(triggers: list[str]) -> list[str]:
    """
    Return triggers that don't look imperative (slash commands or clear verbs).
    Slash commands (/skill) are considered properly formatted.
    Others should be verb phrases or verb-noun pairs.
    """
    non_imperative = []
    for t in triggers:
        t_stripped = t.strip()
        # Slash commands are correctly formatted
        if t_stripped.startswith("/"):
            continue
        # Check for common verb patterns (starts with verb-like word)
        verb_indicators = (
            "add ", "create ", "build ", "make ", "update ", "fix ", "run ",
            "check ", "find ", "show ", "list ", "get ", "set ", "use ",
            "apply ", "implement ", "design ", "plan ", "review ", "audit ",
            "craft ", "improve ", "generate ", "convert ", "migrate "
        )
        if not any(t_stripped.lower().startswith(v) for v in verb_indicators):
            non_imperative.append(t)
    return non_imperative


def _find_large_reference_sections(content: str) -> list[str]:
    """
    Identify large sections (20+ consecutive non-empty lines) that are
    reference-heavy — containing many file paths, URLs, or skill references.
    These should use progressive disclosure (summarized, with references loaded as-needed).
    """
    lines = content.splitlines()
    large_sections = []
    i = 0
    while i < len(lines):
        # Skip to non-empty line
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines):
            break

        # Count consecutive non-empty lines
        section_start = i
        consecutive = 0
        while i < len(lines) and lines[i].strip():
            consecutive += 1
            i += 1

        if consecutive >= 20:
            # Check if it's reference-heavy (many code块s, URLs, or skill paths)
            section_lines = lines[section_start:i]
            reference_count = sum(
                1 for line in section_lines
                if ("/" in line and ("skill" in line.lower() or ".md" in line.lower()))
                or line.strip().startswith("```")
                or "P:/" in line
            )
            if reference_count >= consecutive * 0.3:
                # Extract section title (first heading or line)
                title = section_lines[0].strip() if section_lines else f"lines {section_start}-{i}"
                large_sections.append(title[:60])

        i += 1
    return large_sections
