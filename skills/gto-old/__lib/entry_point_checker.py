"""EntryPointChecker - Verify documented entry points exist.

Priority: P2 (runs during gap detection)
Purpose: Detect when SKILL.md references scripts/commands that don't exist

Checks:
- Extract .py file paths from SKILL.md Usage section
- Verify each referenced .py file exists on disk
- Report missing entry points as gaps
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EntryPointGap:
    """An entry point referenced in documentation but missing on disk."""

    referenced_path: str  # The path as it appears in docs
    resolved_path: str | None = None  # The path after resolving against project root
    exists: bool = False
    line_number: int | None = None
    context: str | None = None  # The line of text containing the reference


@dataclass
class EntryPointResult:
    """Result of entry point validation check."""

    gaps: list[EntryPointGap]
    entry_points_checked: int = 0
    entry_points_valid: int = 0
    entry_points_missing: int = 0


class EntryPointChecker:
    """
    Verify that entry points documented in SKILL.md actually exist.

    Extracts Python file references from SKILL.md and validates they exist.
    """

    # Patterns for finding Python file references in documentation
    # Matches: python "path/file.py", python path/file.py, cd dir && python file.py, etc.
    # Key insight: Use negative lookbehind (?<!/) before python to prevent matching 'python'
    # when it appears as part of a path (e.g., evals/python-gto-assertions.py)
    PYTHON_FILE_PATTERN = re.compile(
        r"""
        (?:^|\s)(?P<lead_in>cd\s+[^\s]+\s+&&\s+)?  # Optional "cd dir && " prefix
        (?<!/)python(?:\s+(?:".*?"|'.*?'|[^\s"]+))?\s+  # "python" command (not preceded by /)
        (?P<path>(?:".*?"|['"][^"']+['"]|[^\s"]+\.py))  # The .py file path
        """,
        re.VERBOSE | re.IGNORECASE | re.MULTILINE,
    )

    # Alternative pattern for bare `file.py` at start of line after cd/&& pattern
    STANDALONE_PY_PATTERN = re.compile(
        r"""
        (?:^|\s)(?P<lead_in>cd\s+[^\s]+\s+&&\s+)  # "cd dir && " prefix
        (?P<path>[^\s]+\.py)                        # The .py file path
        """,
        re.VERBOSE | re.IGNORECASE | re.MULTILINE,
    )

    def __init__(self, project_root: Path | None = None):
        """Initialize checker with project root.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def _extract_paths_from_text(self, text: str) -> list[tuple[str, int, str]]:
        """Extract Python file paths from text with line numbers.

        Args:
            text: Text content to search

        Returns:
            List of (path, line_number, context) tuples
        """
        found_paths: list[tuple[str, int, str]] = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Skip comment-only lines ( YAML comments in examples)
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                continue

            # Skip lines that look like Python code (have import/def/class)
            if re.match(r"^\s*(import|from|def|class)\s+", stripped):
                continue

            # Find python file.py patterns
            for match in self.PYTHON_FILE_PATTERN.finditer(line):
                path_match = match.group("path")
                if path_match:
                    # Strip quotes
                    clean_path = path_match.strip('"').strip("'")
                    if clean_path and clean_path.endswith(".py"):
                        found_paths.append((clean_path, line_num, line.strip()))

            # Find standalone .py files after cd dir && pattern
            for match in self.STANDALONE_PY_PATTERN.finditer(line):
                path_match = match.group("path")
                if path_match:
                    clean_path = path_match.strip('"').strip("'")
                    if clean_path and clean_path.endswith(".py"):
                        found_paths.append((clean_path, line_num, line.strip()))

        return found_paths

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path string against the project root.

        Handles:
        - Absolute paths (P:\\path\\to\\file.py)
        - Paths relative to project root (.claude/skills/foo/bar.py)
        - Skill-level paths (.claude/skills/<skill>/__lib/foo.py -> resolved from .claude/ parent)
        - Paths with variable substitution (P:\\path\\{{variable}}\\file.py)

        Args:
            path_str: Path string from documentation

        Returns:
            Resolved Path object
        """
        # Remove variable placeholders for resolution
        clean_path = re.sub(r"\{\{[^}]+\}\}", "", path_str)

        # Strip quotes
        clean_path = clean_path.strip('"').strip("'")

        # Handle absolute Windows paths
        if re.match(r"^[A-Z]:\\", clean_path, re.IGNORECASE):
            return Path(clean_path)

        # Handle Unix-style absolute paths
        if clean_path.startswith("/"):
            return Path(clean_path)

        # Handle paths starting with P: or similar drive letters without \\
        if re.match(r"^[A-Z]:", clean_path, re.IGNORECASE) and "\\" not in clean_path:
            return Path(clean_path)

        # Handle skill-level paths: .claude/skills/<name>/__lib/foo.py
        # The .claude/ prefix anchors to the workspace's .claude/ directory.
        # project_root.parent.parent = workspace root (P:\\.claude)
        # The path .claude/skills/<name>/... is relative to workspace root
        # So .claude/skills/planning/__lib/auto_verify.py -> workspace_root / .claude/skills/planning/__lib/auto_verify.py
        skill_path_match = re.match(r"^\.claude/skills/([^/]+)(/.+)$", clean_path)
        if skill_path_match:
            # Replace .claude/ at start with workspace root
            remainder = clean_path.replace(".claude/", "", 1)
            workspace_root = self.project_root.parent.parent
            resolved = workspace_root / remainder
            return resolved

        # Treat as relative to project root
        return self.project_root / clean_path

    def _path_exists(self, path: Path) -> bool:
        """Check if a path exists (with Windows/Unix path handling)."""
        # Try as-is first
        if path.exists():
            return True

        # On Windows, try swapping separators
        if "\\" in str(path):
            alt = Path(str(path).replace("\\", "/"))
            if alt.exists():
                return True

        return False

    def check(self, skill_md_path: Path | None = None) -> EntryPointResult:
        """
        Check entry points documented in SKILL.md.

        Args:
            skill_md_path: Path to SKILL.md (defaults to project_root/SKILL.md)

        Returns:
            EntryPointResult with gaps found
        """
        gaps: list[EntryPointGap] = []
        entry_points_checked = 0
        entry_points_valid = 0

        # Default to SKILL.md in project root
        if skill_md_path is None:
            skill_md_path = self.project_root / "SKILL.md"

        # Check if SKILL.md exists
        if not skill_md_path.exists():
            # Not a skill project - skip check
            return EntryPointResult(gaps=[], entry_points_checked=0, entry_points_valid=0)

        try:
            content = skill_md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return EntryPointResult(gaps=[], entry_points_checked=0, entry_points_valid=0)

        # Find all Python file references
        refs = self._extract_paths_from_text(content)

        for path_str, line_num, context in refs:
            entry_points_checked += 1

            resolved = self._resolve_path(path_str)
            exists = self._path_exists(resolved)

            if exists:
                entry_points_valid += 1
            else:
                gaps.append(
                    EntryPointGap(
                        referenced_path=path_str,
                        resolved_path=str(resolved),
                        exists=False,
                        line_number=line_num,
                        context=context,
                    )
                )

        return EntryPointResult(
            gaps=gaps,
            entry_points_checked=entry_points_checked,
            entry_points_valid=entry_points_valid,
            entry_points_missing=len(gaps),
        )


# Convenience function
def check_entry_points(
    project_root: Path | None = None,
    skill_md_path: Path | None = None,
) -> EntryPointResult:
    """
    Quick entry point validation check.

    Args:
        project_root: Project root directory
        skill_md_path: Optional explicit path to SKILL.md

    Returns:
        EntryPointResult with gaps found
    """
    checker = EntryPointChecker(project_root)
    return checker.check(skill_md_path)
