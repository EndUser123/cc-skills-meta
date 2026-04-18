"""CodeMarkerScanner - Scan project for TODO/FIXME markers.

Priority: P2 (runs during gap detection)
Purpose: Find code markers (TODO, FIXME, HACK, XXX) in source files

Features:
- Uses shared FileScanner (Layer0) for safe filesystem traversal
- Path sanitization (prevents directory traversal attacks)
- .gitignore-aware scanning (respects exclusion patterns)
- Configurable file extensions whitelist
- Max file size limit (skip binaries)
- Safe symlink handling (follow=False)
"""

from __future__ import annotations

import json

# Add _shared scanners package to sys.path (required for FileScanner import)
import pathlib as _pathlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

_shared_root = _pathlib.Path.home() / ".claude" / "skills" / "_shared"
if str(_shared_root) not in sys.path:
    sys.path.insert(0, str(_shared_root))

from scanners.base import (  # type: ignore[attr-defined]
    MAX_FILE_SIZE as _SCANNER_MAX_FILE_SIZE,
)
from scanners.base import (
    SKIP_DIRS as _SCANNER_SKIP_DIRS,
)
from scanners.base import (
    FileScanner,
)


@dataclass
class CodeMarker:
    """A code marker found in source file."""

    marker_type: Literal["TODO", "FIXME", "HACK", "XXX", "NOTE", "BUG"]
    content: str
    file_path: str  # Sanitized absolute path
    line_number: int
    relative_path: str  # Path relative to project root


@dataclass
class CodeMarkerResult:
    """Result of code marker scanning."""

    markers: list[CodeMarker]
    total_count: int
    files_scanned: int
    files_with_markers: int
    errors: list[str]


