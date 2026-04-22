#!/usr/bin/env python
"""
Tests for finalize_github_repo.py - PHASE 7: Repository Finalization

Tests cover:
- GitHub Pages enablement
- Initial release creation
- Repository topics/tags
- CODEOWNERS file generation
- SECURITY.md file generation
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module to test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import finalize_github_repo


class TestColors:
    """Test ANSI color codes class."""

    def test_colors_defined(self):
        """Verify all color codes are defined."""
        assert finalize_github_repo.Colors.BLUE == "\033[0;34m"
        assert finalize_github_repo.Colors.GREEN == "\033[0;32m"
        assert finalize_github_repo.Colors.YELLOW == "\033[1;33m"
        assert finalize_github_repo.Colors.RED == "\033[0;31m"
        assert finalize_github_repo.Colors.NC == "\033[0m"


class TestLoggingFunctions:
    """Test logging functions."""

    def test_log_info(self, capsys):
        """Test info message logging."""
        finalize_github_repo.log_info("Test info")
        captured = capsys.readouterr()
        assert "[INFO]" in captured.out
        assert "Test info" in captured.out

    def test_log_success(self, capsys):
        """Test success message logging."""
        finalize_github_repo.log_success("Test success")
        captured = capsys.readouterr()
        assert "[SUCCESS]" in captured.out
        assert "Test success" in captured.out

    def test_log_warning(self, capsys):
        """Test warning message logging."""
        finalize_github_repo.log_warning("Test warning")
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.out
        assert "Test warning" in captured.out

    def test_log_error(self, capsys):
        """Test error message logging."""
        finalize_github_repo.log_error("Test error")
        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out
        assert "Test error" in captured.out


class TestRunCommand:
    """Test command execution."""

    def test_run_command_success(self):
        """Test successful command execution."""
        result = finalize_github_repo.run_command(["echo", "test"], check=False)
        assert result.returncode == 0
        assert "test" in result.stdout

    def test_run_command_failure(self):
        """Test failed command execution."""
        with pytest.raises(subprocess.CalledProcessError):
            finalize_github_repo.run_command(["false"])


class TestCheckGhCli:
    """Test GitHub CLI detection."""

    @patch("finalize_github_repo.run_command")
    def test_check_gh_cli_available(self, mock_run):
        """Test detection when gh CLI is available."""
        mock_run.return_value = MagicMock(returncode=0)
        assert finalize_github_repo.check_gh_cli() is True

    @patch("finalize_github_repo.run_command")
    def test_check_gh_cli_not_available(self, mock_run):
        """Test detection when gh CLI is not available."""
        mock_run.side_effect = Exception("Command not found")
        assert finalize_github_repo.check_gh_cli() is False


class TestGetGithubUsername:
    """Test GitHub username retrieval."""

    @patch("finalize_github_repo.run_command")
    def test_get_username_success(self, mock_run):
        """Test successful username retrieval."""
        mock_run.return_value = MagicMock(stdout="testuser\n", returncode=0)
        assert finalize_github_repo.get_github_username() == "testuser"

    @patch("finalize_github_repo.run_command")
    def test_get_username_failure(self, mock_run):
        """Test username retrieval failure."""
        mock_run.side_effect = Exception("API error")
        assert finalize_github_repo.get_github_username() == "YOUR_USERNAME"


class TestGetPackageTopics:
    """Test package topics generation."""

    def test_plugin_topics(self):
        """Test topics for plugin type."""
        topics = finalize_github_repo.get_package_topics("plugin")
        assert "python" in topics
        assert "gitready" in topics
        assert "claude-code" in topics
        assert "plugin" in topics

    def test_skill_topics(self):
        """Test topics for skill type."""
        topics = finalize_github_repo.get_package_topics("skill")
        assert "python" in topics
        assert "skill" in topics
        assert "ai-assistant" in topics

    def test_mcp_topics(self):
        """Test topics for MCP type."""
        topics = finalize_github_repo.get_package_topics("mcp")
        assert "mcp" in topics
        assert "model-context-protocol" in topics

    def test_library_topics(self):
        """Test topics for library type."""
        topics = finalize_github_repo.get_package_topics("library")
        assert "library" in topics
        assert "package" in topics


class TestGenerateCodeowners:
    """Test CODEOWNERS file generation."""

    def test_generate_codeowners_new_file(self, tmp_path):
        """Test CODEOWNERS file creation."""
        package_name = "test-package"
        username = "testuser"

        result = finalize_github_repo.generate_codeowners(
            package_name, tmp_path, username
        )

        assert result is True
        codeowners_path = tmp_path / "CODEOWNERS"
        assert codeowners_path.exists()

        content = codeowners_path.read_text()
        assert "@testuser" in content
        assert "# CODEOWNERS" in content

    def test_generate_codeowners_existing_file(self, tmp_path):
        """Test CODEOWNERS file exists already."""
        codeowners_path = tmp_path / "CODEOWNERS"
        codeowners_path.write_text("# Existing CODEOWNERS\n")

        result = finalize_github_repo.generate_codeowners("test", tmp_path, "user")
        assert result is False

    def test_generate_codeowners_default_username(self, tmp_path):
        """Test CODEOWNERS with default username."""
        result = finalize_github_repo.generate_codeowners("test", tmp_path, None)
        assert result is True


class TestGenerateSecurityMd:
    """Test SECURITY.md file generation."""

    def test_generate_security_md_new_file(self, tmp_path):
        """Test SECURITY.md file creation."""
        package_name = "test-package"

        result = finalize_github_repo.generate_security_md(package_name, tmp_path)

        assert result is True
        security_path = tmp_path / "SECURITY.md"
        assert security_path.exists()

        content = security_path.read_text()
        assert "Security Policy" in content
        assert package_name in content
        assert "Vulnerability" in content

    def test_generate_security_md_existing_file(self, tmp_path):
        """Test SECURITY.md exists already."""
        security_path = tmp_path / "SECURITY.md"
        security_path.write_text("# Existing Security\n")

        result = finalize_github_repo.generate_security_md("test", tmp_path)
        assert result is False


class TestEnableGithubPages:
    """Test GitHub Pages enablement."""

    @patch("finalize_github_repo.check_gh_cli")
    @patch("finalize_github_repo.run_command")
    def test_enable_pages_success(self, mock_run, mock_check, tmp_path):
        """Test successful Pages enablement."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        result = finalize_github_repo.enable_github_pages("test-pkg", tmp_path)
        assert result is True

    @patch("finalize_github_repo.check_gh_cli")
    def test_enable_pages_no_gh(self, mock_check):
        """Test Pages enablement without gh CLI."""
        mock_check.return_value = False
        result = finalize_github_repo.enable_github_pages("test", Path("/tmp"))
        assert result is False


