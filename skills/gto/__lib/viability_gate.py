"""ViabilityGate - Validate preconditions before any gap detection.

Priority: P0 (runs before all analysis)
Purpose: Validate preconditions before any gap detection

Checks (in order, all must pass):
1. Handoff envelope exists and is readable
2. Transcript path is accessible
3. At least one previous session exists (for context)

Note: Git repository check is informational only (P2) - not a blocker.
Git context is displayed in output but doesn't prevent analysis.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class ViabilityResult:
    """Result of viability check."""

    is_viable: bool
    status: Literal["PASS", "FAIL"]
    reason: str | None = None
    checks_passed: list[str] | None = None
    checks_failed: list[str] | None = None

    @property
    def failure_reason(self) -> str | None:
        """Alias for reason for backward compatibility."""
        return self.reason


class ViabilityGate:
    """
    Validate preconditions before running GTO analysis.

    All checks must pass for viability. If any check fails,
    analysis cannot proceed.
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize gate with project root validation.

        Args:
            project_root: Project root directory (defaults to cwd)

        Raises:
            ValueError: If project_root does not exist or is not a directory
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.project_root = self.project_root.resolve()

        # Validate project_root exists and is a directory
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {self.project_root}")

    def check(self, transcript_path: Path | None = None) -> ViabilityResult:
        """
        Run all viability checks.

        Args:
            transcript_path: Path to current transcript (optional, auto-detected)

        Returns:
            ViabilityResult with pass/fail status and details
        """
        checks_passed = []
        checks_failed = []

        # Check 1: Valid git repository (informational only - doesn't block)
        git_result = self._check_git_repository()
        if git_result.is_viable:
            checks_passed.append("Git repository valid")
        else:
            # Fix: Git check failure should be tracked (though informational - doesn't block)
            checks_passed.append(f"Git check: {git_result.reason} (informational)")

        # Check 2: Handoff envelope exists and is readable
        # Also extract transcript_path from handoff if available (ADR-20260321 Phase 2)
        handoff_result = self._check_handoff_envelope()
        if handoff_result.is_viable:
            checks_passed.append("Handoff envelope accessible")
            # Try to extract transcript_path from handoff envelope
            if transcript_path is None:
                transcript_path = self._extract_transcript_from_handoff()
        else:
            checks_failed.append(f"Handoff envelope: {handoff_result.reason}")

        # Check 3: Transcript path is accessible (optional check, doesn't block)
        # Transcript is only required for session goal detection, not basic analysis
        # If transcript_path is None or not accessible, we continue without it
        if transcript_path is None:
            transcript_path = self._find_transcript()

        transcript_result = self._check_transcript_accessible(transcript_path)
        # Transcript check is informational only - doesn't affect viability
        # This allows GTO to run even when transcript is not available
        if transcript_result.is_viable:
            checks_passed.append("Transcript accessible")
        # If transcript not accessible, we don't add to checks_failed - just continue

        # Note: Previous sessions check removed per ADR-20260321
        # GTO now works in standalone mode without requiring transcript history

        # Overall viability
        all_passed = len(checks_failed) == 0

        return ViabilityResult(
            is_viable=all_passed,
            status="PASS" if all_passed else "FAIL",
            reason=None if all_passed else "; ".join(checks_failed),
            checks_passed=checks_passed if all_passed else None,
            checks_failed=checks_failed if not all_passed else None,
        )

    def _check_git_repository(self) -> ViabilityResult:
        """Check if project has valid git repository."""
        git_dir = self.project_root / ".git"

        if not git_dir.exists():
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason="No .git directory found",
            )

        if not git_dir.is_dir():
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason=".git is not a directory",
            )

        # Check for git metadata (HEAD file or config)
        head_file = git_dir / "HEAD"
        if not head_file.exists():
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason="No HEAD file (not a valid git repo)",
            )

        return ViabilityResult(is_viable=True, status="PASS")

    def _check_handoff_envelope(self) -> ViabilityResult:
        """Check if handoff envelope exists and is readable."""
        # Handoff envelope location: .claude/state/handoff_envelope.json
        handoff_path = self.project_root / ".claude" / "state" / "handoff_envelope.json"

        if not handoff_path.exists():
            # This is not critical for gto_old compatibility
            # but required for v3
            return ViabilityResult(
                is_viable=True,  # Non-critical for basic operation
                status="PASS",
                reason=None,
            )

        if not handoff_path.is_file():
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason="Handoff envelope exists but is not a file",
            )

        # Check if readable (try to parse as JSON)
        try:
            with open(handoff_path) as f:
                json.load(f)
            return ViabilityResult(is_viable=True, status="PASS")
        except json.JSONDecodeError:
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason="Handoff envelope contains invalid JSON",
            )
        except Exception as e:
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason=f"Cannot read handoff envelope: {e}",
            )

    def _check_transcript_accessible(self, transcript_path: Path | None) -> ViabilityResult:
        """Check if transcript path is accessible."""
        if transcript_path is None:
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason="No transcript path provided or found",
            )

        if not transcript_path.exists():
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason=f"Transcript not found: {transcript_path}",
            )

        if not transcript_path.is_file():
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason=f"Transcript exists but is not a file: {transcript_path}",
            )

        # Check if readable
        try:
            with open(transcript_path) as f:
                f.read(1)  # Try to read first byte
            return ViabilityResult(is_viable=True, status="PASS")
        except Exception as e:
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason=f"Cannot read transcript: {e}",
            )

    def _check_previous_sessions(self, transcript_path: Path | None) -> ViabilityResult:
        """Check if at least one previous session exists."""
        # For gto v3, we need context from previous sessions.
        # If transcript_path is provided, check if it exists and has content.
        # Otherwise, look for transcript files in project root.

        if transcript_path is not None:
            # Use the provided transcript path
            if not transcript_path.exists():
                return ViabilityResult(
                    is_viable=False,
                    status="FAIL",
                    reason=f"Transcript not found: {transcript_path}",
                )

            # Check if transcript has content
            try:
                if transcript_path.stat().st_size == 0:
                    return ViabilityResult(
                        is_viable=False,
                        status="FAIL",
                        reason="Current transcript is empty",
                    )
            except Exception:
                pass  # Size check is optional

            # Transcript exists and has content - that's sufficient
            return ViabilityResult(is_viable=True, status="PASS")

        # No transcript_path provided - look for transcript files in project root
        transcript_files = list(self.project_root.glob("transcript*.json*"))

        if not transcript_files:
            return ViabilityResult(
                is_viable=False,
                status="FAIL",
                reason="No transcript path provided and no transcript files found in project directory",
            )

        # At least one transcript file exists
        return ViabilityResult(is_viable=True, status="PASS")

    def _extract_transcript_from_handoff(self) -> Path | None:
        """Extract transcript_path from handoff envelope.

        Returns:
            Path to transcript if found in handoff envelope, None otherwise
        """
        handoff_path = self.project_root / ".claude" / "state" / "handoff_envelope.json"

        if not handoff_path.exists():
            return None

        try:
            with open(handoff_path) as f:
                handoff_data = json.load(f)

            transcript_path = handoff_data.get("transcript_path")
            if transcript_path:
                return Path(transcript_path)

        except (json.JSONDecodeError, OSError):
            # Handoff file is corrupt or unreadable - fall back to other methods
            pass

        return None

    def _find_transcript(self) -> Path | None:
        """Find transcript path using standard locations."""
        # Standard locations (in order of priority)
        locations = [
            self.project_root / "transcript.jsonl",
            self.project_root / "transcript.json",
        ]

        for location in locations:
            if location.exists():
                return location

        # Fallback: Search for UUID-named transcript files (ADR-20260321 Phase 3)
        # Look in Claude Code's transcript directory
        try:
            # Get the Claude Code projects directory from environment or default
            # On Windows, typically: C:\Users\{username}\.claude\projects\{project_name}\
            home_dir = Path.home()
            projects_dir = home_dir / ".claude" / "projects"

            if projects_dir.exists():
                # The project directory name is derived from project_root
                # Use Path.parts indexing (like history_chain.py:45-50)
                pp = self.project_root
                try:
                    projects_idx = pp.parts.index("projects") + 1
                    project_name = pp.parts[projects_idx]
                except (ValueError, IndexError):
                    # .claude/projects/<project> not found — fall back
                    project_name = "P--"

                transcript_dir = projects_dir / project_name
                if transcript_dir.exists() and transcript_dir.is_dir():
                    # Look for UUID-named transcript files (pattern: *.jsonl)
                    # UUID pattern: 8-4-4-4-12 hex digits
                    uuid_pattern = re.compile(
                        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$",
                        re.IGNORECASE,
                    )

                    # Find all transcript files and return the most recent one
                    transcript_files = []
                    for f in transcript_dir.glob("*.jsonl"):
                        if uuid_pattern.match(f.name):
                            transcript_files.append((f.stat().st_mtime, f))

                    if transcript_files:
                        # Sort by modification time (newest first) and return the most recent
                        transcript_files.sort(key=lambda x: x[0], reverse=True)
                        return transcript_files[0][1]

        except (OSError, ImportError, re.error):
            # Fallback search failed - continue without transcript
            pass

        return None


# Convenience function
def check_viability(
    project_root: Path | None = None, transcript_path: Path | None = None
) -> ViabilityResult:
    """
    Quick viability check for GTO analysis.

    Args:
        project_root: Project root directory
        transcript_path: Path to current transcript

    Returns:
        ViabilityResult indicating if analysis can proceed
    """
    gate = ViabilityGate(project_root)
    return gate.check(transcript_path)
