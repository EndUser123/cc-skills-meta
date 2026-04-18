"""Skill Registry Bridge for GTO.

Provides skill metadata to GTO analysis for intelligent recommendations.
Loads skills from the shared skill registry and formats them for
gap-aware skill suggestion generation.

Priority: P1 (core infrastructure for intelligent skill recommendations)
"""

from __future__ import annotations

import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Registry caching
_skill_catalog: dict[str, SkillSummary] | None = None
_skills_by_category: dict[str, list[SkillSummary]] | None = None


@dataclass
class SkillSummary:
    """Summary of a skill for recommendation purposes.

    This is a lightweight view of skill metadata optimized for
    gap-to-skill mapping and LLM context injection.
    """

    name: str  # "/critique"
    description: str  # "Adaptive adversarial critique"
    category: str  # "quality"
    triggers: list[str]  # ["critique", "review"]
    file_path: str = ""
    relevant_domains: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def primary_trigger(self) -> str:
        """Get the primary trigger (first one)."""
        return self.triggers[0] if self.triggers else f"/{self.name.lstrip('/')}"


def _import_skill_registry() -> Any:
    """Import skill_registry from hooks archive.

    Returns the module or None if not available.
    """
    try:
        # Try direct import (if in path)
        from hooks._archive import skill_registry

        return skill_registry
    except ImportError:
        pass

    try:
        # Try adding to path
        hooks_path = Path("P:/.claude/hooks")
        if hooks_path.exists():
            sys.path.insert(0, str(hooks_path.parent))
            from hooks._archive import skill_registry

            return skill_registry
    except ImportError:
        pass

    try:
        # Try from CSF
        csf_path = Path("P:/__csf/src")
        if csf_path.exists():
            sys.path.insert(0, str(csf_path))
            from hooks._archive import skill_registry

            return skill_registry
    except ImportError:
        pass

    # No registry found — fall through to caller, who will use _build_fallback_catalog()
    return None


def _build_fallback_catalog() -> dict[str, SkillSummary]:
    """Build a fallback catalog of commonly used skills.

    Used when skill_registry is not available.
    """
    fallback_skills = [
        SkillSummary(
            name="/t",
            description="Minimal test selection for targeted verification",
            category="testing",
            triggers=["t", "test"],
            relevant_domains=["test_gap", "test_failure", "missing_test", "test_import_error", "flaky_test"],
        ),
        SkillSummary(
            name="/tdd",
            description="Test-driven development workflow",
            category="testing",
            triggers=["tdd", "test-driven"],
            relevant_domains=["test_gap", "test_failure", "missing_test", "test_import_error", "flaky_test"],
        ),
        SkillSummary(
            name="/qa",
            description="Feature certification workflow",
            category="testing",
            triggers=["qa", "certify", "certification"],
            relevant_domains=["test_gap", "test_failure", "test_import_error", "flaky_test"],
        ),
        SkillSummary(
            name="/critique",
            description="Adaptive adversarial code review",
            category="quality",
            triggers=["critique", "review"],
            relevant_domains=["code_quality", "design_issue"],
        ),
        SkillSummary(
            name="/uci",
            description="Unified Code Inspection",
            category="quality",
            triggers=["uci", "inspect"],
            relevant_domains=["code_quality", "design_issue"],
        ),
        SkillSummary(
            name="/doc",
            description="Ingest, update, create documentation",
            category="documentation",
            triggers=["doc", "document", "docs"],
            relevant_domains=["doc_gap", "missing_docs", "missing_readme"],
        ),
        SkillSummary(
            name="/docs-validate",
            description="Validate documentation completeness",
            category="documentation",
            triggers=["docs-validate", "validate-docs"],
            relevant_domains=["doc_gap", "missing_docs"],
        ),
        SkillSummary(
            name="/git",
            description="Sync, worktree, conflict resolution",
            category="vcs",
            triggers=["git", "sync"],
            relevant_domains=["git_dirty", "uncommitted_changes"],
        ),
        SkillSummary(
            name="/push",
            description="Fast push with retry logic",
            category="vcs",
            triggers=["push"],
            relevant_domains=["git_dirty", "uncommitted_changes"],
        ),
        SkillSummary(
            name="/deps",
            description="Dependency management",
            category="dependencies",
            triggers=["deps", "dependencies"],
            relevant_domains=["import_issue", "missing_dependency", "outdated_dependency"],
        ),
        SkillSummary(
            name="/verify",
            description="Verification orchestrator",
            category="verification",
            triggers=["verify", "verification"],
            relevant_domains=["import_issue", "code_quality"],
        ),
        SkillSummary(
            name="/design",
            description="Architecture decision advisor",
            category="architecture",
            triggers=["arch", "architecture"],
            relevant_domains=["design_issue", "architectural_concern"],
        ),
        SkillSummary(
            name="/adf",
            description="Evaluate structural changes",
            category="architecture",
            triggers=["adf", "architecture-decision"],
            relevant_domains=["design_issue", "architectural_concern"],
        ),
        SkillSummary(
            name="/debugRCA",
            description="Root cause analysis engine",
            category="debugging",
            triggers=["debugRCA", "rca", "root-cause"],
            relevant_domains=["test_failure", "runtime_error", "bug", "test_import_error", "flaky_test"],
        ),
        SkillSummary(
            name="/diagnose",
            description="Structured diagnostic protocol",
            category="debugging",
            triggers=["diagnose", "diagnostic"],
            relevant_domains=["test_failure", "runtime_error"],
        ),
        SkillSummary(
            name="/analyze",
            description="Unified analysis engine",
            category="analysis",
            triggers=["analyze", "analysis"],
            relevant_domains=["code_quality", "design_issue"],
        ),
        SkillSummary(
            name="/search",
            description="Unified intelligent search",
            category="search",
            triggers=["search", "find"],
            relevant_domains=["doc_gap", "missing_info"],
        ),
        SkillSummary(
            name="/truth",
            description="Truth verification command",
            category="verification",
            triggers=["truth", "verify-claims"],
            relevant_domains=["unverified_claim", "evidence_gap"],
        ),
        SkillSummary(
            name="/pre-mortem",
            description="Pre-mortem failure analysis",
            category="planning",
            triggers=["pre-mortem", "premortem"],
            relevant_domains=["design_issue", "risk_assessment"],
        ),
    ]

    return {skill.name: skill for skill in fallback_skills}


