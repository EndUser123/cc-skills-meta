"""Gap-to-Skill Mapper for GTO.

Bridges gap types to skill capabilities using pattern matching and LLM context.
Provides skill recommendation context injection for intelligent suggestions.

Priority: P1 (core intelligence for skill recommendations)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .skill_registry_bridge import (
    SkillSummary,
    find_skills_for_gap,
    format_skill_context,
    get_skill_recommendation_context,
    load_skill_catalog,
)

logger = logging.getLogger(__name__)


# ── Gap Type to Skill Category Mapping ─────────────────────────────────────

# Maps GTO gap types to relevant skill categories
# Used for pre-filtering skills before LLM analysis
GAP_TYPE_TO_CATEGORIES: dict[str, list[str]] = {
    # Test-related gaps
    "test_gap": ["testing", "quality"],
    "test_failure": ["testing", "debugging"],
    "missing_test": ["testing", "quality"],
    "test_import_error": ["testing", "dependencies"],
    "flaky_test": ["testing", "quality"],
    # Documentation gaps
    "doc_gap": ["documentation"],
    "missing_docs": ["documentation"],
    "missing_claude_md": ["documentation"],
    "missing_readme": ["documentation"],
    "stale_docs": ["documentation"],
    # Code quality gaps
    "code_quality": ["quality", "review"],
    "design_issue": ["architecture", "quality"],
    "complexity": ["quality", "refactoring"],
    "technical_debt": ["quality", "refactoring"],
    "code_smell": ["quality", "review"],
    # Import/dependency gaps
    "import_error": ["dependencies"],
    "import_issue": ["dependencies"],
    "missing_dependency": ["dependencies"],
    "outdated_dependency": ["dependencies"],
    "vulnerable_dependency": ["dependencies", "security"],
    # Git/VCS gaps
    "git_dirty": ["vcs", "git"],
    "uncommitted_changes": ["vcs", "git"],
    "merge_conflict": ["vcs", "git"],
    "missing_lock_file": ["vcs", "dependencies"],
    # Security gaps
    "security_issue": ["security"],
    "vulnerability": ["security"],
    "exposed_secret": ["security"],
    # Architecture gaps
    "architectural_concern": ["architecture"],
    "boundary_violation": ["architecture"],
    "coupling_issue": ["architecture", "refactoring"],
    # Debugging gaps
    "runtime_error": ["debugging"],
    "bug": ["debugging"],
    "exception": ["debugging"],
    # Verification gaps
    "unverified_claim": ["verification"],
    "evidence_gap": ["verification"],
    "missing_assertion": ["testing", "verification"],
    # Planning gaps
    "missing_plan": ["planning"],
    "scope_unclear": ["planning"],
    "ambiguous_requirement": ["planning"],
    # Search/research gaps
    "missing_info": ["search", "research"],
    "knowledge_gap": ["search", "research"],
    # Improvement gaps
    "improvement_gap": ["quality", "refactoring"],
    # Retrospective/process gaps - patterns suggesting workflow improvements
    "improvement_investigation": ["retrospective", "quality"],
    "process_gap": ["retrospective", "planning"],
    "repeatable_pattern": ["retrospective", "analysis"],
}


# ── Skill Recommendation Context Templates ─────────────────────────────────

# Context template for LLM injection
# This provides the LLM with structured context about available skills
SKILL_RECOMMENDATION_CONTEXT = """
## Available Skills for Gap Resolution

When analyzing gaps, consider these relevant skills:

### Testing & Quality
- /tdd - Test-driven development workflow
- /qa - Feature certification workflow
- /skill-audit - Skill strategy and outcome auditor
- /uci - Unified Code Inspection

### Quality & Refactoring
- /refactor - Multi-file refactoring orchestrator (finds AND fixes implementation quality issues)

### Documentation
- /doc - Ingest, update, create documentation
- /docs-validate - Validate documentation completeness

