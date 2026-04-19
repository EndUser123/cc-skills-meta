"""Results Builder - Consolidate and enrich detector outputs.

Priority: P1 (runs during results assembly)
Purpose: Consolidate outputs from detectors with deduplication and enrichment

Features:
- Detector output consolidation
- Gap deduplication (same gap from multiple sources)
- Metadata enrichment (timestamps, file paths, line numbers)
- JSON artifact generation
"""

from __future__ import annotations

import hashlib
import json
import re
import warnings
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any

# False-positive filter constants for consolidate_from_code_markers
_MARKER_KEYWORDS = frozenset({"TODO:", "FIXME:", "HACK:", "XXX:", "NOTE:", "BUG:"})
_REGEX_METACHAR_PREFIXES = ("\\\\", "(.+)", "(?:")
_SHORT_ACTION_ARTICLES = frozenset({"a", "an", "the", "this"})
_TUPLE_SEPARATOR_PAIRS = ('", "', "', '")


def _is_code_marker_false_positive(content: str) -> bool:
    """Return True if content is a false-positive code marker (scanner metadata).

    Filters out:
    - Regex pattern definitions (r"TODO:", r'FIXME:')
    - Regex metacharacter sequences
    - Comment-style pattern definitions in code marker dictionaries
    - Bare keyword searches used in substring scanning
    - Python expression strings from .contains() calls
    - Tuple/list member patterns
    - Short lowercase action phrases from code marker patterns
    """
    stripped = content.lstrip()

    # Regex pattern definitions: r"TODO: ..." or r'FIXME: ...'
    if content.startswith('r"') or content.startswith("r'"):
        return True

    # Regex metacharacter sequences (pattern definitions, not actual TODOs)
    if any(p in content for p in _REGEX_METACHAR_PREFIXES):
        return True

    # Comment-style pattern definitions: "# TODO: add test"
    if stripped.startswith("#") and ("TODO:" in stripped or "FIXME:" in stripped):
        return True

    # Bare keyword searches: "TODO:", "FIXME:", etc. (substring scan artifacts)
    if content.upper() in _MARKER_KEYWORDS:
        return True

    # Python expression strings: '"in content or "FIXME" in content"'
    if ('"' in content or "'" in content) and (
        " in " in content or " or " in content or " and " in content
    ):
        return True

    # Content starting with quote character (Python string, not actual comment)
    if stripped.startswith('"') or stripped.startswith("'"):
        return True

    # Short lowercase action phrases from code marker pattern definitions
    words = content.split()
    if (
        1 <= len(words) <= 3
        and all(w.islower() or w in _SHORT_ACTION_ARTICLES for w in words)
        and len(content) < 20
    ):
        return True

    return False


