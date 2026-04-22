#!/usr/bin/env python
"""
Tests for scan_package_quality.py - PHASE 4.5: Package Quality Scanning

Tests cover:
- Security scanning (bandit, safety)
- Dependency auditing (pip-audit)
- Badge validation
- Quality metrics
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module to test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import scan_package_quality


class TestColors:
    """Test ANSI color codes class."""

    def test_colors_defined(self):
        """Verify all color codes are defined."""
        assert scan_package_quality.Colors.BLUE == "\033[0;34m"
        assert scan_package_quality.Colors.GREEN == "\033[0;32m"
        assert scan_package_quality.Colors.YELLOW == "\033[1;33m"
        assert scan_package_quality.Colors.RED == "\033[0;31m"
        assert scan_package_quality.Colors.NC == "\033[0m"


class TestLoggingFunctions:
    """Test logging functions."""

    def test_log_info(self, capsys):
        """Test info message logging."""
        scan_package_quality.log_info("Test info")
        captured = capsys.readouterr()
        assert "[INFO]" in captured.out
        assert "Test info" in captured.out

    def test_log_success(self, capsys):
        """Test success message logging."""
        scan_package_quality.log_success("Test success")
        captured = capsys.readouterr()
        assert "[SUCCESS]" in captured.out
        assert "Test success" in captured.out

    def test_log_warning(self, capsys):
        """Test warning message logging."""
        scan_package_quality.log_warning("Test warning")
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.out
        assert "Test warning" in captured.out

    def test_log_error(self, capsys):
        """Test error message logging."""
        scan_package_quality.log_error("Test error")
        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out
        assert "Test error" in captured.out


class TestRunCommand:
    """Test command execution."""

    def test_run_command_success(self):
        """Test successful command execution."""
        result = scan_package_quality.run_command(["echo", "test"], check=False)
        assert result.returncode == 0
        assert "test" in result.stdout

    def test_run_command_failure(self):
        """Test failed command execution."""
        with pytest.raises(subprocess.CalledProcessError):
            scan_package_quality.run_command(["false"])


class TestCheckToolInstalled:
    """Test tool installation detection."""

    @patch("scan_package_quality.run_command")
    def test_check_tool_installed_true(self, mock_run):
        """Test detection when tool is installed."""
        mock_run.return_value = MagicMock(returncode=0)
        assert scan_package_quality.check_tool_installed("pytest") is True

    @patch("scan_package_quality.run_command")
    def test_check_tool_installed_false(self, mock_run):
        """Test detection when tool is not installed."""
        mock_run.side_effect = Exception("Command not found")
        assert scan_package_quality.check_tool_installed("bandit") is False


class TestRunBanditScan:
    """Test bandit security scanning."""

    @patch("scan_package_quality.check_tool_installed")
    def test_bandit_not_installed(self, mock_check):
        """Test bandit scan when tool not installed."""
        mock_check.return_value = False
        result = scan_package_quality.run_bandit_scan(Path("/tmp"))
        assert result["installed"] is False
        assert result["issues"] == 0

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_bandit_no_issues(self, mock_run, mock_check, tmp_path):
        """Test bandit scan with no issues."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout='{"results": []}')

        # Create a test Python file
        (tmp_path / "test.py").write_text("print('hello')\n")

        result = scan_package_quality.run_bandit_scan(tmp_path)
        assert result["installed"] is True
        assert result["issues"] == 0

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_bandit_with_issues(self, mock_run, mock_check):
        """Test bandit scan with issues found."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='{"results": [{"issue_severity": "HIGH", "issue_text": "Test issue"}]}',
        )

        # Use tempfile to avoid pytest's "test_" prefixed directories
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Create a non-test Python file (won't be filtered)
            (temp_path / "main.py").write_text("print('hello')\n")

            result = scan_package_quality.run_bandit_scan(temp_path)
            assert result["installed"] is True
            assert result["issues"] == 1

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_bandit_no_python_files(self, mock_run, mock_check, tmp_path):
        """Test bandit scan with no Python files."""
        mock_check.return_value = True

        # Create only non-Python files
        (tmp_path / "test.txt").write_text("hello\n")

        result = scan_package_quality.run_bandit_scan(tmp_path)
        assert result["installed"] is True
        assert result.get("skipped") is True


class TestRunSafetyScan:
    """Test safety dependency check."""

    @patch("scan_package_quality.check_tool_installed")
    def test_safety_not_installed(self, mock_check):
        """Test safety scan when tool not installed."""
        mock_check.return_value = False
        result = scan_package_quality.run_safety_scan(Path("/tmp"))
        assert result["installed"] is False

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_safety_no_vulnerabilities(self, mock_run, mock_check, tmp_path):
        """Test safety scan with no vulnerabilities."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="[]")

        # Create requirements file
        (tmp_path / "requirements.txt").write_text("pytest>=7.0\n")

        result = scan_package_quality.run_safety_scan(tmp_path)
        assert result["installed"] is True
        assert result["vulnerabilities"] == 0

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_safety_with_vulnerabilities(self, mock_run, mock_check, tmp_path):
        """Test safety scan with vulnerabilities found."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='[{"package": "requests", "id": "12345", "affected_versions": ["2.0.0"]}]',
        )

        (tmp_path / "requirements.txt").write_text("requests==2.0.0\n")

        result = scan_package_quality.run_safety_scan(tmp_path)
        assert result["installed"] is True
        assert result["vulnerabilities"] == 1


class TestRunPipAudit:
    """Test pip-audit vulnerability scanning."""

    @patch("scan_package_quality.check_tool_installed")
    def test_pip_audit_not_installed(self, mock_check):
        """Test pip-audit when tool not installed."""
        mock_check.return_value = False
        result = scan_package_quality.run_pip_audit(Path("/tmp"))
        assert result["installed"] is False

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_pip_audit_no_vulnerabilities(self, mock_run, mock_check):
        """Test pip-audit with no vulnerabilities."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="[]")

        result = scan_package_quality.run_pip_audit(Path("/tmp"))
        assert result["installed"] is True
        assert result["vulnerabilities"] == 0

    @patch("scan_package_quality.check_tool_installed")
    @patch("scan_package_quality.run_command")
    def test_pip_audit_with_vulnerabilities(self, mock_run, mock_check):
        """Test pip-audit with vulnerabilities found."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='[{"name": "requests", "vuln_ids": ["CVE-2023-1234"]}]',
        )

        result = scan_package_quality.run_pip_audit(Path("/tmp"))
        assert result["installed"] is True
        assert result["vulnerabilities"] == 1


class TestValidateBadges:
    """Test badge validation."""

    def test_validate_badges_with_badges(self, tmp_path):
        """Test badge validation with badges present."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text(
            "# Test\n\n"
            "![Badge](https://img.shields.io/badge/test-success-green)\n"
            "![Version](https://img.shields.io/badge/version-1.0.0-blue)\n"
        )

        result = scan_package_quality.validate_badges(tmp_path)
        # Should find shields.io badges
        assert result["checked"] == 2
        assert result["invalid"] == 0

    def test_validate_badges_no_readme(self, tmp_path):
        """Test badge validation without README."""
        result = scan_package_quality.validate_badges(tmp_path)
        assert result["checked"] == 0

    def test_validate_badges_missing_workflow(self, tmp_path):
        """Test badge validation with workflow badge reference (missing workflow file)."""
        readme_path = tmp_path / "README.md"
        readme_path.write_text(
            "# Test\n\n"
            "![Badge](https://img.shields.io/badge/test-success)\n"
            "![Workflow](/.github/workflows/test.yml/badge.svg)\n"
        )

        result = scan_package_quality.validate_badges(tmp_path)
        # Should find the shields.io badge
        assert result["checked"] >= 1


