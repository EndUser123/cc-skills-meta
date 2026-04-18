"""GTO v3 internal library.

This module contains the core deterministic components for GTO analysis.
"""

from __future__ import annotations

__all__ = [
    "AdjacentFileScanner",
    "AdjacentScanResult",
    "TouchedFile",
    "scan_adjacent_files",
    "ViabilityGate",
    "check_viability",
    "GitContext",
    "detect_git_context",
    "SkillSelfHealthChecker",
    "check_skill_health",
    "ChainIntegrityChecker",
    "check_chain_integrity",
    "SessionGoalDetector",
    "detect_session_goal",
    "SessionGoalResult",
    "ChainIntegrityResult",
    "UnfinishedBusinessDetector",
    "detect_unfinished_business",
    "UnfinishedBusinessResult",
    "UnfinishedItem",
    "SessionOutcomeDetector",
    "detect_session_outcomes",
    "SessionOutcomeResult",
    "SessionOutcomeItem",
    "SuspicionDetector",
    "detect_suspicion",
    "SuspicionResult",
    "SuspicionItem",
    "CodeMarkerScanner",
    "scan_code_markers",
    "CodeMarkerResult",
    "CodeMarker",
    "TestPresenceChecker",
    "check_test_presence",
    "TestPresenceResult",
    "TestGap",
    "DocsPresenceChecker",
    "check_docs_presence",
    "DocPresenceResult",
    "DocGap",
    "DependencyChecker",
    "check_dependencies",
    "DependencyResult",
    "DependencyIssue",
    "NextStepsFormatter",
    "format_recommended_next_steps",
    "NextStep",
    "FormattedNextSteps",
    "StateManager",
    "StateFile",
    "get_state_manager",
    "Gap",
    "ConsolidatedResults",
    "InitialResultsBuilder",
    "build_initial_results",
    # Subagents
    "GapFinding",
    "HealthCalculatorSubagent",
    "calculate_health",
    "HealthMetric",
    "HealthReport",
    # Self-health detector
    "SelfHealthFinding",
    "SelfHealthResult",
    "HealthMetrics",
    "HealthTrend",
    "detect_gto_self_health",
    "check_gto_self_health",
    # Task list gap detector
    "TaskListGapDetector",
    "TaskListGapResult",
    "detect_task_list_gaps",
    # Gap resolution tracker
    "ResolutionResult",
    "track_gap_resolutions",
    "get_gap_decay_metrics",
]

# Import subagents - handle both package and direct import
try:
    from ..subagents import (
        GapFinding,
        HealthCalculatorSubagent,
        HealthMetric,
        HealthReport,
        calculate_health,
    )
except ImportError:
    # When imported directly (e.g., in tests), import from subagents
    from subagents import (
        GapFinding,
        HealthCalculatorSubagent,
        HealthMetric,
        HealthReport,
        calculate_health,
    )
from .chain_integrity_checker import (
    ChainIntegrityChecker,
    ChainIntegrityResult,
    check_chain_integrity,
)
from .adjacent_file_scanner import (
    AdjacentFileScanner,
    AdjacentScanResult,
    TouchedFile,
    scan_adjacent_files,
)
try:
    from .code_marker_scanner import (
        CodeMarker,
        CodeMarkerResult,
        CodeMarkerScanner,
        scan_code_markers,
    )
except ImportError:
    # scanners.base not available (e.g. _shared package missing)
    # Gracefully degrade so other detectors remain importable
    CodeMarker = None  # type: ignore[assignment]
    CodeMarkerResult = None  # type: ignore[assignment]
    CodeMarkerScanner = None  # type: ignore[assignment]
    scan_code_markers = None  # type: ignore[assignment]
from .dependency_checker import (
    DependencyChecker,
    DependencyIssue,
    DependencyResult,
    check_dependencies,
)
from .docs_presence_checker import (
    DocGap,
    DocPresenceResult,
    DocsPresenceChecker,
    check_docs_presence,
)
from .entry_point_checker import (
    EntryPointChecker,
    EntryPointGap,
    EntryPointResult,
    check_entry_points,
)
from .gap_resolution_tracker import (
    ResolutionResult,
    get_gap_decay_metrics,
    track_gap_resolutions,
)
from .git_context import (
    GitContext,
    detect_git_context,
)
from .gto_self_health_detector import (
    HealthMetrics,
    HealthTrend,
    SelfHealthFinding,
    SelfHealthResult,
    check_gto_self_health,
    detect_gto_self_health,
)
from .next_steps_formatter import (
    FormattedNextSteps,
    NextStep,
    NextStepsFormatter,
    format_recommended_next_steps,
    format_rsn_from_gaps,
)
from .results_builder import (
    ConsolidatedResults,
    Gap,
    InitialResultsBuilder,
    build_initial_results,
)
from .session_goal_detector import (
    SessionGoalDetector,
    SessionGoalResult,
    detect_session_goal,
)
from .session_outcome_detector import (
    SessionOutcomeDetector,
    SessionOutcomeItem,
    SessionOutcomeResult,
    detect_session_outcomes,
)
from .skill_self_health_checker import (
    SkillSelfHealthChecker,
    check_skill_health,
)
from .state_manager import (
    StateFile,
    StateManager,
    get_state_manager,
)
from .suspicion_detector import (
    SuspicionDetector,
    SuspicionItem,
    SuspicionResult,
    detect_suspicion,
)
from .task_list_gap_detector import (
    TaskListGapDetector,
    TaskListGapResult,
    detect_task_list_gaps,
)
from .test_presence_checker import (
    TestGap,
    TestPresenceChecker,
    TestPresenceResult,
    check_test_presence,
)
from .unfinished_business_detector import (
    UnfinishedBusinessDetector,
    UnfinishedBusinessResult,
    UnfinishedItem,
    detect_unfinished_business,
)
from .viability_gate import ViabilityGate, check_viability
