"""Tests for code_marker_scanner module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.code_marker_scanner import (
    CodeMarker,
    CodeMarkerResult,
    CodeMarkerScanner,
    scan_code_markers,
)


class TestCodeMarkerScanner:
    """Smoke tests for CodeMarkerScanner."""

    def test_scanner_instantiation(self, tmp_path: Path) -> None:
        """Test scanner can be instantiated."""
        scanner = CodeMarkerScanner(tmp_path)
        assert scanner is not None

    def test_scan_empty_dir(self, tmp_path: Path) -> None:
        """Test scanning empty directory."""
        result = scan_code_markers(tmp_path)
        assert isinstance(result, CodeMarkerResult)
        assert result.total_count == 0


class TestCodeMarker:
    """Tests for CodeMarker dataclass."""

    def test_marker_dataclass(self) -> None:
        """Test marker can be constructed."""
        marker = CodeMarker(
            marker_type="TODO",
            content="test content",
            file_path="/fake/path.py",
            line_number=10,
            relative_path="path.py",
        )
        assert marker.marker_type == "TODO"
        assert marker.content == "test content"


class TestCodeMarkerResult:
    """Tests for CodeMarkerResult dataclass."""

    def test_result_dataclass(self) -> None:
        """Test result can be constructed."""
        result = CodeMarkerResult(
            markers=[],
            total_count=0,
            files_scanned=0,
            files_with_markers=0,
            errors=[],
        )
        assert result.total_count == 0
        assert len(result.markers) == 0
