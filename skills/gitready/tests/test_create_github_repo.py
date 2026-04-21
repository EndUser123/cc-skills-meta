"""Tests for create_github_repo.py script."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the script module
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from create_github_repo import (
    check_gh_cli,
    create_with_gh_cli,
    get_github_username,
    log_error,
    log_info,
    log_success,
    log_warning,
    main,
    run_command,
    show_manual_instructions,
    verify_repository,
)


class TestRunCommand:
    """Tests for run_command function."""

    @patch("create_github_repo.subprocess.run")
    def test_run_command_success(self, mock_run: Mock) -> None:
        """Test successful command execution."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "test"], returncode=0, stdout="test output", stderr=""
        )
        result = run_command(["echo", "test"])
        assert result.returncode == 0
        assert result.stdout == "test output"

    @patch("create_github_repo.subprocess.run")
    @patch("create_github_repo.log_error")
    def test_run_command_failure_raises(self, mock_log: Mock, mock_run: Mock) -> None:
        """Test that command failure raises CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["false"], stderr="error output"
        )
        with pytest.raises(subprocess.CalledProcessError):
            run_command(["false"])
        mock_log.assert_called()

    @patch("create_github_repo.subprocess.run")
    def test_run_command_check_false(self, mock_run: Mock) -> None:
        """Test command with check=False does not raise."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"], returncode=1, stdout="", stderr="error"
        )
        result = run_command(["false"], check=False)
        assert result.returncode == 1


class TestLogging:
    """Tests for logging functions."""

    @patch("builtins.print")
    def test_log_info(self, mock_print: Mock) -> None:
        """Test info message formatting."""
        log_info("test message")
        mock_print.assert_called_once()
        args = mock_print.call_args.args
        assert "[INFO]" in args[0]

    @patch("builtins.print")
    def test_log_success(self, mock_print: Mock) -> None:
        """Test success message formatting."""
        log_success("test message")
        mock_print.assert_called_once()
        args = mock_print.call_args.args
        assert "[SUCCESS]" in args[0]

    @patch("builtins.print")
    def test_log_warning(self, mock_print: Mock) -> None:
        """Test warning message formatting."""
        log_warning("test message")
        mock_print.assert_called_once()
        args = mock_print.call_args.args
        assert "[WARNING]" in args[0]

    @patch("builtins.print")
    def test_log_error(self, mock_print: Mock) -> None:
        """Test error message formatting."""
        log_error("test message")
        mock_print.assert_called_once()
        args = mock_print.call_args.args
        assert "[ERROR]" in args[0]


class TestCheckGhCli:
    """Tests for check_gh_cli function."""

    @patch("create_github_repo.run_command")
    def test_check_gh_cli_available_and_authenticated(self, mock_run: Mock) -> None:
        """Test returns True when gh CLI is available and authenticated."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        result = check_gh_cli()
        assert result is True

    @patch("create_github_repo.run_command")
    def test_check_gh_cli_not_authenticated(self, mock_run: Mock) -> None:
        """Test returns False when gh CLI exists but not authenticated."""
        # First call for --version succeeds, second for auth status fails
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr=""
        )

        result = check_gh_cli()
        assert result is False

    @patch("create_github_repo.run_command")
    def test_check_gh_cli_not_installed(self, mock_run: Mock) -> None:
        """Test returns False when gh CLI is not installed."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["gh"])

        result = check_gh_cli()
        assert result is False


class TestGetGithubUsername:
    """Tests for get_github_username function."""

    @patch("create_github_repo.run_command")
    def test_get_github_username_success(self, mock_run: Mock) -> None:
        """Test successful username retrieval."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "api", "user"],
            returncode=0,
            stdout="testuser\n",
            stderr="",
        )

        result = get_github_username()
        assert result == "testuser"

    @patch("create_github_repo.run_command")
    def test_get_github_username_failure(self, mock_run: Mock) -> None:
        """Test returns placeholder when gh command fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "api", "user"],
            returncode=1,
            stdout="",
            stderr="",
        )

        result = get_github_username()
        assert result == "YOUR_USERNAME"

    @patch("create_github_repo.run_command")
    def test_get_github_username_exception(self, mock_run: Mock) -> None:
        """Test returns placeholder when exception occurs."""
        mock_run.side_effect = Exception("Network error")

        result = get_github_username()
        assert result == "YOUR_USERNAME"