def load_skill_catalog(force_reload: bool = False) -> dict[str, SkillSummary]:
    """Load user-facing skills with metadata for recommendation analysis.

    Skills are loaded from the skill registry if available, otherwise
    falls back to a curated list of commonly used skills.

    Args:
        force_reload: Force reload even if cached.

    Returns:
        Dictionary mapping skill names to SkillSummary objects.
    """
    global _skill_catalog

    if _skill_catalog is not None and not force_reload:
        return _skill_catalog

    skill_registry = _import_skill_registry()

    if skill_registry is None:
        _skill_catalog = _build_fallback_catalog()
        return _skill_catalog

    try:
        # Load from registry
        registry = skill_registry.list_user_facing_skills()

        catalog: dict[str, SkillSummary] = {}
        seen_names: set[str] = set()

        for trigger, spec in registry.items():
            # Avoid duplicates (same skill may have multiple triggers)
            skill_name = f"/{spec.name.lstrip('/')}"
            if skill_name in seen_names:
                continue
            seen_names.add(skill_name)

            # Derive relevant domains from category and triggers
            relevant_domains = _derive_relevant_domains(spec.category, spec.triggers)

            summary = SkillSummary(
                name=skill_name,
                description=spec.description or f"{spec.category.title()} skill",
                category=spec.category,
                triggers=spec.triggers if spec.triggers else [skill_name.lstrip("/")],
                file_path=spec.file_path,
                relevant_domains=relevant_domains,
                metadata=spec.metadata,
            )
            catalog[skill_name] = summary

        _skill_catalog = catalog
        logger.info("Loaded %d skills from skill registry", len(catalog))
        return catalog

    except Exception as e:
        logger.exception("Failed to load skill registry: %s", e)
        _skill_catalog = _build_fallback_catalog()
        return _skill_catalog


def _derive_relevant_domains(category: str, triggers: list[str]) -> list[str]:
    """Derive relevant gap domains from skill category and triggers.

    Args:
        category: Skill category (e.g., "testing", "quality")
        triggers: Skill triggers (e.g., ["tdd", "test"])

    Returns:
        List of relevant gap domains.
    """
    domains = []

    # Category-based domains
    category_domains: dict[str, list[str]] = {
        "testing": ["test_gap", "test_failure", "missing_test", "test_import_error", "flaky_test"],
        "quality": ["code_quality", "design_issue", "complexity"],
        "documentation": ["doc_gap", "missing_docs", "missing_readme"],
        "vcs": ["git_dirty", "uncommitted_changes", "merge_conflict"],
        "dependencies": ["import_issue", "missing_dependency", "outdated_dependency"],
        "debugging": ["test_failure", "runtime_error", "bug", "test_import_error", "flaky_test"],
        "verification": ["unverified_claim", "evidence_gap"],
        "architecture": ["design_issue", "architectural_concern"],
        "planning": ["missing_plan", "scope_unclear"],
        "analysis": ["code_quality", "design_issue"],
        "search": ["doc_gap", "missing_info"],
    }

    if category in category_domains:
        domains.extend(category_domains[category])

    # Trigger-based domains
    trigger_lower = " ".join(triggers).lower()
    if "rca" in trigger_lower or "root" in trigger_lower:
        domains.extend(["test_failure", "runtime_error", "bug"])
    if "doc" in trigger_lower:
        domains.extend(["doc_gap", "missing_docs"])
    if "test" in trigger_lower or "tdd" in trigger_lower:
        domains.extend(["test_gap", "missing_test"])
    if "git" in trigger_lower or "push" in trigger_lower:
        domains.extend(["git_dirty", "uncommitted_changes"])
    if "dep" in trigger_lower:
        domains.extend(["import_issue", "missing_dependency"])

    return list(set(domains))  # Deduplicate


