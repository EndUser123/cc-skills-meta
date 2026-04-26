"""Tests for GTO orchestrator."""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch

from skills.gto.orchestrator import run, parse_args


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project directory with .git and README."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "README.md").write_text("# Test Project\n", encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def redirect_artifacts(tmp_path):
    """Redirect artifacts to tmp_path so tests don't write to real drive root."""
    with patch.dict(os.environ, {"CLAUDE_ARTIFACTS_ROOT": str(tmp_path / ".claude" / ".artifacts")}):
        yield


class TestParseArgs:
    def test_defaults(self):
        args = parse_args([])
        assert args.mode == "full"
        assert args.skip_agents is False
        assert args.terminal_id == "default"

    def test_custom_args(self):
        args = parse_args(["--mode", "quick", "--terminal-id", "t1", "--skip-agents"])
        assert args.mode == "quick"
        assert args.terminal_id == "t1"
        assert args.skip_agents is True


class TestOrchestratorRun:
    def test_quick_mode(self, project_dir):
        rc = run([
            "--mode", "quick",
            "--skip-agents",
            "--terminal-id", "test-term",
            "--session-id", "test-session",
            "--root", str(project_dir),
        ])
        # rc may be 0 or 1 depending on git SHA availability in temp dirs
        assert rc in (0, 1)

        artifacts_dir = project_dir / ".claude" / ".artifacts" / "test-term" / "gto"
        artifact = artifacts_dir / "outputs" / "artifact.json"
        assert artifact.exists()

        data = json.loads(artifact.read_text(encoding="utf-8"))
        assert data["terminal_id"] == "test-term"
        assert data["session_id"] == "test-session"
        assert "machine_output" in data
        assert isinstance(data["findings"], list)

    def test_state_completed(self, project_dir):
        run([
            "--mode", "quick", "--skip-agents",
            "--terminal-id", "t1", "--root", str(project_dir),
        ])
        state_file = project_dir / ".claude" / ".artifacts" / "t1" / "gto" / "state" / "run_state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["phase"] == "completed"

    def test_machine_output_has_rns(self, project_dir):
        run([
            "--mode", "quick", "--skip-agents",
            "--terminal-id", "t1", "--root", str(project_dir),
        ])
        artifact_path = project_dir / ".claude" / ".artifacts" / "t1" / "gto" / "outputs" / "artifact.json"
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        machine = data.get("machine_output", [])
        has_z = any(l.startswith("RNS|Z|") for l in machine)
        assert has_z  # RNS|Z|0|NONE always present
