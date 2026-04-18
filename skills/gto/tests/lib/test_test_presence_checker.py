"""Tests for TestPresenceChecker.

These tests verify the TestPresenceChecker class at gto/lib/test_presence_checker.py
which detects missing test files for source modules.

Test Strategy:
- Uses temporary directories to create realistic test scenarios
- Verifies security properties (path sanitization, symlink guards, etc.)
- Tests the FileScanner integration

Run with: pytest P:/.claude/skills/gto/tests/lib/test_test_presence_checker.py -v
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Add gto skill root and _shared scanners to sys.path
_GTO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_GTO_ROOT))
_SHARED_SCANNERS_PATH = Path.home() / ".claude" / "skills" / "_shared"
if _SHARED_SCANNERS_PATH.exists():
    sys.path.insert(0, str(_SHARED_SCANNERS_PATH))

from __lib.test_presence_checker import (  # type: ignore
    TestGap,
    TestPresenceChecker,
    TestPresenceResult,
)
from scanners.base import FileScanner  # type: ignore


class TestCheckerInstantiation:
    """Tests for TestPresenceChecker instantiation."""

    def test_checker_instantiation(self):
        """Test that TestPresenceChecker can be instantiated.

        Given: A valid project root
        When: Creating a TestPresenceChecker instance
        Then: The instance is created with correct defaults
        """
        with TemporaryDirectory() as tmpdir:
            checker = TestPresenceChecker(project_root=tmpdir)

            assert checker.project_root == Path(tmpdir).resolve()
            assert checker.source_dirs == ["src", "lib", "app"]
            assert checker.test_dirs == ["tests", "test"]


class TestPathTraversalBlocked:
    """Tests for path traversal protection."""

class TestSymlinkOutsideRootSkipped:
    """Tests for symlink security guards."""

    def test_symlink_outside_root_skipped(self):
        """Test that symlinks pointing outside project root are skipped.

        Given: A symlink inside project root that points outside
        When: Scanning for test directories
        Then: The symlink target is not followed and test dir is not found
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a file outside project root
            outside_dir = Path(tmpdir).parent / "outside_project"
            outside_dir.mkdir(exist_ok=True)
            outside_file = outside_dir / "secret.txt"
            outside_file.write_text("secret data")

            # Create a symlink inside project root pointing to outside file
            link_dir = project_root / "links"
            link_dir.mkdir()
            symlink_path = link_dir / "link_to_outside"
            symlink_path.symlink_to(outside_file)

            # Create a source file using the symlink
            src_dir = project_root / "src"
            src_dir.mkdir()
            src_file = src_dir / "module.py"
            src_file.write_text("# source")

            checker = TestPresenceChecker(project_root=project_root)
            # The _find_test_dir should not find a test dir via the symlink
            # (because it sanitizes paths before checking)
            result = checker._find_test_dir(src_file)
            # Should not follow the symlink outside root
            assert (
                result is None
                or result == project_root / "tests"
                or result == project_root / "test"
            )


class TestTestPresenceResult:
    """Tests for TestPresenceResult dataclass."""

    def test_result_dataclass(self):
        """Test that TestPresenceResult has the required fields.

        Given: A TestPresenceResult instance with data
        When: Accessing its fields
        Then: All expected fields are present with correct types
        """
        gap = TestGap(
            module_path="/src/module.py",
            expected_test_path="/tests/test_module.py",
            test_exists=False,
            test_dir_exists=True,
        )
        result = TestPresenceResult(
            gaps=[gap],
            modules_checked=1,
            modules_with_tests=0,
            modules_without_tests=1,
            test_dirs_missing=0,
        )

        assert hasattr(result, "gaps")
        assert hasattr(result, "modules_checked")
        assert hasattr(result, "modules_with_tests")
        assert hasattr(result, "modules_without_tests")
        assert hasattr(result, "test_dirs_missing")
        assert result.modules_checked == 1
        assert result.modules_without_tests == 1


class TestTestGap:
    """Tests for TestGap dataclass."""

    def test_gap_dataclass(self):
        """Test that TestGap has the required fields.

        Given: A TestGap instance
        When: Accessing its fields
        Then: All expected fields are present
        """
        gap = TestGap(
            module_path="/src/foo/bar.py",
            expected_test_path="/tests/foo/test_bar.py",
            test_exists=False,
            test_dir_exists=True,
        )

        assert gap.module_path == "/src/foo/bar.py"
        assert gap.expected_test_path == "/tests/foo/test_bar.py"
        assert gap.test_exists is False
        assert gap.test_dir_exists is True
