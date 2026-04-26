"""TestPresenceChecker - Verify test file coverage.

Priority: P2 (runs during gap detection)
Purpose: Detect missing test files for source modules

Checks:
- For each .py file in src/ or lib/, check if tests/ exists
- Check if corresponding test_*.py file exists
- Report modules without tests
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestGap:
    """A module missing test coverage."""

    module_path: str
    expected_test_path: str
    test_exists: bool
    test_dir_exists: bool
    tier: str = "unit"  # unit | integration | e2e — inferred from path patterns


@dataclass
class TestPresenceResult:
    """Result of test presence check."""

    gaps: list[TestGap]
    modules_checked: int
    modules_with_tests: int
    modules_without_tests: int
    test_dirs_missing: int


class TestPresenceChecker:
    """
    Verify test file coverage for source modules.

    Checks for existence of test files corresponding to source modules.
    """

    # Default source directories to check
    DEFAULT_SOURCE_DIRS = ["src", "lib", "app"]

    # Default test directory names
    DEFAULT_TEST_DIRS = ["tests", "test"]

    # File extensions to consider
    SOURCE_EXTENSIONS = {".py"}

    def __init__(
        self,
        project_root: Path | None = None,
        source_dirs: list[str] | None = None,
        test_dirs: list[str] | None = None,
    ):
        """Initialize checker with project root and directories.

        Args:
            project_root: Project root directory (defaults to cwd)
            source_dirs: Source directory names to check
            test_dirs: Test directory names to search
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.source_dirs = source_dirs or self.DEFAULT_SOURCE_DIRS
        self.test_dirs = test_dirs or self.DEFAULT_TEST_DIRS

    def _find_test_dir(self, module_path: Path) -> Path | None:
        """Find the test directory for a given module.

        Args:
            module_path: Path to source module

        Returns:
            Path to test directory if found, None otherwise
        """
        # Check each test directory name
        for test_dir_name in self.test_dirs:
            # Check at project root
            test_dir = self.project_root / test_dir_name
            if test_dir.is_dir():
                return test_dir

            # Check alongside the module
            module_dir = module_path.parent
            test_dir = module_dir / test_dir_name
            if test_dir.is_dir():
                return test_dir

        return None

    def _get_expected_test_name(self, module_path: Path) -> str:
        """Get expected test file name for a module.

        Args:
            module_path: Path to source module

        Returns:
            Expected test file name
        """
        # For module named foo.py, expect test_foo.py
        # For module named foo/bar.py, expect test_bar.py in tests/foo/
        module_name = module_path.stem
        return f"test_{module_name}.py"

    def _get_expected_test_path(self, module_path: Path, test_dir: Path) -> Path:
        """Get expected test file path for a module.

        Args:
            module_path: Path to source module
            test_dir: Path to test directory

        Returns:
            Expected test file path
        """
        module_name = module_path.stem

        # Try to preserve directory structure
        # src/foo/bar.py -> tests/foo/test_bar.py
        try:
            relative_path = module_path.relative_to(self.project_root)
        except ValueError:
            # Module not under project root, use simple name
            return test_dir / f"test_{module_name}.py"

        # Build path preserving structure
        # src/foo/bar.py -> tests/foo/test_bar.py
        parts = list(relative_path.parts[:-1])  # All but filename
        parts.append(f"test_{module_name}.py")
        return test_dir.joinpath(*parts)

    def _infer_test_tier(self, module_path: Path) -> str:
        """Infer the test tier for a module based on its location and role.

        Tiers:
        - unit: Individual module/function tests (default)
        - integration: Tests for cross-module interaction
        - e2e: End-to-end workflow tests

        Args:
            module_path: Path to source module

        Returns:
            Test tier string
        """
        path_str = str(module_path).lower().replace("\\", "/")
        module_name = module_path.stem.lower()

        # E2E indicators: CLI entry points, main modules, app runners
        if any(k in module_name for k in ("cli", "main", "app", "server", "entry")):
            return "e2e"
        if any(k in path_str for k in ("api/", "routes/", "endpoints/", "handlers/")):
            return "integration"

        # Integration indicators: multi-module coordinators
        if any(k in module_name for k in ("orchestrator", "coordinator", "dispatcher", "pipeline")):
            return "integration"
        if any(k in path_str for k in ("services/", "workflows/", "pipelines/")):
            return "integration"

        # Default: unit test
        return "unit"

    def check(self) -> TestPresenceResult:
        """
        Check test presence for all source modules.

        Returns:
            TestPresenceResult with gaps found
        """
        gaps = []
        modules_checked = 0
        modules_with_tests = 0
        modules_without_tests = 0
        test_dirs_missing = 0

        # Find source directories
        source_paths = []
        for source_dir_name in self.source_dirs:
            source_dir = self.project_root / source_dir_name
            if source_dir.is_dir():
                source_paths.append(source_dir)

        # Check each source directory
        for source_dir in source_paths:
            for module_path in source_dir.rglob("*.py"):
                # Skip __init__.py and test files
                if module_path.name == "__init__.py":
                    continue
                if module_path.name.startswith("test_"):
                    continue

                modules_checked += 1

                # Find test directory
                test_dir = self._find_test_dir(module_path)
                test_dir_exists = test_dir is not None

                if not test_dir_exists:
                    test_dirs_missing += 1
                    gaps.append(
                        TestGap(
                            module_path=str(module_path),
                            expected_test_path="<no test dir found>",
                            test_exists=False,
                            test_dir_exists=False,
                            tier=self._infer_test_tier(module_path),
                        )
                    )
                    modules_without_tests += 1
                    continue

                # Get expected test path (test_dir is guaranteed to be non-None here)
                assert test_dir is not None  # for mypy type narrowing
                expected_test_path = self._get_expected_test_path(module_path, test_dir)
                test_exists = expected_test_path.exists()

                # Also check flat naming convention: tests/test_{module}.py
                # (Some projects use flat naming instead of mirroring directory structure)
                if not test_exists:
                    flat_test_path = test_dir / f"test_{module_path.stem}.py"
                    if flat_test_path.exists():
                        expected_test_path = flat_test_path
                        test_exists = True

                if not test_exists:
                    gaps.append(
                        TestGap(
                            module_path=str(module_path),
                            expected_test_path=str(expected_test_path),
                            test_exists=False,
                            test_dir_exists=True,
                            tier=self._infer_test_tier(module_path),
                        )
                    )
                    modules_without_tests += 1
                else:
                    modules_with_tests += 1

        return TestPresenceResult(
            gaps=gaps,
            modules_checked=modules_checked,
            modules_with_tests=modules_with_tests,
            modules_without_tests=modules_without_tests,
            test_dirs_missing=test_dirs_missing,
        )


# Convenience function
def check_test_presence(
    project_root: Path | None = None,
    source_dirs: list[str] | None = None,
    test_dirs: list[str] | None = None,
) -> TestPresenceResult:
    """
    Quick test presence check.

    Args:
        project_root: Project root directory
        source_dirs: Source directory names to check
        test_dirs: Test directory names to search

    Returns:
        TestPresenceResult with gaps found
    """
    checker = TestPresenceChecker(project_root, source_dirs, test_dirs)
    return checker.check()
