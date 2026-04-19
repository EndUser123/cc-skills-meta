"""Recommended Next Steps Formatter.

Priority: P1 (runs during results assembly)
Purpose: Generate deterministic next steps from gap list

Features:
- Grouping by category (tests, docs, git, dependencies, code_quality)
- Sorting by priority (critical → high → medium → low)
- Effort estimation formatting
- Recurrence tracking display
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Thresholds for effort formatting
MINUTES_PER_HOUR = 60
EFFORT_LARGE_THRESHOLD = 120  # Efforts >= 120 min shown in hours


@dataclass
class NextStep:
    """A recommended next step."""

    gap_id: str
    description: str
    category: str
    priority: Literal["critical", "high", "medium", "low"]
    effort_estimate_minutes: int
    recurrence_count: int = 1
    file_path: str | None = None
    line_number: int | None = None
    driven_by: str | None = None  # Which integrity prompt generated this step


@dataclass
class FormattedNextSteps:
    """Result of next steps formatting."""

    steps_by_category: dict[str, list[NextStep]]
    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_effort_minutes: int

    @property
    def steps(self) -> list[NextStep]:
        """All steps flattened from categories."""
        all_steps = []
        for category_steps in self.steps_by_category.values():
            all_steps.extend(category_steps)
        return all_steps


class NextStepsFormatter:
    """
    Format recommended next steps from gap list.

    Groups by category and sorts by priority.
    """

    # Category mapping from gap types
    CATEGORY_MAP = {
        # Tests
        "test_failure": "tests",
        "missing_test": "tests",
        "test_import_error": "tests",
        # Docs
        "missing_docs": "docs",
        "missing_claude_md": "docs",
        "missing_readme": "docs",
        # Git
        "git_dirty": "git",
        "uncommitted_changes": "git",
        "missing_lock_file": "git",
        # Dependencies
        "import_error": "dependencies",
        "missing_dependency": "dependencies",
        "outdated_dependency": "dependencies",
        "vulnerable_dependency": "dependencies",
        # Session outcomes (conversation-level outstanding items)
        "session_outcomes": "session",
        # Suspicion signals (conversation-level reasoning gaps)
        "suspicion_misalignment": "session",
        "suspicion_contradiction": "session",
        "suspicion_unresolved_confusion": "session",
        "suspicion_resigned_acceptance": "session",
        "suspicion_commitment_reversal": "session",
        "suspicion_confidence_mirage": "session",
        "suspicion_silent_failure_masking": "session",
        "suspicion_excessive_breadcrumbs": "session",
        "suspicion_reasoning_action": "session",
        # Improvement/retrospective gaps
        "improvement_gap": "improvements",
        "improvement_investigation": "improvements",
        "process_gap": "improvements",
        "repeatable_pattern": "improvements",
        # Code quality (default)
        "pending_task": "pending_tasks",
        "pending_tasks": "pending_tasks",
    }

    # Priority order for sorting
    PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    # Default category for unmapped gap types
    DEFAULT_CATEGORY = "code_quality"

    def __init__(self, show_effort: bool = True) -> None:
        """Initialize formatter with effort map."""
        self._effort_map: dict[str, int] = {}
        self._show_effort = show_effort

    def _map_category(self, gap_type: str) -> str:
        """Map gap type to category.

        Args:
            gap_type: Gap type string

        Returns:
            Category name
        """
        return self.CATEGORY_MAP.get(gap_type, self.DEFAULT_CATEGORY)

    def _format_effort(self, effort_minutes: int) -> str:
        """Format effort estimate for display.

        Args:
            effort_minutes: Effort in minutes

        Returns:
            Formatted effort string (e.g., "[~5min]", "[~30min]", "[~2hr]")
        """
        if effort_minutes >= 60:
            hours = round(effort_minutes / 60, 1)
            if hours == int(hours):
                hours = int(hours)
            return f"[~{hours}hr]"
        return f"[~{effort_minutes}min]"

    def _format_step(self, step: NextStep, index: int, category_index: int) -> str:
        """Format a single step for display.

        Args:
            step: The next step to format
            index: Global step index
            category_index: Index within category

        Returns:
            Formatted step string
        """
        parts = []

        # Step number with category letter
        parts.append(f"{category_index}.{index}")

        # Gap ID reference
        parts.append(f"[{step.gap_id}]")

        # Effort estimate
        if self._show_effort:
            parts.append(self._format_effort(step.effort_estimate_minutes))

        # Recurrence marker
        if step.recurrence_count > 1:
            parts.append(f"[RECURRING x{step.recurrence_count}]")

        # Description
        parts.append(step.description)

        # File reference if available
        if step.file_path:
            location = step.file_path
            if step.line_number:
                location += f":{step.line_number}"
            parts.append(f"({location})")

        return " ".join(parts)

    def format(self, gaps: list[dict]) -> FormattedNextSteps:
        """
        Format recommended next steps from gap list.

        Args:
            gaps: List of gap dictionaries with keys:
                - id: gap identifier
                - type: gap type
                - severity: priority level
                - message: description
                - file_path: optional file path
                - line_number: optional line number
                - recurrence_count: times this gap has recurred
                - effort_estimate_minutes: estimated effort

        Returns:
            FormattedNextSteps with grouped and sorted steps
        """
        # Convert gaps to NextStep objects
        steps = []
        for gap in gaps:
            # Handle both dict and Gap dataclass
            if isinstance(gap, dict):
                gap_id = gap.get("id", gap.get("gap_id", "unknown"))
                description = gap.get("message", "")
                category = self._map_category(gap.get("type", ""))
                priority = gap.get("severity", "low")
                effort = gap.get("effort_estimate_minutes", 5)
                recurrence = gap.get("recurrence_count", 1)
                file_path = gap.get("file_path")
                line_number = gap.get("line_number")
            else:
                # Gap dataclass
                gap_id = getattr(gap, "gap_id", "unknown")
                description = getattr(gap, "message", "")
                category = self._map_category(getattr(gap, "type", ""))
                priority = getattr(gap, "severity", "low")
                effort = getattr(gap, "effort_estimate_minutes", 5)
                recurrence = getattr(gap, "recurrence_count", 1)
                file_path = getattr(gap, "file_path", None)
                line_number = getattr(gap, "line_number", None)

            step = NextStep(
                gap_id=gap_id,
                description=description,
                category=category,
                priority=priority,
                effort_estimate_minutes=effort,
                recurrence_count=recurrence,
                file_path=file_path,
                line_number=line_number,
            )
            steps.append(step)

        # Group by category
        steps_by_category: dict[str, list[NextStep]] = {
            "tests": [],
            "docs": [],
            "git": [],
            "dependencies": [],
            "code_quality": [],
        }

        for step in steps:
            if step.category not in steps_by_category:
                steps_by_category[step.category] = []
            steps_by_category[step.category].append(step)

        # Sort each category by priority
        for category in steps_by_category:
            steps_by_category[category].sort(
                key=lambda s: (self.PRIORITY_ORDER.get(s.priority, 99), s.gap_id)
            )

        # Count by priority
        critical_count = sum(1 for s in steps if s.priority == "critical")
        high_count = sum(1 for s in steps if s.priority == "high")
        medium_count = sum(1 for s in steps if s.priority == "medium")
        low_count = sum(1 for s in steps if s.priority == "low")

        # Calculate total effort
        total_effort = sum(s.effort_estimate_minutes for s in steps)

        return FormattedNextSteps(
            steps_by_category=steps_by_category,
            total_count=len(steps),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            total_effort_minutes=total_effort,
        )

    def format_markdown(self, formatted: FormattedNextSteps) -> str:
        """
        Format next steps as markdown.

        Args:
            formatted: FormattedNextSteps from format()

        Returns:
            Markdown string with grouped steps
        """
        lines = []

        # Category order
        category_order = ["tests", "docs", "git", "dependencies", "code_quality"]

        global_index = 1
        domain_idx = 0
        for category in category_order:
            steps = formatted.steps_by_category.get(category, [])
            if not steps:
                continue

            domain_idx += 1
            step_idx = 0

            # Category header
            lines.append(f"\n### {category.title()}")
            lines.append("")

            for step in steps:
                step_idx += 1
                lines.append(f"{global_index}. {self._format_step(step, step_idx, domain_idx)}")
                global_index += 1

            lines.append("")

        # Footer with "do all" option
        if formatted.total_count > 0:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("")
            lines.append(f"0 - Do ALL Recommended Next Actions ({formatted.total_count} items)")
            if self._show_effort:
                total_hours = formatted.total_effort_minutes / 60
                if total_hours >= 1:
                    lines.append(f"    Total estimated effort: {total_hours:.1f} hours")
                else:
                    lines.append(
                        f"    Total estimated effort: {formatted.total_effort_minutes} minutes"
                    )

        return "\n".join(lines)


# Convenience function
def format_recommended_next_steps(gaps: list[dict]) -> FormattedNextSteps:
    """
    Quick next steps formatting.

    Args:
        gaps: List of gap dictionaries

    Returns:
        FormattedNextSteps with grouped and sorted steps
    """
    formatter = NextStepsFormatter()
    return formatter.format(gaps)


# GTO type → RSN domain mapping
# Maps gap types to RSN domain strings for section routing
GTO_TYPE_TO_RSN_DOMAIN: dict[str, str] = {
    "test_gap": "test",
    "doc_gap": "docs",
    "code_quality": "quality",
    "import_issue": "import",
    "skill_suggestion": "skill_coverage",
    "correctness_gap": "correctness",
    "pending_task": "pending_tasks",
    "improvement_investigation": "improvements",
    "process_gap": "improvements",
    "other": "other",  # fallback for unknown gap types
}

# GTO-specific section definitions
# Maps domain → (section_name, section_key) for custom RSN sections
# These are more specific than the generic RSN defaults
GTO_SECTION_DEFINITIONS: dict[str, tuple[str, str]] = {
    "test": ("Test Coverage Gaps", "test_gaps"),
    "docs": ("Documentation Gaps", "doc_gaps"),
    "quality": ("Code Quality Issues", "code_quality_gaps"),
    "import": ("Import/Dependency Issues", "import_gaps"),
    "skill_coverage": ("Relevant Skills to Run", "skill_coverage"),
    "correctness": ("Correctness Issues", "correctness_gaps"),
    "improvements": ("Process Improvement Issues", "improvements"),
    "other": ("Other Issues", "other_gaps"),
}

# Gap type → reversibility score
# From reversibility_scale.md: 1.0=trivial, 1.5=moderate, 1.75=hard, 2.0=irreversible
# "worst wins" aggregation (max) for batches — highest score wins
GAP_TYPE_REVERSIBILITY: dict[str, float] = {
    "git_dirty": 1.0,
    "missing_lock_file": 1.0,
    "missing_docs": 1.0,
    "missing_claude_md": 1.0,
    "test_failure": 1.25,
    "missing_test": 1.25,
    "import_error": 1.5,
    "missing_dependency": 1.5,
    "outdated_dependency": 1.5,
    "vulnerable_dependency": 1.75,
    "code_quality": 1.75,
    "correctness_gap": 1.75,
    "pending_task": 1.5,
}

# Gap type → evidence tier
# Lower tier = higher confidence. "worst wins" aggregation (min) for batches.
# Tier 1: execution artifacts, logs, test output (95%)
# Tier 2: official docs, specs (85%)
# Tier 3: static analysis, logical derivation (75%)
# Tier 4: comments, unverified claims (50%)
EVIDENCE_TIER_BY_TYPE: dict[str, int] = {
    "git_dirty": 1,
    "missing_lock_file": 1,
    "missing_docs": 1,
    "missing_claude_md": 1,
    "test_failure": 1,
    "missing_test": 2,
    "import_error": 2,
    "missing_dependency": 1,
    "outdated_dependency": 2,
    "vulnerable_dependency": 1,
    "code_quality": 3,
    "correctness_gap": 3,
    "pending_task": 2,
}

# ── Batch detection constants ─────────────────────────────────────────────────

# Severity ordering for aggregate severity calculation (worst = lowest number)
# UPPERCASE version for batch detection (reads uppercased gap severities)
SEVERITY_ORDER: dict[str, int] = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Lowercase version for results builder (Gap.severity is normalized to lowercase)
_SEVERITY_ORDER_LOWER: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _detect_batch_groups(gaps: list[dict]) -> list[dict]:
    """
    Detect batchable groups of gaps sharing same file or root cause.

    Strategies:
    1. Same (file_path, line_number) location → batch with blast_radius = n_gaps
    2. # type: ignore root cause pattern → batch with blast_radius = n_gaps
    3. Remaining gaps → individual entries with blast_radius = 1

    blast_radius semantics: "reverse mobility" = number of related gaps addressed
    together. batch_size (not epidemiological R-value). Individual gaps have
    blast_radius=1 meaning only themselves are addressed.

    Args:
        gaps: List of gap dictionaries

    Returns:
        List of RSN finding dicts with batch metadata

    Raises:
        TypeError: If gaps is not a list
    """
    from collections import defaultdict

    if not isinstance(gaps, list):
        raise TypeError(f"gaps must be a list, got {type(gaps).__name__}")

    results: list[dict] = []
    used_indices: set[int] = set()

    # ── Helper: extract safe string from gap message ──────────────────────
    def _safe_msg(g: dict) -> str:
        """Extract message from gap, safely handling non-string types."""
        msg = g.get("message", "")
        return str(msg) if isinstance(msg, str) else repr(msg)

    # ── Helper: sanitize reason string for filesystem-safe ID ─────────────
    def _sanitize_id_segment(text: str) -> str:
        """Remove filesystem-unsafe characters for use in IDs."""
        return text.replace("|", "_").replace("/", "_").replace("\\", "_").replace(":", "_")[:20]

    # ── Strategy 1: Same (file_path, line_number) location ────────────────
    # Group gaps by exact file+line location
    location_groups: dict[tuple, list[int]] = defaultdict(list)
    for i, gap in enumerate(gaps):
        msg = gap.get("message", "")
        # Skip # type: ignore gaps — Strategy 2 handles these by root cause
        if isinstance(msg, str) and "# type: ignore" in msg:
            continue
        # Skip findings without a meaningful file location (e.g., skill_coverage findings)
        # These don't have source code references and shouldn't be batched by location
        fp = gap.get("file_path") or ""
        ln = gap.get("line_number")
        if not fp and ln is None:
            continue
        key = (fp, ln)
        location_groups[key].append(i)

    for (file_path, line_number), indices in location_groups.items():
        if len(indices) < 2:
            continue
        if any(i in used_indices for i in indices):
            continue

        # Batch them
        used_indices.update(indices)
        batch_gaps = [gaps[i] for i in indices]
        gap_ids = [gaps[i].get("id", gaps[i].get("gap_id", "?")) for i in indices]

        # Aggregate severity (worst wins = lowest numeric score)
        # Normalize to lowercase for consistent lookup in PRIORITY_ORDER
        severities = [(g.get("severity") or "low").lower() for g in batch_gaps]
        aggregate_severity = min(severities, key=lambda s: _SEVERITY_ORDER_LOWER.get(s, 99))

        # Aggregate message (sanitize unhashable types for dict.fromkeys)
        unique_msgs = list(dict.fromkeys(_safe_msg(g) for g in batch_gaps))
        if len(unique_msgs) == 1:
            message = unique_msgs[0]
        else:
            message = f"Multiple issues at {file_path}:{line_number} ({len(indices)} related gaps)"

        file_ref = f"{file_path}:{line_number}" if line_number else file_path

        # Derive domain from batch gap types (consistent with Strategy 3)
        batch_domains = [
            GTO_TYPE_TO_RSN_DOMAIN.get(g.get("type", ""), "code_quality") for g in batch_gaps
        ]
        # Use most common domain, tie-break by preferring non-default
        domain = (
            max(set(batch_domains), key=batch_domains.count) if batch_domains else "code_quality"
        )

        # Aggregate reversibility (worst wins = max score)
        batch_reversibilities = [
            GAP_TYPE_REVERSIBILITY.get(g.get("type", ""), 1.75) for g in batch_gaps
        ]
        aggregate_reversibility = max(batch_reversibilities)

        # Aggregate evidence tier (worst wins = min tier = highest confidence)
        batch_tiers = [EVIDENCE_TIER_BY_TYPE.get(g.get("type", ""), 3) for g in batch_gaps]
        aggregate_evidence_tier = min(batch_tiers)

        # Aggregate effort (sum of batch members — all addressed together)
        aggregate_effort = sum(g.get("effort_estimate_minutes", 5) for g in batch_gaps)

        # Cascade depth: worst in batch (DEEP > MEDIUM > SHALLOW)
        cascade_depths = [g.get("cascade_depth") for g in batch_gaps if g.get("cascade_depth")]
        depth_order = {"DEEP": 0, "MEDIUM": 1, "SHALLOW": 2}
        best_depth = min(cascade_depths, key=lambda d: depth_order.get(d, 3)) if cascade_depths else None

        results.append(
            {
                "id": f"BATCH-LOC-{file_path.replace('|', '_')}|{line_number or 'NOLINE'}",
                "severity": aggregate_severity.upper(),
                "message": message,
                "file_ref": file_ref,
                "action_type": "Manual",
                "blast_radius": len(indices),
                "domain": domain,
                "reversibility": aggregate_reversibility,
                "evidence_tier": aggregate_evidence_tier,
                "is_batch": True,
                "batch_count": len(indices),
                "gap_ids": gap_ids,
                "effort_minutes": aggregate_effort,
                "driven_by": batch_gaps[0].get("driven_by"),
                "cascade_depth": best_depth,
                "advisory": any(g.get("advisory") for g in batch_gaps),
            }
        )

    # ── Strategy 2: # type: ignore root cause pattern ─────────────────────
    # Detect gaps that are all # type: ignore comments pointing to missing deps
    # Domain is derived from matched keyword (consistent with Strategy 3)
    keyword_to_domain: dict[str, str] = {
        "missing": "import",
        "import": "import",
        "cannot find": "code_quality",
        "no attribute": "code_quality",
    }
    # Group by (reason, matched_keyword) to preserve domain derivation
    type_ignore_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, gap in enumerate(gaps):
        if i in used_indices:
            continue
        msg = gap.get("message", "")
        # Guard: skip non-string messages
        if not isinstance(msg, str):
            continue
        # Guard: skip if "# type: ignore" not found (-1 case)
        reason_start = msg.find("# type: ignore")
        if reason_start == -1:
            continue
        # Match: "# type: ignore" + "missing" or "cannot find" or "import"
        matched_kw: str | None = None
        for kw in ("missing", "cannot find", "import", "no attribute"):
            if kw in msg.lower():
                matched_kw = kw
                break
        if matched_kw is not None:
            # Group by the "reason" after # type: ignore
            reason = msg[reason_start:].split(".")[0][:40]  # first clause
            type_ignore_groups[(reason, matched_kw)].append(i)

    for (reason, matched_kw), indices in type_ignore_groups.items():
        if len(indices) < 2:
            continue

        used_indices.update(indices)
        batch_gaps = [gaps[i] for i in indices]
        gap_ids = [gaps[i].get("id", gaps[i].get("gap_id", "?")) for i in indices]

        # Worst severity (lowest numeric score = most severe)
        severities = [(g.get("severity") or "low").lower() for g in batch_gaps]
        aggregate_severity = min(severities, key=lambda s: _SEVERITY_ORDER_LOWER.get(s, 99))

        # Derive domain from matched keyword (consistent with Strategy 3)
        domain = keyword_to_domain.get(matched_kw, "import")

        # Aggregate effort from batch members
        aggregate_effort = sum(g.get("effort_estimate_minutes", 5) for g in batch_gaps)

        results.append(
            {
                "id": f"BATCH-IGNORE-{_sanitize_id_segment(reason)}",
                "severity": aggregate_severity.upper(),
                "message": f"Multiple # type: ignore entries: {reason} ({len(indices)} gaps — install missing dependency to fix all)",
                "file_ref": None,
                "action_type": "Manual",
                "blast_radius": len(indices),
                "domain": domain,
                "reversibility": 1.5,
                "evidence_tier": 2,  # Tier 2: import errors are doc/spec based
                "is_batch": True,
                "batch_count": len(indices),
                "gap_ids": gap_ids,
                "effort_minutes": aggregate_effort,
                "driven_by": batch_gaps[0].get("driven_by"),
                "cascade_depth": "MEDIUM",
                "advisory": False,
            }
        )

    # ── Strategy 3: Remaining individual gaps ─────────────────────────────
    for i, gap in enumerate(gaps):
        if i in used_indices:
            continue

        file_path = gap.get("file_path")
        line_number = gap.get("line_number")
        file_ref = f"{file_path}:{line_number}" if line_number and file_path else file_path

        gap_type = gap.get("type", "")
        domain = GTO_TYPE_TO_RSN_DOMAIN.get(gap_type, "")
        reversibility = GAP_TYPE_REVERSIBILITY.get(gap_type, 1.75)
        evidence_tier = EVIDENCE_TIER_BY_TYPE.get(gap_type, 3)

        results.append(
            {
                "id": gap.get("id", gap.get("gap_id", "unknown")),
                "severity": (gap.get("severity") or "low").upper(),
                "message": gap.get("message", ""),
                "file_ref": file_ref,
                "action_type": "Manual",
                "blast_radius": 1,
                "domain": domain,
                "reversibility": reversibility,
                "evidence_tier": evidence_tier,
                "is_batch": False,
                "batch_count": 0,
                "gap_ids": [gap.get("id", gap.get("gap_id", "unknown"))],
                "driven_by": gap.get("driven_by"),
                "cascade_depth": gap.get("cascade_depth"),
                "advisory": gap.get("advisory", False),
            }
        )

    return results


# Emoji mapping for domain headers
_DOMAIN_EMOJI: dict[str, str] = {
    "tests": "🧪",
    "docs": "📄",
    "quality": "🔧",
    "code_quality": "🔧",
    "git": "🐙",
    "dependencies": "📦",
    "deps": "📦",
    "import": "⚡",
    "skill_coverage": "🎯",
    "correctness": "✅",
    "improvements": "🚀",
    "session": "🎯",
    "pending_tasks": "📋",
    "other": "📌",
}

# Human-readable domain names for section headers
_DOMAIN_DISPLAY: dict[str, str] = {
    "tests": "TESTS",
    "docs": "DOCS",
    "quality": "QUALITY",
    "code_quality": "QUALITY",
    "git": "GIT",
    "dependencies": "DEPS",
    "deps": "DEPS",
    "import": "IMPORT",
    "skill_coverage": "SKILL COVERAGE",
    "correctness": "CORRECTNESS",
    "improvements": "IMPROVEMENTS",
    "session": "SESSION",
    "pending_tasks": "YOUR TASKS",
    "other": "OTHER",
}


def _format_gto_rsn_markdown(findings: list[dict], show_effort: bool = True) -> str:
    """
    Format GTO findings as GTO-native RNS text.

    Produces output matching GTO v4.0 RNS spec:
        🧪 TESTS
          TEST-001 [~5min] [R:1.25] Fix missing test (file:45)
          [caused-by: TEST-002]

        📄 DOCS
          DOC-001 [~10min] [R:1.0] Add docstring (src/utils.py:78)

        0 — Do ALL Recommended Next Actions (N items, ~Xmin total)

    Args:
        findings: RSN findings from _detect_batch_groups()

    Returns:
        Formatted string (no markdown code fences)
    """
    if not findings:
        return ""

    # ── Split: skill routing vs actual work items ────────────────────────────
    # Skill suggestions (action_type == "Use /skill") go to separate section at bottom
    skill_suggestions: list[dict] = []
    work_items: list[dict] = []

    for f in findings:
        if f.get("action_type") in ("Use /skill", "Run skill"):
            skill_suggestions.append(f)
        else:
            work_items.append(f)

    # ── Sort work items: severity first, then reversibility (trivial→hard) ──
    def sort_key(f: dict) -> tuple:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sev = severity_order.get(f.get("severity", "LOW"), 99)
        rev = f.get("reversibility", 1.75)  # lower = easier/should sort first
        blast = f.get("blast_radius") or 0
        return (sev, rev, -blast, f.get("id", ""))

    work_items.sort(key=sort_key)
    skill_suggestions.sort(key=lambda f: (f.get("severity", "LOW"), f.get("id", "")))

    # ── Tier sections by reversibility within the work items ─────────────────
    # TRIVIAL: R ≤ 1.25 (do immediately)
    # MODERATE: R ≤ 1.5 (do next)
    # DEFER: R > 1.5 (defer unless critical)
    trivial = [f for f in work_items if f.get("reversibility", 1.75) <= 1.25]
    moderate = [f for f in work_items if 1.25 < f.get("reversibility", 1.75) <= 1.5]
    defer = [f for f in work_items if f.get("reversibility", 1.75) > 1.5]

    lines: list[str] = []
    total_items = 0
    total_effort_minutes = 0

    # ── Global flat counter per domain type ─────────────────────────────────
    # e.g. TEST-001, TEST-002, then DOC-001, etc.
    domain_counters: dict[str, int] = {}

    def render_domain(domain: str, domain_findings: list[dict]) -> None:
        """Render a domain section with reversibility-sorted items."""
        nonlocal total_items, total_effort_minutes, domain_counters

        if not domain_findings:
            return

        emoji = _DOMAIN_EMOJI.get(domain, "📌")
        display_name = _DOMAIN_DISPLAY.get(domain, domain.upper())
        lines.append(f"{emoji} {display_name}")

        for f in domain_findings:
            prefix = domain[:4].upper()
            if domain not in domain_counters:
                domain_counters[domain] = 1
            item_num = domain_counters[domain]
            domain_counters[domain] += 1
            flat_id = f"{prefix}-{item_num:03d}"

            reversibility = f.get("reversibility", 1.75)
            rev_str = f"[R:{reversibility}]"

            effort = f.get("effort_minutes", f.get("effort_estimate_minutes", 5))
            total_effort_minutes += effort
            effort_str = f"[~{effort // MINUTES_PER_HOUR}hr]" if effort >= EFFORT_LARGE_THRESHOLD else f"[~{effort}min]"
            message = f.get("message", "")
            file_ref = f.get("file_ref") or f.get("file_path", "")
            location = f"({file_ref})" if file_ref else ""

            parts = [f"  {flat_id}"]
            if show_effort:
                parts.append(effort_str)
            parts.append(rev_str)
            parts.append(f"{message} {location}" if location else message)
            lines.append(" ".join(parts))
            total_items += 1

            for dep_key in ("causes", "caused_by", "blocks"):
                if f.get(dep_key):
                    lines.append(f"  [{dep_key}: {f[dep_key]}]")

            if f.get("driven_by"):
                lines.append(f"  [from: {f['driven_by']}]")

            # Cascade depth annotation (pre-mortem Step 4.5)
            if f.get("cascade_depth"):
                lines.append(f"  [CASCADE: {f['cascade_depth']}]")

            # Advisory enforcement flag (pre-mortem Step 3.6 advisory heuristic)
            if f.get("advisory"):
                lines.append(f"  [ADVISORY — base rate 80%+ ignore]")

        lines.append("")

    # ── Render in reversibility tiers ────────────────────────────────────────
    # Group by domain within each tier
    for tier_name, tier_items in [
        ("TRIVIAL — DO FIRST", trivial),
        ("MODERATE — DO NEXT", moderate),
        ("DEFER — LOW PRIORITY", defer),
    ]:
        if not tier_items:
            continue

        # Group by domain within tier
        by_domain: dict[str, list[dict]] = {}
        for f in tier_items:
            d = f.get("domain", "other") or "other"
            by_domain.setdefault(d, []).append(f)

        if by_domain:
            lines.append(f"### {tier_name}")
            lines.append("")
            for domain in by_domain.keys():
                render_domain(domain, by_domain[domain])

    # ── Skill suggestions section at bottom ─────────────────────────────────
    if skill_suggestions:
        lines.append("### SUGGESTED SKILLS")
        lines.append("")
        lines.append(
            "  These gaps can be addressed by running the suggested skill:"
        )
        lines.append("")
        for f in skill_suggestions:
            skill_name = f.get("message", "").strip()
            if skill_name:
                lines.append(f"  → {skill_name}")
        lines.append("")

    # ── Footer ─────────────────────────────────────────────────────────────
    lines.append("━" * 64)
    lines.append("")
    total_hours = total_effort_minutes / 60
    if total_hours >= 1:
        effort_summary = f"~{total_hours:.1f}hr"
    else:
        effort_summary = f"~{total_effort_minutes}min"
    lines.append(
        f"0 — Do ALL Recommended Next Actions ({total_items} items, {effort_summary} total)"
    )

    return "\n".join(lines)


def format_rsn_from_gaps(
    gaps: list[dict],
    show_effort: bool = False,
    intent_summary: str = "",
) -> str:
    """
    Format GTO gaps as GTO-native RNS markdown.

    Produces output matching GTO SKILL.md RNS spec:
        ### Domain: {category}
        1.1 [gap_id] [~effort] Description (file:line)

    Does NOT produce a "Recommended Next Steps" header — that is added
    by the orchestrator (format_output).

    Args:
        gaps: List of gap dictionaries from Gap.to_dict() with keys:
            - gap_id: gap identifier
            - severity: CRITICAL/HIGH/MEDIUM/LOW
            - message: description
            - file_path: optional file path
            - line_number: optional line number
            - type: gap type (test_gap, doc_gap, code_quality, import_issue)
            - effort_estimate_minutes: estimated effort
        intent_summary: One-line description of what was analyzed (unused, kept for API compat)

    Returns:
        Formatted RNS markdown string (no "Recommended Next Steps" header)
    """
    # Detect batch groups (gaps sharing same file or root cause)
    rsn_findings = _detect_batch_groups(gaps)

    if not rsn_findings:
        return ""

    # Use GTO-native formatter (not RSNFormatter.render_text which uses wrong format)
    return _format_gto_rsn_markdown(rsn_findings, show_effort=show_effort)
