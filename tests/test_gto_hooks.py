"""Tests for GTO hooks — sessionstart, pretooluse, posttooluse, stop.

Uses mocked stdin/stdout to test the Claude Code hook protocol without
real terminal state or artifact files.
"""
from __future__ import annotations

import json
import os
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from skills.gto.hooks.common import (
    get_artifacts_root,
    get_project_root,
    get_terminal_id,
    gto_state_dir,
    is_gto_active,
    read_state,
    write_hook_output,
)
from skills.gto.hooks.sessionstart import run as sessionstart_run
from skills.gto.hooks.pretooluse import run as pretooluse_run
from skills.gto.hooks.posttooluse import (
    _is_failure,
    _validate_artifact_write,
    run as posttooluse_run,
)
from skills.gto.hooks.stop import run as stop_run


# --- Fixtures ---


@pytest.fixture
def artifacts_dir(tmp_path):
    """Create a terminal-scoped artifacts directory with .git marker."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
    return artifacts


@pytest.fixture(autouse=True)
def isolate_env(tmp_path):
    """Set env vars for deterministic terminal ID, project root, and artifacts path."""
    env = {
        "CLAUDE_TERMINAL_ID": "test-term",
        "CLAUDE_PROJECT_DIR": str(tmp_path),
        "CLAUDE_ARTIFACTS_ROOT": str(tmp_path / ".claude" / ".artifacts"),
        "WT_SESSION": "",
    }
    with patch.dict(os.environ, env, clear=False):
        yield


def _write_state(artifacts_dir: Path, state: dict) -> None:
    """Helper to write a GTO state file."""
    state_dir = artifacts_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "run_state.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _write_artifact(path: Path, data: dict) -> None:
    """Helper to write a GTO artifact JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# --- Common module tests ---


class TestTerminalId:
    def test_env_override(self):
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "my-term", "WT_SESSION": ""}):
            assert get_terminal_id() == "my-term"

    def test_wt_session(self):
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "", "WT_SESSION": "abc-123"}):
            assert get_terminal_id() == "console_abc-123"

    def test_fallback_hash(self):
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "", "WT_SESSION": ""}):
            tid = get_terminal_id()
            assert len(tid) == 12
            assert tid.isalnum()


