"""Tests for adjacent_file_scanner module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.adjacent_file_scanner import AdjacentFileScanner, AdjacentScanResult, TouchedFile


class TestAdjacentFileScanner:
    """Smoke tests for AdjacentFileScanner."""

    def test_scanner_instantiation(self, tmp_path: Path) -> None:
        """Test scanner can be instantiated."""
        scanner = AdjacentFileScanner(tmp_path)
        assert scanner is not None

    def test_scan_adjacent_files_missing_transcript_raises(self, tmp_path: Path) -> None:
        """Test scanning with missing transcript raises FileNotFoundError."""
        scanner = AdjacentFileScanner(tmp_path)
        transcript = tmp_path / "nonexistent_transcript.jsonl"
        try:
            scanner.scan_adjacent_files(transcript)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError as e:
            assert "Transcript not found" in str(e)

    def test_scan_adjacent_files_with_valid_transcript(self, tmp_path: Path) -> None:
        """Test scanning with a valid transcript returns result."""
        scanner = AdjacentFileScanner(tmp_path)
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text('{"type":"user","content":[]}\n')
        result = scanner.scan_adjacent_files(transcript)
        assert isinstance(result, AdjacentScanResult)
        assert result.total_files_scanned == 0  # no code files touched


class TestAdjacentScanResult:
    """Tests for AdjacentScanResult dataclass."""

    def test_dataclass(self) -> None:
        """Test AdjacentScanResult can be constructed."""
        result = AdjacentScanResult(
            touched_files=[],
            missing_tests=[],
            todo_comments=[],
            docstring_gaps=[],
            total_files_scanned=0,
        )
        assert result.total_files_scanned == 0
        assert len(result.touched_files) == 0


class TestTouchedFile:
    """Tests for TouchedFile dataclass."""

    def test_dataclass(self) -> None:
        """Test TouchedFile can be constructed."""
        file = TouchedFile(
            path=Path("/fake/file.py"),
            operation_count=1,
            operations=["Read"],
        )
        assert file.path == Path("/fake/file.py")
        assert file.operation_count == 1
