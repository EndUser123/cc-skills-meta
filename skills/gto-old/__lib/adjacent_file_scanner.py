"""Adjacent File Scanner - Scan only files touched in the chat.

Domain 2 of GTO v4: Smart adjacency scanning
Instead of scanning the entire project, scan only files that were
actually read/edited in the chat transcript.

Priority: P2 (runs during gap detection)
Purpose: Targeted code quality feedback without excessive scanning
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TouchedFile:
    """A file that was touched in the chat."""

    path: Path
    operation_count: int
    operations: list[str]  # Read, Edit, Write, etc.


@dataclass
class AdjacentScanResult:
    """Result of adjacent file scanning."""

    touched_files: list[TouchedFile]
    missing_tests: list[str]
    todo_comments: list[tuple[str, int]]  # (file, line_count)
    docstring_gaps: list[str]
    total_files_scanned: int


class AdjacentFileScanner:
    """
    Scan only files that were touched in the chat transcript.

    This provides targeted code quality feedback without scanning
    the entire filesystem.
    """

    # File patterns to scan
    CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c"}
    TEST_FILE_PATTERNS = [
        r"test_.*\.py$",
        r".*_test\.go$",
        r".*\.test\.ts$",
        r".*\.spec\.ts$",
    ]

    def __init__(self, project_root: Path):
        """Initialize scanner.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root).resolve()

    def extract_touched_files(self, transcript_path: Path) -> list[TouchedFile]:
        """Extract files touched in the chat transcript.

        Args:
            transcript_path: Path to chat transcript JSONL file

        Returns:
            List of TouchedFile objects
        """
        file_operations: dict[str, list[str]] = {}

        try:
            with open(transcript_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        message = json.loads(line)

                        # Claude Code transcripts store tool_use inside content list,
                        # not at root level. Each content block has a type field.
                        content = message.get("content", [])
                        if not isinstance(content, list):
                            content = [content]

                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            block_type = block.get("type", "")

                            # Handle tool_use blocks
                            if block_type == "tool_use":
                                tool_name = block.get("name", "")
                                input_data = block.get("input", {})
                                self._extract_path_from_tool(
                                    input_data, tool_name, file_operations
                                )

                            # Handle tool_result blocks - file paths appear here too
                            elif block_type == "tool_result":
                                tool_name = block.get("name", "")
                                content_val = block.get("content", {})
                                if isinstance(content_val, dict):
                                    self._extract_path_from_tool(
                                        content_val, tool_name, file_operations
                                    )

                    except json.JSONDecodeError:
                        continue

        except FileNotFoundError:
            return []

        # Convert to TouchedFile objects
        touched_files = []
        for file_path, operations in file_operations.items():
            # Resolve path relative to project root
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            # Only include code files
            if path.suffix in self.CODE_EXTENSIONS:
                touched_files.append(
                    TouchedFile(
                        path=path,
                        operation_count=len(operations),
                        operations=operations,
                    )
                )

        return touched_files

    def _extract_path_from_tool(
        self,
        input_data: dict,
        tool_name: str,
        file_operations: dict[str, list[str]],
    ) -> None:
        """Extract file path from tool input data and record operation.

        Args:
            input_data: Tool input dictionary
            tool_name: Name of the tool
            file_operations: Dict to accumulate operations per file
        """
        # Don't scan glob results - too many files
        if tool_name == "Glob" and "pattern" in input_data:
            return

        # Try file_path first, then fallbacks
        file_path = input_data.get("file_path")
        if not file_path:
            file_path = input_data.get("relative_path")
        if not file_path:
            file_path = input_data.get("path")

        if file_path:
            if file_path not in file_operations:
                file_operations[file_path] = []
            file_operations[file_path].append(tool_name)

    def scan_adjacent_files(self, transcript_path: Path) -> AdjacentScanResult:
        """Scan files touched in the transcript for code quality issues.

        Args:
            transcript_path: Path to chat transcript

        Returns:
            AdjacentScanResult with findings
        """
        touched_files = self.extract_touched_files(transcript_path)

        missing_tests = []
        todo_comments = []
        docstring_gaps = []

        for file in touched_files:
            if not file.path.exists():
                continue

            # Check for missing tests
            if not self._has_test_file(file.path):
                missing_tests.append(str(file.path))

            # Scan for TODO comments
            todos = self._scan_for_todos(file.path)
            if todos:
                todo_comments.append((str(file.path), todos))

            # Check for docstring gaps
            if not self._has_docstrings(file.path):
                docstring_gaps.append(str(file.path))

        return AdjacentScanResult(
            touched_files=touched_files,
            missing_tests=missing_tests,
            todo_comments=todo_comments,
            docstring_gaps=docstring_gaps,
            total_files_scanned=len(touched_files),
        )

    def _has_test_file(self, source_file: Path) -> bool:
        """Check if a test file exists for the source file.

        Args:
            source_file: Path to source file

        Returns:
            True if test file exists
        """
        # Check for test_*.py pattern
        test_file = source_file.parent / f"test_{source_file.name}"
        if test_file.exists():
            return True

        # Check for *_test.py pattern
        test_file = source_file.with_name(f"{source_file.stem}_test{source_file.suffix}")
        if test_file.exists():
            return True

        # Check for test directory
        test_dir = source_file.parent.parent / "tests"
        if test_dir.exists():
            test_file = test_dir / source_file.name
            if test_file.exists():
                return True

        return False

    def _scan_for_todos(self, file_path: Path) -> int:
        """Scan file for TODO/FIXME comments.

        Args:
            file_path: Path to file

        Returns:
            Number of TODO comments found
        """
        todo_count = 0
        todo_pattern = re.compile(r"#\s*(TODO|FIXME|XXX|HACK)", re.IGNORECASE)

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if todo_pattern.search(line):
                        todo_count += 1
        except (OSError, PermissionError):
            pass

        return todo_count

    def _has_docstrings(self, file_path: Path) -> bool:
        """Check if file has module-level docstring.

        Args:
            file_path: Path to Python file

        Returns:
            True if docstring exists
        """
        if file_path.suffix != ".py":
            return True  # Skip non-Python files

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                # Skip shebang and encoding pragma lines, then check for docstring
                prefix_skips = 2  # max shebang + encoding lines to skip
                lines_checked = 0
                while lines_checked < 4:
                    line = f.readline()
                    if not line:
                        return False  # EOF
                    lines_checked += 1
                    if lines_checked <= prefix_skips and (line.startswith("#!") or line.startswith("# -*-")):
                        continue  # Skip this prefix line

                    if line.strip().startswith('"""') or line.strip().startswith("'''"):
                        return True

                    # Not a docstring — try one more line
                    next_line = f.readline()
                    if next_line:
                        stripped = next_line.strip()
                        if stripped.startswith('"""') or stripped.startswith("'''"):
                            return True
                    return False

                return False
        except (OSError, PermissionError):
            return False


# Convenience function
def scan_adjacent_files(
    transcript_path: Path,
    project_root: Path,
) -> AdjacentScanResult:
    """Quick adjacent file scanning.

    Args:
        transcript_path: Path to chat transcript
        project_root: Project root directory

    Returns:
        AdjacentScanResult with findings
    """
    scanner = AdjacentFileScanner(project_root)
    return scanner.scan_adjacent_files(transcript_path)
