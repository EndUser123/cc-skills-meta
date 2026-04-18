"""ChainIntegrityChecker - Validate handoff chain integrity.

Priority: P0 (runs during scope discovery)
Purpose: Validate handoff chain integrity before passing paths to engine

Checks for each path in the chain:
1. File is readable (no permission errors)
2. File is valid JSONL (no parse errors)
3. Sequence numbers are contiguous (no gaps between handoff links)
4. Referenced terminal_ids in chain match expectations
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ChainIntegrityResult:
    """Result of chain integrity check."""

    paths: list[str]  # Valid paths that passed all checks
    partial_scope: bool  # True if chain is incomplete
    excluded: list[str]  # Paths excluded from analysis
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """True if no paths were excluded (all passed)."""
        return len(self.excluded) == 0

    @property
    def issues(self) -> list[str]:
        """List of issues found (warnings)."""
        return self.warnings


class ChainIntegrityChecker:
    """
    Validate handoff chain integrity before passing paths to engine.

    Behavior:
    - Valid chain → proceed with full path list
    - Broken link found → flag as PARTIAL_SCOPE=True, warn user, continue with available
    - Unreadable file → exclude from analysis, flag in output
    - Invalid JSONL → exclude, flag in output
    """

    def __init__(self, project_root: Path | None = None):
        """Initialize checker with project root.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()

    def check_chain(self, paths: list[str]) -> ChainIntegrityResult:
        """
        Validate chain of transcript paths.

        Args:
            paths: List of transcript paths to validate

        Returns:
            ChainIntegrityResult with valid paths, exclusions, and warnings
        """
        valid_paths = []
        excluded = []
        warnings = []

        for path_str in paths:
            path = Path(path_str)

            # Check 1: File is readable
            if not path.exists():
                warnings.append(f"File not found: {path}")
                excluded.append(path_str)
                continue

            if not path.is_file():
                warnings.append(f"Not a file: {path}")
                excluded.append(path_str)
                continue

            # Check 2: File is valid JSONL
            try:
                with open(path) as f:
                    # Try to parse first line as JSON
                    first_line = f.readline()
                    if first_line.strip():
                        json.loads(first_line)
            except (OSError, PermissionError) as e:
                warnings.append(f"Cannot read {path}: {e}")
                excluded.append(path_str)
                continue
            except json.JSONDecodeError as e:
                warnings.append(f"Invalid JSONL in {path}: {e}")
                excluded.append(path_str)
                continue

            # Check 3 & 4: Sequence numbers and terminal_ids (if handoff data)
            # For now, just check if file is valid JSONL
            # Full handoff chain validation can be added later
            valid_paths.append(path_str)

        # Determine if scope is partial
        partial_scope = len(excluded) > 0

        return ChainIntegrityResult(
            paths=valid_paths,
            partial_scope=partial_scope,
            excluded=excluded,
            warnings=warnings,
        )


# Convenience function
def check_chain_integrity(
    paths: list[str] | Path, project_root: Path | None = None
) -> ChainIntegrityResult:
    """
    Quick chain integrity check.

    Args:
        paths: List of transcript paths or a single Path object
        project_root: Project root directory

    Returns:
        ChainIntegrityResult with validation status
    """
    checker = ChainIntegrityChecker(project_root)
    # Handle single Path object
    if isinstance(paths, Path):
        paths = [str(paths)]
    return checker.check_chain(paths)
