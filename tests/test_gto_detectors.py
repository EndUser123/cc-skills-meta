"""Tests for GTO deterministic detectors."""
import pytest
from pathlib import Path

from skills.gto.__lib.detectors import run_basic_detectors


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with README."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def bare_dir(tmp_path):
    """Create a directory without .git or README."""
    return tmp_path


class TestRunBasicDetectors:
    def test_git_repo_with_readme_no_findings(self, git_repo):
        findings = run_basic_detectors(git_repo, "t1", "s1", "sha")
        assert len(findings) == 0

    def test_no_git_dir(self, bare_dir):
        findings = run_basic_detectors(bare_dir, "t1", "s1", None)
        ids = [f.id for f in findings]
        assert "GIT-001" in ids

    def test_no_readme(self, tmp_path):
        (tmp_path / ".git").mkdir()
        findings = run_basic_detectors(tmp_path, "t1", "s1", "sha")
        ids = [f.id for f in findings]
        assert "DOC-001" in ids

    def test_finding_fields_populated(self, bare_dir):
        findings = run_basic_detectors(bare_dir, "t1", "s1", "sha")
        git_finding = next(f for f in findings if f.id == "GIT-001")
        assert git_finding.severity == "high"
        assert git_finding.domain == "git"
        assert git_finding.source_type == "detector"
        assert git_finding.terminal_id == "t1"
        assert git_finding.session_id == "s1"
        assert git_finding.git_sha == "sha"