class TestCreateInitialRelease:
    """Test initial release creation."""

    @patch("finalize_github_repo.check_gh_cli")
    @patch("finalize_github_repo.run_command")
    def test_create_release_success(self, mock_run, mock_check):
        """Test successful release creation."""
        mock_check.return_value = True

        # Note: check_gh_cli is mocked, so it doesn't call run_command
        # Actual calls:
        # 1: get_github_username() (gh api user)
        # 2: gh release view (release doesn't exist)
        # 3+: gh release create (success)
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # get_github_username - success
                return MagicMock(returncode=0, stdout="testuser")
            elif call_count[0] == 2:
                # gh release view - release doesn't exist
                return MagicMock(returncode=1, stderr="release not found")
            else:
                # gh release create - success
                return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        # Create a temp directory with .git
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            (target_dir / ".git").mkdir()

            result = finalize_github_repo.create_initial_release("test-pkg", target_dir)
            assert result is True

    @patch("finalize_github_repo.check_gh_cli")
    @patch("finalize_github_repo.run_command")
    def test_create_release_exists(self, mock_run, mock_check, tmp_path):
        """Test release already exists."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="Release exists")

        # First call checks for existing release (returns 0)
        # Second call is the actual create (we'll make it succeed)
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return MagicMock(returncode=0, stdout="v0.1.0 exists")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        result = finalize_github_repo.create_initial_release("test-pkg", tmp_path)
        assert result is False  # Already exists


class TestAddRepositoryTopics:
    """Test repository topics addition."""

    @patch("finalize_github_repo.check_gh_cli")
    @patch("finalize_github_repo.run_command")
    def test_add_topics_success(self, mock_run, mock_check):
        """Test successful topics addition."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        result = finalize_github_repo.add_repository_topics("test-pkg", "plugin")
        assert result is True

    @patch("finalize_github_repo.check_gh_cli")
    def test_add_topics_no_gh(self, mock_check):
        """Test topics addition without gh CLI."""
        mock_check.return_value = False
        result = finalize_github_repo.add_repository_topics("test", "library")
        assert result is False


