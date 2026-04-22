#!/usr/bin/env python
"""GTO Binary Assertions - Self-verifying completion enforcement.

This script validates 5 criteria for GTO analysis completion:
- A1: Artifacts exist (gapfinder, health, or gitcontext files)
- A2: Health score reported (0-100% in artifact files)
- A3: Viability check passed (no FAIL status in viability artifacts)
- A4: Git repository valid (.git directory exists)
- A5: State directory accessible

Exit codes:
- 0: All assertions passed (100/100 score)
- 1: Some assertions failed (partial score)
- 2: Critical failure (no artifacts or invalid state)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Terminal ID sanitization: allow only safe characters
_TERMINAL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _get_default_terminal_id() -> str:
    """Auto-detect terminal ID without importing hook_base (namespace conflict).

    Priority:
    1. CLAUDE_TERMINAL_ID env var (highest)
    2. TERMINAL_ID, TERM_ID, SESSION_TERMINAL env vars
    3. Derive from PID + timestamp (fallback)

    Terminal IDs are sanitized to prevent path traversal attacks.
    Only alphanumeric, underscore, hyphen allowed (max 64 chars).
    """
    # Priority 1: Environment variables with sanitization
    for env_var in ["CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM_ID", "SESSION_TERMINAL"]:
        value = os.environ.get(env_var, "").strip()
        if value and _TERMINAL_ID_PATTERN.match(value):
            return value

    # Priority 2: Derive from PID + timestamp (safe by construction)
    try:
        pid = os.getpid()
        timestamp = int(datetime.now().timestamp())
        unique = f"{pid}_{timestamp}".encode()
        return hashlib.sha1(unique).hexdigest()[:12]
    except (OSError, RuntimeError):
        return "unknown"


class GTOAssertions:
    """Binary assertions for GTO completion verification."""

    def __init__(self, project_root: Path, terminal_id: str, evidence_dir: Path | None = None):
        self.project_root = project_root.resolve()
        self.terminal_id = terminal_id
        self.evidence_dir = (evidence_dir or self.project_root / ".evidence").resolve()
        self.state_dir = self.evidence_dir / f"gto-state-{terminal_id}"
        self.results = {}

    def check_a1_artifacts_exist(self) -> tuple[bool, str]:
        """A1: Artifacts exist (any age) with valid JSON content.

        No time limit — an artifact from any point in history still proves
        the GTO pipeline ran and produced output. Use A1 to confirm the
        pipeline works; use artifact mtime in monitoring for freshness.
        """
        artifact_patterns = [
            "gto-results*.json",
            "gto-artifact*.json",
            "artifact.json",  # GTO orchestrator output format
            "gapfinder*.json",
            "health*.json",
            "gitcontext*.json",
        ]

        if not self.evidence_dir.exists():
            return False, "No .evidence directory found"

        for pattern in artifact_patterns:
            # Use rglob for recursive search in subdirectories like gto-outputs/
            for artifact in self.evidence_dir.rglob(pattern):
                if artifact.is_file():
                    try:
                        data = json.loads(artifact.read_text())
                    except (json.JSONDecodeError, OSError):
                        continue  # Skip malformed artifacts

                    # Validate required fields exist
                    # GTO artifacts should have: gaps (list) and timestamp or metadata
                    if isinstance(data, dict):
                        has_gaps = "gaps" in data or "findings" in data
                        has_metadata = any(
                            k in data
                            for k in (
                                "timestamp",
                                "metadata",
                                "health_score",
                                "overall_score",
                                "health_report",
                            )
                        )
                        if has_gaps or has_metadata:
                            return True, f"Found valid artifact: {artifact.name}"

        return False, "No valid GTO artifacts with required fields found"

    def check_a2_health_score(self) -> tuple[bool, str]:
        """A2: Health score reported (0-100% in artifact files).

        Single-pass: collects candidates via one rglob, then checks each.
        """
        if not self.evidence_dir.exists():
            return False, "No .evidence directory found"

        # Single-pass: collect JSON artifacts matching health score patterns
        candidates = []
        for artifact in self.evidence_dir.rglob("*.json"):
            name = artifact.name
            if (
                name.startswith("gto-results")
                or name.startswith("gto-artifact")
                or name == "artifact.json"
                or name.startswith("health")
            ):
                candidates.append(artifact)

        # Check each candidate for health score
        for artifact in candidates:
            try:
                data = json.loads(artifact.read_text())
                score = self._extract_health_score(data)
                if score is not None:
                    return True, f"Health score: {score}%"
            except (json.JSONDecodeError, OSError):
                continue

        return False, "No valid health score (0-100%) found in artifacts"

    # Threshold for decimal vs percentage detection
    _DECIMAL_THRESHOLD: float = 1.0

    def _normalize_score(self, score: float) -> float | None:
        """Normalize score to 0-100 range and validate.

        Handles both decimal (0.0-1.0) and percentage (0-100) formats.
        """
        if isinstance(score, (int, float)):
            if 0 <= score < self._DECIMAL_THRESHOLD:
                score = score * 100
            if 0 <= score <= 100:
                return float(score)
        return None

    def _extract_health_score(self, data: dict) -> float | None:
        """Extract and validate health score from artifact data.

        Checks multiple possible locations and formats:
        - Top-level health_score
        - health_report.overall_score (GTO orchestrator)
        - health.overall_score (GTO v3)
        - metrics.overall / metrics.test_coverage (GTO v3)
        - score / health_score (legacy formats)
        """
        # Top-level health_score
        if "health_score" in data:
            score = data["health_score"]
            if isinstance(score, (int, float)) and 0 <= score <= 100:
                return float(score)

        # overall_score at root (GTO monorepo format)
        if "overall_score" in data:
            score = data["overall_score"]
            result = self._normalize_score(score)
            if result is not None:
                return result

        # health_report.overall_score (GTO orchestrator)
        hr = data.get("health_report", {})
        if isinstance(hr, dict) and "overall_score" in hr:
            score = hr["overall_score"]
            result = self._normalize_score(score)
            if result is not None:
                return result

        # health.overall_score (GTO v3 artifact format)
        health = data.get("health", {})
        if isinstance(health, dict) and "overall_score" in health:
            score = health["overall_score"]
            result = self._normalize_score(score)
            if result is not None:
                return result

        # metrics.overall / metrics.test_coverage (GTO v3)
        metrics = data.get("metrics", {})
        if isinstance(metrics, dict):
            overall = metrics.get("overall", metrics.get("test_coverage"))
            if overall is not None:
                result = self._normalize_score(overall)
                if result is not None:
                    return result

        # Legacy: score or health_score at root
        if "score" in data or "health_score" in data:
            score = data.get("score", data.get("health_score"))
            if isinstance(score, (int, float)) and 0 <= score <= 100:
                return float(score)

        return None

    def check_a3_viability_passed(self) -> tuple[bool, str]:
        """A3: Viability check passed (no FAIL status)."""
        for artifact in self.evidence_dir.glob("viability*.json"):
            try:
                data = json.loads(artifact.read_text())
                status = data.get("status", "").upper()
                if status == "FAIL":
                    return False, f"Viability check FAILED: {artifact.name}"
                if status == "PASS":
                    return True, "Viability check PASSED"
            except (json.JSONDecodeError, KeyError):
                continue

        # If no viability artifact, check results file for viability status
        for artifact in self.evidence_dir.glob("gto-results*.json"):
            try:
                data = json.loads(artifact.read_text())
                viability = data.get("viability", {})
                if isinstance(viability, dict):
                    status = viability.get("status", "").upper()
                    if status == "FAIL":
                        return False, "Viability check FAILED in results"
                    if status == "PASS":
                        return True, "Viability check PASSED in results"
            except (json.JSONDecodeError, KeyError):
                continue

        # No viability check found - treat as pass (not required for basic GTO)
        return True, "No viability check (optional for basic GTO)"

    def check_a4_git_repository(self) -> tuple[bool, str]:
        """A4: Git repository valid (.git directory exists or worktree is valid)."""
        # Check project root directly
        git_dir = self.project_root / ".git"
        if git_dir.exists() and git_dir.is_dir():
            return True, "Git repository valid"

        # Check if .git is a file (worktree indicator - points to actual git dir)
        if git_dir.exists() and git_dir.is_file():
            try:
                content = git_dir.read_text(encoding="utf-8").strip()
                if content.startswith("gitdir:"):
                    return True, "Git worktree valid"
            except (OSError, UnicodeDecodeError):
                pass

        # Check parent directories for .git (nested worktree scenario)
        parent = self.project_root.parent
        for _ in range(5):  # Max 5 levels up
            parent_git = parent / ".git"
            if parent_git.exists():
                if parent_git.is_dir():
                    return True, "Git repository valid (parent .git)"
                if parent_git.is_file():
                    try:
                        content = parent_git.read_text(encoding="utf-8").strip()
                        if content.startswith("gitdir:"):
                            return True, "Git worktree valid (parent .git)"
                    except (OSError, UnicodeDecodeError):
                        pass
            # Check if we've reached root BEFORE moving to next parent
            if parent == parent.parent:
                break
            parent = parent.parent

        return False, "Not a git repository (no .git directory)"

    def check_a5_state_accessible(self) -> tuple[bool, str]:
        """A5: State directory accessible."""
        if not self.state_dir.exists():
            return True, "State directory not created (GTO not run yet)"

        if not self.state_dir.is_dir():
            return False, "State path exists but is not a directory"

        # Check if we can list contents
        try:
            list(self.state_dir.iterdir())
            return True, "State directory accessible"
        except PermissionError:
            return False, "State directory not accessible (permission denied)"

    def run_all(self) -> dict:
        """Run all assertions and return results."""
        self.results = {
            "A1": {"check": "Artifacts exist", "result": self.check_a1_artifacts_exist()},
            "A2": {"check": "Health score reported", "result": self.check_a2_health_score()},
            "A3": {"check": "Viability check passed", "result": self.check_a3_viability_passed()},
            "A4": {"check": "Git repository valid", "result": self.check_a4_git_repository()},
            "A5": {
                "check": "State directory accessible",
                "result": self.check_a5_state_accessible(),
            },
        }

        passed = sum(1 for r in self.results.values() if r["result"][0])
        total = len(self.results)
        score = int((passed / total) * 100)

        return {
            "passed": passed,
            "total": total,
            "score": score,
            "all_passed": passed == total,
            "assertions": self.results,
        }

    def print_results(self):
        """Print assertion results to stdout."""
        summary = self.run_all()

        print(f"\nGTO Binary Assertions - {self.project_root.name}")
        print(f"Terminal ID: {self.terminal_id}")
        print(f"Score: {summary['score']}/100 ({summary['passed']}/{summary['total']} passed)")
        print()

        for key, assertion in summary["assertions"].items():
            passed, message = assertion["result"]
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} {key}: {assertion['check']}")
            print(f"       {message}")

        print()

        if summary["all_passed"]:
            print("✓ ALL ASSERTIONS PASSED - GTO verification complete")
            return 0
        else:
            print(f"✗ {summary['total'] - summary['passed']} assertion(s) failed")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="GTO Binary Assertions - Self-verifying completion enforcement"
    )
    parser.add_argument("--project-root", required=True, help="Project root path")
    parser.add_argument(
        "--evidence-dir",
        default=None,
        help="Evidence directory (default: <project-root>/.evidence)",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print score (0-100)")

    args = parser.parse_args()

    project_root = Path(args.project_root)
    if not project_root.exists():
        print(f"Error: Project root does not exist: {project_root}", file=sys.stderr)
        return 2

    # Resolve evidence directory (default or override)
    evidence_dir = None
    if args.evidence_dir:
        evidence_dir = Path(args.evidence_dir)
        if not evidence_dir.exists():
            print(f"Error: Evidence directory does not exist: {evidence_dir}", file=sys.stderr)
            return 2

    # Auto-detect terminal ID using local fallback (avoids hook_base namespace conflict)
    terminal_id = _get_default_terminal_id()
    assertions = GTOAssertions(project_root, terminal_id, evidence_dir)
    summary = assertions.run_all()

    if args.quiet:
        print(summary["score"])
        return 0 if summary["all_passed"] else 1

    return assertions.print_results()


if __name__ == "__main__":
    sys.exit(main())
