"""Tests for history_scanner module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.history_scanner import HistoryScanner


class TestHistoryScanner:
    """Smoke tests for HistoryScanner."""

    def test_scanner_instantiation(self, tmp_path: Path) -> None:
        """Test scanner can be instantiated."""
        scanner = HistoryScanner(tmp_path)
        assert scanner is not None
