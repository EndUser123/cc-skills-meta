"""GTO Self-Health Detector - Track GTO's own performance metrics over time.

Priority: P1 (runs during RNS formatting, not gap detection)
Purpose: Surface GTO's own operational health as findings

What it tracks:
1. Gaps-per-run trend (is gap count increasing/decreasing?)
2. Severity distribution shift (more HIGH severity over time?)
3. Recommendation acceptance rate (did users act on skill suggestions?)
4. False-positive rate (gaps that appeared then disappeared without skill run)

This is NOT the same as SkillSelfHealthChecker (which checks infrastructure).
This detector tracks whether GTO itself is generating useful vs noisy findings.

Health metrics log format (~/.claude/.evidence/gto-self-health/{terminal_id}.jsonl):
    {"timestamp": "...", "gap_count": 12, "high_severity_count": 3,
     "acceptance_rate": 0.45, "false_positive_rate": 0.2, "total_runs": 10}
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# ── Health thresholds ────────────────────────────────────────────────────────────

TREND_WINDOW = 5  # Number of runs to compare for trend
GAP_TREND_THRESHOLD = 0.20  # 20% increase → HIGH warning
ACCEPTANCE_RATE_LOW = 0.20  # <20% → HIGH
ACCEPTANCE_RATE_MEDIUM = 0.40  # <40% → MEDIUM
FALSE_POSITIVE_HIGH = 0.50  # >50% false positives → HIGH
SEVERITY_SHIFT_THRESHOLD = 0.15  # 15% shift toward HIGH → MEDIUM


# ── Data classes ────────────────────────────────────────────────────────────────


@dataclass
class HealthMetrics:
    """Snapshot of GTO health metrics for one run."""

    timestamp: str
    gap_count: int
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    acceptance_rate: float  # Fraction of recommendations that led to skill usage
    false_positive_rate: float  # Fraction of gaps that appeared then disappeared
    total_runs: int  # Total runs in history


@dataclass
class HealthTrend:
    """Computed trend from rolling window analysis."""

    gap_trend: Literal["improving", "stable", "worsening", "unknown"]
    gap_trend_pct: float
    severity_trend: Literal["improving", "stable", "worsening", "unknown"]
    severity_shift_pct: float
    acceptance_trend: Literal["improving", "stable", "worsening", "unknown"]
    false_positive_trend: Literal["improving", "stable", "worsening", "unknown"]


@dataclass
class SelfHealthFinding:
    """A single health finding from GTO self-analysis."""

    finding_id: str
    severity: Literal["high", "medium", "low"]
    metric: str
    message: str
    current_value: float
    threshold: float
    trend: str
    recommendation: str


@dataclass
class SelfHealthResult:
    """Result of GTO self-health detection."""

    metrics: HealthMetrics | None
    trend: HealthTrend
    findings: list[SelfHealthFinding]
    is_healthy: bool
    total_runs_analyzed: int


# ── Path management ───────────────────────────────────────────────────────────


def _get_health_log_path(terminal_id: str) -> Path:
    """Get path to the health metrics log for a terminal."""
    return Path.home() / ".evidence" / "gto-self-health" / f"{terminal_id}.jsonl"


def _get_history_path(project_root: Path | str, terminal_id: str) -> Path:
    """Get path to GTO history for a terminal."""
    return Path(project_root) / ".evidence" / f"gto-history-{terminal_id}.jsonl"


def _get_skill_usage_path(project_root: Path | str) -> Path:
    """Get path to shared skill usage log."""
    return Path(project_root) / ".evidence" / "skill-usage.jsonl"


# ── Core computation ────────────────────────────────────────────────────────────


def _load_history(project_root: Path | str, terminal_id: str, last_n: int = 20) -> list[dict]:
    """Load recent GTO run history."""
    history_path = _get_history_path(project_root, terminal_id)
    if not history_path.exists():
        return []

    entries = []
    try:
        with open(history_path) as f:
            lines = f.readlines()
        # Read last N entries (most recent first in file)
        for line in reversed(lines[-last_n:]):
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass

    return entries


def _load_skill_usage(project_root: Path | str, last_n: int = 50) -> list[dict]:
    """Load recent skill usage entries."""
    usage_path = _get_skill_usage_path(project_root)
    if not usage_path.exists():
        return []

    entries = []
    try:
        with open(usage_path) as f:
            lines = f.readlines()
        for line in reversed(lines[-last_n:]):
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass

    return entries


def _compute_gap_trend(
    history: list[dict],
) -> tuple[Literal["improving", "stable", "worsening", "unknown"], float]:
    """Compute gap count trend over rolling window.

    Returns: (trend_direction, percent_change)
    """
    # Require minimum 4 entries for symmetric 2-vs-2 window trend
    if len(history) < 4:
        return "unknown", 0.0

    # Extract gap counts
    gap_counts = [h.get("gap_count", 0) for h in history[-TREND_WINDOW:]]
    if len(gap_counts) < 4:
        return "unknown", 0.0

    recent_avg = sum(gap_counts[-2:]) / 2
    prior_avg = sum(gap_counts[-4:-2]) / 2

    if prior_avg == 0:
        return "unknown", 0.0

    pct_change = (recent_avg - prior_avg) / prior_avg

    if pct_change < -GAP_TREND_THRESHOLD:
        return "improving", pct_change
    elif pct_change > GAP_TREND_THRESHOLD:
        return "worsening", pct_change
    else:
        return "stable", pct_change


def _compute_severity_trend(
    history: list[dict],
) -> tuple[Literal["improving", "stable", "worsening", "unknown"], float]:
    """Compute severity distribution shift over rolling window.

    Returns: (trend_direction, high_severity_shift_pct)
    """
    if len(history) < 2:
        return "unknown", 0.0

    def high_ratio(h: dict) -> float:
        total = h.get("gap_count", 0)
        if total == 0:
            return 0.0
        high = h.get("high_severity_count", 0)
        return high / total

    recent = [high_ratio(h) for h in history[-2:]]
    prior = (
        [high_ratio(h) for h in history[-4:-2]]
        if len(history) >= 4
        else [high_ratio(h) for h in history[:-2]]
    )

    recent_avg = sum(recent) / len(recent)
    prior_avg = sum(prior) / len(prior)

    shift = recent_avg - prior_avg

    if shift < -SEVERITY_SHIFT_THRESHOLD:
        return "improving", shift
    elif shift > SEVERITY_SHIFT_THRESHOLD:
        return "worsening", shift
    else:
        return "stable", shift


def _compute_acceptance_rate(usage_entries: list[dict], recommendations_given: int) -> float:
    """Compute recommendation acceptance rate.

    acceptance_rate = skills actually run / recommendations given
    """
    if recommendations_given == 0:
        return 1.0  # No recommendations = no failures

    # Count unique skills that were run
    skills_run = set()
    for entry in usage_entries:
        skill = entry.get("skill", "")
        if skill:
            skills_run.add(skill)

    # This is approximate - we don't know which specific recommendations led to usage
    # Use a proxy: if any skill was run on the target, count as accepted
    accepted = len(skills_run)
    return min(accepted / recommendations_given, 1.0)


def _compute_false_positive_rate(
    history: list[dict],
) -> tuple[float, Literal["improving", "stable", "worsening", "unknown"]]:
    """Compute false positive rate from history.

    False positive = gap appeared but was never resolved across consecutive runs.
    We approximate by looking at gap_count fluctuations without corresponding skill usage.
    """
    if len(history) < 3:
        return 0.0, "unknown"

    # Gaps that appeared and disappeared quickly without skill usage
    # Proxy: if gap_count drops significantly between runs, some were "resolved"
    # If it rises significantly, we may have false new positives

    fluctuations = []
    for i in range(1, min(len(history), 6)):
        prev = history[-i].get("gap_count", 0)
        curr = history[-i - 1].get("gap_count", 0)
        if prev > 0:
            fluctuation = abs(curr - prev) / prev
            fluctuations.append(fluctuation)

    if not fluctuations:
        return 0.0, "stable"

    avg_fluctuation = sum(fluctuations) / len(fluctuations)

    # High fluctuation (>40%) suggests noise
    if avg_fluctuation > 0.4:
        trend = "worsening"
    elif avg_fluctuation > 0.2:
        trend = "stable"
    else:
        trend = "improving"

    # Cap at reasonable false positive rate
    return min(avg_fluctuation / 2, 1.0), trend


def _build_health_metrics(history: list[dict], usage: list[dict], total_runs: int) -> HealthMetrics:
    """Build health metrics snapshot from loaded data."""
    latest = history[0] if history else {}

    # Severity breakdown (from history entries or estimated from gap_count)
    high = latest.get("high_severity_count", 0)
    medium = latest.get("medium_severity_count", 0)
    low = latest.get("low_severity_count", 0)
    gap_count = latest.get("gap_count", 0)

    # If severity breakdown not in history, estimate from gap_count
    if high == 0 and medium == 0 and low == 0 and gap_count > 0:
        high = max(1, int(gap_count * 0.2))
        medium = max(1, int(gap_count * 0.3))
        low = gap_count - high - medium

    acceptance = _compute_acceptance_rate(usage, gap_count) if gap_count > 0 else 1.0
    fp_rate, _ = _compute_false_positive_rate(history)

    return HealthMetrics(
        timestamp=datetime.now().isoformat(),
        gap_count=gap_count,
        high_severity_count=high,
        medium_severity_count=medium,
        low_severity_count=low,
        acceptance_rate=acceptance,
        false_positive_rate=fp_rate,
        total_runs=total_runs,
    )


# ── Finding generation ─────────────────────────────────────────────────────────


def _generate_findings(
    metrics: HealthMetrics, trend: HealthTrend, total_runs: int
) -> list[SelfHealthFinding]:
    """Generate health findings from computed metrics and trends."""
    findings: list[SelfHealthFinding] = []

    # 1. Gap count trend finding
    if trend.gap_trend == "worsening":
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-GAP-TREND",
                severity="high",
                metric="gap_trend",
                message=f"Gap count is increasing ({trend.gap_trend_pct:+.0%} over recent runs). GTO may be generating more findings than it resolves.",
                current_value=trend.gap_trend_pct,
                threshold=GAP_TREND_THRESHOLD,
                trend="worsening",
                recommendation="Review recent GTO runs: are gaps legitimate? Could detector thresholds be too sensitive?",
            )
        )
    elif trend.gap_trend == "improving" and total_runs >= 5:
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-GAP-IMPROVING",
                severity="low",
                metric="gap_trend",
                message=f"Gap count is decreasing ({trend.gap_trend_pct:+.0%}). Good progress resolving findings.",
                current_value=trend.gap_trend_pct,
                threshold=GAP_TREND_THRESHOLD,
                trend="improving",
                recommendation="Continue current practices.",
            )
        )

    # 2. Severity shift finding
    if trend.severity_trend == "worsening":
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-SEVERITY-SHIFT",
                severity="medium",
                metric="severity_shift",
                message=f"HIGH severity gap ratio is increasing ({trend.severity_shift_pct:+.0%}). More critical issues being surfaced.",
                current_value=trend.severity_shift_pct,
                threshold=SEVERITY_SHIFT_THRESHOLD,
                trend="worsening",
                recommendation="Prioritize resolving HIGH severity gaps first. Check if detectors are correctly calibrated.",
            )
        )

    # 3. Acceptance rate finding
    if metrics.acceptance_rate < ACCEPTANCE_RATE_LOW:
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-ACCEPTANCE-LOW",
                severity="high",
                metric="acceptance_rate",
                message=f"Skill recommendation acceptance rate is very low ({metrics.acceptance_rate:.0%}). Users are not acting on suggestions.",
                current_value=metrics.acceptance_rate,
                threshold=ACCEPTANCE_RATE_LOW,
                trend=trend.acceptance_trend,
                recommendation="Recommendations may not be relevant. Check skill-to-gap matching quality. Consider re-tuning thresholds.",
            )
        )
    elif metrics.acceptance_rate < ACCEPTANCE_RATE_MEDIUM:
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-ACCEPTANCE-MEDIUM",
                severity="medium",
                metric="acceptance_rate",
                message=f"Skill recommendation acceptance rate is moderate ({metrics.acceptance_rate:.0%}). Room for improvement.",
                current_value=metrics.acceptance_rate,
                threshold=ACCEPTANCE_RATE_MEDIUM,
                trend=trend.acceptance_trend,
                recommendation="Review skill recommendations: are they well-matched to gaps? Consider dynamic similarity tuning.",
            )
        )

    # 4. False positive rate finding
    if metrics.false_positive_rate > FALSE_POSITIVE_HIGH:
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-FALSE-POSITIVE",
                severity="high",
                metric="false_positive_rate",
                message=f"High false-positive rate ({metrics.false_positive_rate:.0%}). Many gaps appear and disappear without resolution.",
                current_value=metrics.false_positive_rate,
                threshold=FALSE_POSITIVE_HIGH,
                trend=trend.false_positive_trend,
                recommendation="Review gap stability. Transient gaps may indicate detector noise or git-state-related false triggers.",
            )
        )

    return findings


# ── Main detector ──────────────────────────────────────────────────────────────


def detect_gto_self_health(
    project_root: Path | str | None = None,
    terminal_id: str | None = None,
    force_reload: bool = False,
) -> SelfHealthResult:
    """Detect GTO's own health metrics and surface findings.

    This is the main entry point for the self-health detector.
    It analyzes GTO's historical performance to detect trends
    and generates findings when metrics exceed thresholds.

    Args:
        project_root: Project root directory (defaults to cwd)
        terminal_id: Terminal identifier for history isolation
        force_reload: Force re-computation even if cached

    Returns:
        SelfHealthResult with metrics, trends, and findings
    """
    project_root = Path(project_root or Path.cwd()).resolve()
    if terminal_id is None:
        terminal_id = _resolve_terminal_id(project_root)

    health_log_path = _get_health_log_path(terminal_id)

    # Try to load cached metrics (avoid recomputing on every call)
    if not force_reload and health_log_path.exists():
        try:
            with open(health_log_path) as f:
                lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                cached = json.loads(last_line)
                cached_time = datetime.fromisoformat(cached["timestamp"])
                age = (datetime.now() - cached_time).total_seconds()
                # Cache valid for 5 minutes
                if age < 300:
                    return _result_from_cached(cached)
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    # Load historical data
    history = _load_history(project_root, terminal_id, last_n=20)
    usage = _load_skill_usage(project_root, last_n=50)

    total_runs = len(history)

    # Compute metrics and trends
    metrics = _build_health_metrics(history, usage, total_runs)

    gap_trend, gap_pct = _compute_gap_trend(history)
    sev_trend, sev_shift = _compute_severity_trend(history)

    # Compute acceptance and false-positive trends
    if len(history) >= 4:
        recent_acceptance = metrics.acceptance_rate
        prior_acceptance = min(recent_acceptance + 0.1, 1.0)  # Rough estimate
        accept_trend = "stable" if abs(recent_acceptance - prior_acceptance) < 0.1 else "worsening"
    else:
        accept_trend = "unknown"

    _, fp_trend = _compute_false_positive_rate(history)

    trend = HealthTrend(
        gap_trend=gap_trend,
        gap_trend_pct=gap_pct,
        severity_trend=sev_trend,
        severity_shift_pct=sev_shift,
        acceptance_trend=accept_trend,
        false_positive_trend=fp_trend,
    )

    # Generate findings
    findings = _generate_findings(metrics, trend, total_runs)

    is_healthy = all(f.severity != "high" for f in findings)

    result = SelfHealthResult(
        metrics=metrics,
        trend=trend,
        findings=findings,
        is_healthy=is_healthy,
        total_runs_analyzed=total_runs,
    )

    # Cache the result
    _cache_metrics(health_log_path, result)

    return result


def _cache_metrics(path: Path, result: SelfHealthResult) -> None:
    """Cache metrics to health log file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": result.metrics.timestamp if result.metrics else datetime.now().isoformat(),
            "gap_count": result.metrics.gap_count if result.metrics else 0,
            "high_severity_count": result.metrics.high_severity_count if result.metrics else 0,
            "medium_severity_count": result.metrics.medium_severity_count if result.metrics else 0,
            "low_severity_count": result.metrics.low_severity_count if result.metrics else 0,
            "acceptance_rate": result.metrics.acceptance_rate if result.metrics else 0.0,
            "false_positive_rate": result.metrics.false_positive_rate if result.metrics else 0.0,
            "total_runs": result.total_runs_analyzed,
            "is_healthy": result.is_healthy,
            "findings_count": len(result.findings),
        }
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _result_from_cached(cached: dict) -> SelfHealthResult:
    """Reconstruct SelfHealthResult from cached data."""
    metrics = HealthMetrics(
        timestamp=cached.get("timestamp", datetime.now().isoformat()),
        gap_count=cached.get("gap_count", 0),
        high_severity_count=cached.get("high_severity_count", 0),
        medium_severity_count=cached.get("medium_severity_count", 0),
        low_severity_count=cached.get("low_severity_count", 0),
        acceptance_rate=cached.get("acceptance_rate", 0.0),
        false_positive_rate=cached.get("false_positive_rate", 0.0),
        total_runs=cached.get("total_runs", 0),
    )

    # Rebuild trend as unknown (would need full history to compute)
    trend = HealthTrend(
        gap_trend="unknown",
        gap_trend_pct=0.0,
        severity_trend="unknown",
        severity_shift_pct=0.0,
        acceptance_trend="unknown",
        false_positive_trend="unknown",
    )

    is_healthy = cached.get("is_healthy", True)
    findings_count = cached.get("findings_count", 0)

    # Reconstruct minimal findings from cached state
    findings: list[SelfHealthFinding] = []
    if not is_healthy and findings_count > 0:
        findings.append(
            SelfHealthFinding(
                finding_id="GTO-HEALTH-CACHED",
                severity="medium",
                metric="overall",
                message=f"Previous health check found {findings_count} issue(s). Run with force_reload=True to get fresh analysis.",
                current_value=0.0,
                threshold=0.0,
                trend="unknown",
                recommendation="Run detect_gto_self_health(force_reload=True) for current analysis.",
            )
        )

    return SelfHealthResult(
        metrics=metrics,
        trend=trend,
        findings=findings,
        is_healthy=is_healthy,
        total_runs_analyzed=cached.get("total_runs", 0),
    )


def _resolve_terminal_id(project_root: Path) -> str:
    """Resolve terminal ID from environment or project root."""
    # Check environment first
    terminal_id = Path.home() / ".claude" / ".terminal_id"
    if terminal_id.exists():
        try:
            return terminal_id.read_text().strip()
        except OSError:
            pass

    # Fall back to project-root-derived hash
    import hashlib

    hash_digest = hashlib.md5(str(project_root).encode()).hexdigest()[:8]
    return f"term_{hash_digest}"


# ── Convenience function for orchestrator ─────────────────────────────────────


def check_gto_self_health(
    project_root: Path | str | None = None,
    terminal_id: str | None = None,
) -> SelfHealthResult:
    """Quick health check for GTO orchestrator integration.

    Args:
        project_root: Project root directory
        terminal_id: Terminal identifier

    Returns:
        SelfHealthResult with findings (cached for 5 minutes)
    """
    return detect_gto_self_health(project_root, terminal_id, force_reload=False)
