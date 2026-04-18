"""Tests for gto_failure_capture module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hooks.gto_failure_capture import (
    classify_gto_failure,
    extract_missing_module,
    log_failure_pattern,
)


class TestClassifyGtoFailure:
    """Tests for classify_gto_failure function."""

    def test_viability_validation_failure(self) -> None:
        """Test classification of viability validation failures."""
        result = classify_gto_failure(
            "python gto_orchestrator.py --project-root /invalid", "ValueError: invalid project root"
        )
        assert result["category"] == "viability-validation"
        assert result["severity"] == "high"

    def test_import_error_classification(self) -> None:
        """Test classification of import errors."""
        result = classify_gto_failure(
            "python gto_orchestrator.py", "ImportError: No module named 'pydantic'"
        )
        assert result["category"] == "dependency-missing"
        assert result["severity"] == "high"

    def test_handoff_timeout_classification(self) -> None:
        """Test classification of handoff timeout."""
        result = classify_gto_failure(
            "python gto_orchestrator.py with handoff", "TimeoutError: handoff chain timeout"
        )
        assert result["category"] == "handoff-timeout"
        assert result["severity"] == "medium"

    def test_state_access_error_classification(self) -> None:
        """Test classification of state access errors."""
        result = classify_gto_failure(
            "python gto_orchestrator.py state operation",
            "PermissionError: state file access denied",
        )
        assert result["category"] == "state-access-error"
        assert result["severity"] == "high"

    def test_git_repository_error_classification(self) -> None:
        """Test classification of git repository errors."""
        result = classify_gto_failure(
            "python gto_orchestrator.py git operation", "GitError: repository not found"
        )
        assert result["category"] == "git-repository-error"
        assert result["severity"] == "medium"

    def test_generic_gto_failure(self) -> None:
        """Test classification of generic GTO failures."""
        result = classify_gto_failure("python gto_orchestrator.py", "Some unexpected error")
        assert result["category"] == "gto-unknown"
        assert result["severity"] == "medium"


class TestExtractMissingModule:
    """Tests for extract_missing_module function."""

    def test_extract_from_no_module_named(self) -> None:
        """Test extraction from 'No module named' error."""
        result = extract_missing_module("No module named 'pydantic'")
        assert result == "pydantic"

    def test_extract_from_cannot_import(self) -> None:
        """Test extraction from 'cannot import name' error."""
        result = extract_missing_module("cannot import name 'SomeClass'")
        assert result == "SomeClass"

    def test_extract_unknown_module(self) -> None:
        """Test extraction when module cannot be determined."""
        result = extract_missing_module("Some unrelated error")
        assert result == "<unknown>"


class TestLogFailurePattern:
    """Tests for log_failure_pattern function."""

    def test_logs_to_failure_patterns_directory(self, tmp_path: Path, monkeypatch) -> None:
        """Test failure pattern is logged to correct directory."""
        # Change to tmp_path to avoid polluting .claude/failure-patterns/
        monkeypatch.chdir(tmp_path)
        failure_data = {
            "category": "test-category",
            "severity": "low",
            "remediation": "Test remediation",
            "pattern": "Test pattern",
            "raw_error": "Test error",
        }
        log_path = log_failure_pattern(failure_data)
        assert log_path.exists()
        assert "test-category" in str(log_path)
