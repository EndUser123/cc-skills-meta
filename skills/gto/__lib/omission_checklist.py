"""Omission Checklist — post-scan category completeness check.

Priority: P2 (runs after all L1 detectors)
Purpose: Ensure GTO checked all expected gap categories, not just the ones that found gaps.

After all L1 detectors have run, this module checks which gap categories
were actually represented in the results. If expected categories are
missing entirely, it flags them as potential blind spots.

This prevents GTO from silently skipping entire categories of gaps
(e.g., reporting code markers but never checking test coverage).

Ported from /r skill's build_omission_checklist step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Expected gap categories that GTO should check
EXPECTED_CATEGORIES: dict[str, str] = {
    "tests": "Test coverage gaps (missing tests, failing tests)",
    "docs": "Documentation gaps (missing README, SKILL.md, docstrings)",
    "code_quality": "Code quality gaps (TODO, FIXME, HACK markers)",
    "dependencies": "Dependency health (missing, outdated, vulnerable packages)",
    "contracts": "Contract gaps (producer/consumer mismatches, stale data)",
    "git": "Git state (uncommitted changes, missing lock files)",
    "entry_points": "Entry point integrity (broken junctions, missing references)",
    "session": "Session continuity (unfinished business, broken handoffs)",
}

# Map gap types to categories
_GAP_TYPE_TO_CATEGORY: dict[str, str] = {
    "missing_test": "tests",
    "test_failure": "tests",
    "test_import_error": "tests",
    "missing_docs": "docs",
    "missing_claude_md": "docs",
    "missing_readme": "docs",
    "code_marker": "code_quality",
    "dependency_vulnerable": "dependencies",
    "dependency_outdated": "dependencies",
    "dependency_missing": "dependencies",
    "dependency_unused": "dependencies",
    "contract_gap": "contracts",
    "consumer_gap": "contracts",
    "stale_data_risk": "contracts",
    "git_dirty": "git",
    "uncommitted_changes": "git",
    "missing_lock_file": "git",
    "entry_point_mismatch": "entry_points",
    "chain_integrity_issue": "session",
    "unfinished_business": "session",
    "session_outcome": "session",
    "suspicion_misalignment": "session",
    "low_confidence_goal": "session",
}


@dataclass
class OmissionFinding:
    """A category that was not checked by any detector."""
    category: str
    description: str
    severity: str = "low"
    detector_available: bool = True  # False if the detector was skipped entirely


@dataclass
class OmissionChecklistResult:
    """Result of the omission checklist check."""
    missing_categories: list[OmissionFinding]
    categories_found: list[str]
    categories_expected: list[str]
    completeness_pct: float


def check_omission(gaps: list[dict[str, Any]] | list[Any]) -> OmissionChecklistResult:
    """Check which gap categories are missing from the results.

    Args:
        gaps: List of Gap objects or gap dictionaries from L1 detectors.

    Returns:
        OmissionChecklistResult with missing categories and completeness score.
    """
    # Extract gap types from results
    found_categories: set[str] = set()
    for gap in gaps:
        if isinstance(gap, dict):
            gap_type = gap.get("type", "")
        else:
            gap_type = getattr(gap, "type", "")
        category = _GAP_TYPE_TO_CATEGORY.get(gap_type)
        if category:
            found_categories.add(category)

    # Check for missing categories
    missing: list[OmissionFinding] = []
    for cat, description in EXPECTED_CATEGORIES.items():
        if cat not in found_categories:
            missing.append(OmissionFinding(
                category=cat,
                description=description,
                severity="low",
                detector_available=True,
            ))

    total = len(EXPECTED_CATEGORIES)
    completeness = (len(found_categories) / total * 100) if total > 0 else 0.0

    return OmissionChecklistResult(
        missing_categories=missing,
        categories_found=sorted(found_categories),
        categories_expected=list(EXPECTED_CATEGORIES.keys()),
        completeness_pct=round(completeness, 1),
    )


def omission_to_gaps(result: OmissionChecklistResult) -> list[dict[str, Any]]:
    """Convert omission findings to gap dictionaries for RNS inclusion.

    Only converts findings to gaps when completeness is below a threshold,
    avoiding noise when most categories were covered.

    Args:
        result: OmissionChecklistResult from check_omission().

    Returns:
        List of gap dictionaries for missing categories.
    """
    if result.completeness_pct >= 75.0:
        return []

    gaps = []
    for idx, finding in enumerate(result.missing_categories):
        gaps.append({
            "gap_id": f"GAP-{idx:04d}-omission",
            "type": "omission_checklist",
            "severity": finding.severity,
            "message": f"Gap category not checked: {finding.category} — {finding.description}",
            "source": "OmissionChecklist",
            "scope": "ARCHITECTURAL",
        })
    return gaps
