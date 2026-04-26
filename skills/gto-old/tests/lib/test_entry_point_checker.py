"""Tests for entry_point_checker module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.entry_point_checker import (
    EntryPointChecker,
    EntryPointGap,
    EntryPointResult,
    check_entry_points,
)


class TestEntryPointChecker:
    """Tests for EntryPointChecker class."""

    def test_checker_instantiation(self, tmp_path: Path) -> None:
        """Test checker can be instantiated."""
        checker = EntryPointChecker(tmp_path)
        assert checker is not None
        assert checker.project_root == tmp_path.resolve()

    def test_checker_default_root(self) -> None:
        """Test checker uses cwd as default root."""
        checker = EntryPointChecker()
        assert checker.project_root == Path.cwd().resolve()


class TestExtractPathsFromText:
    """Tests for _extract_paths_from_text method."""

    def test_extract_simple_python_invocation(self, tmp_path: Path) -> None:
        """Test extraction of simple python file.py invocation."""
        checker = EntryPointChecker(tmp_path)
        text = 'python "scripts/test.py" --arg'
        results = checker._extract_paths_from_text(text)
        assert len(results) == 1
        assert results[0][0] == "scripts/test.py"

    def test_extract_python_without_quotes(self, tmp_path: Path) -> None:
        """Test extraction of python invocation without quotes."""
        checker = EntryPointChecker(tmp_path)
        text = "python scripts/test.py --arg"
        results = checker._extract_paths_from_text(text)
        assert len(results) == 1
        assert results[0][0] == "scripts/test.py"

    def test_extract_cd_then_python(self, tmp_path: Path) -> None:
        """Test extraction of cd dir && python pattern."""
        checker = EntryPointChecker(tmp_path)
        text = "cd scripts && python test.py --arg"
        results = checker._extract_paths_from_text(text)
        assert len(results) == 1
        assert results[0][0] == "test.py"

    def test_extract_multiple_invocations(self, tmp_path: Path) -> None:
        """Test extraction of multiple python invocations."""
        checker = EntryPointChecker(tmp_path)
        text = """python scripts/a.py
