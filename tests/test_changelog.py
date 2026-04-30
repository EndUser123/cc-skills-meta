"""Tests for GTO changelog detector."""
import subprocess

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from skills.gto.__lib.changelog import (
    get_changed_files,
    get_commit_count,
    map_changed_files_to_skills,
    detect_changelog_findings,
    _matches_entry,
)


class TestMatchesEntry:
    def test_prefix_and_extension(self):
        assert _matches_entry("tests/test_foo.py", "tests/", ".py")

    def test_no_prefix_match(self):
        assert not _matches_entry("src/main.py", "tests/", ".py")

    def test_no_extension_match(self):
        assert not _matches_entry("tests/test_foo.txt", "tests/", ".py")

    def test_nested_path(self):
        assert _matches_entry("skills/gto/SKILL.md", "skills/", "SKILL.md")

    def test_empty_prefix_matches_any(self):
        assert _matches_entry("any/path/docs.md", "", ".md")

    def test_empty_extension_matches_any(self):
        assert _matches_entry("pyproject.toml", "", "pyproject.toml")


class TestGetChangedFiles:
    @patch("subprocess.check_output")
    def test_returns_changed_files(self, mock_run):
        mock_run.return_value = "file1.py\nfile2.py\n"
        result = get_changed_files(Path("."), "abc123", "def456")
        assert result == ["file1.py", "file2.py"]

    @patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git"))
    def test_returns_empty_on_error(self, mock_run):
        result = get_changed_files(Path("."), "abc123", "def456")
        assert result == []


class TestGetCommitCount:
    @patch("subprocess.check_output")
    def test_returns_count(self, mock_run):
        mock_run.return_value = "5\n"
        assert get_commit_count(Path("."), "abc", "def") == 5

    @patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git"))
    def test_returns_zero_on_error(self, mock_run):
        assert get_commit_count(Path("."), "abc", "def") == 0


class TestMapChangedFilesToSkills:
    def test_maps_skill_files(self):
        changed = [
            "skills/gto/SKILL.md",
            "skills/gto/orchestrator.py",
            "tests/test_gto.py",
        ]
        result = map_changed_files_to_skills(changed)
        assert "/sqa" in result
        assert "pytest" in result

    def test_no_match_returns_empty(self):
        changed = ["random.txt"]
        result = map_changed_files_to_skills(changed)
        assert result == {}


class TestDetectChangelogFindings:
    def test_returns_empty_when_no_prev_sha(self):
        result = detect_changelog_findings(
            Path("."), None, "abc123", "t1", "s1", "sha"
        )
        assert result == []

    def test_returns_empty_when_shas_match(self):
        result = detect_changelog_findings(
            Path("."), "abc123", "abc123", "t1", "s1", "sha"
        )
        assert result == []

    @patch("skills.gto.__lib.changelog.get_commit_count", return_value=3)
    @patch("skills.gto.__lib.changelog.get_changed_files")
    @patch("subprocess.check_output")
    def test_produces_findings_for_changed_files(
        self, mock_cat_file, mock_changed, mock_count
    ):
        mock_cat_file.return_value = "commit\n"
        mock_changed.return_value = [
            "skills/gto/orchestrator.py",
            "tests/test_gto.py",
        ]
        result = detect_changelog_findings(
            Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
        )
        assert len(result) >= 1
        ids = [f.id for f in result]
        assert any("CHANGELOG" in fid for fid in ids)

    @patch("skills.gto.__lib.changelog.get_changed_files", return_value=[])
    @patch("subprocess.check_output")
    def test_returns_empty_when_no_changes(self, mock_cat_file, mock_changed):
        mock_cat_file.return_value = "commit\n"
        result = detect_changelog_findings(
            Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
        )
        assert result == []

    @patch("skills.gto.__lib.changelog.get_changed_files")
    @patch("subprocess.check_output")
    def test_finding_has_correct_fields(self, mock_cat_file, mock_changed):
        mock_cat_file.return_value = "commit\n"
        mock_changed.return_value = ["skills/gto/SKILL.md"]
        result = detect_changelog_findings(
            Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
        )
        # "skills/gto/SKILL.md" matches both ("skills/", "SKILL.md", "/sqa")
        # and ("", ".md", "/docs"), plus anti-recommendation for /deps
        assert len(result) == 3
        sqa = [f for f in result if f.owner_skill == "/sqa"][0]
        assert sqa.domain == "session"
        assert sqa.gap_type == "stale_skill"
        assert sqa.action == "realize"
        assert sqa.evidence_level == "verified"
        assert len(sqa.evidence) == 1
        assert "prev1234" in sqa.evidence[0].value

    @patch("skills.gto.__lib.changelog.get_changed_files")
    @patch("subprocess.check_output")
    def test_unmatched_files_get_generic_finding(
        self, mock_cat_file, mock_changed
    ):
        mock_cat_file.return_value = "commit\n"
        mock_changed.return_value = ["unknown_file.xyz"]
        result = detect_changelog_findings(
            Path("."), "prev12345678", "curr12345678", "t1", "s1", "sha"
        )
        ids = [f.id for f in result]
        assert "CHANGELOG-UNMATCHED-001" in ids