class TestCheckCodeQualityMetrics:
    """Test code quality metrics."""

    def test_quality_metrics_with_files(self, tmp_path):
        """Test metrics calculation with Python files."""
        # Create Python files
        (tmp_path / "main.py").write_text("print('hello')\n" * 10)
        (tmp_path / "test_main.py").write_text("assert True\n" * 5)

        result = scan_package_quality.check_code_quality_metrics(tmp_path)
        assert result["python_files"] == 1
        assert result["test_files"] == 1
        assert result["total_lines"] == 10

    def test_quality_metrics_no_files(self, tmp_path):
        """Test metrics with no Python files."""
        result = scan_package_quality.check_code_quality_metrics(tmp_path)
        assert result["python_files"] == 0
        assert result["test_files"] == 0


class TestGenerateReport:
    """Test quality scan report generation."""

    def test_generate_report(self, tmp_path):
        """Test report generation."""
        bandit_results = {"installed": True, "issues": 0}
        safety_results = {"installed": True, "vulnerabilities": 0}
        audit_results = {"installed": True, "vulnerabilities": 0}
        badge_results = {"checked": 2, "invalid": 0, "missing": []}
        quality_metrics = {"python_files": 5, "test_files": 2, "total_lines": 500}

        report = scan_package_quality.generate_report(
            tmp_path,
            bandit_results,
            safety_results,
            audit_results,
            badge_results,
            quality_metrics,
        )

        assert report["target"] == str(tmp_path)
        assert report["bandit"] == bandit_results
        assert report["safety"] == safety_results


