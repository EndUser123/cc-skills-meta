"""Tests for gap_finder_subagent module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from subagents.gap_finder_subagent import (
    GapFinderResult,
    GapFinderSubagent,
    GapFinding,
    find_gaps,
)


class TestGapFinding:
    """Tests for GapFinding dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test GapFinding can be constructed."""
        finding = GapFinding(
            gap_type="test_gap",
            message="Missing test coverage",
            file_path="src/test.py",
            line_number=42,
        )
        assert finding.gap_type == "test_gap"
        assert finding.message == "Missing test coverage"
        assert finding.file_path == "src/test.py"
        assert finding.line_number == 42

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        finding = GapFinding(
            gap_type="test_gap",
            message="Missing test coverage",
            file_path="src/test.py",
            line_number=42,
        )
        result = finding.to_dict()
        assert isinstance(result, dict)
        assert result["type"] == "test_gap"
        assert result["line_number"] == 42
        assert "id" in result


class TestGapFinderResult:
    """Tests for GapFinderResult dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test GapFinderResult can be constructed."""
        finding = GapFinding(
            gap_type="test_gap",
            message="Missing test coverage",
            file_path="src/test.py",
            line_number=42,
        )
        result = GapFinderResult(
            gaps=[finding],
            files_scanned=10,
            gaps_found=1,
        )
        assert len(result.gaps) == 1
        assert result.files_scanned == 10
        assert result.gaps_found == 1


class TestGapFinderSubagent:
    """Smoke tests for GapFinderSubagent class."""

    def test_instantiation(self, tmp_path: Path) -> None:
        """Test GapFinderSubagent can be instantiated."""
        finder = GapFinderSubagent(tmp_path)
        assert finder.project_root == tmp_path.resolve()

    def test_find_gaps_returns_result(self, tmp_path: Path) -> None:
        """Test find_gaps returns GapFinderResult."""
        finder = GapFinderSubagent(tmp_path)
        result = finder.find_gaps()
        assert isinstance(result, GapFinderResult)
        assert isinstance(result.gaps, list)
        assert isinstance(result.files_scanned, int)
        assert isinstance(result.gaps_found, int)

    def test_find_gaps_convenience_function(self, tmp_path: Path) -> None:
        """Test find_gaps convenience function."""
        result = find_gaps(tmp_path)
        assert isinstance(result, GapFinderResult)
