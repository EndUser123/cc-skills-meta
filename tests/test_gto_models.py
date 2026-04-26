"""Tests for GTO core models."""
import pytest
from dataclasses import asdict

from skills.gto.models import Finding, EvidenceRef, GTOArtifact, AgentResult


def _make_finding(**overrides):
    defaults = dict(
        id="TEST-001",
        title="Test finding",
        description="A test finding for unit tests",
        source_type="detector",
        source_name="test",
        domain="quality",
        gap_type="testgap",
        severity="medium",
        evidence_level="verified",
    )
    defaults.update(overrides)
    return Finding(**defaults)


class TestFinding:
    def test_to_dict_roundtrip(self):
        f = _make_finding()
        d = f.to_dict()
        assert d["id"] == "TEST-001"
        assert d["domain"] == "quality"
        assert d["evidence"] == []
        assert d["tags"] == []

    def test_default_values(self):
        f = _make_finding()
        assert f.action == "recover"
        assert f.priority == "medium"
        assert f.status == "open"
        assert f.scope == "local"
        assert f.unverified is False
        assert f.owner_skill is None

    def test_evidence_ref(self):
        f = _make_finding(evidence=[EvidenceRef(kind="path", value="/foo.py")])
        assert len(f.evidence) == 1
        assert f.evidence[0].kind == "path"

    def test_optional_fields_none(self):
        f = _make_finding()
        assert f.file is None
        assert f.line is None
        assert f.git_sha is None
        assert f.freshness is None


class TestGTOArtifact:
    def test_empty_creates_valid_artifact(self):
        a = GTOArtifact.empty(
            mode="quick",
            terminal_id="t1",
            session_id="s1",
            target="test-project",
            git_sha="abc123",
        )
        assert a.artifact_version == "1.0.0"
        assert a.mode == "quick"
        assert a.terminal_id == "t1"
        assert a.findings == []
        assert a.machine_output == []
        assert a.health_score is None
        assert a.freshness == "unknown"

    def test_empty_timestamp(self):
        a = GTOArtifact.empty(mode="full", terminal_id="t", session_id="s", target="x", git_sha=None)
        assert a.created_at  # not empty
        assert "T" in a.created_at  # ISO format


class TestAgentResult:
    def test_defaults(self):
        r = AgentResult(agent="test", findings=[])
        assert r.raw_notes == ""
        assert r.success is True

    def test_with_findings(self):
        f = _make_finding()
        r = AgentResult(agent="domain_analyzer", findings=[f])
        assert len(r.findings) == 1
        assert r.findings[0].source_type == "detector"
