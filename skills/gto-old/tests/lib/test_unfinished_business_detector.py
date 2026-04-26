"""Tests for unfinished_business_detector module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.unfinished_business_detector import (
    UnfinishedBusinessDetector,
    UnfinishedBusinessResult,
    UnfinishedItem,
)


class TestUnfinishedBusinessDetector:
    """Smoke tests for UnfinishedBusinessDetector."""

    def test_detector_instantiation(self, tmp_path: Path) -> None:
        """Test detector can be instantiated."""
        detector = UnfinishedBusinessDetector(tmp_path)
        assert detector is not None


class TestUnfinishedBusinessResult:
    """Tests for UnfinishedBusinessResult dataclass."""

    def test_dataclass(self) -> None:
        """Test UnfinishedBusinessResult can be constructed."""
        result = UnfinishedBusinessResult(
            tasks=[],
            questions=[],
            deferred=[],
            total_count=0,
        )
        assert result.total_count == 0
        assert len(result.items) == 0


class TestUnfinishedItem:
    """Tests for UnfinishedItem dataclass."""

    def test_dataclass(self) -> None:
        """Test UnfinishedItem can be constructed."""
        item = UnfinishedItem(
            category="task",
            content="Test item",
            turn_number=1,
            confidence=0.9,
        )
        assert item.category == "task"
        assert item.content == "Test item"
        assert item.turn_number == 1
