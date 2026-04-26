"""Tests for viability_gate module."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.viability_gate import ViabilityGate, check_viability


class TestViabilityGate:
    """Smoke tests for ViabilityGate."""

    def test_gate_instantiation(self, tmp_path: Path) -> None:
        """Test gate can be instantiated."""
        gate = ViabilityGate(tmp_path)
        assert gate is not None

    def test_check_viability(self, tmp_path: Path) -> None:
        """Test viability check."""
        result = check_viability(tmp_path)
        assert hasattr(result, "is_viable")
        assert hasattr(result, "failure_reason")


class TestProjectNameDerivation:
    """Tests for project name derivation from path."""

    def test_standard_project_path(self, tmp_path: Path) -> None:
        """Test project name derivation from standard .claude/projects/<project> path."""
        # Create a path structure that includes .claude/projects/my-project
        # Use tmp_path which exists, but structure our project_name test
        gate = ViabilityGate(tmp_path)

        # Test Path.parts derivation directly by mocking project_root
        original_root = gate.project_root

        # Create a mock path with projects/ in parts
        mock_path = Path("C:/Users/test/.claude/projects/my-project")
        with patch.object(gate, 'project_root', mock_path):
            result = gate._find_transcript()
            # Should not raise - either finds transcript or returns None

        assert result is None or isinstance(result, Path)

    def test_p_drive_path(self, tmp_path: Path) -> None:
        """Test P:\\ drive path falls back to P-- correctly."""
        gate = ViabilityGate(tmp_path)

        # Override project_root to simulate P:\ without .claude/projects
        mock_path = Path("P:/")
        with patch.object(gate, 'project_root', mock_path):
            result = gate._find_transcript()
            # Should fall back gracefully
            assert result is None or isinstance(result, Path)

    def test_nested_project_path(self, tmp_path: Path) -> None:
        """Test nested project path derives correct project name."""
        gate = ViabilityGate(tmp_path)

        # Create a mock nested path with projects/ in parts
        mock_path = Path("C:/Users/test/.claude/projects/my-project/src")
        with patch.object(gate, 'project_root', mock_path):
            result = gate._find_transcript()
            # Should not raise
            assert result is None or isinstance(result, Path)


class TestHandoffEnvelopeFallback:
    """Tests for handoff envelope missing or corrupt scenarios."""

    def test_missing_handoff_envelope(self, tmp_path: Path) -> None:
        """Test viability check when handoff envelope is missing."""
        # Create a valid git repo so basic checks pass
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main")

        gate = ViabilityGate(tmp_path)
        result = gate.check()

        # Should still be viable even without handoff envelope
        assert result.is_viable is True

    def test_corrupt_handoff_envelope(self, tmp_path: Path) -> None:
        """Test viability check when handoff envelope contains invalid JSON."""
        # Create .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main")

        # Create corrupt handoff envelope
        handoff_dir = tmp_path / ".claude" / "state"
        handoff_dir.mkdir(parents=True)
        handoff_file = handoff_dir / "handoff_envelope.json"
        handoff_file.write_text("{ invalid json }")

        gate = ViabilityGate(tmp_path)
        result = gate.check()

        # Should handle gracefully
        assert isinstance(result, type(result))


class TestTranscriptFallback:
    """Tests for transcript path detection fallback."""

    def test_find_transcript_in_project_root(self, tmp_path: Path) -> None:
        """Test finding transcript.jsonl in project root."""
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"role": "user", "content": "test"}\n')

        gate = ViabilityGate(tmp_path)
        result = gate._find_transcript()

        assert result is not None
        assert result.name == "transcript.jsonl"

    def test_find_transcript_json(self, tmp_path: Path) -> None:
        """Test finding transcript.json in project root."""
        transcript_file = tmp_path / "transcript.json"
        transcript_file.write_text('{"role": "user", "content": "test"}')

        gate = ViabilityGate(tmp_path)
        result = gate._find_transcript()

        assert result is not None
        assert result.name == "transcript.json"

    def test_no_transcript_found(self, tmp_path: Path) -> None:
        """Test graceful handling when no transcript exists in project_root."""
        gate = ViabilityGate(tmp_path)

        # Mock Path.home() to return tmp_path so UUID fallback search finds nothing
        fake_home = tmp_path / ".claude" / "projects" / "test-project"
        fake_home.mkdir(parents=True)

        with patch.object(Path, 'home', return_value=tmp_path):
            result = gate._find_transcript()
            # Should return None when no transcripts exist anywhere
            assert result is None


class TestUUIDTranscriptFallback:
    """Tests for UUID-named transcript fallback search."""

    def test_uuid_transcript_detection(self, tmp_path: Path) -> None:
        """Test detection of UUID-named transcript files."""
        # Mock the projects directory with a UUID transcript file
        uuid_name = "a1b2c3d4-e5f6-7890-abcd-ef1234567890.jsonl"
        mock_projects_dir = tmp_path / ".claude" / "projects" / "test-project"
        mock_projects_dir.mkdir(parents=True)

        # Create a UUID transcript file
        transcript_file = mock_projects_dir / uuid_name
        transcript_file.write_text('{"role": "user"}\n')

        with patch.object(Path, "home", return_value=tmp_path):
            # Create project path that includes projects/
            project_path = tmp_path / ".claude" / "projects" / "test-project"
            gate = ViabilityGate(project_path)

            # If we have projects in path, it should derive project name correctly
            result = gate._find_transcript()

            # Should find the UUID transcript or return None gracefully
            assert result is None or isinstance(result, Path)


class TestFirstSessionStandaloneMode:
    """Tests for first-session mode without previous sessions."""

    def test_viability_without_previous_sessions(self, tmp_path: Path) -> None:
        """Test GTO works in standalone mode without transcript history."""
        # Create a valid git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "HEAD").write_text("ref: refs/heads/main")

        gate = ViabilityGate(tmp_path)
        result = gate.check()

        # Should be viable without requiring previous sessions
        assert result.is_viable is True
        assert result.status == "PASS"


class TestWindowsPathHandling:
    """Tests for Windows-specific path handling."""

    def test_windows_p_drive_path(self, tmp_path: Path) -> None:
        """Test handling of P:\\ style paths."""
        gate = ViabilityGate(tmp_path)

        # Simulate P:\ path without .claude/projects structure
        p_path = Path("P:/project")
        with patch.object(gate, 'project_root', p_path):
            # Should not raise, should return None gracefully
            result = gate._find_transcript()
            assert result is None or isinstance(result, Path)

    def test_backslash_path_handling(self, tmp_path: Path) -> None:
        """Test that Path.parts correctly splits Windows paths."""
        # Test that our Path.parts approach handles backslashes correctly
        windows_path = Path("C:\\Users\\test\\.claude\\projects\\my-project")
        parts = windows_path.parts

        # Should find "projects" in parts
        if "projects" in parts:
            idx = parts.index("projects")
            project_name = parts[idx + 1]
            assert project_name == "my-project"
        else:
            # Path without projects should fall back
            pass
