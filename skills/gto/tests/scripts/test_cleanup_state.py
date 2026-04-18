"""Tests for cleanup_state module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.cleanup_state import cleanup_all_evidence_dirs


class TestCleanupAllEvidenceDirs:
    """Tests for cleanup_all_evidence_dirs function."""

    def test_returns_dict_with_required_keys(self) -> None:
        """Test that function returns expected dictionary structure."""
        result = cleanup_all_evidence_dirs()
        assert isinstance(result, dict)
        assert "removed" in result
        assert "errors" in result
        assert "skipped" in result
        assert isinstance(result["removed"], list)
        assert isinstance(result["errors"], list)
        assert isinstance(result["skipped"], list)
