"""Tests for gap_reviewer agent — handoff write/read round-trip and context injection."""
import json
import pytest
from pathlib import Path

from skills.gto.agents.gap_reviewer import write_handoff, read_result
from skills.gto.models import Finding, EvidenceRef, AgentResult


def _make_finding(fid: str = "TEST-001", title: str = "Test finding") -> Finding:
    return Finding(
        id=fid,
        title=title,
        description="Test description",
        source_type="detector",
        source_name="test_detector",
        domain="quality",
        gap_type="test_gap",
        severity="medium",
        evidence_level="verified",
        action="recover",
        priority="medium",
    )


class TestWriteHandoff:
    def test_writes_valid_json(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [_make_finding()])
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["role"] == "gap_reviewer"

    def test_includes_detected_facts(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [_make_finding(title="Missing README")])
        data = json.loads(path.read_text(encoding="utf-8"))
        assert any("Missing README" in f["claim"] for f in data["detected_facts"])

    def test_includes_source_in_facts(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [_make_finding()])
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["detected_facts"][0]["source"] == "test_detector"

    def test_includes_file_in_source(self, tmp_path):
        f = _make_finding()
        f.file = "src/main.py"
        f.line = 42
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [f])
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "src/main.py:42" in data["detected_facts"][0]["source"]

    def test_includes_session_outcomes(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        outcomes = [{"category": "deferred_item", "content": "clean up later"}]
        write_handoff(path, [], session_outcomes=outcomes)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert any("clean up later" in f["claim"] for f in data["detected_facts"])

    def test_includes_changed_files(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [], changed_files=["src/main.py", "tests/test_main.py"])
        data = json.loads(path.read_text(encoding="utf-8"))
        assert any("src/main.py" in f["claim"] for f in data["detected_facts"])

    def test_limits_changed_files_to_20(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        files = [f"file_{i}.py" for i in range(30)]
        write_handoff(path, [], changed_files=files)
        data = json.loads(path.read_text(encoding="utf-8"))
        file_claims = [f for f in data["detected_facts"] if "File changed" in f["claim"]]
        assert len(file_claims) == 20

    def test_includes_signals_absent(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [], detectors_empty=["stuckness_detector", "context_boundary_detector"])
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["signals_absent"]) == 2
        assert data["signals_absent"][0]["detector"] == "stuckness_detector"

    def test_includes_session_context(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [], session_context={"terminal_id": "t1", "git_sha": "abc123"})
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["session_context"]["terminal_id"] == "t1"

    def test_creates_parent_directory(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "gap_reviewer_handoff.json"
        write_handoff(path, [])
        assert path.exists()

    def test_output_path_in_handoff(self, tmp_path):
        path = tmp_path / "gap_reviewer_handoff.json"
        write_handoff(path, [])
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["output_path"].endswith("gap_reviewer_result.json")


class TestReadResult:
    def test_missing_file_returns_failure(self, tmp_path):
        result = read_result(tmp_path / "nope.json")
        assert result.success is False
        assert result.findings == []

    def test_invalid_json_returns_failure(self, tmp_path):
        path = tmp_path / "gap_reviewer_result.json"
        path.write_text("not json", encoding="utf-8")
        result = read_result(path)
        assert result.success is False

    def test_reads_review_sections(self, tmp_path):
        path = tmp_path / "gap_reviewer_result.json"
        path.write_text(json.dumps({
            "review": {
                "facts": [{"claim": "test fact", "source": "detector"}],
                "inferences": [{"hypothesis": "might break", "confidence": "medium"}],
                "unknowns": [{"question": "will it scale?"}],
                "recommendations": [{"action": "add tests", "goal": "coverage"}],
            },
            "findings": [],
        }), encoding="utf-8")
        result = read_result(path)
        assert result.success is True
        assert "FACT" in result.raw_notes
        assert "INFERENCE" in result.raw_notes
        assert "UNKNOWN" in result.raw_notes
        assert "RECOMMENDATION" in result.raw_notes

    def test_reads_new_findings(self, tmp_path):
        path = tmp_path / "gap_reviewer_result.json"
        path.write_text(json.dumps({
            "review": {"facts": [], "inferences": [], "unknowns": [], "recommendations": []},
            "findings": [{
                "id": "GAPR-qual-001",
                "title": "Missing error handling",
                "description": "No try/except around file reads",
                "domain": "quality",
                "gap_type": "review_gap",
                "severity": "high",
                "action": "realize",
                "priority": "high",
            }],
        }), encoding="utf-8")
        result = read_result(path)
        assert result.success is True
        assert len(result.findings) == 1
        assert result.findings[0].id == "GAPR-qual-001"

    def test_bare_array_format(self, tmp_path):
        path = tmp_path / "gap_reviewer_result.json"
        path.write_text(json.dumps([{
            "id": "GAPR-test-001",
            "title": "Bare finding",
            "description": "test",
            "domain": "quality",
            "gap_type": "test",
            "severity": "low",
            "action": "realize",
            "priority": "low",
        }]), encoding="utf-8")
        result = read_result(path)
        assert result.success is True
        assert len(result.findings) == 1

    def test_rejected_findings_excluded(self, tmp_path):
        path = tmp_path / "gap_reviewer_result.json"
        path.write_text(json.dumps({
            "review": {"facts": [], "inferences": [], "unknowns": [], "recommendations": []},
            "findings": [
                {"id": "GAPR-001", "title": "kept", "description": "valid", "domain": "quality", "severity": "low"},
                {"id": "GAPR-002", "title": "rejected", "description": "bad", "domain": "quality", "severity": "low", "status": "rejected"},
            ],
        }), encoding="utf-8")
        result = read_result(path)
        assert len(result.findings) == 1
        assert result.findings[0].title == "kept"


class TestRoundTrip:
    def test_handoff_then_result(self, tmp_path):
        handoff_path = tmp_path / "gap_reviewer_handoff.json"
        result_path = tmp_path / "gap_reviewer_result.json"

        write_handoff(
            handoff_path,
            [_make_finding("TEST-001", "Missing docs")],
            session_outcomes=[{"category": "deferred_item", "content": "add later"}],
            changed_files=["README.md"],
            session_context={"terminal_id": "t1"},
        )

        # Verify handoff is valid
        data = json.loads(handoff_path.read_text(encoding="utf-8"))
        assert len(data["detected_facts"]) >= 3  # finding + outcome + changed file

        # Simulate agent writing result
        result_path.write_text(json.dumps({
            "review": {
                "facts": [{"claim": "Missing docs detected", "source": "test_detector"}],
                "inferences": [],
                "unknowns": [],
                "recommendations": [{"action": "Write README", "goal": "documentation"}],
            },
            "findings": [],
        }), encoding="utf-8")

        result = read_result(result_path)
        assert result.success is True
        assert "Missing docs" in result.raw_notes