class CodeMarkerScanner:
    """
    Scan project for TODO/FIXME markers with safety constraints.

    Scans source files for code markers like TODO, FIXME, HACK, etc.
    Enforces path sanitization and respects .gitignore patterns.
    """

    # Marker patterns with type classification
    MARKER_PATTERNS = {
        "TODO": r"TODO:\s*(.+)",
        "FIXME": r"FIXME:\s*(.+)",
        "HACK": r"HACK:\s*(.+)",
        "XXX": r"XXX:\s*(.+)",
        "NOTE": r"NOTE:\s*(.+)",
        "BUG": r"BUG:\s*(.+)",
    }

    # Default file extensions to scan
    DEFAULT_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".md",
        ".txt",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
    }

    # Directories to always skip (regardless of .gitignore)
    # Union of FileScanner defaults + "tests" (pattern repos have example TODOs)
    SKIP_DIRS = _SCANNER_SKIP_DIRS | {"tests"}

    # Max file size (1MB) - skip binaries
    MAX_FILE_SIZE = _SCANNER_MAX_FILE_SIZE

    def __init__(
        self,
        project_root: Path | None = None,
        extensions: set[str] | None = None,
        max_file_size: int = MAX_FILE_SIZE,
    ):
        """Initialize scanner with project root and constraints.

        Args:
            project_root: Project root directory (defaults to cwd)
            extensions: File extensions to scan (whitelist)
            max_file_size: Maximum file size in bytes (skip larger files)
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.extensions = extensions or self.DEFAULT_EXTENSIONS
        self.max_file_size = max_file_size
        # Layer0: FileScanner for safe filesystem traversal
        self._scanner = FileScanner(
            project_root=self.project_root,
            skip_dirs=self.SKIP_DIRS,
            max_file_size=max_file_size,
            extensions=self.extensions,
        )

    def _sanitize_path(self, path: Path) -> Path:
        """Sanitize path to prevent directory traversal.

        Args:
            path: Path to sanitize

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path escapes project root
        """
        try:
            resolved = path.resolve()
        except OSError:
            raise ValueError(f"Invalid path: {path}")

        # Check if resolved path is within project root
        try:
            resolved.relative_to(self.project_root)
        except ValueError:
            raise ValueError(f"Path escapes project root: {path} -> {resolved}")

        return resolved

    def _load_gitignore_patterns(self) -> list[str]:
        """Load .gitignore patterns if available.

        Returns:
            List of .gitignore patterns (empty if missing/unreadable)
        """
        gitignore_path = self.project_root / ".gitignore"

        if not gitignore_path.exists():
            return []

        try:
            with open(gitignore_path) as f:
                lines = f.readlines()
        except OSError as e:
            # Log warning but continue without filters
            return [f"_GITIGNORE_ERROR: {e}"]

        patterns = []
        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            patterns.append(line)

        return patterns

    def _should_skip_directory(self, dir_name: str) -> bool:
        """Check if directory should be skipped.

        Args:
            dir_name: Directory name to check

        Returns:
            True if directory should be skipped
        """
        return dir_name in self.SKIP_DIRS

    def _should_scan_file(self, file_path: Path) -> bool:
        """Check if file should be scanned.

        Args:
            file_path: File path to check

        Returns:
            True if file should be scanned
        """
        # Check extension whitelist
        if file_path.suffix not in self.extensions:
            return False

        # SECURITY: Check for symlink traversal attack
        # Use lstat() to not follow symlinks, then resolve to check actual location
        try:
            # lstat() does NOT follow symlinks - gets info about the symlink itself
            file_stat = file_path.lstat()

            # If it's a symlink, verify it points within project root
            import os

            if os.path.islink(file_path):
                resolved = file_path.resolve()
                # Ensure symlink target is within project root
                try:
                    resolved.relative_to(self.project_root)
                except ValueError:
                    # Symlink points outside project root - skip for security
                    return False

            # Check file size using lstat (doesn't follow symlinks)
            if file_stat.st_size > self.max_file_size:
                return False
        except OSError:
            return False

        # Check if any parent directory is in SKIP_DIRS
        # This handles nested directories like references/, tests/, etc.
        try:
            relative = file_path.relative_to(self.project_root)
            for parent in relative.parents:
                if parent.name in self.SKIP_DIRS:
                    return False
        except ValueError:
            # Path not relative to project root - skip
            return False

        return True

    def _scan_file(self, file_path: Path) -> list[CodeMarker]:
        """Scan a single file for markers.

        Args:
            file_path: Path to file to scan

        Returns:
            List of markers found in file
        """
        markers = []

        # SECURITY: Verify resolved path is within project root before opening
        # This prevents reading files outside project via symlink traversal
        import os

        if os.path.islink(file_path):
            resolved = file_path.resolve()
            try:
                resolved.relative_to(self.project_root)
            except ValueError:
                # Symlink points outside project root - skip for security
                return []

        try:
            relative_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            # Path not relative to project root - skip
            return []

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except OSError:
            return []

        for line_num, line in enumerate(lines, start=1):
            # Check each marker pattern
            for marker_type, pattern in self.MARKER_PATTERNS.items():
                match = re.search(pattern, line)
                if match:
                    markers.append(
                        CodeMarker(
                            marker_type=marker_type,  # type: ignore[arg-type]
                            content=match.group(1).strip(),
                            file_path=str(file_path),
                            line_number=line_num,
                            relative_path=relative_path,
                        )
                    )

        return markers

    def scan(self, output_path: Path | None = None) -> CodeMarkerResult:
        """
        Scan project for code markers.

        Args:
            output_path: Optional path to write JSON artifact

        Returns:
            CodeMarkerResult with all found markers
        """
        all_markers = []
        errors = []
        files_scanned = 0
        files_with_markers = 0

        # Layer0: Use FileScanner for safe traversal — all path guards handled there
        scan_result = self._scanner.scan(pattern="**/*.py")

        # Layer1: For each file from scanner, apply detector logic
        for rel_path in scan_result.files:
            file_path = self.project_root / rel_path
            # Additional filter: skip "tests" parent dirs (CodeMarkerScanner-specific)
            # This complements FileScanner's skip_dirs with detector-specific rules
            if any(p.name == "tests" for p in rel_path.parents):
                continue

            files_scanned += 1

            # Scan file for markers
            try:
                markers = self._scan_file(file_path)
                if markers:
                    all_markers.extend(markers)
                    files_with_markers += 1
            except Exception as e:
                errors.append(f"Error scanning {file_path}: {e}")

        result = CodeMarkerResult(
            markers=all_markers,
            total_count=len(all_markers),
            files_scanned=files_scanned,
            files_with_markers=files_with_markers,
            errors=errors,
        )

        # Write JSON artifact if path provided
        if output_path:
            self._write_artifact(result, output_path)

        return result

    def _write_artifact(self, result: CodeMarkerResult, output_path: Path) -> None:
        """Write scan result to JSON artifact.

        Args:
            result: Scan result to write
            output_path: Path to write artifact
        """
        artifact = {
            "markers": [
                {
                    "type": m.marker_type,
                    "content": m.content,
                    "file_path": m.file_path,
                    "line_number": m.line_number,
                    "relative_path": m.relative_path,
                }
                for m in result.markers
            ],
            "summary": {
                "total_count": result.total_count,
                "files_scanned": result.files_scanned,
                "files_with_markers": result.files_with_markers,
                "errors": result.errors,
            },
        }

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(artifact, f, indent=2)
        except OSError as e:
            # Log error but don't fail the scan
            result.errors.append(f"Cannot write artifact to {output_path}: {e}")


# Convenience function
def scan_code_markers(
    project_root: Path | None = None,
    output_path: Path | None = None,
) -> CodeMarkerResult:
    """
    Quick code marker scanning.

    Args:
        project_root: Project root directory
        output_path: Optional path to write JSON artifact

    Returns:
        CodeMarkerResult with detected markers
    """
    scanner = CodeMarkerScanner(project_root)
    return scanner.scan(output_path)
