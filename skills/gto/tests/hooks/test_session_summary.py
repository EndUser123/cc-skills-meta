"""Tests for session_summary module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.session_summary import generate_session_summary


class TestGenerateSessionSummary:
    """Tests for generate_session_summary function."""

    def test_no_artifacts_returns_basic_summary(self, tmp_path: Path) -> None:
        """Test summary when no artifacts exist."""
        result = generate_session_summary(tmp_path)
        assert "GTO Session Summary" in result
        assert "No artifacts found" in result

    def test_with_json_artifacts(self, tmp_path: Path) -> None:
        """Test summary with JSON artifact files."""
        artifact = tmp_path / "gto-results.json"
        artifact.write_text(json.dumps({"gaps": [{"id": "GAP-001"}], "unfinished": []}))

        result = generate_session_summary(tmp_path)
        assert "GTO Session Summary" in result
        assert "1" in result  # One gap

    def test_counts_unfinished_items(self, tmp_path: Path) -> None:
        """Test that unfinished items are counted."""
        artifact = tmp_path / "gto-results.json"
        artifact.write_text(
            json.dumps({"gaps": [], "unfinished": [{"id": "TASK-001"}, {"id": "TASK-002"}]})
        )

        result = generate_session_summary(tmp_path)
        assert "2" in result  # Two unfinished items
