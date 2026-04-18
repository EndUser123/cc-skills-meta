"""Tests for checklist_gate module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.checklist_gate import run_checklist_gate


class TestChecklistGate:
    """Tests for run_checklist_gate function."""

    def test_missing_checklist_returns_true(self, tmp_path: Path) -> None:
        """Test that missing checklist passes the gate."""
        result = run_checklist_gate(tmp_path / "nonexistent.md")
        assert result is True

    def test_checklist_all_checked_returns_true(self, tmp_path: Path) -> None:
        """Test that fully checked checklist passes."""
        checklist = tmp_path / "checklist.md"
        checklist.write_text("- [x] Item 1\n- [x] Item 2\n")
        result = run_checklist_gate(checklist)
        assert result is True

    def test_checklist_with_unchecked_returns_false(self, tmp_path: Path) -> None:
        """Test that unchecked items fail the gate."""
        checklist = tmp_path / "checklist.md"
        checklist.write_text("- [x] Item 1\n- [ ] Item 2\n- [ ] Item 3\n")
        result = run_checklist_gate(checklist)
        assert result is False
