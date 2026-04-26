"""Tests for validate_format module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.validate_format import validate_artifact_format


class TestValidateArtifactFormat:
    """Tests for validate_artifact_format function."""

    def test_missing_artifact_returns_false(self, tmp_path: Path) -> None:
        """Test that missing artifact returns False."""
        result = validate_artifact_format(tmp_path / "nonexistent.json")
        assert result is False

    def test_valid_json_artifact_returns_true(self, tmp_path: Path) -> None:
        """Test that valid JSON artifact returns True."""
        artifact = tmp_path / "test.json"
        artifact.write_text(json.dumps({"key": "value"}))
        result = validate_artifact_format(artifact)
        assert result is True

    def test_invalid_json_returns_false(self, tmp_path: Path) -> None:
        """Test that invalid JSON returns False."""
        artifact = tmp_path / "test.json"
        artifact.write_text("{ invalid json }")
        result = validate_artifact_format(artifact)
        assert result is False

    def test_markdown_artifact_returns_true(self, tmp_path: Path) -> None:
        """Test that markdown artifact with headers returns True."""
        artifact = tmp_path / "test.md"
        artifact.write_text("# Title\n## Section\nContent")
        result = validate_artifact_format(artifact)
        assert result is True
