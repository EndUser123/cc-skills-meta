"""Tests for skill_self_health_checker module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.skill_self_health_checker import (
    HealthCheckResult,
    SkillSelfHealthChecker,
    check_skill_health,
)


class TestSkillSelfHealthChecker:
    """Smoke tests for SkillSelfHealthChecker."""

    def test_checker_instantiation(self, tmp_path: Path) -> None:
        """Test checker can be instantiated."""
        checker = SkillSelfHealthChecker(tmp_path)
        assert checker is not None

    def test_check_skill_health(self, tmp_path: Path) -> None:
        """Test health check."""
        result = check_skill_health(tmp_path)
        assert isinstance(result, HealthCheckResult)


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_dataclass(self) -> None:
        """Test HealthCheckResult can be constructed."""
        result = HealthCheckResult(
            status="PASS",
            warnings=[],
            checked=True,
        )
        assert result.status == "PASS"
        assert len(result.warnings) == 0
