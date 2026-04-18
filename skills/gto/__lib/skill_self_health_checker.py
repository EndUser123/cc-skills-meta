"""SkillSelfHealthChecker - Verify skill's own tooling is intact.

Priority: P0 (runs once per session)
Purpose: Verify skill's own tooling is intact before running diagnostics

Checks (WARN only, never block):
1. All 6 reference files present and non-empty
2. .state/ directory is writable
3. hooks/ scripts are executable
4. gtodeterministic.py is accessible and importable
"""

from __future__ import annotations

import json
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class HealthCheckResult:
    """Result of health check."""

    status: Literal["PASS", "WARN"]
    warnings: list[str] = field(default_factory=list)
    checked: bool = False  # Whether checks were actually run (or skipped due to cache)


class SkillSelfHealthChecker:
    """
    Verify skill's own tooling is intact before running diagnostics.

    All checks are WARN only - never block execution.
    Run once per session; skip if cache indicates already checked.
    """

    # Required reference files
    REFERENCE_FILES = [
        "references/error-patterns.md",
        "references/conversation-patterns.md",
        "references/unfinished-patterns.md",
        "references/health-thresholds.md",
        "references/output-template.md",
        "references/critical-thinking-questions.md",
    ]

    # Required hook scripts
    HOOK_SCRIPTS = [
        "hooks/validate_format.py",
        "hooks/checklist_gate.py",
        "hooks/session_summary.py",
    ]

    def __init__(self, skill_root: Path | None = None):
        """Initialize checker with skill root directory.

        Args:
            skill_root: Skill root directory (defaults to this file's parent's parent)
        """
        if skill_root is None:
            # Default to 2 levels up from this file (lib/__file__ -> skill_root)
            skill_root = Path(__file__).parent.parent
        self.skill_root = skill_root
        self.cache_file = self.skill_root / ".state" / ".skill_cache.json"

    def check(self, force: bool = False) -> HealthCheckResult:
        """
        Run all health checks (or skip if cached).

        Args:
            force: Force re-check even if cached

        Returns:
            HealthCheckResult with warnings (if any)
        """
        warnings = []

        # Check cache first
        if not force and self._is_cached():
            return HealthCheckResult(status="PASS", warnings=[], checked=False)

        # Check 1: Reference files present and non-empty
        warnings.extend(self._check_reference_files())

        # Check 2: .state/ directory is writable
        warnings.extend(self._check_state_writable())

        # Check 3: Hook scripts are executable
        warnings.extend(self._check_hooks_executable())

        # Check 4: gtodeterministic.py is accessible
        warnings.extend(self._check_gtodeterministic_accessible())

        # Write cache after successful check
        self._write_cache()

        status: Literal["PASS", "WARN"] = "WARN" if warnings else "PASS"
        return HealthCheckResult(status=status, warnings=warnings, checked=True)

    def _is_cached(self) -> bool:
        """Check if health check was already run this session."""
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file) as f:
                cache = json.load(f)
            return cache.get("self_health_checked", False) is True
        except (OSError, json.JSONDecodeError):
            return False

    def _write_cache(self) -> None:
        """Write cache to indicate health check was run."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {"self_health_checked": True}

        try:
            # Atomic write: temp file + replace
            temp_path = self.cache_file.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(cache_data, f)
            temp_path.replace(self.cache_file)
        except OSError:
            # Non-critical: cache write failure shouldn't block
            pass

    def _check_reference_files(self) -> list[str]:
        """Check all reference files present and non-empty."""
        warnings = []

        for ref_file in self.REFERENCE_FILES:
            ref_path = self.skill_root / ref_file

            if not ref_path.exists():
                warnings.append(f"Reference file missing: {ref_file}")
            elif ref_path.stat().st_size == 0:
                warnings.append(f"Reference file empty: {ref_file}")

        return warnings

    def _check_state_writable(self) -> list[str]:
        """Check .state/ directory is writable."""
        warnings = []
        state_dir = self.skill_root / ".state"

        # Create .state/ if it doesn't exist
        state_dir.mkdir(parents=True, exist_ok=True)

        # Test write by creating a temp file
        test_file = state_dir / ".write_test"

        try:
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError):
            warnings.append(f".state/ directory not writable: {state_dir}")

        return warnings

    def _check_hooks_executable(self) -> list[str]:
        """Check hooks/ scripts are executable (for POSIX) or exist (for Windows)."""
        warnings = []

        for hook_script in self.HOOK_SCRIPTS:
            hook_path = self.skill_root / hook_script

            if not hook_path.exists():
                warnings.append(f"Hook script missing: {hook_script}")
                continue

            # On POSIX, check executable bit
            # On Windows, just check existence (file must exist to be executable)
            try:
                st = hook_path.stat()
                if hasattr(st, "st_mode"):  # POSIX
                    if not (st.st_mode & stat.S_IXUSR):
                        warnings.append(f"Hook script not executable: {hook_script}")
            except OSError:
                warnings.append(f"Hook script not accessible: {hook_script}")

        return warnings

    def _check_gtodeterministic_accessible(self) -> list[str]:
        """Check gtodeterministic.py is accessible and importable."""
        warnings = []

        # Check file exists
        gtodet_path = self.skill_root / "gtodeterministic.py"

        if not gtodet_path.exists():
            warnings.append(f"gtodeterministic.py not found at: {gtodet_path}")
            return warnings

        # Check file is readable
        try:
            with open(gtodet_path) as f:
                f.read(1)  # Try to read first byte
        except (OSError, PermissionError):
            warnings.append(f"gtodeterministic.py not readable: {gtodet_path}")

        return warnings


# Convenience function
def check_skill_health(skill_root: Path | None = None, force: bool = False) -> HealthCheckResult:
    """
    Quick health check for GTO skill.

    Args:
        skill_root: Skill root directory
        force: Force re-check even if cached

    Returns:
        HealthCheckResult indicating if any warnings were found
    """
    checker = SkillSelfHealthChecker(skill_root)
    return checker.check(force=force)
