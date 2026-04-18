"""Tests for skill_coverage_detector module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.skill_coverage_detector import (
    SkillCoverageEntry,
    SkillCoverageResult,
)


class TestSkillCoverageEntry:
    """Tests for SkillCoverageEntry dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test SkillCoverageEntry can be constructed."""
        entry = SkillCoverageEntry(
            skill="/test",
            target="test_target",
            terminal_id="test_terminal",
            timestamp="2026-03-25T00:00:00Z",
        )
        assert entry.skill == "/test"
        assert entry.target == "test_target"


class TestSkillCoverageResult:
    """Tests for SkillCoverageResult dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test SkillCoverageResult can be constructed with default fields."""
        result = SkillCoverageResult()
        assert result is not None
