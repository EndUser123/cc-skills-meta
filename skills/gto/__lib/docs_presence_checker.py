"""DocsPresenceChecker - Verify documentation coverage.

Priority: P2 (runs during gap detection)
Purpose: Detect missing documentation for source modules

Checks:
- For each .py file, check if README.md or docs/ exists
- Check if corresponding documentation exists
- Report modules without documentation
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocGap:
    """A module missing documentation."""

    module_path: str
    expected_doc_paths: list[str]
    any_doc_exists: bool


@dataclass
class DocPresenceResult:
    """Result of documentation presence check."""

    gaps: list[DocGap]
    modules_checked: int
    modules_with_docs: int
    modules_without_docs: int


class DocsPresenceChecker:
    """
    Verify documentation coverage for source modules.

    Checks for existence of documentation files corresponding to source modules.
    """

    # Default documentation patterns to look for
    DOC_PATTERNS = [
        "README.md",
        "readme.md",
        "docs.md",
        "DOCS.md",
        # Skills typically document themselves via SKILL.md at project root
        "SKILL.md",
    ]

    # Default documentation directories
    DOC_DIRS = ["docs", "doc", "documentation"]

    def __init__(self, project_root: Path | None = None):
        """Initialize checker with project root.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def _find_docs_for_module(self, module_path: Path) -> list[str]:
        """Find documentation files for a given module.

        Args:
            module_path: Path to source module

        Returns:
            List of documentation file paths found
        """
        found_docs = []

        # Get module directory
        module_dir = module_path.parent

        # Check for README/docs in same directory
        for doc_pattern in self.DOC_PATTERNS:
            doc_path = module_dir / doc_pattern
            if doc_path.exists():
                found_docs.append(str(doc_path))

        # Check for docs/ directory alongside module
        for doc_dir_name in self.DOC_DIRS:
            doc_dir = module_dir / doc_dir_name
            if doc_dir.is_dir():
                # Check for index.md or README.md in docs dir
                for index_file in ["index.md", "README.md"]:
                    index_path = doc_dir / index_file
                    if index_path.exists():
                        found_docs.append(str(index_path))
                        break

        # Also check for SKILL.md at project root (skills self-document via SKILL.md)
        skill_md = self.project_root / "SKILL.md"
        if skill_md.exists() and str(skill_md) not in found_docs:
            found_docs.append(str(skill_md))

        return found_docs

    def _has_centralized_docs(self) -> bool:
        """Check if project uses centralized documentation (docs/ at root).

        Returns:
            True if project has docs/ or doc/ directory at root
        """
        for doc_dir_name in self.DOC_DIRS:
            doc_dir = self.project_root / doc_dir_name
            if doc_dir.is_dir():
                # Check if it has at least one .md file
                md_files = list(doc_dir.rglob("*.md"))
                if md_files:
                    return True
        return False

    def check(self, source_paths: list[Path] | None = None) -> DocPresenceResult:
        """
        Check documentation presence for source modules.

        Args:
            source_paths: List of source paths to check (defaults to all .py files)

        Returns:
            DocPresenceResult with gaps found
        """
        gaps = []
        modules_checked = 0
        modules_with_docs = 0
        modules_without_docs = 0

        # If no source paths provided, scan all .py files
        if source_paths is None:
            source_paths = list(self.project_root.rglob("*.py"))
            # Filter out test files and __init__.py
            source_paths = [
                p
                for p in source_paths
                if p.name != "__init__.py" and not p.name.startswith("test_")
            ]

        # Check if project uses centralized documentation
        has_centralized_docs = self._has_centralized_docs()

        for module_path in source_paths:
            # Skip __init__.py and test files
            if module_path.name == "__init__.py":
                continue
            if module_path.name.startswith("test_"):
                continue

            modules_checked += 1

            # Find documentation for this module
            found_docs = self._find_docs_for_module(module_path)

            if found_docs:
                modules_with_docs += 1
            elif not has_centralized_docs:
                # Only flag as missing if project doesn't use centralized docs
                # (centralized docs are checked separately as a single gap)
                modules_without_docs += 1
                # Build expected doc paths
                module_dir = module_path.parent
                expected_paths = [
                    str(module_dir / "README.md"),
                    str(module_dir / "docs.md"),
                    str(module_dir / "docs" / "index.md"),
                    # Skills self-document via SKILL.md at project root
                    str(self.project_root / "SKILL.md"),
                ]
                gaps.append(
                    DocGap(
                        module_path=str(module_path),
                        expected_doc_paths=expected_paths,
                        any_doc_exists=False,
                    )
                )
            # If has_centralized_docs and no per-module docs found, don't flag
            # (the centralized docs cover the module)

        return DocPresenceResult(
            gaps=gaps,
            modules_checked=modules_checked,
            modules_with_docs=modules_with_docs,
            modules_without_docs=modules_without_docs,
        )


# Convenience function
def check_docs_presence(
    project_root: Path | None = None,
    source_paths: list[Path] | None = None,
) -> DocPresenceResult:
    """
    Quick documentation presence check.

    Args:
        project_root: Project root directory
        source_paths: List of source paths to check

    Returns:
        DocPresenceResult with gaps found
    """
    checker = DocsPresenceChecker(project_root)
    return checker.check(source_paths)
