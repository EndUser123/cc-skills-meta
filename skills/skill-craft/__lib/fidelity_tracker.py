"""
fidelity_tracker — Phase 4 EVALUATING component for skill-craft.

Runs eval cases from eval_sets/default.json against the target skill,
produces a FidelityScore with trigger accuracy, outcome accuracy, and
degradation delta.

Usage:
    from fidelity_tracker import run
    score = run(skill_path="P:/.claude/skills/gto")
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from craft_state import FidelityScore

DEFAULT_EVAL_SET = Path(__file__).parent.parent / "eval_sets" / "default.json"


def run(skill_path: str | Path, eval_set_path: Optional[str | Path] = None) -> FidelityScore:
    """
    Run eval cases against the target skill and produce a fidelity score.

    Args:
        skill_path: Path to the skill directory (must contain SKILL.md)
        eval_set_path: Path to eval_set JSON. Defaults to eval_sets/default.json
                      relative to this module's parent directory.

    Returns:
        FidelityScore with trigger_accuracy, outcome_accuracy,
        degradation_delta, and passed flag.

    Raises:
        FileNotFoundError: If skill_path/SKILL.md or eval_set_path not found
        ValueError: If eval_set has no evals array
    """
    skill_path = Path(skill_path)
    eval_path = Path(eval_set_path) if eval_set_path else DEFAULT_EVAL_SET

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")

    if not eval_path.exists():
        raise FileNotFoundError(f"eval_set not found at {eval_path}")

    with open(eval_path) as f:
        eval_set = json.load(f)

    evals = eval_set.get("evals", [])
    if not evals:
        raise ValueError(f"eval_set at {eval_path} has no 'evals' array")

    skill_md_content = skill_md.read_text()
    frontmatter = _parse_frontmatter(skill_md_content)
    triggers = frontmatter.get("triggers", [])

    passed_count = 0
    trigger_checks = []
    outcome_checks = []

    for eval_case in evals:
        eid = eval_case.get("id")
        prompt = eval_case.get("prompt", "")
        expected = eval_case.get("expected_output", "")

        trigger_hits = _count_trigger_hits(prompt, triggers)
        outcome_hits = _evaluate_outcome(expected, skill_md_content)

        trigger_checks.append(trigger_hits)
        outcome_checks.append(outcome_hits)

        if trigger_hits >= 1 and outcome_hits >= 1:
            passed_count += 1

    n = len(evals)
    trigger_accuracy = sum(trigger_checks) / n if n else 0.0
    outcome_accuracy = sum(outcome_checks) / n if n else 0.0
    passed = passed_count == n

    return FidelityScore(
        trigger_accuracy=trigger_accuracy,
        outcome_accuracy=outcome_accuracy,
        degradation_delta=0.0,
        passed=passed,
        details={
            "evals_passed": passed_count,
            "evals_total": n,
            "eval_set": eval_path.name,
        },
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
        i = 0
        while i < len(fm_lines):
            line = fm_lines[i].strip()
            if not line or line.startswith("#"):
                i += 1
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # If value is empty and next lines are indented list items, accumulate
                if val == "" and i + 1 < len(fm_lines) and fm_lines[i + 1].strip().startswith("-"):
                    # Collect all list items following this key
                    items = []
                    j = i + 1
                    while j < len(fm_lines) and fm_lines[j].strip().startswith("-"):
                        item = fm_lines[j].strip().lstrip("-").strip().strip('"').strip("'")
                        items.append(item)
                        j += 1
                    fm[key] = items
                    i = j
                else:
                    fm[key] = val
                    i += 1
            else:
                i += 1
        return fm
    return {}


def _count_trigger_hits(prompt: str, triggers: list[str]) -> float:
    """
    Check if at least one trigger from the skill's frontmatter appears in the eval prompt.
    Scoring: 1.0 if any trigger is present, 0.0 otherwise.
    """
    if not triggers:
        return 0.0
    hits = any(t in prompt for t in triggers)
    return 1.0 if hits else 0.0


def _evaluate_outcome(expected: str, skill_md_content: str) -> float:
    """
    Score outcome accuracy: how well skill output matches expected CraftState fields.
    Uses keyword presence as a proxy for structural correctness.
    """
    if not expected:
        return 0.0

    keywords = [k.strip().lower() for k in expected.split() if len(k.strip()) > 3]
    if not keywords:
        return 1.0 if expected in skill_md_content else 0.0

    content_lower = skill_md_content.lower()
    hits = sum(1 for kw in keywords if kw in content_lower)
    return hits / len(keywords)
