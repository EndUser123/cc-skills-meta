"""Tests for finding resolution checker."""
import pytest
from pathlib import Path

from skills.gto.models import Finding, EvidenceRef
from skills.gto.__lib.resolve import resolve_findings


def make_finding(
    fid: str = "TEST-001",
    file: str | None = None,
    status: str = "open",
    evidence: list[EvidenceRef] | None = None,
    domain: str = "test",
) -> Finding:
    return Finding(
        id=fid,
        title="Test finding",
        description="desc",
        source_type="detector",
        source_name="test",
        domain=domain,
        gap_type="test",
        severity="medium",
        evidence_level="verified",
        status=status,
        file=file,
        evidence=evidence or [],
    )


class TestFileEditMatch:
    def test_matching_file_resolved(self):
        findings = [make_finding(file="src/foo.py")]
        changed = {"src/foo.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        assert result[0].status == "resolved"

    def test_non_matching_file_stays_open(self):
        findings = [make_finding(file="src/bar.py")]
        changed = {"src/other.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        assert result[0].status == "open"

    def test_backslash_file_matches_forward_slash_change(self):
        findings = [make_finding(file=r"src\foo.py")]
        changed = {"src/foo.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        assert result[0].status == "resolved"

    def test_no_file_field_stays_open(self):
        findings = [make_finding(file=None)]
        changed = {"src/foo.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        assert result[0].status == "open"


class TestAlreadyResolved:
    def test_already_resolved_stays_resolved(self):
        findings = [make_finding(status="resolved")]
        result = resolve_findings(findings, set(), Path("/fake"))
        assert result[0].status == "resolved"


class TestDetectorRecheck:
    def test_doc001_resolved_when_readme_exists(self, tmp_path):
        (tmp_path / "README.md").write_text("# Hi\n", encoding="utf-8")
        findings = [make_finding(fid="DOC-001")]
        result = resolve_findings(findings, set(), tmp_path)
        assert result[0].status == "resolved"

    def test_doc001_stays_open_when_no_readme(self, tmp_path):
        findings = [make_finding(fid="DOC-001")]
        result = resolve_findings(findings, set(), tmp_path)
        assert result[0].status == "open"

    def test_git001_resolved_when_git_exists(self, tmp_path):
        (tmp_path / ".git").mkdir()
        findings = [make_finding(fid="GIT-001")]
        result = resolve_findings(findings, set(), tmp_path)
        assert result[0].status == "resolved"


class TestResolvedEvidence:
    def test_resolved_gets_auto_resolved_evidence(self):
        findings = [make_finding(file="src/a.py")]
        changed = {"src/a.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        kinds = [e.kind for e in result[0].evidence]
        assert "auto_resolved" in kinds

    def test_original_evidence_preserved(self):
        orig = EvidenceRef(kind="path", value="/fake/src/a.py")
        findings = [make_finding(file="src/a.py", evidence=[orig])]
        changed = {"src/a.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        kinds = [e.kind for e in result[0].evidence]
        assert "path" in kinds and "auto_resolved" in kinds


class TestMultipleFindings:
    def test_mixed_resolution(self):
        findings = [
            make_finding(fid="F1", file="src/a.py"),
            make_finding(fid="F2", file="src/b.py"),
            make_finding(fid="F3", file=None),
        ]
        changed = {"src/a.py"}
        result = resolve_findings(findings, changed, Path("/fake"))
        statuses = {f.id: f.status for f in result}
        assert statuses["F1"] == "resolved"
        assert statuses["F2"] == "open"
        assert statuses["F3"] == "open"
