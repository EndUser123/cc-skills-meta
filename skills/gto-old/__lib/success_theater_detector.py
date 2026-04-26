"""Success Theater Detector.

Priority: P1 (runs post-merge, before RNS output)
Purpose: Detect misleading health metrics where the numbers look good but underlying
evidence is weak or absent.

Success theater patterns detected:
- health_score=100 but assertions were skipped or failed
- gaps=0 but only because detectors were disabled/silenced
- health_score=100 but no assertions script was ever run
- artifact written but verification step was bypassed
- metric improvements that don't reflect actual system state
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def _get_terminal_id() -> str:
    """Get terminal ID for state directory."""
    import hashlib
    import os

    if value := os.environ.get("CLAUDE_TERMINAL_ID", "").strip():
        return value
    return hashlib.md5(str(os.getpid()).encode()).hexdigest()[:8]


@dataclass
class SuccessTheaterFlag:
    """A detected success theater pattern."""

    pattern: str
    severity: str
    description: str
    evidence: dict[str, Any]
    recommendation: str


@dataclass
class SuccessTheaterResult:
    """Result from success theater detection."""

    is_healthy: bool
    flags: list[SuccessTheaterFlag]
    overall_verdict: str

    def to_gaps(self) -> list[dict[str, Any]]:
        """Convert flags to gap dicts for RNS output."""
        if self.is_healthy:
            return []
        return [
            {
                "gap_id": f"THEATER-{flag.pattern.upper()}",
                "type": "success_theater",
                "severity": flag.severity,
                "message": f"[SUCCESS THEATER] {flag.description}",
                "source": "SuccessTheaterDetector",
                "metadata": {
                    "pattern": flag.pattern,
                    "evidence": flag.evidence,
                    "recommendation": flag.recommendation,
                },
                "effort_estimate_minutes": 5,
                "advisory": True,
            }
            for flag in self.flags
        ]


class SuccessTheaterDetector:
    """Detect success theater patterns in GTO outputs."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def check(
        self,
        artifact: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SuccessTheaterResult:
        """Run success theater detection."""
        flags: list[SuccessTheaterFlag] = []

        if artifact:
            health_score = (
                artifact.get("health_score")
                or artifact.get("overall")
                or artifact.get("health", {}).get("overall_score")
            )
            if health_score == 100:
                flag = self._check_assertions_ran(artifact)
                if flag:
                    flags.append(flag)

        if artifact:
            if artifact.get("total_gap_count", 0) == 0:
                flag = self._check_quiet_means_disabled(metadata)
                if flag:
                    flags.append(flag)

        if artifact:
            flag = self._check_empty_health(artifact)
            if flag:
                flags.append(flag)

        if artifact:
            flag = self._check_stale_assertions(artifact)
            if flag:
                flags.append(flag)

        if not flags:
            verdict = "GENUINE"
        elif any(f.severity == "HIGH" for f in flags):
            verdict = "THEATER"
        elif any(f.severity == "MEDIUM" for f in flags):
            verdict = "SUSPECT"
        else:
            verdict = "GENUINE"

        return SuccessTheaterResult(
            is_healthy=verdict == "GENUINE",
            flags=flags,
            overall_verdict=verdict,
        )

    def _check_assertions_ran(self, artifact: dict[str, Any]) -> SuccessTheaterFlag | None:
        """Check if assertions actually ran for a 100% health score."""
        assertions_passed = artifact.get("assertions_passed")
        assertions_total = artifact.get("assertions_total")

        if assertions_passed is not None and assertions_total is not None:
            if assertions_passed < assertions_total:
                return SuccessTheaterFlag(
                    pattern="assertions_failed",
                    severity="HIGH",
                    description=f"health_score=100 but {assertions_total - assertions_passed}/{assertions_total} assertions failed",
                    evidence={"assertions_passed": assertions_passed, "assertions_total": assertions_total},
                    recommendation="Run gto_assertions.py to get real validation",
                )

        metadata = artifact.get("metadata", {})
        viability = metadata.get("viability_check", {})
        if viability.get("is_viable") is False:
            return SuccessTheaterFlag(
                pattern="viability_bypassed",
                severity="HIGH",
                description="health_score=100 despite viability check failure",
                evidence={"viability_check": viability},
                recommendation="Fix viability failure before claiming healthy",
            )

        if assertions_passed is None and assertions_total is None:
            if artifact.get("total_gap_count", 0) == 0:
                return SuccessTheaterFlag(
                    pattern="no_assertions",
                    severity="MEDIUM",
                    description="health_score=100 but no assertion data found — assertions may not have run",
                    evidence={"has_assertions_data": False, "total_gaps": artifact.get("total_gap_count")},
                    recommendation="Run gto_assertions.py to verify health",
                )
        return None

    def _check_quiet_means_disabled(self, metadata: dict[str, Any] | None) -> SuccessTheaterFlag | None:
        """Check if zero gaps means detectors were disabled."""
        if not metadata:
            return None
        if metadata.get("subagents_disabled", False):
            return SuccessTheaterFlag(
                pattern="subagents_disabled",
                severity="MEDIUM",
                description="0 gaps found but subagents were disabled — gap list may be incomplete",
                evidence={"subagents_disabled": True},
                recommendation="Run with subagents enabled for complete analysis",
            )
        detector_count = metadata.get("detector_count", 0)
        if detector_count < 5:
            return SuccessTheaterFlag(
                pattern="few_detectors",
                severity="LOW",
                description=f"Only {detector_count} detectors ran — gap list may be incomplete",
                evidence={"detector_count": detector_count},
                recommendation="Check if slow detectors were skipped in --quick mode",
            )
        return None

    def _check_empty_health(self, artifact: dict[str, Any]) -> SuccessTheaterFlag | None:
        """Check if health_score is present but health report is absent."""
        has_health_score = artifact.get("health_score") or artifact.get("overall")
        has_health_report = artifact.get("health_report") or artifact.get("health")
        if has_health_score and not has_health_report:
            return SuccessTheaterFlag(
                pattern="score_without_report",
                severity="LOW",
                description="health_score computed but no detailed health report — can't verify what was checked",
                evidence={"has_health_score": True, "has_health_report": False},
                recommendation="Run with health check enabled for full validation",
            )
        return None

    def _check_stale_assertions(self, artifact: dict[str, Any]) -> SuccessTheaterFlag | None:
        """Check if artifact is older than 24 hours."""
        artifact_time = artifact.get("timestamp", "")
        if not artifact_time:
            return None
        try:
            artifact_dt = datetime.fromisoformat(artifact_time.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
        if datetime.now() - artifact_dt > timedelta(hours=24):
            return SuccessTheaterFlag(
                pattern="stale_artifact",
                severity="LOW",
                description=f"Artifact is {artifact.get('timestamp')} — assertions may be stale",
                evidence={"artifact_timestamp": artifact_time},
                recommendation="Re-run GTO and assertions to get current state",
            )
        return None


def detect_success_theater(
    artifact: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    project_root: Path | str | None = None,
) -> SuccessTheaterResult:
    """Quick entry point for success theater detection."""
    detector = SuccessTheaterDetector(project_root=project_root)
    return detector.check(artifact=artifact, metadata=metadata)