### Git & Version Control
- /git - Sync, worktree, conflict resolution
- /push - Fast push with retry logic

### Dependencies
- /deps - Dependency management
- /verify - Verification orchestrator

### Architecture
- /design - Architecture decision advisor
- /adf - Evaluate structural changes

### Debugging & RCA
- /debugRCA - Root cause analysis engine
- /diagnose - Structured diagnostic protocol

### Search & Research
- /search - Unified intelligent search
- /research - Research and learning

### Verification
- /truth - Truth verification command
- /verify - Verification orchestrator

### Planning
- /breakdown - Implementation planning
- /pre-mortem - Pre-mortem failure analysis
- /retro - Self-Contrast retrospective orchestrator (use when gaps span process + code)

When recommending skills:
1. Match skill capabilities to specific gap issues
2. Provide rationale for WHY this skill helps
3. Consider gap severity - critical gaps need immediate skills
"""


# ── Data Classes ───────────────────────────────────────────────────────────


@dataclass
class SkillRecommendation:
    """A skill recommendation with rationale.

    Attributes:
        skill: The recommended skill.
        gap_ids: IDs of gaps this skill addresses.
        rationale: Why this skill is recommended.
        confidence: Confidence level (0.0 to 1.0).
        priority: Priority level (critical, high, medium, low).
        verified: True if skill has fresh evidence in coverage log.
    """

    skill: SkillSummary
    gap_ids: list[str]
    rationale: str
    confidence: float
    priority: str
    verified: bool = False


# ── Core Functions ─────────────────────────────────────────────────────────


def get_categories_for_gap_type(gap_type: str) -> list[str]:
    """Get relevant skill categories for a gap type.

    Args:
        gap_type: The type of gap (e.g., "test_gap", "doc_gap").

    Returns:
        List of relevant skill categories.
    """
    return GAP_TYPE_TO_CATEGORIES.get(gap_type, [])


def find_relevant_skills_for_gaps(
    gaps: list[dict],
    limit_per_gap: int = 5,
) -> dict[str, list[SkillSummary]]:
    """Find skills relevant to a list of gaps.

    Groups skills by gap ID for targeted recommendations.

    Args:
        gaps: List of gap dictionaries with 'id', 'type', 'message' fields.
        limit_per_gap: Maximum skills to return per gap.

    Returns:
        Dictionary mapping gap IDs to lists of relevant skills.
    """
    skills_by_gap: dict[str, list[SkillSummary]] = {}

    for gap in gaps:
        gap_id = gap.get("id", gap.get("gap_id", "unknown"))
        relevant_skills = find_skills_for_gap(gap, limit=limit_per_gap)
        if relevant_skills:
            skills_by_gap[gap_id] = relevant_skills

    return skills_by_gap


def generate_skill_recommendations(
    gaps: list[dict],
    limit: int = 20,
) -> list[SkillRecommendation]:
    """Generate skill recommendations from gap findings.

    Analyzes gaps and produces prioritized skill recommendations
    with rationale for each.

    Args:
        gaps: List of gap dictionaries.
        limit: Maximum recommendations to return (0 = no limit).

    Returns:
        List of SkillRecommendation objects sorted by confidence.
    """
    if not gaps:
        return []

    catalog = load_skill_catalog()
    recommendations: dict[str, SkillRecommendation] = {}

    for gap in gaps:
        gap_id = gap.get("id", gap.get("gap_id", "unknown"))
        gap_type = gap.get("type", "")
        gap_message = gap.get("message", "")
        gap_severity = gap.get("severity", "medium")

        # Find relevant skills for this gap
        relevant_skills = find_skills_for_gap(gap, limit=10)

        for skill in relevant_skills:
            skill_name = skill.name

            if skill_name in recommendations:
                # Add this gap to existing recommendation
                recommendations[skill_name].gap_ids.append(gap_id)
                # Update confidence based on multiple matches
                recommendations[skill_name].confidence = min(
                    recommendations[skill_name].confidence + 0.05, 0.95
                )
            else:
                # Create new recommendation
                rationale = _generate_rationale(skill, gap_type, gap_message)
                confidence = _calculate_confidence(skill, gap_type, gap_message)
                priority = _map_severity_to_priority(gap_severity)

                recommendations[skill_name] = SkillRecommendation(
                    skill=skill,
                    gap_ids=[gap_id],
                    rationale=rationale,
                    confidence=confidence,
                    priority=priority,
                )

    # Sort by confidence descending
    sorted_recs = sorted(
        recommendations.values(),
        key=lambda r: (r.confidence, len(r.gap_ids)),
        reverse=True,
    )

    # Apply limit (0 means no limit)
    if limit > 0:
        return sorted_recs[:limit]
    return sorted_recs


def _generate_rationale(skill: SkillSummary, gap_type: str, gap_message: str) -> str:
    """Generate rationale for why a skill is recommended.

    Args:
        skill: The recommended skill.
        gap_type: The type of gap.
        gap_message: The gap message.

    Returns:
        Human-readable rationale string.
    """
    category = skill.category

    # Category-based rationales
    category_rationales: dict[str, str] = {
        "testing": "Addresses test coverage and quality issues",
        "documentation": "Resolves documentation gaps and improves clarity",
        "quality": "Improves code quality and maintainability",
        "review": "Provides structured code review and analysis",
        "dependencies": "Handles dependency and import issues",
        "vcs": "Manages version control and git operations",
        "git": "Handles git-specific operations",
        "debugging": "Helps diagnose and fix bugs",
        "architecture": "Guides architectural decisions",
        "verification": "Verifies claims and evidence",
        "planning": "Helps plan and structure work",
        "search": "Finds relevant information across sources",
        "research": "Researches and learns about topics",
        "security": "Addresses security concerns",
        "refactoring": "Improves code structure",
    }

    base_rationale = category_rationales.get(category, f"Relevant for {category} concerns")

    # Add gap-specific context
    if gap_type:
        base_rationale += f" for {gap_type.replace('_', ' ')}"

    return base_rationale


def _calculate_confidence(skill: SkillSummary, gap_type: str, gap_message: str) -> float:
    """Calculate confidence score for a skill recommendation.

    Args:
        skill: The recommended skill.
        gap_type: The type of gap.
        gap_message: The gap message.

    Returns:
        Confidence score (0.0 to 1.0).
    """
    base_confidence = 0.5

    # Check category match
    categories = get_categories_for_gap_type(gap_type)
    if skill.category in categories:
        base_confidence += 0.2

    # Check domain match
    gap_domain = _infer_domain_from_gap_type(gap_type)
    if gap_domain in skill.relevant_domains:
        base_confidence += 0.15

    # Check trigger match in message
    gap_message_lower = gap_message.lower() if gap_message else ""
    for trigger in skill.triggers:
        if trigger.lower() in gap_message_lower:
            base_confidence += 0.1
            break

    return min(base_confidence, 0.95)


def _infer_domain_from_gap_type(gap_type: str) -> str:
    """Infer gap domain from gap type.

    Delegates to GAP_TYPE_TO_CATEGORIES to avoid duplicate mapping logic.

    Args:
        gap_type: The gap type string.

    Returns:
        Inferred domain string (first category for known gap types,
        otherwise the gap_type itself).
    """
    categories = GAP_TYPE_TO_CATEGORIES.get(gap_type, [])
    if categories:
        return categories[0]
    return gap_type


def _map_severity_to_priority(severity: str) -> str:
    """Map gap severity to recommendation priority.

    Args:
        severity: Gap severity (critical, high, medium, low).

    Returns:
        Priority level string.
    """
    severity_lower = severity.lower() if severity else "medium"
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return mapping.get(severity_lower, "medium")


def inject_skill_context_for_gaps(gaps: list[dict]) -> str:
    """Inject skill context for LLM analysis of gaps.

    Creates a formatted context string that provides the LLM
    with information about relevant skills for the given gaps.

    Args:
        gaps: List of gap dictionaries.

    Returns:
        Formatted context string for LLM injection.
    """
    if not gaps:
        return ""

    # Get unique gap types
    gap_types = set()
    for gap in gaps:
        gap_type = gap.get("type", "")
        if gap_type:
            gap_types.add(gap_type)

    # Find relevant skills for all gaps
    all_relevant_skills: list[SkillSummary] = []
    seen_skills: set[str] = set()

    for gap in gaps:
        skills = find_skills_for_gap(gap, limit=5)
        for skill in skills:
            if skill.name not in seen_skills:
                seen_skills.add(skill.name)
                all_relevant_skills.append(skill)

    # Build context
    lines = [
        "## Relevant Skills for Current Gaps",
        "",
        f"Based on {len(gaps)} gaps found (types: {', '.join(sorted(gap_types))}):",
        "",
    ]

    if all_relevant_skills:
        lines.append(format_skill_context(all_relevant_skills, max_skills=30))
    else:
        lines.append(SKILL_RECOMMENDATION_CONTEXT)

    return "\n".join(lines)


def format_recommendations_for_rsn(
    recommendations: list[SkillRecommendation],
) -> list[dict[str, Any]]:
    """Format skill recommendations as RSN findings.

    Converts SkillRecommendation objects to the format
    expected by the RSN formatter.

    Args:
        recommendations: List of SkillRecommendation objects.

    Returns:
        List of RSN finding dictionaries.
    """
    findings: list[dict[str, Any]] = []

    for rec in recommendations:
        finding = {
            "id": f"skill-{rec.skill.name.lstrip('/')}",
            "severity": rec.priority.upper(),
            "message": f"Run {rec.skill.name} - {rec.rationale}",
            "file_ref": None,
            "action_type": "Run skill",
            "blast_radius": len(rec.gap_ids),
            "domain": "skill_coverage",
            "reversibility": 1.0,  # Running skills is trivially reversible
            "is_batch": len(rec.gap_ids) > 1,
            "batch_count": len(rec.gap_ids),
            "gap_ids": rec.gap_ids,
            "skill_name": rec.skill.name,
            "skill_description": rec.skill.description,
            "confidence": rec.confidence,
            "verified": rec.verified,  # True if skill has fresh coverage evidence
        }
        findings.append(finding)

    return findings


def get_skill_summary_for_display(recommendations: list[SkillRecommendation]) -> str:
    """Get a human-readable summary of skill recommendations.

    Args:
        recommendations: List of SkillRecommendation objects.

    Returns:
        Formatted summary string.
    """
    if not recommendations:
        return "No skill recommendations."

    lines = ["## Recommended Skills", ""]

    for i, rec in enumerate(recommendations, 1):
        gap_count = len(rec.gap_ids)
        count_str = f" ({gap_count} gaps)" if gap_count > 1 else ""
        lines.append(f"{i}. **{rec.skill.name}**{count_str} - {rec.skill.description}")
        lines.append(f"   - Rationale: {rec.rationale}")
        lines.append(f"   - Confidence: {rec.confidence:.0%}")
        lines.append("")

    return "\n".join(lines)


# ── Convenience Functions ───────────────────────────────────────────────────


def get_all_skill_context() -> str:
    """Get full skill recommendation context.

    Returns:
        Context string with all available skills.
    """
    return get_skill_recommendation_context()


def recommend_skills(gaps: list[dict], limit: int = 0) -> list[SkillRecommendation]:
    """Convenience function to get skill recommendations.

    Args:
        gaps: List of gap dictionaries.
        limit: Maximum recommendations (0 = no limit).

    Returns:
        List of SkillRecommendation objects.
    """
    return generate_skill_recommendations(gaps, limit=limit)
