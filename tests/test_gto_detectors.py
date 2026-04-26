"""Tests for GTO deterministic detectors."""
import pytest
from pathlib import Path
import tempfile
import os

from skills.gto.__lib.detectors import run_basic_detectors, _count_todos


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
    def test_git_repo_with_readme_no_todos(self, git_repo):
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

    def test_todo_markers(self, git_repo):
        py_file = git_repo / "example.py"
        py_file.write_text("# TODO: fix this\n# FIXME: broken\npass\n", encoding="utf-8")
        findings = run_basic_detectors(git_repo, "t1", "s1", "sha")
        ids = [f.id for f in findings]
        assert "QUAL-001" in ids

    def test_finding_fields_populated(self, bare_dir):
        findings = run_basic_detectors(bare_dir, "t1", "s1", "sha")
        git_finding = next(f for f in findings if f.id == "GIT-001")
        assert git_finding.severity == "high"
        assert git_finding.domain == "git"
        assert git_finding.source_type == "detector"
        assert git_finding.terminal_id == "t1"
        assert git_finding.session_id == "s1"
        assert git_finding.git_sha == "sha"


class TestCountTodos:
    def test_count_todos(self, tmp_path):
        py = tmp_path / "a.py"
        py.write_text("# TODO: x\n# FIXME: y\n# HACK: z\n", encoding="utf-8")
        assert _count_todos(tmp_path) == 3

    def test_ignores_non_py(self, tmp_path):
        (tmp_path / "readme.md").write_text("# TODO: not counted\n", encoding="utf-8")
        assert _count_todos(tmp_path) == 0

    def test_ignores_git_dirs(self, tmp_path):
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "mod.py").write_text("# TODO: ignored\n", encoding="utf-8")
        assert _count_todos(tmp_path) == 0