class TestVerifyFinalization:
    """Test finalization verification."""

    @patch("finalize_github_repo.check_gh_cli")
    @patch("finalize_github_repo.run_command")
    def test_verify_all_success(self, mock_run, mock_check):
        """Test verification with all checks passing."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout="true")

        # Create a temp directory with .git
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            (target_dir / ".git").mkdir()

            result = finalize_github_repo.verify_finalization("test-pkg")
            assert result.get("pages") is True
            assert result.get("release") is True
            assert result.get("topics") is True

    @patch("finalize_github_repo.check_gh_cli")
    def test_verify_no_gh(self, mock_check):
        """Test verification without gh CLI."""
        mock_check.return_value = False
        result = finalize_github_repo.verify_finalization("test-pkg")
        assert result == {}


class TestMain:
    """Test main entry point."""

    @patch("finalize_github_repo.verify_finalization")
    @patch("finalize_github_repo.push_updates")
    @patch("finalize_github_repo.generate_security_md")
    @patch("finalize_github_repo.generate_codeowners")
    @patch("finalize_github_repo.add_repository_topics")
    @patch("finalize_github_repo.create_initial_release")
    @patch("finalize_github_repo.enable_github_pages")
    def test_main_verify_mode(self, *mocks):
        """Test main in verify mode."""
        # Create a temp directory with .git
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            (target_dir / ".git").mkdir()

            with patch.object(
                sys,
                "argv",
                ["finalize_github_repo.py", "test-pkg", str(target_dir), "--verify"],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    finalize_github_repo.main()
                assert exc_info.value.code == 0

    @patch("finalize_github_repo.verify_finalization")
    @patch("finalize_github_repo.push_updates")
    @patch("finalize_github_repo.generate_security_md")
    @patch("finalize_github_repo.generate_codeowners")
    @patch("finalize_github_repo.add_repository_topics")
    @patch("finalize_github_repo.create_initial_release")
    @patch("finalize_github_repo.enable_github_pages")
    @patch("finalize_github_repo.check_gh_cli")
    def test_main_full_flow(self, mock_check, *mocks):
        """Test main with full finalization flow."""
        import tempfile

        mock_check.return_value = True
        # Make all functions return True
        for mock in mocks:
            mock.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            (target_dir / ".git").mkdir()

            with patch.object(
                sys,
                "argv",
                ["finalize_github_repo.py", "test-pkg", str(target_dir)],
            ):
                # main() doesn't call sys.exit() in normal flow
                finalize_github_repo.main()
                # If we get here, main() completed without error

    def test_main_not_git_repo(self):
        """Test main with non-git directory."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = Path(temp_dir)
            # Don't create .git directory

            with patch.object(
                sys,
                "argv",
                ["finalize_github_repo.py", "test-pkg", str(target_dir)],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    finalize_github_repo.main()
                assert exc_info.value.code == 1