@dataclass
class Gap:
    """A detected gap or issue."""

    gap_id: str
    type: str
    severity: str
    message: str
    file_path: str | None = None
    line_number: int | None = None
    source: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
    # TASK-009c: Confidence scoring
    confidence: float = 0.8
    # TASK-009d: Effort estimation
    effort_estimate_minutes: int = 5
    # TASK-009e: Theme detection
    theme: str | None = None
    recurrence_count: int = 1
    # Cascade depth annotation (Step 4.5 from pre-mortem)
    cascade_depth: str | None = None  # SHALLOW/MEDIUM/DEEP
    # Operational verification gate (Step 3.8 from pre-mortem)
    verification_required: bool = False  # True for HIGH/CRITICAL gaps needing empirical evidence
    verification_evidence: str | None = None  # What evidence confirmed this gap
    is_verified: bool = False  # True once evidence is provided
    # Advisory enforcement heuristic (pre-mortem advisory rule)
    advisory: bool = False  # True for advisory-only recommendations

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.gap_id,
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "source": self.source,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "effort_estimate_minutes": self.effort_estimate_minutes,
            "theme": self.theme,
            "recurrence_count": self.recurrence_count,
            "cascade_depth": self.cascade_depth,
            "verification_required": self.verification_required,
            "verification_evidence": self.verification_evidence,
            "is_verified": self.is_verified,
            "advisory": self.advisory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Gap:
        """Create from dictionary."""
        return cls(
            gap_id=data.get("id", ""),
            type=data.get("type", ""),
            severity=data.get("severity", "low"),
            message=data.get("message", ""),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            source=data.get("source", "unknown"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 0.8),
            effort_estimate_minutes=data.get("effort_estimate_minutes", 5),
            theme=data.get("theme"),
            recurrence_count=data.get("recurrence_count", 1),
            cascade_depth=data.get("cascade_depth"),
            verification_required=data.get("verification_required", False),
            verification_evidence=data.get("verification_evidence"),
            is_verified=data.get("is_verified", False),
            advisory=data.get("advisory", False),
        )

    def signature(self) -> str:
        """Create unique signature for deduplication.

        Normalizes whitespace to handle semantic equivalents:
        - "foo  bar" and "foo bar" (multiple spaces vs single) → same signature
        - "foo\nbar" and "foo bar" (newline vs space) → same signature
        - "Foo" and "FOO" (case) → same signature
        """
        file_part = self.file_path or ""
        line_part = str(self.line_number) if self.line_number else ""
        # Normalize all whitespace to single space, then lowercase
        message_part = re.sub(r"\s+", " ", self.message).lower().strip()
        sig_content = f"{self.type}:{file_part}:{line_part}:{message_part}"
        return hashlib.md5(sig_content.encode()).hexdigest()