class TestProjectRoot:
    def test_env_dir(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            assert get_project_root() == tmp_path

    def test_walk_up_git(self, tmp_path):
        subdir = tmp_path / "deep" / "nested"
        subdir.mkdir(parents=True)
        (tmp_path / ".git").mkdir()
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": ""}):
            with patch("skills.gto.hooks.common.Path.cwd", return_value=subdir):
                root = get_project_root()
                assert root == tmp_path


class TestIsGtoActive:
    def test_inactive(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            assert is_gto_active() is False

    def test_active(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto" / "state"
        artifacts.mkdir(parents=True)
        (artifacts / "run_state.json").write_text("{}", encoding="utf-8")
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            assert is_gto_active() is True


class TestReadState:
    def test_missing_file(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            assert read_state() == {}

    def test_valid_state(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto" / "state"
        artifacts.mkdir(parents=True)
        state = {"phase": "completed", "run_id": "r1"}
        (artifacts / "run_state.json").write_text(json.dumps(state), encoding="utf-8")
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            assert read_state() == state


class TestWriteHookOutput:
    def test_outputs_json(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            write_hook_output({"decision": "allow"})
        assert json.loads(buf.getvalue()) == {"decision": "allow"}


# --- SessionStart hook tests ---


class TestSessionStart:
    def test_inactive_gto(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = sessionstart_run({})
            assert result is None

    def test_completed_phase(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        artifact_path = artifacts / "outputs" / "artifact.json"
        _write_artifact(artifact_path, {
            "terminal_id": "test-term",
            "findings": [{"id": "F1"}, {"id": "F2"}],
            "machine_output": ["RNS|Z|0|NONE"],
        })
        _write_state(artifacts, {
            "phase": "completed",
            "current_target": "src/",
            "expected_artifacts": [str(artifact_path)],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = sessionstart_run({})
        assert result is not None
        assert result["decision"] == "allow"
        assert "completed" in result["reason"]
        assert "2 findings" in result["reason"]

    def test_running_phase(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running", "current_target": "src/"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = sessionstart_run({})
        assert result is not None
        assert "running" in result["reason"]

    def test_empty_state(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = sessionstart_run({})
        assert result is None


# --- PreToolUse hook tests ---


class TestPreToolUse:
    def test_inactive_gto(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
            assert result is None

    def test_not_running_phase(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "completed"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
            assert result is None

    def test_non_warn_tool(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({"tool_name": "Read", "tool_input": {}})
            assert result is None

    def test_block_destructive_command(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({
                "tool_name": "Bash",
                "tool_input": {"command": "git reset --hard HEAD"},
            })
        assert result is not None
        assert result["decision"] == "block"
        assert "destructive" in result["reason"]

    def test_block_rm_rf(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /tmp/thing"},
            })
        assert result is not None
        assert result["decision"] == "block"

    def test_block_rm_separate_flags(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({
                "tool_name": "Bash",
                "tool_input": {"command": "rm -r -f /tmp/thing"},
            })
        assert result is not None
        assert result["decision"] == "block"

    def test_block_git_clean(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({
                "tool_name": "Bash",
                "tool_input": {"command": "git clean -f ."},
            })
        assert result is not None
        assert result["decision"] == "block"

    def test_allow_safe_bash(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = pretooluse_run({
                "tool_name": "Bash",
                "tool_input": {"command": "python -m pytest tests/"},
            })
        assert result is None


# --- PostToolUse hook tests ---


class TestIsFailure:
    def test_empty(self):
        assert _is_failure("") is False
        assert _is_failure(None) is False

    def test_error(self):
        assert _is_failure("Error: something broke") is True
        assert _is_failure("Traceback (most recent call)") is True

    def test_normal_output(self):
        assert _is_failure("All tests passed") is False


class TestPostToolUse:
    def test_inactive_gto(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = posttooluse_run({"tool_name": "Bash", "tool_input": {}, "tool_output": ""})
            assert result is None

    def test_failure_capture(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = posttooluse_run({
                "tool_name": "Bash",
                "tool_input": {"command": "pytest"},
                "tool_output": "Error: test failed",
            })
        # Should not block, just capture
        assert result is None
        # Check failure was logged
        log_file = artifacts / "logs" / "failures.jsonl"
        assert log_file.exists()
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["tool"] == "Bash"

    def test_validate_good_artifact(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        artifact_path = artifacts / "outputs" / "artifact.json"
        _write_artifact(artifact_path, {
            "terminal_id": "test-term",
            "machine_output": ["RNS|D|1|📋|Findings", "RNS|Z|0|NONE"],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = posttooluse_run({
                "tool_name": "Write",
                "tool_input": {"file_path": str(artifact_path)},
                "tool_output": "",
            })
        assert result is None

    def test_validate_bad_json_artifact(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        artifact_path = artifacts / "outputs" / "artifact.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("NOT JSON{{{", encoding="utf-8")
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = posttooluse_run({
                "tool_name": "Write",
                "tool_input": {"file_path": str(artifact_path)},
                "tool_output": "",
            })
        assert result is not None
        assert result["decision"] == "warn"
        assert "invalid JSON" in result["reason"]

    def test_validate_missing_rns_markers(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "running"})
        artifact_path = artifacts / "outputs" / "artifact.json"
        _write_artifact(artifact_path, {
            "terminal_id": "test-term",
            "machine_output": ["some line"],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = posttooluse_run({
                "tool_name": "Write",
                "tool_input": {"file_path": str(artifact_path)},
                "tool_output": "",
            })
        assert result is not None
        assert result["decision"] == "warn"
        assert "RNS" in result["reason"]


# --- Stop hook tests ---


class TestStop:
    def test_inactive_gto(self, tmp_path):
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
            assert result is None

    def test_no_verification_required(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {"phase": "completed", "verification_required": False})
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
        assert result is None

    def test_incomplete_phase(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {
            "phase": "running",
            "verification_required": True,
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
        assert result is not None
        assert result["decision"] == "block"
        assert "phase" in result["reason"]

    def test_missing_artifact(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        _write_state(artifacts, {
            "phase": "completed",
            "verification_required": True,
            "last_artifact": str(tmp_path / "nonexistent.json"),
            "expected_artifacts": [str(tmp_path / "nonexistent.json")],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
        assert result is not None
        assert result["decision"] == "block"
        assert "missing" in result["reason"]

    def test_valid_completion(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        artifact_path = artifacts / "outputs" / "artifact.json"
        _write_artifact(artifact_path, {
            "terminal_id": "test-term",
            "session_id": "s1",
            "findings": [],
            "machine_output": ["RNS|D|1|📋|Findings", "RNS|Z|0|NONE"],
        })
        _write_state(artifacts, {
            "phase": "completed",
            "verification_required": True,
            "last_artifact": str(artifact_path),
            "expected_artifacts": [str(artifact_path)],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
        assert result is None

    def test_artifact_missing_fields(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        artifact_path = artifacts / "outputs" / "artifact.json"
        _write_artifact(artifact_path, {"terminal_id": "test-term"})
        _write_state(artifacts, {
            "phase": "completed",
            "verification_required": True,
            "last_artifact": str(artifact_path),
            "expected_artifacts": [str(artifact_path)],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
        assert result is not None
        assert result["decision"] == "block"
        assert "missing field" in result["reason"]

    def test_artifact_missing_rns_markers(self, tmp_path):
        artifacts = tmp_path / ".claude" / ".artifacts" / "test-term" / "gto"
        artifact_path = artifacts / "outputs" / "artifact.json"
        _write_artifact(artifact_path, {
            "terminal_id": "test-term",
            "session_id": "s1",
            "findings": [],
            "machine_output": ["no markers here"],
        })
        _write_state(artifacts, {
            "phase": "completed",
            "verification_required": True,
            "last_artifact": str(artifact_path),
            "expected_artifacts": [str(artifact_path)],
        })
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
            result = stop_run({})
        assert result is not None
        assert result["decision"] == "block"
        assert "RNS|D|" in result["reason"]