python scripts/b.py"""
        results = checker._extract_paths_from_text(text)
        assert len(results) == 2
        paths = [r[0] for r in results]
        assert "scripts/a.py" in paths
        assert "scripts/b.py" in paths

    def test_skip_comment_lines(self, tmp_path: Path) -> None:
        """Test that comment lines are skipped."""
        checker = EntryPointChecker(tmp_path)
        text = "# python scripts/test.py"
        results = checker._extract_paths_from_text(text)
        assert len(results) == 0

    def test_skip_python_code_lines(self, tmp_path: Path) -> None:
        """Test that Python code import lines are skipped."""
        checker = EntryPointChecker(tmp_path)
        text = "import scripts.test"
        results = checker._extract_paths_from_text(text)
        assert len(results) == 0

    def test_skip_def_class_lines(self, tmp_path: Path) -> None:
        """Test that def/class lines are skipped."""
        checker = EntryPointChecker(tmp_path)
        text = "def test():"
        results = checker._extract_paths_from_text(text)
        assert len(results) == 0

    def test_path_with_variable_substitution(self, tmp_path: Path) -> None:
        """Test extraction of paths with variable placeholders."""
        checker = EntryPointChecker(tmp_path)
        text = 'python "scripts/{{module}}/test.py"'
        results = checker._extract_paths_from_text(text)
        assert len(results) == 1


class TestResolvePath:
    """Tests for _resolve_path method."""

    def test_resolve_absolute_windows_path(self, tmp_path: Path) -> None:
        """Test resolving absolute Windows path."""
        checker = EntryPointChecker(tmp_path)
        resolved = checker._resolve_path("P:/scripts/test.py")
        assert resolved == Path("P:/scripts/test.py")

    def test_resolve_relative_path(self, tmp_path: Path) -> None:
        """Test resolving relative path against project root."""
        checker = EntryPointChecker(tmp_path)
        resolved = checker._resolve_path("scripts/test.py")
        assert resolved == tmp_path / "scripts/test.py"

    def test_resolve_path_with_variable_placeholder(self, tmp_path: Path) -> None:
        """Test resolving path with variable placeholder."""
        checker = EntryPointChecker(tmp_path)
        resolved = checker._resolve_path("scripts/{{module}}/test.py")
        assert resolved == tmp_path / "scripts" / "test.py"

    def test_resolve_path_with_quotes(self, tmp_path: Path) -> None:
        """Test resolving quoted path."""
        checker = EntryPointChecker(tmp_path)
        resolved = checker._resolve_path('"scripts/test.py"')
        assert resolved == tmp_path / "scripts/test.py"


class TestCheck:
    """Tests for check method."""

    def test_check_no_skill_md(self, tmp_path: Path) -> None:
        """Test check when SKILL.md doesn't exist."""
        checker = EntryPointChecker(tmp_path)
        result = checker.check()
        assert result.entry_points_checked == 0
        assert result.entry_points_valid == 0

    def test_check_with_valid_entry_point(self, tmp_path: Path) -> None:
        """Test check with valid entry point."""
        # Create a SKILL.md with a reference to an existing file
        skill_md = tmp_path / "SKILL.md"
        # Create the scripts directory and a real file
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        real_file = scripts_dir / "test.py"
        real_file.write_text("# real file")

        skill_md.write_text('python "scripts/test.py" --arg')

        checker = EntryPointChecker(tmp_path)
        result = checker.check(skill_md)

        assert result.entry_points_checked == 1
        assert result.entry_points_valid == 1
        assert result.entry_points_missing == 0
        assert len(result.gaps) == 0

    def test_check_with_missing_entry_point(self, tmp_path: Path) -> None:
        """Test check with missing entry point."""
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text('python "scripts/nonexistent.py" --arg')

        checker = EntryPointChecker(tmp_path)
        result = checker.check(skill_md)

        assert result.entry_points_checked == 1
        assert result.entry_points_valid == 0
        assert result.entry_points_missing == 1
        assert len(result.gaps) == 1
        assert result.gaps[0].referenced_path == "scripts/nonexistent.py"


class TestEntryPointResult:
    """Tests for EntryPointResult dataclass."""

    def test_result_dataclass(self) -> None:
        """Test result can be constructed."""
        result = EntryPointResult(
            gaps=[],
            entry_points_checked=5,
            entry_points_valid=3,
            entry_points_missing=2,
        )
        assert result.entry_points_checked == 5
        assert result.entry_points_valid == 3
        assert result.entry_points_missing == 2
        assert len(result.gaps) == 0


class TestEntryPointGap:
    """Tests for EntryPointGap dataclass."""

    def test_gap_dataclass(self) -> None:
        """Test gap can be constructed."""
        gap = EntryPointGap(
            referenced_path="scripts/test.py",
            resolved_path="/fake/scripts/test.py",
            exists=False,
            line_number=42,
            context='python "scripts/test.py" --arg',
        )
        assert gap.referenced_path == "scripts/test.py"
        assert gap.resolved_path == "/fake/scripts/test.py"
        assert gap.exists is False
        assert gap.line_number == 42


class TestConvenienceFunction:
    """Tests for check_entry_points convenience function."""

    def test_convenience_function(self, tmp_path: Path) -> None:
        """Test convenience function works."""
        # Create a SKILL.md with valid entry point
        skill_md = tmp_path / "SKILL.md"
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        real_file = scripts_dir / "test.py"
        real_file.write_text("# real file")

        skill_md.write_text('python "scripts/test.py"')

        result = check_entry_points(tmp_path, skill_md)
        assert result.entry_points_checked == 1
        assert result.entry_points_valid == 1