def get_skills_by_category(force_reload: bool = False) -> dict[str, list[SkillSummary]]:
    """Group skills by category for domain matching.

    Args:
        force_reload: Force reload even if cached.

    Returns:
        Dictionary mapping category names to lists of SkillSummary.
    """
    global _skills_by_category

    if _skills_by_category is not None and not force_reload:
        return _skills_by_category

    catalog = load_skill_catalog(force_reload)

    by_category: dict[str, list[SkillSummary]] = {}
    for skill in catalog.values():
        cat = skill.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(skill)

    _skills_by_category = by_category
    return by_category


# ── Keyword Extraction for Dynamic Similarity ──────────────────────────────────

_STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "when",
    "for",
    "of",
    "with",
    "by",
    "from",
    "to",
    "in",
    "on",
    "at",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "need",
    "this",
    "that",
    "these",
    "those",
    "use",
    "used",
    "using",
    "make",
    "made",
    "get",
    "got",
    "into",
    "over",
    "under",
    "about",
    "above",
    "below",
    "after",
    "before",
    "between",
    "through",
    "during",
    "without",
    "within",
    "upon",
    "via",
    "per",
    "skill",
    "skills",
    "command",
    "workflow",
    "system",
    "tool",
    "file",
    "based",
    "enabled",
    "related",
    "specific",
    "general",
    "auto",
    "automatic",
    "also",
    "its",
    "dont",
    "doesnt",
    "wont",
    "cant",
    "shouldnt",
    "wouldnt",
    "couldnt",
    "didnt",
    "not",
    "no",
    "yes",
    "all",
    "any",
    "some",
    "each",
    "every",
    "both",
    "few",
    "most",
    "other",
    "such",
    "only",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "now",
    "here",
    "there",
    "once",
    "again",
    "always",
    "never",
    "ever",
    "still",
    "already",
    "even",
    "much",
    "many",
    "well",
    "back",
    "way",
    "new",
    "old",
    "first",
    "last",
}


def _extract_keywords(text: str, max_keywords: int = 20) -> set[str]:
    """Extract meaningful keywords from text using word frequency.

    Used for dynamic gap-to-skill similarity scoring without hardcoded mappings.

    Args:
        text: Input text to extract keywords from.
        max_keywords: Maximum number of keywords to return.

    Returns:
        Set of meaningful keyword strings.
    """
    if not text:
        return set()

    text_lower = text.lower()

    # Remove markdown code blocks and inline code
    text_lower = re.sub(r"```.*?```", "", text_lower, flags=re.DOTALL)
    text_lower = re.sub(r"`[^`]+`", "", text_lower)

    # Extract words
    words = re.findall(r"\b[a-z][a-z0-9_-]+\b", text_lower)

    # Filter stop words and short words
    words = [w for w in words if w not in _STOP_WORDS and len(w) >= 3]

    # Count frequency and take top keywords
    word_freq: dict[str, int] = defaultdict(int)
    for word in words:
        word_freq[word] += 1

    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return {word for word, _ in sorted_words[:max_keywords]}


def _build_gap_text_profile(gap: dict) -> str:
    """Build a text profile from a gap for keyword extraction.

    Combines all text fields from a gap into a single string
    suitable for keyword extraction.

    Args:
        gap: Gap dictionary with 'type', 'message', 'domain' fields.

    Returns:
        Combined text string for keyword extraction.
    """
    parts = []
    if gap.get("type"):
        parts.append(gap["type"].replace("_", " ").replace("-", " "))
    if gap.get("message"):
        parts.append(gap["message"])
    if gap.get("domain"):
        parts.append(gap["domain"])
    if gap.get("severity"):
        parts.append(gap["severity"])
    return " ".join(parts)


