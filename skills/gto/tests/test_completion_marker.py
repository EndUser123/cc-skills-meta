"""Tests for GTO completion marker functionality (TDD RED phase)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from gto_orchestrator import GTOOrchestrator, OrchestratorConfig


class TestCompletionMarker:
    """Tests for completion marker write/read/idempotency."""

    def test_write_completion_marker_creates_file(self, tmp_path: Path) -> None:
        """Test that _write_completion_marker creates the completion.json file."""
        # Setup
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(tmp_path),
            "terminal_id": "test_terminal",
        }

        # Create mock results
        mock_results = MagicMock()
        mock_results.gaps = []
        mock_results.total_gap_count = 0
        mock_results.critical_count = 0
        mock_results.high_count = 0
        mock_results.medium_count = 0
        mock_results.low_count = 0

        # Execute
        orchestrator._write_completion_marker(metadata, mock_results)

        # Verify - completion.json should exist in terminal-isolated state dir
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        completion_file = state_dir / "completion.json"

        assert completion_file.exists(), "completion.json should be created"

    def test_write_completion_marker_schema(self, tmp_path: Path) -> None:
        """Test that completion marker has all required fields."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        metadata = {
            "timestamp": "2026-04-16T12:58:46Z",
            "project_root": str(tmp_path),
            "terminal_id": "test_terminal",
        }

        mock_results = MagicMock()
        mock_results.gaps = []
        mock_results.total_gap_count = 0
        mock_results.critical_count = 0
        mock_results.high_count = 0
        mock_results.medium_count = 0
        mock_results.low_count = 0

        orchestrator._write_completion_marker(metadata, mock_results)

        # Verify schema
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        completion_file = state_dir / "completion.json"

        data = json.loads(completion_file.read_text())

        # Required fields
        assert data["schema_version"] == "1"
        assert data["terminal_id"] == "test_terminal"
        assert data["timestamp"] == "2026-04-16T12:58:46Z"
        assert data["target"] == str(tmp_path)
        assert "git_sha" in data
        assert data["health_score"] == 100  # No gaps = 100%
        assert data["assertions_passed"] == 5
        assert data["assertions_total"] == 5
        assert isinstance(data["artifact_paths"], list)
        assert data["completion_status"] == "complete"

    def test_check_completion_marker_not_exists(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker returns None when no marker exists."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        result = orchestrator._check_completion_marker()

        assert result is None, "Should return None when marker doesn't exist"

    def test_check_completion_marker_valid(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker returns marker when valid."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create a valid marker
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_data = {
            "schema_version": "1",
            "session_id": "test-session",
            "terminal_id": "test_terminal",
            "timestamp": datetime.now().isoformat(),
            "target": str(tmp_path),
            "git_sha": "abc123",
            "health_score": 100,
            "assertions_passed": 5,
            "assertions_total": 5,
            "artifact_paths": [],
            "completion_status": "complete",
        }

        completion_file = state_dir / "completion.json"
        completion_file.write_text(json.dumps(marker_data))

        # Mock _get_git_sha to return same SHA
        with patch.object(orchestrator, "_get_git_sha", return_value="abc123"):
            result = orchestrator._check_completion_marker()

        assert result is not None, "Should return marker when valid"
        assert result["git_sha"] == "abc123"
        assert result["completion_status"] == "complete"

    def test_check_completion_marker_stale_git_sha(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker returns None when git_sha changed."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create marker with old git_sha
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_data = {
            "schema_version": "1",
            "session_id": "test-session",
            "terminal_id": "test_terminal",
            "timestamp": datetime.now().isoformat(),
            "target": str(tmp_path),
            "git_sha": "old_sha",
            "health_score": 100,
            "assertions_passed": 5,
            "assertions_total": 5,
            "artifact_paths": [],
            "completion_status": "complete",
        }

        completion_file = state_dir / "completion.json"
        completion_file.write_text(json.dumps(marker_data))

        # Mock _get_git_sha to return different SHA
        with patch.object(orchestrator, "_get_git_sha", return_value="new_sha"):
            result = orchestrator._check_completion_marker()

        assert result is None, "Should return None when git_sha changed (stale)"

    def test_check_completion_marker_stale_ttl(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker returns None when marker > 24h old."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create old marker (> 24 hours)
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        state_dir.mkdir(parents=True, exist_ok=True)

        old_timestamp = datetime.now() - timedelta(hours=25)

        marker_data = {
            "schema_version": "1",
            "session_id": "test-session",
            "terminal_id": "test_terminal",
            "timestamp": old_timestamp.isoformat(),
            "target": str(tmp_path),
            "git_sha": "abc123",
            "health_score": 100,
            "assertions_passed": 5,
            "assertions_total": 5,
            "artifact_paths": [],
            "completion_status": "complete",
        }

        completion_file = state_dir / "completion.json"
        completion_file.write_text(json.dumps(marker_data))

        # Mock _get_git_sha to return same SHA
        with patch.object(orchestrator, "_get_git_sha", return_value="abc123"):
            result = orchestrator._check_completion_marker()

        assert result is None, "Should return None when marker > 24h old (TTL expired)"

    def test_get_git_sha_success(self, tmp_path: Path) -> None:
        """Test that _get_git_sha returns SHA when in git repo."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Mock subprocess.run to return git SHA
        mock_run = MagicMock(return_value=MagicMock(
            stdout=b"abc123def456\n",
            stderr=b"",
            returncode=0
        ))

        with patch("subprocess.run", mock_run):
            result = orchestrator._get_git_sha()

        assert result == "abc123def456"

    def test_get_git_sha_no_repo(self, tmp_path: Path) -> None:
        """Test that _get_git_sha returns None when not in git repo."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Mock subprocess.run to simulate not a git repo
        mock_run = MagicMock(return_value=MagicMock(
            stdout=b"",
            stderr=b"fatal: not a git repository",
            returncode=128
        ))

        with patch("subprocess.run", mock_run):
            result = orchestrator._get_git_sha()

        assert result is None

    def test_idempotency_skip_rerun(self, tmp_path: Path) -> None:
        """Test that orchestrator skips re-run when completion marker exists and is current."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create a valid completion marker
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_data = {
            "schema_version": "1",
            "session_id": "cached-session",
            "terminal_id": "test_terminal",
            "timestamp": datetime.now().isoformat(),
            "target": str(tmp_path),
            "git_sha": "current_sha",
            "health_score": 95,
            "assertions_passed": 5,
            "assertions_total": 5,
            "artifact_paths": ["cached_artifact.json"],
            "completion_status": "complete",
        }

        completion_file = state_dir / "completion.json"
        completion_file.write_text(json.dumps(marker_data))

        # Mock git SHA and viability check
        with patch.object(orchestrator, "_get_git_sha", return_value="current_sha"):
            with patch("gto_orchestrator.check_viability", return_value=MagicMock(is_viable=True)):
                result = orchestrator.run()

        # Should return cached result, not re-run analysis
        assert result.success is True
        # Verify metadata contains cached session info
        assert result.metadata.get("cached_from_marker") is True

    def test_terminal_id_validation_rejects_path_traversal(self, tmp_path: Path) -> None:
        """Test that StateManager rejects path traversal in terminal_id."""
        from __lib.state_manager import StateManager

        # Path traversal attempt
        malicious_id = "../../../etc/passwd"

        with pytest.raises(ValueError, match="Invalid terminal_id"):
            StateManager(project_root=tmp_path, terminal_id=malicious_id)

    def test_terminal_id_validation_rejects_special_chars(self, tmp_path: Path) -> None:
        """Test that StateManager rejects special characters in terminal_id."""
        from __lib.state_manager import StateManager

        # Various invalid inputs
        invalid_ids = [
            "terminal/with/slash",
            "terminal\\with\\backslash",
            "terminal with spaces",
            "terminal.with.dots",
            "",
            "a" * 65,  # Too long
        ]

        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match="Invalid terminal_id"):
                StateManager(project_root=tmp_path, terminal_id=invalid_id)

    def test_terminal_id_validation_accepts_valid_ids(self, tmp_path: Path) -> None:
        """Test that StateManager accepts valid terminal_id formats."""
        from __lib.state_manager import StateManager

        # Valid inputs
        valid_ids = [
            "test_terminal",
            "Test-Terminal-123",
            "test_terminal_01",
            "a" * 64,  # Max length
        ]

        for valid_id in valid_ids:
            # Should not raise
            manager = StateManager(project_root=tmp_path, terminal_id=valid_id)
            assert manager.terminal_id == valid_id

    def test_check_completion_marker_terminal_mismatch(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker rejects markers from different terminals."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="terminal_A",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create marker from different terminal
        state_dir = tmp_path / ".evidence" / "gto-state-terminal_A"
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_data = {
            "schema_version": "1",
            "session_id": "test-session",
            "terminal_id": "terminal_B",  # Different terminal
            "timestamp": datetime.now().isoformat(),
            "target": str(tmp_path),
            "git_sha": "abc123",
            "health_score": 100,
            "assertions_passed": 5,
            "assertions_total": 5,
            "artifact_paths": [],
            "completion_status": "complete",
        }

        completion_file = state_dir / "completion.json"
        completion_file.write_text(json.dumps(marker_data))

        # Mock git SHA to match
        with patch.object(orchestrator, "_get_git_sha", return_value="abc123"):
            result = orchestrator._check_completion_marker()

        assert result is None, "Should return None when terminal_id mismatches"

    def test_git_sha_none_comparison(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker handles git_sha=None correctly."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create marker with git_sha
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_data = {
            "schema_version": "1",
            "session_id": "test-session",
            "terminal_id": "test_terminal",
            "timestamp": datetime.now().isoformat(),
            "target": str(tmp_path),
            "git_sha": "old_sha",  # Marker has SHA
            "health_score": 100,
            "assertions_passed": 5,
            "assertions_total": 5,
            "artifact_paths": [],
            "completion_status": "complete",
        }

        completion_file = state_dir / "completion.json"
        completion_file.write_text(json.dumps(marker_data))

        # Mock git SHA as None (git unavailable)
        with patch.object(orchestrator, "_get_git_sha", return_value=None):
            result = orchestrator._check_completion_marker()

        # Should return None because None != "old_sha"
        assert result is None, "Should return None when current_git_sha=None and marker has SHA"

    def test_get_git_sha_handles_non_utf8_output(self, tmp_path: Path) -> None:
        """Test that _get_git_sha handles non-UTF-8 git output gracefully."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Mock subprocess to return non-UTF-8 bytes
        mock_run = MagicMock(return_value=MagicMock(
            stdout=b"abc123\x80\x81\x82\n",  # Invalid UTF-8 bytes
            stderr=b"",
            returncode=0
        ))

        with patch("subprocess.run", mock_run):
            result = orchestrator._get_git_sha()

        # Should return string with invalid bytes stripped/ignored
        assert result == "abc123"  # Non-UTF-8 bytes ignored

    def test_write_cleanup_temp_file_on_failure(self, tmp_path: Path) -> None:
        """Test that _write_completion_marker cleans up temp file on OSError."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(tmp_path),
            "terminal_id": "test_terminal",
        }

        mock_results = MagicMock()
        mock_results.gaps = []
        mock_results.total_gap_count = 0

        # Mock os.replace to raise OSError (simulating write failure)
        original_replace = __import__("os").replace
        call_count = [0]

        def failing_replace(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call fails
                raise OSError("Simulated write failure")
            return original_replace(*args, **kwargs)

        with patch("os.replace", side_effect=failing_replace):
            # First call should fail and clean up temp file
            with pytest.raises(OSError):
                orchestrator._write_completion_marker(metadata, mock_results)

        # Verify temp file was cleaned up (should not exist)
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        temp_files = list(state_dir.glob("*.tmp"))
        assert len(temp_files) == 0, "Temp file should be cleaned up after failure"

    def test_read_only_state_directory(self, tmp_path: Path) -> None:
        """Test behavior when state directory creation fails."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Mock state_manager to raise OSError on _ensure_state_dir
        with patch.object(orchestrator.state_manager, "_ensure_state_dir", side_effect=OSError("Permission denied")):
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(tmp_path),
                "terminal_id": "test_terminal",
            }

            mock_results = MagicMock()
            mock_results.gaps = []
            mock_results.total_gap_count = 0

            # Should raise OSError when state dir cannot be created
            with pytest.raises(OSError, match="Permission denied"):
                orchestrator._write_completion_marker(metadata, mock_results)

    def test_check_completion_marker_malformed_json(self, tmp_path: Path) -> None:
        """Test that _check_completion_marker handles malformed JSON gracefully."""
        config = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="test_terminal",
            transcript_path=None,
        )
        orchestrator = GTOOrchestrator(config)

        # Create completion file with malformed JSON
        state_dir = tmp_path / ".evidence" / "gto-state-test_terminal"
        state_dir.mkdir(parents=True, exist_ok=True)

        completion_file = state_dir / "completion.json"
        completion_file.write_text("{invalid json content")

        # Should return None for malformed JSON
        result = orchestrator._check_completion_marker()
        assert result is None, "Should return None for malformed JSON"

    def test_concurrent_write_terminal_isolation(self, tmp_path: Path) -> None:
        """Test that concurrent writes from different terminals are isolated."""
        import threading
        import time

        # Create two orchestrators with different terminal IDs
        config_a = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="terminal_A",
            transcript_path=None,
        )
        orchestrator_a = GTOOrchestrator(config_a)

        config_b = OrchestratorConfig(
            project_root=tmp_path,
            terminal_id="terminal_B",
            transcript_path=None,
        )
        orchestrator_b = GTOOrchestrator(config_b)

        results = {"success": [], "errors": []}

        def write_marker_a():
            try:
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "project_root": str(tmp_path),
                    "terminal_id": "terminal_A",
                }
                mock_results = MagicMock()
                mock_results.gaps = []
                mock_results.total_gap_count = 0
                orchestrator_a._write_completion_marker(metadata, mock_results)
                results["success"].append("A")
            except Exception as e:
                results["errors"].append(f"A: {e}")

        def write_marker_b():
            try:
                metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "project_root": str(tmp_path),
                    "terminal_id": "terminal_B",
                }
                mock_results = MagicMock()
                mock_results.gaps = []
                mock_results.total_gap_count = 0
                orchestrator_b._write_completion_marker(metadata, mock_results)
                results["success"].append("B")
            except Exception as e:
                results["errors"].append(f"B: {e}")

        # Start both threads concurrently
        thread_a = threading.Thread(target=write_marker_a)
        thread_b = threading.Thread(target=write_marker_b)

        thread_a.start()
        thread_b.start()

        thread_a.join(timeout=5)
        thread_b.join(timeout=5)

        # Both should succeed without corruption
        assert len(results["errors"]) == 0, f"Concurrent writes failed: {results['errors']}"
        assert len(results["success"]) == 2, "Both terminals should write successfully"

        # Verify each terminal has its own marker
        state_dir_a = tmp_path / ".evidence" / "gto-state-terminal_A"
        state_dir_b = tmp_path / ".evidence" / "gto-state-terminal_B"
        assert (state_dir_a / "completion.json").exists(), "Terminal A marker should exist"
        assert (state_dir_b / "completion.json").exists(), "Terminal B marker should exist"