class TestSaveReport:
    """Test report saving."""

    def test_save_report(self, tmp_path):
        """Test saving report to file."""
        report = {"test": "data", "issues": 0}

        scan_package_quality.save_report(report, tmp_path)

        report_path = tmp_path / ".quality-report.json"
        assert report_path.exists()

        content = json.loads(report_path.read_text())
        assert content["test"] == "data"
        assert content["issues"] == 0


class TestMain:
    """Test main entry point."""

    @patch("scan_package_quality.save_report")
    @patch("scan_package_quality.check_code_quality_metrics")
    @patch("scan_package_quality.validate_badges")
    @patch("scan_package_quality.run_pip_audit")
    @patch("scan_package_quality.run_safety_scan")
    @patch("scan_package_quality.run_bandit_scan")
    @patch("sys.argv", ["scan_package_quality.py", "."])
    def test_main_success(self, *mocks):
        """Test main with successful scan."""
        # Setup mocks
        mocks[0].return_value = {"installed": True, "issues": 0}  # bandit
        mocks[1].return_value = {"installed": True, "vulnerabilities": 0}  # safety
        mocks[2].return_value = {"installed": True, "vulnerabilities": 0}  # audit
        mocks[3].return_value = {"checked": 0, "invalid": 0, "missing": []}  # badges
        mocks[4].return_value = {
            "python_files": 1,
            "test_files": 1,
            "total_lines": 100,
        }  # quality

        # Create a minimal git repo structure
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".git").mkdir()
            with patch.object(sys, "argv", ["scan_package_quality.py", str(temp_path)]):
                with pytest.raises(SystemExit) as exc_info:
                    scan_package_quality.main()
                assert exc_info.value.code == 0

    @patch("scan_package_quality.save_report")
    @patch("scan_package_quality.check_code_quality_metrics")
    @patch("scan_package_quality.validate_badges")
    @patch("scan_package_quality.run_pip_audit")
    @patch("scan_package_quality.run_safety_scan")
    @patch("scan_package_quality.run_bandit_scan")
    @patch("sys.argv", ["scan_package_quality.py", ".", "--fail-on-issues"])
    def test_main_with_issues(self, *mocks):
        """Test main with issues found and fail-on-issues flag."""
        # Setup mocks with issues
        mocks[0].return_value = {"installed": True, "issues": 2}  # bandit
        mocks[1].return_value = {"installed": True, "vulnerabilities": 1}  # safety
        mocks[2].return_value = {"installed": True, "vulnerabilities": 0}  # audit
        mocks[3].return_value = {"checked": 0, "invalid": 0, "missing": []}  # badges
        mocks[4].return_value = {
            "python_files": 1,
            "test_files": 0,
            "total_lines": 50,
        }  # quality

        # Create a minimal git repo structure
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / ".git").mkdir()
            with patch.object(
                sys,
                "argv",
                ["scan_package_quality.py", str(temp_path), "--fail-on-issues"],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    scan_package_quality.main()
                assert exc_info.value.code == 1

    @patch(
        "sys.argv",
        ["scan_package_quality.py", "X:/this_directory_does_not_exist_12345"],
    )
    def test_main_invalid_directory(self):
        """Test main with invalid directory."""
        with pytest.raises(SystemExit) as exc_info:
            scan_package_quality.main()
        assert exc_info.value.code == 1