@dataclass
class ConsolidatedResults:
    """Consolidated results from all detectors."""

    gaps: list[Gap]
    total_gap_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "gaps": [gap.to_dict() for gap in self.gaps],
            "total_gap_count": self.total_gap_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class InitialResultsBuilder:
    """
    Consolidate and enrich detector outputs.

    Takes outputs from detectors (TASK-002 through TASK-007) and produces
    consolidated JSON with deduplication and metadata enrichment.
    """

    # Severity order for sorting
    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def __init__(self, project_root: Path | None = None):
        """Initialize results builder.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def _create_gap_id(self, index: int, gap_type: str) -> str:
        """Create unique gap ID.

        Args:
            index: Gap index
            gap_type: Type of gap

        Returns:
            Unique gap ID string
        """
        return f"GAP-{index:04d}-{gap_type.upper()}"

    def _normalize_severity(self, severity: str | None) -> str:
        """Normalize severity to standard values.

        Args:
            severity: Input severity string

        Returns:
            Normalized severity (critical/high/medium/low)

        Raises:
            Warns if severity is unknown and defaults to "medium"
        """
        if not severity:
            warnings.warn("Empty severity provided, defaulting to 'medium'")
            return "medium"

        severity_lower = severity.lower().strip()
        if severity_lower in {"critical", "crit", "c"}:
            return "critical"
        elif severity_lower in {"high", "h", "major", "important"}:
            return "high"
        elif severity_lower in {"medium", "med", "m", "moderate", "warning"}:
            return "medium"
        elif severity_lower in {"low", "l", "minor", "info"}:
            return "low"
        else:
            warnings.warn(f"Unknown severity '{severity}', defaulting to 'medium'")
            return "medium"

    def _deduplicate_gaps(self, gaps: list[Gap]) -> list[Gap]:
        """Remove duplicate gaps based on signature while preserving metadata.

        When duplicates are found, merges metadata from all sources:
        - Combines source information
        - Preserves highest confidence
        - Uses highest severity
        - Aggregates recurrence counts

        Args:
            gaps: List of gaps (may contain duplicates)

        Returns:
            Deduplicated list of gaps with merged metadata
        """
        seen_signatures: dict[str, Gap] = {}
        for gap in gaps:
            sig = gap.signature()
            if sig not in seen_signatures:
                seen_signatures[sig] = gap
            else:
                # Merge metadata from duplicate sources
                existing = seen_signatures[sig]
                # Combine sources (avoid duplicates)
                sources = set(existing.source.split(", ")) if existing.source else set()
                sources.add(gap.source)
                new_source = ", ".join(sorted(sources))
                # Use highest confidence
                new_confidence = max(existing.confidence, gap.confidence)
                # Use highest severity (lower order number = higher severity)
                new_severity = (
                    gap.severity
                    if self.SEVERITY_ORDER.get(gap.severity, 99)
                    < self.SEVERITY_ORDER.get(existing.severity, 99)
                    else existing.severity
                )
                # Aggregate recurrence count
                new_recurrence = max(existing.recurrence_count, gap.recurrence_count)
                # Create new Gap with merged values (avoid in-place mutation)
                seen_signatures[sig] = replace(
                    existing,
                    source=new_source,
                    confidence=new_confidence,
                    severity=new_severity,
                    recurrence_count=new_recurrence,
                )

        return list(seen_signatures.values())

    def _sort_gaps(self, gaps: list[Gap]) -> list[Gap]:
        """Sort gaps by severity and ID.

        Args:
            gaps: List of gaps

        Returns:
            Sorted list of gaps
        """
        return sorted(
            gaps,
            key=lambda g: (
                self.SEVERITY_ORDER.get(g.severity, 99),
                g.gap_id,
            ),
        )

    def _count_by_severity(self, gaps: list[Gap]) -> dict[str, int]:
        """Count gaps by severity level, deduplicating by signature.

        Args:
            gaps: List of gaps

        Returns:
            Dictionary with severity counts
        """
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        seen_signatures: set[str] = set()
        for gap in gaps:
            sig = gap.signature()
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                severity = gap.severity
                if severity in counts:
                    counts[severity] += 1
        return counts

    def consolidate_from_viability_gate(
        self, result: Any, source: str = "ViabilityGate"
    ) -> list[Gap]:
        """Extract gaps from ViabilityGate result.

        Args:
            result: ViabilityGate result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "is_viable") and result.is_viable is False:
            # Viability failed - add critical gap
            gaps.append(
                Gap(
                    gap_id=self._create_gap_id(0, "viability"),
                    type="viability_failure",
                    severity="critical",
                    message="GTO viability check failed - preconditions not met",
                    source=source,
                )
            )
        return gaps

    def consolidate_from_chain_integrity(
        self, result: Any, source: str = "ChainIntegrityChecker"
    ) -> list[Gap]:
        """Extract gaps from ChainIntegrityChecker result.

        Args:
            result: ChainIntegrityChecker result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "issues"):
            for idx, issue in enumerate(result.issues):
                # result.issues is a list of warning strings (not objects with .message)
                # Use the string directly as the message
                issue_str = str(issue) if issue is not None else "Unknown chain integrity issue"
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "chain_integrity"),
                        type="chain_integrity_issue",
                        severity=self._normalize_severity("medium"),
                        message=issue_str,
                        source=source,
                    )
                )
        return gaps

    def consolidate_from_session_goal(
        self, result: Any, source: str = "SessionGoalDetector"
    ) -> list[Gap]:
        """Extract gaps from SessionGoalDetector result.

        Args:
            result: SessionGoalDetector result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        # Only create gap if goal was sought but confidence is low
        # confidence == 0.0 means no transcript or no goal found - not a project gap
        if hasattr(result, "confidence") and 0.0 < result.confidence < 0.5:
            gaps.append(
                Gap(
                    gap_id=self._create_gap_id(0, "session_goal"),
                    type="low_confidence_goal",
                    severity="medium",
                    message=f"Low confidence session goal detection (confidence: {result.confidence:.2f})",
                    source=source,
                    metadata={"confidence": result.confidence},
                )
            )
        return gaps

    def consolidate_from_unfinished_business(
        self, result: Any, source: str = "UnfinishedBusinessDetector"
    ) -> list[Gap]:
        """Extract gaps from UnfinishedBusinessDetector result.

        Args:
            result: UnfinishedBusinessDetector result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "items"):
            for idx, item in enumerate(result.items):
                content = getattr(item, "content", None) or ""
                if not content.strip():
                    continue  # Skip items with empty content
                category = getattr(item, "category", "unknown")
                confidence = getattr(item, "confidence", 0.5)
                # Map category to severity
                severity_map = {"task": "medium", "question": "low", "deferred": "low"}
                severity = severity_map.get(category, "medium")
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "unfinished"),
                        type="unfinished_business",
                        severity=severity,
                        message=f"[{category}] {content[:100]}",
                        file_path=None,
                        source=source,
                        confidence=confidence,
                    )
                )
        return gaps

    def consolidate_from_task_list(
        self, result: Any, source: str = "TaskListGapDetector"
    ) -> list[Gap]:
        """Extract gaps from TaskListGapDetector result.

        Args:
            result: TaskListGapDetector result (TaskListGapResult with dicts)
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if not hasattr(result, "gaps"):
            return gaps
        for idx, gap_dict in enumerate(result.gaps):
            if not isinstance(gap_dict, dict):
                continue
            # Use custom gap_id if it starts with "tasklist-"
            if gap_dict.get("gap_id", "").startswith("tasklist-"):
                final_gap_id = gap_dict["gap_id"]
            else:
                final_gap_id = self._create_gap_id(idx, gap_dict.get("type", "task_list"))
            gaps.append(
                Gap(
                    gap_id=final_gap_id,
                    type=gap_dict.get("type", "task_list_gap"),
                    severity=gap_dict.get("severity", "medium"),
                    message=gap_dict.get("message", "Pending task from shared task list"),
                    file_path=gap_dict.get("file_path"),
                    line_number=gap_dict.get("line_number"),
                    source=source,
                    confidence=gap_dict.get("confidence", 0.95),
                    effort_estimate_minutes=gap_dict.get("effort_estimate_minutes", 30),
                )
            )
        return gaps

    def consolidate_from_session_outcomes(
        self, result: Any, source: str = "SessionOutcomeDetector"
    ) -> list[Gap]:
        """Extract gaps from SessionOutcomeDetector result.

        Args:
            result: SessionOutcomeDetector result (SessionOutcomeResult with to_gaps())
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if not hasattr(result, "to_gaps"):
            return gaps
        for gap_dict in result.to_gaps():
            if not isinstance(gap_dict, dict):
                continue
            gaps.append(
                Gap(
                    gap_id=gap_dict.get("gap_id", self._create_gap_id(0, "session_outcome")),
                    type=gap_dict.get("type", "session_outcome"),
                    severity=gap_dict.get("severity", "medium"),
                    message=gap_dict.get("message", "Unresolved session outcome"),
                    file_path=gap_dict.get("file_path"),
                    line_number=gap_dict.get("line_number"),
                    source=source,
                    confidence=gap_dict.get("confidence", 0.85),
                    effort_estimate_minutes=gap_dict.get("effort_estimate_minutes", 30),
                )
            )
        return gaps

    def consolidate_from_suspicion(
        self, result: Any, source: str = "SuspicionDetector"
    ) -> list[Gap]:
        """Extract gaps from SuspicionDetector result.

        Args:
            result: SuspicionDetector result (SuspicionResult with to_gaps())
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if not hasattr(result, "to_gaps"):
            return gaps
        for gap_dict in result.to_gaps():
            if not isinstance(gap_dict, dict):
                continue
            gaps.append(
                Gap(
                    gap_id=gap_dict.get("gap_id", self._create_gap_id(0, "suspicion")),
                    type=gap_dict.get("type", "suspicion"),
                    severity=gap_dict.get("severity", "medium"),
                    message=gap_dict.get("message", "Suspicious pattern detected"),
                    file_path=gap_dict.get("file_path"),
                    line_number=gap_dict.get("line_number"),
                    source=source,
                    confidence=gap_dict.get("confidence", 0.85),
                    effort_estimate_minutes=gap_dict.get("effort_estimate_minutes", 30),
                )
            )
        return gaps

    def consolidate_from_code_markers(
        self, result: Any, source: str = "CodeMarkerScanner"
    ) -> list[Gap]:
        """Extract gaps from CodeMarkerScanner result.

        Args:
            result: CodeMarkerScanner result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "markers"):
            for idx, marker in enumerate(result.markers):
                content = getattr(marker, "content", "") or ""

                # Filter false positives using centralized predicate
                if _is_code_marker_false_positive(content):
                    continue

                marker_type = getattr(marker, "type", "unknown")
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "code_marker"),
                        type="code_marker",
                        severity=self._normalize_severity(getattr(marker, "severity", "low")),
                        message=f"Code marker found: {marker_type}",
                        file_path=getattr(marker, "file_path", None),
                        line_number=getattr(marker, "line_number", None),
                        source=source,
                        metadata={"marker_type": marker_type},
                    )
                )
        return gaps

    def consolidate_from_test_presence(
        self, result: Any, source: str = "TestPresenceChecker"
    ) -> list[Gap]:
        """Extract gaps from TestPresenceChecker result.

        Args:
            result: TestPresenceChecker result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "gaps"):
            for idx, gap in enumerate(result.gaps):
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "test"),
                        type="missing_test",
                        severity="high",
                        message=f"Missing test for {getattr(gap, 'module_path', 'unknown module')} — expected {getattr(gap, 'expected_test_path', 'unknown path')}",
                        file_path=getattr(gap, "file_path", None),
                        source=source,
                    )
                )
        return gaps

    def consolidate_from_docs_presence(
        self, result: Any, source: str = "DocsPresenceChecker"
    ) -> list[Gap]:
        """Extract gaps from DocsPresenceChecker result.

        Args:
            result: DocsPresenceChecker result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "gaps"):
            for idx, gap in enumerate(result.gaps):
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "docs"),
                        type="missing_docs",
                        severity="medium",
                        message=f"Missing documentation for {getattr(gap, 'module_path', 'unknown module')}",
                        file_path=getattr(gap, "module_path", None),
                        source=source,
                    )
                )
        return gaps

    def consolidate_from_dependencies(
        self, result: Any, source: str = "DependencyChecker"
    ) -> list[Gap]:
        """Extract gaps from DependencyChecker result.

        Args:
            result: DependencyChecker result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "issues"):
            for idx, issue in enumerate(result.issues):
                issue_type = getattr(issue, "issue_type", "unknown")
                severity_map = {
                    "vulnerable": "critical",
                    "outdated": "medium",
                    "missing": "high",
                    "unused": "low",
                }
                severity = severity_map.get(issue_type, "medium")
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "dependency"),
                        type=f"dependency_{issue_type}",
                        severity=severity,
                        message=getattr(issue, "description", f"Dependency issue: {issue_type}"),
                        source=source,
                        metadata={
                            "package_name": getattr(issue, "package_name", ""),
                            "current_version": getattr(issue, "current_version", ""),
                            "latest_version": getattr(issue, "latest_version", ""),
                        },
                    )
                )
        return gaps

    def consolidate_from_entry_points(
        self, result: Any, source: str = "EntryPointChecker"
    ) -> list[Gap]:
        """Extract gaps from EntryPointChecker result.

        Args:
            result: EntryPointChecker result object
            source: Source name

        Returns:
            List of gaps
        """
        gaps = []
        if hasattr(result, "gaps"):
            for idx, gap in enumerate(result.gaps):
                gaps.append(
                    Gap(
                        gap_id=self._create_gap_id(idx, "entry_point"),
                        type="entry_point_mismatch",
                        severity="high",
                        message=f"Missing entry point: {getattr(gap, 'referenced_path', 'unknown path')}",
                        file_path=getattr(gap, "resolved_path", None),
                        line_number=getattr(gap, "line_number", None),
                        source=source,
                        metadata={
                            "referenced_path": getattr(gap, "referenced_path", ""),
                            "resolved_path": getattr(gap, "resolved_path", ""),
                            "context": getattr(gap, "context", ""),
                        },
                    )
                )
        return gaps

    # Dispatch table: detector_name -> consolidation method
    _DETECTOR_DISPATCH: dict[str, str] = {
        "viability_gate": "consolidate_from_viability_gate",
        "chain_integrity": "consolidate_from_chain_integrity",
        "session_goal": "consolidate_from_session_goal",
        "unfinished_business": "consolidate_from_unfinished_business",
        "entry_points": "consolidate_from_entry_points",
        "task_list": "consolidate_from_task_list",
        "session_outcomes": "consolidate_from_session_outcomes",
        "suspicion": "consolidate_from_suspicion",
    }

    def build(self, detector_results: dict[str, Any]) -> ConsolidatedResults:
        """
        Build consolidated results from all detector outputs.

        Args:
            detector_results: Dictionary mapping detector names to their results

        Returns:
            ConsolidatedResults with all gaps consolidated and enriched
        """
        all_gaps: list[Gap] = []

        # Extract gaps from each detector using dispatch table
        for detector_name, result in detector_results.items():
            if result is None:
                continue

            method_name = self._DETECTOR_DISPATCH.get(detector_name)
            if method_name is not None:
                method = getattr(self, method_name, None)
                if method is not None:
                    all_gaps.extend(method(result))

        # Deduplicate gaps
        deduplicated_gaps = self._deduplicate_gaps(all_gaps)

        # TASK-009c: Apply confidence scoring
        scored_gaps = self._apply_confidence_scoring(deduplicated_gaps)

        # TASK-009d: Apply effort estimation
        effort_enriched_gaps = self._apply_effort_estimation(scored_gaps)

        # TASK-009e: Apply theme detection
        themed_gaps = self._apply_theme_detection(effort_enriched_gaps)

        # Cascade depth annotation (Step 4.5 from pre-mortem)
        cascade_annotated_gaps = self._apply_cascade_depth(themed_gaps)

        # Advisory enforcement heuristic (pre-mortem Step 3.6 advisory rule)
        advisory_marked_gaps = self._apply_advisory_heuristic(cascade_annotated_gaps)

        # Sort gaps by severity and ID
        sorted_gaps = self._sort_gaps(advisory_marked_gaps)

        # Count by severity
        severity_counts = self._count_by_severity(sorted_gaps)

        return ConsolidatedResults(
            gaps=sorted_gaps,
            total_gap_count=len(sorted_gaps),
            critical_count=severity_counts["critical"],
            high_count=severity_counts["high"],
            medium_count=severity_counts["medium"],
            low_count=severity_counts["low"],
            metadata={
                "project_root": str(self.project_root),
                "detector_count": len(detector_results),
                "raw_gap_count": len(all_gaps),
                "deduplicated_count": len(sorted_gaps),
                "duplicates_removed": len(all_gaps) - len(sorted_gaps),
            },
        )

    # TASK-009c: Confidence Scoring
    def _apply_confidence_scoring(self, gaps: list[Gap]) -> list[Gap]:
        """Apply confidence scoring based on gap characteristics.

        Args:
            gaps: List of gaps to score

        Returns:
            Gaps with confidence scores applied
        """
        result_gaps = []
        for gap in gaps:
            base_confidence = 0.8  # Default confidence

            # Higher confidence for file-specific gaps
            if gap.file_path:
                base_confidence += 0.1

            # Higher confidence for gaps with line numbers
            if gap.line_number:
                base_confidence += 0.05

            # Lower confidence for generic gap types
            if gap.type in {"code_marker", "session_goal"}:
                base_confidence -= 0.15

            # Higher confidence for dependency issues
            if gap.type.startswith("dependency_"):
                base_confidence += 0.1

            # Clamp to valid range and create new Gap (avoid in-place mutation)
            new_confidence = max(0.0, min(1.0, base_confidence))
            result_gaps.append(replace(gap, confidence=new_confidence))

        return result_gaps

    # TASK-009d: Effort Estimation
    def _apply_effort_estimation(self, gaps: list[Gap]) -> list[Gap]:
        """Apply effort estimation based on gap type and severity.

        Args:
            gaps: List of gaps to estimate

        Returns:
            Gaps with effort estimates applied
        """
        effort_map = {
            # Critical issues take longer
            "viability_failure": 60,
            "chain_integrity_issue": 30,
            "dependency_vulnerable": 45,
            # Missing tests/docs
            "missing_test": 15,
            "missing_docs": 10,
            # Unfinished business
            "unfinished_business": 20,
            # Code markers (quick fixes)
            "code_marker": 5,
            # Dependencies
            "dependency_outdated": 10,
            "dependency_missing": 15,
            "dependency_unused": 5,
            # Session goal detection
            "low_confidence_goal": 10,
            # Entry points
            "entry_point_mismatch": 15,
        }

        severity_multiplier = {
            "critical": 2.0,
            "high": 1.5,
            "medium": 1.0,
            "low": 0.5,
        }

        result_gaps = []
        for gap in gaps:
            base_effort = effort_map.get(gap.type, 10)  # Default 10 minutes
            multiplier = severity_multiplier.get(gap.severity, 1.0)
            new_effort = int(base_effort * multiplier)
            result_gaps.append(replace(gap, effort_estimate_minutes=new_effort))

        return result_gaps

    # TASK-009e: Cross-Session Theme Detection
    def _apply_theme_detection(self, gaps: list[Gap]) -> list[Gap]:
        """Apply theme detection based on gap patterns.

        Args:
            gaps: List of gaps to analyze

        Returns:
            Gaps with theme labels applied
        """
        # Define theme keywords
        theme_keywords = {
            "testing": ["test", "pytest", "coverage", "assert"],
            "documentation": ["doc", "readme", "comment", "api"],
            "dependencies": ["import", "package", "module", "dependency"],
            "code_quality": ["refactor", "clean", "format", "lint"],
            "architecture": ["structure", "design", "pattern", "layer"],
            "git": ["commit", "push", "branch", "merge"],
            "security": ["vulnerability", "exploit", "security", "auth"],
        }

        result_gaps = []
        for gap in gaps:
            message_lower = gap.message.lower()
            type_lower = gap.type.lower()

            # Check for theme matches
            detected_theme = None
            for theme, keywords in theme_keywords.items():
                if any(keyword in message_lower or keyword in type_lower for keyword in keywords):
                    detected_theme = theme
                    break

            result_gaps.append(replace(gap, theme=detected_theme))

        return result_gaps

    # Cascade depth: pre-mortem Step 4.5
    def _apply_cascade_depth(self, gaps: list[Gap]) -> list[Gap]:
        """Annotate gaps with cascade depth.

        For HIGH/CRITICAL gaps, traces 'and then what?' chains to determine
        cascade depth:
        - SHALLOW (1-2 steps): Localized failure, easy recovery
        - MEDIUM (3-4 steps): Affects multiple subsystems
        - DEEP (5+ steps): System-wide collapse

        Uses a rule-based knowledge base of known cascade patterns
        derived from pre-mortem second-order effects methodology.

        Args:
            gaps: List of gaps to analyze

        Returns:
            Gaps with cascade_depth annotated
        """
        # Knowledge base: gap type → typical cascade depth
        # Higher values = more systemic the gap type is
        CASCADE_POTENTIAL: dict[str, int] = {
            # Critical path failures are DEEP
            "viability_failure": 5,
            "dependency_vulnerable": 5,
            "entry_point_mismatch": 4,
            # High severity gaps get boost
            "missing_dependency": 4,
            "import_error": 3,
            "test_failure": 3,
            "missing_test": 2,
            # Medium severity
            "missing_docs": 2,
            "dependency_outdated": 2,
            "low_confidence_goal": 1,
            "unfinished_business": 1,
            # Low severity
            "code_marker": 1,
            "dependency_unused": 1,
        }

        def _classify_depth(potential: int) -> str:
            if potential >= 5:
                return "DEEP"
            elif potential >= 3:
                return "MEDIUM"
            return "SHALLOW"

        def _estimate_cascade_steps(gap: Gap) -> int:
            """Estimate cascade depth for a gap."""
            base = CASCADE_POTENTIAL.get(gap.type, 2)

            # Severity multiplier
            sev_mult = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5}
            mult = sev_mult.get(gap.severity, 1.0)

            # Core infrastructure gaps cascade further
            infra_boost = 0
            if gap.file_path:
                fp = gap.file_path.lower()
                if any(k in fp for k in ("orchestrator", "state_manager", "results_builder")):
                    infra_boost = 2
                elif any(k in fp for k in ("lib/", "__lib/", "hooks/", "subagents/")):
                    infra_boost = 1

            # Skill self-analysis gaps are deeper (they affect GTO itself)
            if "gto" in (gap.source or "").lower():
                infra_boost += 1

            return int(base * mult + infra_boost)

        result_gaps = []
        for gap in gaps:
            if gap.severity not in ("critical", "high"):
                result_gaps.append(gap)
                continue

            steps = _estimate_cascade_steps(gap)
            depth = _classify_depth(steps)

            # Also mark as verification-required for DEEP cascades
            # (these need empirical evidence, not just speculation)
            needs_verification = depth == "DEEP" and not gap.is_verified

            annotated = replace(
                gap,
                cascade_depth=depth,
                verification_required=gap.verification_required or needs_verification,
            )
            result_gaps.append(annotated)

        return result_gaps

    # Advisory enforcement heuristic: pre-mortem Step 3.6
    def _apply_advisory_heuristic(self, gaps: list[Gap]) -> list[Gap]:
        """Mark gaps that are advisory-only with weak enforcement.

        Advisory enforcement has ~80% ignore base rate. When a recommended
        mitigation is advisory-only (not blocking), boost risk score by +2
        and annotate with advisory=True so users know the enforcement is weak.

        Advisory gap types:
        - skill_coverage: Running a skill is a suggestion, not a requirement
        - session_goal: Low-confidence goal detection is informational
        - improvements: Process suggestions are advisory
        - skill_suggestion: Explicit skill recommendations

        Args:
            gaps: List of gaps to annotate

        Returns:
            Gaps with advisory flag set for weak-enforcement items
        """
        ADVISORY_TYPES = {
            "skill_coverage",
            "skill_suggestion",
            "session_goal",
            "low_confidence_goal",
            "improvement_gap",
            "improvement_investigation",
            "process_gap",
        }

        result_gaps = []
        for gap in gaps:
            is_advisory = gap.type in ADVISORY_TYPES or (
                gap.metadata.get("action_type") in ("Use /skill", "Run skill", "Manual")
                and gap.severity not in ("critical", "high")
            )

            if is_advisory and not gap.advisory:
                annotated = replace(gap, advisory=True)
                result_gaps.append(annotated)
            else:
                result_gaps.append(gap)

        return result_gaps

    def to_json(self, results: ConsolidatedResults, output_path: Path) -> None:
        """Write consolidated results to JSON file.

        Args:
            results: ConsolidatedResults to write
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results.to_dict(), f, indent=2)


# Convenience function
def build_initial_results(
    detector_results: dict[str, Any],
    project_root: Path | None = None,
) -> ConsolidatedResults:
    """
    Quick initial results build.

    Args:
        detector_results: Dictionary mapping detector names to their results
        project_root: Project root directory

    Returns:
        ConsolidatedResults with all gaps consolidated
    """
    builder = InitialResultsBuilder(project_root)
    return builder.build(detector_results)