def _dynamic_skill_score(skill: SkillSummary, gap: dict) -> float:
    """Compute dynamic similarity score between a skill and a gap.

    Uses TF-IDF-inspired keyword overlap between:
    - Gap text profile (type + message + domain)
    - Skill profile (description + triggers + category)

    This replaces the hardcoded GAP_TYPE_TO_CATEGORIES mapping with
    dynamic, text-driven similarity scoring.

    Args:
        skill: Skill to score.
        gap: Gap to score against.

    Returns:
        Similarity score (0.0 to ~1.0, not capped).
    """
    gap_text = _build_gap_text_profile(gap)
    gap_keywords = _extract_keywords(gap_text, max_keywords=25)

    if not gap_keywords:
        return 0.0

    # Build skill text profile
    skill_text_parts = [
        skill.description,
        skill.category,
        " ".join(skill.triggers),
        " ".join(skill.relevant_domains),
    ]
    skill_text = " ".join(skill_text_parts)
    skill_keywords = _extract_keywords(skill_text, max_keywords=30)

    # Compute keyword overlap scores
    overlap = gap_keywords & skill_keywords
    overlap_score = len(overlap) * 1.0  # Each shared keyword = 1.0

    # Bonus: skill category matches gap domain
    gap_domain = gap.get("domain", "")
    if gap_domain and gap_domain in skill.relevant_domains:
        overlap_score += 3.0

    # Bonus: trigger appears in gap message
    gap_message = gap.get("message", "").lower()
    for trigger in skill.triggers:
        if trigger.lower() in gap_message:
            overlap_score += 2.0
            break

    # Bonus: gap type tokens in skill description
    gap_type = gap.get("type", "")
    if gap_type:
        type_tokens = set(re.findall(r"[a-z]+", gap_type.lower()))
        desc_words = set(re.findall(r"[a-z]+", skill.description.lower()))
        type_overlap = type_tokens & desc_words
        overlap_score += len(type_overlap) * 1.5

    return overlap_score


def find_skills_for_gap(gap: dict, limit: int = 10) -> list[SkillSummary]:
    """Find skills relevant to a specific gap.

    Args:
        gap: Gap dictionary with 'type', 'message', 'domain' fields.
        limit: Maximum number of skills to return.

    Returns:
        List of relevant SkillSummary objects, sorted by relevance.
    """
    catalog = load_skill_catalog()

    # Score each skill using dynamic similarity (replaces hardcoded GAP_TYPE_TO_CATEGORIES)
    scored_skills: list[tuple[float, SkillSummary]] = []

    for skill in catalog.values():
        score = _dynamic_skill_score(skill, gap)
        if score > 0:
            scored_skills.append((score, skill))

    # Sort by score descending
    scored_skills.sort(key=lambda x: x[0], reverse=True)

    return [skill for _, skill in scored_skills[:limit]]


def format_skill_context(skills: list[SkillSummary], max_skills: int = 20) -> str:
    """Format skill info for LLM context injection.

    Creates a concise summary of available skills that the LLM
    can use to make intelligent recommendations.

    Args:
        skills: List of skills to format.
        max_skills: Maximum number of skills to include.

    Returns:
        Formatted string for context injection.
    """
    if not skills:
        return ""

    lines = [
        "## Available Skills for Gap Resolution",
        "",
        "When analyzing gaps, consider these relevant skills:",
        "",
    ]

    # Group by category
    by_category: dict[str, list[SkillSummary]] = {}
    for skill in skills[:max_skills]:
        cat = skill.category.title()
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(skill)

    # Format each category
    for category in sorted(by_category.keys()):
        cat_skills = by_category[category]
        lines.append(f"### {category}")
        for skill in cat_skills:
            trigger = skill.primary_trigger
            desc = (
                skill.description[:60] + "..." if len(skill.description) > 60 else skill.description
            )
            lines.append(f"- {trigger} - {desc}")
        lines.append("")

    lines.extend(
        [
            "When recommending skills:",
            "1. Match skill capabilities to specific gap issues",
            "2. Provide rationale for WHY this skill helps",
            "3. Consider gap severity - critical gaps need immediate skills",
        ]
    )

    return "\n".join(lines)


def get_skill_recommendation_context() -> str:
    """Get the full skill recommendation context for LLM injection.

    Returns:
        Context string with all available skills organized by category.
    """
    catalog = load_skill_catalog()
    skills = list(catalog.values())
    return format_skill_context(skills)


def get_all_skill_names() -> list[str]:
    """Get list of all available skill names.

    Returns:
        List of skill names (e.g., ["/tdd", "/critique", ...]).
    """
    catalog = load_skill_catalog()
    return list(catalog.keys())


# Convenience function for direct import
def get_skill_summary(skill_name: str) -> SkillSummary | None:
    """Get summary for a specific skill.

    Args:
        skill_name: Skill name (e.g., "/critique" or "critique").

    Returns:
        SkillSummary if found, None otherwise.
    """
    catalog = load_skill_catalog()

    # Try with slash
    if not skill_name.startswith("/"):
        skill_name = f"/{skill_name}"

    return catalog.get(skill_name)
