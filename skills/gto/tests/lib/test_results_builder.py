"""Tests for results_builder module."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.results_builder import (
    ConsolidatedResults,
    Gap,
    InitialResultsBuilder,
    build_initial_results,
)


class TestInitialResultsBuilder:
    """Smoke tests for InitialResultsBuilder."""

    def test_builder_instantiation(self) -> None:
        """Test builder can be instantiated."""
        builder = InitialResultsBuilder()
        assert builder is not None

    def test_gap_signature_includes_line_number(self) -> None:
        """Gap.signature() differs for same message at different line numbers.

        Regression test: signature() previously omitted line_number, causing
        multi-line markers at different lines to deduplicate incorrectly.
        """
        gap1 = Gap(
            gap_id="GAP-001",
            type="multi_line",
            severity="high",
            message="Duplicate issue here",
            file_path="src/test.py",
            line_number=10,
            source="test",
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="multi_line",
            severity="high",
            message="Duplicate issue here",
            file_path="src/test.py",
            line_number=20,
            source="test",
        )
        # Signatures MUST differ when line numbers differ
        assert gap1.signature() != gap2.signature(), (
            "Gap.signature() must include line_number to distinguish "
            "multi-line markers at different positions"
        )

    def test_gap_signature_same_when_identical(self) -> None:
        """Gap.signature() is same for identical type/file/message/line."""
        gap1 = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="Same message",
            file_path="src/test.py",
            line_number=10,
            source="test",
        )
        gap2 = Gap(
            gap_id="GAP-002",
            type="test",
            severity="high",
            message="Same message",
            file_path="src/test.py",
            line_number=10,
            source="test",
        )
        assert gap1.signature() == gap2.signature()


class TestGap:
    """Tests for Gap dataclass."""

    def test_gap_dataclass(self) -> None:
        """Test Gap can be constructed."""
        gap = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="Test gap",
            file_path=None,
            line_number=None,
            source="test",
        )
        assert gap.gap_id == "GAP-001"
        assert gap.type == "test"
        assert gap.severity == "high"

    def test_gap_to_dict(self) -> None:
        """Test Gap serialization."""
        gap = Gap(
            gap_id="GAP-001",
            type="test",
            severity="high",
            message="Test gap",
            file_path=None,
            line_number=None,
            source="test",
        )
        d = gap.to_dict()
        assert d["id"] == "GAP-001"


class TestConsolidatedResults:
    """Tests for ConsolidatedResults dataclass."""

    def test_dataclass(self) -> None:
        """Test ConsolidatedResults can be constructed."""
        results = ConsolidatedResults(
            gaps=[],
            total_gap_count=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
        )
        assert results.total_gap_count == 0


class TestBuildInitialResults:
    """Tests for build_initial_results function."""

    def test_build_with_empty_detectors(self, tmp_path: Path) -> None:
        """Test building with empty detector results."""
        detector_results = {
            "chain_integrity": Mock(is_valid=True, issues=[]),
            "test_presence": Mock(gaps=[], modules_checked=0),
            "docs_presence": Mock(gaps=[]),
            "dependencies": Mock(issues=[]),
        }
        results = build_initial_results(detector_results, tmp_path)
        assert isinstance(results, ConsolidatedResults)
