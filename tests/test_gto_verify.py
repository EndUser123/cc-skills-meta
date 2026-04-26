"""Tests for GTO verification."""
import pytest
import json
from pathlib import Path

from skills.gto.__lib.verify import verify_artifact, verify_state


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestVerifyArtifact:
    def test_missing_file(self, tmp_path):
        result = verify_artifact(tmp_path / "nonexistent.json")
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])

    def test_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json{{{", encoding="utf-8")
        result = verify_artifact(p)
        assert result["valid"] is False

    def test_missing_required_fields(self, tmp_path):
        p = tmp_path / "partial.json"
        _write_json(p, {"artifact_version": "1.0.0"})
        result = verify_artifact(p)
        assert result["valid"] is False
        assert any("terminal_id" in e for e in result["errors"])

    def test_valid_artifact(self, tmp_path):
        p = tmp_path / "good.json"
        _write_json(p, {
            "artifact_version": "1.0.0",
            "mode": "full",
            "terminal_id": "t1",
            "session_id": "s1",
            "target": "project",
            "findings": [],
            "machine_output": ["<!-- format: machine -->", "RNS|D|1|🔧|QUALITY", "RNS|Z|0|NONE"],
            "human_output": "No findings.",
            "verification": {},
            "coverage": {},
        })
        result = verify_artifact(p)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_missing_rns_markers(self, tmp_path):
        p = tmp_path / "no_rns.json"
        _write_json(p, {
            "artifact_version": "1.0.0", "mode": "full",
            "terminal_id": "t1", "session_id": "s1", "target": "p",
            "findings": [], "machine_output": ["some text"],
            "human_output": "", "verification": {}, "coverage": {},
        })
        result = verify_artifact(p)
        assert result["valid"] is False


class TestVerifyState:
    def test_missing_file(self, tmp_path):
        result = verify_state(tmp_path / "nonexistent.json")
        assert result["valid"] is False

    def test_wrong_phase(self, tmp_path):
        p = tmp_path / "state.json"
        _write_json(p, {"phase": "running"})
        result = verify_state(p)
        assert result["valid"] is False

    def test_completed_phase(self, tmp_path):
        p = tmp_path / "state.json"
        _write_json(p, {"phase": "completed"})
        result = verify_state(p)
        assert result["valid"] is True
