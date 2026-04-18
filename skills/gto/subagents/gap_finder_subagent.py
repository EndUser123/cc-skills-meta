"""GapFinderSubagent - Extract gaps with line numbers from codebase.

Priority: P2 (subagent for gap detection)
Purpose: Find and categorize code gaps with precise line numbers

Features:
- Line number extraction for precise gap location
- Gap categorization by type (testing, docs, dependencies, code_quality)
- Structured JSON output for ResultsBuilder consumption
"""

from __future__ import annotations

import ast
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GapFinding:
    """A gap found with precise location."""

    gap_type: str
    message: str
    file_path: str
    line_number: int
    severity: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        # Generate a unique ID based on gap attributes
        id_string = f"{self.gap_type}:{self.file_path}:{self.line_number}:{self.message}"
        gap_id = f"GAP-{hashlib.md5(id_string.encode()).hexdigest()[:8]}"

        return {
            "id": gap_id,
            "type": self.gap_type,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "severity": self.severity,
            "metadata": self.metadata,
        }


@dataclass
class GapFinderResult:
    """Result of gap finding."""

    gaps: list[GapFinding]
    files_scanned: int
    gaps_found: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "gaps": [gap.to_dict() for gap in self.gaps],
            "files_scanned": self.files_scanned,
            "gaps_found": self.gaps_found,
        }