class TestCreateWithGhCli:
    """Tests for create_with_gh_cli function."""

    @patch("create_github_repo.get_github_username")
    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.run_command")
    @patch("create_github_repo.log_info")
    @patch("create_github_repo.log_success")
    def test_create_with_gh_cli_new_repo(
        self,
        mock_succ: Mock,
        mock_info: Mock,
        mock_run: Mock,
        mock_check: Mock,
        mock_user: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful new repository creation."""
        mock_check.return_value = True
        mock_user.return_value = "testuser"

        # Mock repo view (doesn't exist) and create (succeeds)
        call_count = [0]

        def run_side_effect(cmd, *args, **kwargs):
            call_count[0] += 1
            if "repo" in cmd and "view" in cmd:
                return subprocess.CompletedProcess(
                    cmd, returncode=1, stdout="", stderr="Not found"
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        result = create_with_gh_cli("test-repo", tmp_path, "Test description")

        assert result is True
        mock_succ.assert_called()

    @patch("create_github_repo.get_github_username")
    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.run_command")
    @patch("create_github_repo.log_warning")
    @patch("create_github_repo.log_success")
    def test_create_with_gh_cli_repo_exists(
        self,
        mock_succ: Mock,
        mock_warn: Mock,
        mock_run: Mock,
        mock_check: Mock,
        mock_user: Mock,
        tmp_path: Path,
    ) -> None:
        """Test handling when repository already exists."""
        mock_check.return_value = True
        mock_user.return_value = "testuser"

        # Mock repo view succeeds (repo exists)
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        result = create_with_gh_cli("test-repo", tmp_path, "Test description")

        assert result is True
        mock_warn.assert_called()
        # Should add remote and push
        assert mock_run.call_count >= 2

    @patch("create_github_repo.check_gh_cli")
    def test_create_with_gh_cli_not_available(
        self, mock_check: Mock, tmp_path: Path
    ) -> None:
        """Test returns False when gh CLI is not available."""
        mock_check.return_value = False

        result = create_with_gh_cli("test-repo", tmp_path, "Test description")

        assert result is False

    @patch("create_github_repo.get_github_username")
    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.run_command")
    @patch("create_github_repo.log_error")
    def test_create_with_gh_cli_create_fails(
        self,
        mock_log: Mock,
        mock_run: Mock,
        mock_check: Mock,
        mock_user: Mock,
        tmp_path: Path,
    ) -> None:
        """Test returns False when repository creation fails."""
        mock_check.return_value = True
        mock_user.return_value = "testuser"

        def run_side_effect(cmd, *args, **kwargs):
            if "repo" in cmd and "view" in cmd:
                return subprocess.CompletedProcess(
                    cmd, returncode=1, stdout="", stderr=""
                )
            if "repo" in cmd and "create" in cmd:
                raise subprocess.CalledProcessError(1, cmd)
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        result = create_with_gh_cli("test-repo", tmp_path, "Test description")

        assert result is False


class TestShowManualInstructions:
    """Tests for show_manual_instructions function."""

    @patch("create_github_repo.get_github_username")
    @patch("builtins.print")
    @patch("create_github_repo.log_info")
    def test_show_manual_instructions_content(
        self, mock_log: Mock, mock_print: Mock, mock_user: Mock, tmp_path: Path
    ) -> None:
        """Test manual instructions include required content."""
        mock_user.return_value = "testuser"

        show_manual_instructions("test-repo", tmp_path, "Test description")

        # Verify print was called multiple times
        assert mock_print.call_count > 5

        # Check for key content in printed output
        all_args = [str(call.args) for call in mock_print.call_args_list]
        output_str = " ".join(all_args)

        assert "test-repo" in output_str
        assert "Test description" in output_str
        assert "github.com/new" in output_str


class TestVerifyRepository:
    """Tests for verify_repository function."""

    @patch("create_github_repo.get_github_username")
    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.run_command")
    @patch("create_github_repo.log_info")
    @patch("create_github_repo.log_success")
    @patch("create_github_repo.log_warning")
    def test_verify_repository_success(
        self,
        mock_warn: Mock,
        mock_succ: Mock,
        mock_info: Mock,
        mock_run: Mock,
        mock_check: Mock,
        mock_user: Mock,
    ) -> None:
        """Test successful repository verification."""
        mock_check.return_value = True
        mock_user.return_value = "testuser"

        # Mock repo view success
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="https://github.com/testuser/test-repo",
            stderr="",
        )

        result = verify_repository("test-repo")

        assert result is True
        mock_succ.assert_called()

    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.log_info")
    @patch("create_github_repo.log_warning")
    def test_verify_repository_no_gh(
        self, mock_warn: Mock, mock_info: Mock, mock_check: Mock
    ) -> None:
        """Test verification when gh CLI not available."""
        mock_check.return_value = False

        result = verify_repository("test-repo")

        assert result is True  # Returns True to not block flow
        mock_warn.assert_called()

    @patch("create_github_repo.get_github_username")
    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.run_command")
    @patch("create_github_repo.log_info")
    @patch("create_github_repo.log_warning")
    def test_verify_repository_not_found(
        self,
        mock_warn: Mock,
        mock_info: Mock,
        mock_run: Mock,
        mock_check: Mock,
        mock_user: Mock,
    ) -> None:
        """Test verification when repository not found."""
        mock_check.return_value = True
        mock_user.return_value = "testuser"

        # Mock repo view failure
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="Not found"
        )

        result = verify_repository("test-repo")

        assert result is False

    @patch("create_github_repo.get_github_username")
    @patch("create_github_repo.check_gh_cli")
    @patch("create_github_repo.run_command")
    @patch("create_github_repo.log_info")
    @patch("create_github_repo.log_success")
    @patch("create_github_repo.log_warning")
    def test_verify_repository_private(
        self,
        mock_warn: Mock,
        mock_succ: Mock,
        mock_info: Mock,
        mock_run: Mock,
        mock_check: Mock,
        mock_user: Mock,
    ) -> None:
        """Test verification detects private repository."""
        mock_check.return_value = True
        mock_user.return_value = "testuser"

        call_count = [0]

        def run_side_effect(cmd, *args, **kwargs):
            call_count[0] += 1
            if "view" in cmd:
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="", stderr=""
                )
            if "isPublic" in cmd:
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="false", stderr=""
                )
            if "url" in cmd:
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout="https://github.com/testuser/test-repo",
                    stderr="",
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        result = verify_repository("test-repo")

        assert result is True
        # Should warn about private visibility
        mock_warn.assert_called()


class TestMain:
    """Tests for main function."""

    @patch("create_github_repo.create_with_gh_cli")
    @patch("create_github_repo.verify_repository")
    @patch("create_github_repo.log_success")
    @patch("create_github_repo.sys.exit")
    def test_main_success(
        self,
        mock_exit: Mock,
        mock_succ: Mock,
        mock_verify: Mock,
        mock_create: Mock,
        tmp_path: Path,
    ) -> None:
        """Test successful main execution."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        mock_create.return_value = True

        with patch(
            "sys.argv",
            ["create_github_repo.py", "test-repo", str(tmp_path), "Test description"],
        ):
            main()

        mock_create.assert_called_once()
        mock_verify.assert_called_once()

    @patch("create_github_repo.create_with_gh_cli")
    @patch("create_github_repo.show_manual_instructions")
    @patch("create_github_repo.log_info")
    @patch("create_github_repo.sys.exit")
    def test_main_gh_cli_fallback(
        self,
        mock_exit: Mock,
        mock_info: Mock,
        mock_manual: Mock,
        mock_create: Mock,
        tmp_path: Path,
    ) -> None:
        """Test main falls back to manual instructions when gh CLI fails."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        mock_create.return_value = False

        with patch(
            "sys.argv",
            ["create_github_repo.py", "test-repo", str(tmp_path), "Test description"],
        ):
            main()

        mock_manual.assert_called_once()
        mock_exit.assert_called_with(1)

    @patch("create_github_repo.log_error")
    @patch("create_github_repo.sys.exit")
    def test_main_not_git_repo(
        self, mock_exit: Mock, mock_log: Mock, tmp_path: Path
    ) -> None:
        """Test main exits when target is not a git repository."""
        # Don't create .git directory

        with patch("sys.argv", ["create_github_repo.py", "test-repo", str(tmp_path)]):
            main()

        mock_exit.assert_called_with(1)


class TestArgparse:
    """Tests for CLI argument parsing."""

    @patch("create_github_repo.create_with_gh_cli")
    @patch("create_github_repo.verify_repository")
    @patch("create_github_repo.log_success")
    @patch("create_github_repo.sys.exit")
    def test_positional_args(
        self,
        mock_exit: Mock,
        mock_succ: Mock,
        mock_verify: Mock,
        mock_create: Mock,
        tmp_path: Path,
    ) -> None:
        """Test positional arguments are parsed correctly."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        mock_create.return_value = True

        with patch(
            "sys.argv",
            ["create_github_repo.py", "my-repo", str(tmp_path), "My awesome library"],
        ):
            main()

        # Verify create was called with correct arguments
        mock_create.assert_called_once()
        args = mock_create.call_args.args
        assert args[0] == "my-repo"
        assert args[1] == tmp_path
        assert args[2] == "My awesome library"

    @patch("create_github_repo.create_with_gh_cli")
    @patch("create_github_repo.verify_repository")
    @patch("create_github_repo.log_success")
    @patch("create_github_repo.sys.exit")
    def test_default_description(
        self,
        mock_exit: Mock,
        mock_succ: Mock,
        mock_verify: Mock,
        mock_create: Mock,
        tmp_path: Path,
    ) -> None:
        """Test default description is used when not provided."""
        # Create .git directory
        (tmp_path / ".git").mkdir()

        mock_create.return_value = True

        with patch("sys.argv", ["create_github_repo.py", "my-repo", str(tmp_path)]):
            main()

        # Verify create was called with default description
        mock_create.assert_called_once()
        args = mock_create.call_args.args
        assert args[2] == "A Claude Code package"
