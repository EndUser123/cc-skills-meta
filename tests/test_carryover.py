"""Tests for GTO carryover persistence and resolution tracking."""
import pytest
from pathlib import Path

from skills.gto.models import Finding, EvidenceRef
from skills.gto.__lib.carryover import (
    load_carryover,
    save_carryover,
    load_carryover_open_only,
    prune_carryover,
)


def make_finding(
    fid: str = "TEST-001",
    status: str = "open",
    file: str | None = None,
) -> Finding:
    return Finding(
        id=fid,
        title="Test finding",
        description="desc",
        source_type="detector",
        source_name="test",
        domain="test",
        gap_type="test",
        severity="medium",
        evidence_level="verified",
        status=status,
        file=file,
    )


class TestSaveCarryover:
    def test_saves_open_findings(self, tmp_path):
        f = make_finding(status="open")
        save_carryover(tmp_path, [f])
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 1
        assert loaded[0].status == "open"

    def test_saves_resolved_findings(self, tmp_path):
        f = make_finding(status="resolved")
        save_carryover(tmp_path, [f])
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 1
        assert loaded[0].status == "resolved"

    def test_rejects_rejected_findings(self, tmp_path):
        f = make_finding(status="rejected")
        save_carryover(tmp_path, [f])
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 0

    def test_mixed_statuses(self, tmp_path):
        findings = [
            make_finding(fid="F1", status="open"),
            make_finding(fid="F2", status="resolved"),
            make_finding(fid="F3", status="rejected"),
        ]
        save_carryover(tmp_path, findings)
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 2
        statuses = {f.id: f.status for f in loaded}
        assert "F1" in statuses
        assert "F2" in statuses
        assert "F3" not in statuses


class TestLoadCarryoverOpenOnly:
    def test_returns_only_open(self, tmp_path):
        findings = [
            make_finding(fid="F1", status="open"),
            make_finding(fid="F2", status="resolved"),
        ]
        save_carryover(tmp_path, findings)
        open_only = load_carryover_open_only(tmp_path)
        assert len(open_only) == 1
        assert open_only[0].id == "F1"

    def test_returns_empty_when_all_resolved(self, tmp_path):
        findings = [make_finding(status="resolved")]
        save_carryover(tmp_path, findings)
        assert load_carryover_open_only(tmp_path) == []

    def test_returns_empty_when_no_file(self, tmp_path):
        assert load_carryover_open_only(tmp_path) == []


class TestPruneCarryover:
    def test_no_prune_under_limit(self, tmp_path):
        findings = [make_finding(fid=f"R{i}", status="resolved") for i in range(5)]
        save_carryover(tmp_path, findings)
        prune_carryover(tmp_path, max_resolved=10)
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 5

    def test_prunes_over_limit(self, tmp_path):
        findings = [make_finding(fid=f"R{i}", status="resolved") for i in range(10)]
        save_carryover(tmp_path, findings)
        prune_carryover(tmp_path, max_resolved=3)
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 3

    def test_prune_keeps_open_findings(self, tmp_path):
        findings = [
            make_finding(fid="OPEN", status="open"),
            *[make_finding(fid=f"R{i}", status="resolved") for i in range(10)],
        ]
        save_carryover(tmp_path, findings)
        prune_carryover(tmp_path, max_resolved=3)
        loaded = load_carryover(tmp_path)
        ids = {f.id for f in loaded}
        assert "OPEN" in ids


class TestRoundTrip:
    def test_save_and_load_preserves_fields(self, tmp_path):
        original = Finding(
            id="CARRY-001",
            title="Carryover test",
            description="test desc",
            source_type="carryover",
            source_name="carryover",
            domain="quality",
            gap_type="techdebt",
            severity="high",
            evidence_level="verified",
            status="resolved",
            file="src/main.py",
            evidence=[EvidenceRef(kind="auto_resolved", value="file_edited")],
        )
        save_carryover(tmp_path, [original])
        loaded = load_carryover(tmp_path)
        assert len(loaded) == 1
        f = loaded[0]
        assert f.id == "CARRY-001"
        assert f.status == "resolved"
        assert f.file == "src/main.py"
        assert f.evidence[0].kind == "auto_resolved"