class GapFinderSubagent:
    """
    Find gaps in codebase with line number precision.

    Extracts gaps with precise file and line number information
    for ResultsBuilder consolidation.
    """

    # Patterns for gap detection
    GAP_PATTERNS = {
        "test_gap": {
            "patterns": [
                (r"# TODO: add test", "medium"),
                (r"# FIXME: test", "high"),
                (r"# XXX: no test", "medium"),
            ],
            "description": "Missing test coverage",
        },
        "doc_gap": {
            "patterns": [
                (r"# TODO: document", "low"),
                (r"# FIXME: docstring", "medium"),
            ],
            "description": "Missing documentation",
        },
        "code_quality": {
            "patterns": [
                (r"# HACK:", "medium"),
                (r"# FIXME:", "high"),
                (r"# XXX:", "medium"),
                (r"# TODO:", "low"),
            ],
            "description": "Code quality issue",
        },
        "import_issue": {
            "patterns": [
                (r"# type: ignore", "medium"),
            ],
            "description": "Import or type issue",
        },
    }

    def __init__(self, project_root: Path | None = None):
        """Initialize gap finder.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def _extract_line_number(
        self, file_path: Path, pattern: str, content: str
    ) -> list[tuple[int, str]]:
        """Extract line numbers for pattern matches.

        Args:
            file_path: Path to file
            pattern: Regex pattern to search
            content: File content

        Returns:
            List of (line_number, matched_text) tuples
        """
        matches = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            if re.search(pattern, line, re.IGNORECASE):
                matches.append((line_num, line.strip()))

        return matches

    def _scan_file_for_gaps(self, file_path: Path) -> list[GapFinding]:
        """Scan a single file for gaps.

        Args:
            file_path: Path to file

        Returns:
            List of GapFinding objects
        """
        gaps = []

        # Skip scanning this file itself to avoid detecting pattern definitions as gaps
        if file_path.name == "gap_finder_subagent.py":
            return gaps

        try:
            with open(file_path) as f:
                content = f.read()

            # Check each gap pattern
            for gap_type, config in self.GAP_PATTERNS.items():
                for pattern, severity in config["patterns"]:
                    matches = self._extract_line_number(file_path, pattern, content)

                    for line_num, matched_text in matches:
                        gaps.append(
                            GapFinding(
                                gap_type=gap_type,
                                message=f"{config['description']}: {matched_text}",
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_num,
                                severity=severity,
                                metadata={"matched_text": matched_text},
                            )
                        )

        except (OSError, UnicodeDecodeError):
            # Skip files that can't be read
            pass

        return gaps

    def _scan_for_missing_tests(self, source_files: list[Path]) -> list[GapFinding]:
        """Scan for missing test files.

        Args:
            source_files: Pre-filtered list of Python source files (excludes tests)

        Returns:
            List of GapFinding objects for missing tests
        """
        gaps = []

        for source_file in source_files:
            # Check if tested by thematic test file (e.g., layer1_* → test_layer1)
            if self._is_tested_by_thematic(source_file):
                continue

            # Check if corresponding test file exists
            test_path = source_file.parent / f"test_{source_file.name}"
            tests_dir = source_file.parent / "tests"
            alt_test_path = tests_dir / f"test_{source_file.name}"

            # Also check flat naming convention: tests/test_{module}.py at project root
            # (Some projects use flat naming instead of mirroring directory structure)
            root_tests_dir = self.project_root / "tests"
            flat_test_path = root_tests_dir / f"test_{source_file.stem}.py"

            if (
                not test_path.exists()
                and not alt_test_path.exists()
                and not flat_test_path.exists()
            ):
                gaps.append(
                    GapFinding(
                        gap_type="missing_test",
                        message=f"No test file found for {source_file.name}",
                        file_path=str(source_file.relative_to(self.project_root)),
                        line_number=1,  # File-level gap
                        severity="high",
                    )
                )

        return gaps

    def _is_tested_by_thematic(self, source_file: Path) -> bool:
        """Check if source_file is covered by a thematic test file.

        Some projects organize tests thematically rather than 1:1:
        - layers/layer{N}_*.py → tests/test_layer{N}[_suffix].py
          (e.g. layer1_syntactic.py → test_layer1.py)
        - orchestrator.py → tests/test_integration.py
        - findings/models.py → tests/test_health_score.py
        """
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists():
            return False

        # Pattern: layer{N}_*.py → test_layer{N}[_suffix].py
        layer_match = re.match(r"^layer(\d+)_.+\.py$", source_file.name)
        if layer_match:
            layer_num = layer_match.group(1)
            # Check for test_layer1.py, test_layer1_something.py, etc.
            test_pattern = re.compile(rf"^test_layer{layer_num}(?:_\w+)?\.py$")
            for test_file in tests_dir.glob("test_layer*.py"):
                if test_pattern.match(test_file.name):
                    return True

        # orchestrator.py → test_integration.py
        if source_file.name == "orchestrator.py":
            return (tests_dir / "test_integration.py").exists()

        # findings/models.py → test_health_score.py
        if source_file.name == "models.py" and source_file.parent.name == "findings":
            return (tests_dir / "test_health_score.py").exists()

        return False

    def _scan_for_missing_docs(self, source_files: list[Path]) -> list[GapFinding]:
        """Scan for missing documentation.

        Args:
            source_files: Pre-filtered list of Python source files (excludes tests)

        Returns:
            List of GapFinding objects for missing docs
        """
        gaps = []

        for source_file in source_files:
            # Check for docstring
            try:
                with open(source_file) as f:
                    content = f.read()
                    tree = ast.parse(content)

                    # Check if module has docstring
                    has_docstring = (
                        ast.get_docstring(tree) is not None
                        or len(tree.body) > 0
                        and isinstance(tree.body[0], ast.Expr)
                        and isinstance(tree.body[0].value, ast.Constant)
                        and isinstance(tree.body[0].value.value, str)
                    )

                    if not has_docstring:
                        gaps.append(
                            GapFinding(
                                gap_type="missing_docs",
                                message=f"Module missing docstring: {source_file.name}",
                                file_path=str(source_file.relative_to(self.project_root)),
                                line_number=1,
                                severity="medium",
                            )
                        )

            except (OSError, UnicodeDecodeError, SyntaxError):
                # Skip problematic files
                pass

        return gaps

    def find_gaps(self) -> GapFinderResult:
        """
        Find all gaps in the codebase.

        Returns:
            GapFinderResult with all gaps found
        """
        all_gaps = []

        # Compute source files once (excludes tests, __init__.py)
        source_files = [
            p
            for p in self.project_root.rglob("*.py")
            if p.name != "__init__.py" and not p.name.startswith("test_") and "tests" not in p.parts
        ]

        # Scan Python files for inline gap markers (all files including tests)
        py_files = list(self.project_root.rglob("*.py"))
        for py_file in py_files:
            all_gaps.extend(self._scan_file_for_gaps(py_file))

        # Scan for missing tests (uses pre-filtered source_files)
        all_gaps.extend(self._scan_for_missing_tests(source_files))

        # Scan for missing docs (uses pre-filtered source_files)
        all_gaps.extend(self._scan_for_missing_docs(source_files))

        return GapFinderResult(
            gaps=all_gaps,
            files_scanned=len(py_files),
            gaps_found=len(all_gaps),
        )


# Convenience function
def find_gaps(project_root: Path | None = None) -> GapFinderResult:
    """
    Quick gap finding.

    Args:
        project_root: Project root directory

    Returns:
        GapFinderResult with all gaps found
    """
    finder = GapFinderSubagent(project_root)
    return finder.find_gaps()
