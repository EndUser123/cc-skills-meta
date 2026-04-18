"""Tests for dependency_checker module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.dependency_checker import (
    DependencyChecker,
    DependencyIssue,
    DependencyResult,
    check_dependencies,
)


class TestDependencyChecker:
    """Smoke tests for DependencyChecker."""

    def test_get_installed_packages_uses_sys_executable(self, tmp_path: Path) -> None:
        """_get_installed_packages uses sys.executable, not bare 'pip'.

        Regression test: bare 'pip' fails in venvs and special Python environments.
        The correct invocation is 'python -m pip' via sys.executable.
        """
        import subprocess
        from unittest.mock import Mock, patch

        checker = DependencyChecker(tmp_path)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"

        with patch.object(subprocess, "run", return_value=mock_result) as mock_run:
            checker._get_installed_packages()
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            cmd = call_args.kwargs.get("command") or call_args.args[0]
            # Must use sys.executable, NOT bare 'pip'
            assert cmd[0] == sys.executable, (
                f"Expected sys.executable ({sys.executable}) but got {cmd[0]}. "
                "pip must be invoked via 'python -m pip' to work in venvs."
            )
            assert cmd[1] == "-m", f"Expected '-m' flag but got {cmd[1]}"
            assert cmd[2] == "pip", f"Expected 'pip' but got {cmd[2]}"

    def test_checker_instantiation(self, tmp_path: Path) -> None:
        """Test checker can be instantiated."""
        checker = DependencyChecker(tmp_path)
        assert checker is not None

    def test_check_dependencies_empty_dir(self, tmp_path: Path) -> None:
        """Test checking empty directory."""
        result = check_dependencies(tmp_path)
        assert isinstance(result, DependencyResult)


class TestDependencyResult:
    """Tests for DependencyResult dataclass."""

    def test_result_dataclass(self) -> None:
        """Test result can be constructed."""
        result = DependencyResult(
            issues=[],
            packages_checked=0,
            outdated_count=0,
            vulnerable_count=0,
            missing_count=0,
            unused_count=0,
        )
        assert result.packages_checked == 0
        assert len(result.issues) == 0


class TestDependencyIssue:
    """Tests for DependencyIssue dataclass."""

    def test_issue_dataclass(self) -> None:
        """Test issue can be constructed."""
        issue = DependencyIssue(
            issue_type="missing",
            package_name="test-package",
            current_version=None,
            latest_version=None,
            severity="medium",
            description="Package not found",
        )
        assert issue.package_name == "test-package"
        assert issue.issue_type == "missing"
        assert issue.severity == "medium"
