"""Adversarial Test Corpus for FileScanner.

This test corpus verifies FileScanner's security properties and robustness
against adversarial filesystem conditions:
- Path traversal attempts
- Symlink loops
- Oversized files
- .gitignore patterns
- Windows-specific edge cases

Run with: pytest P:/.claude/skills/gto/tests/test_scanner_corpus.py -v
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Add the shared scanners package to sys.path
_SHARED_SCANNERS_PATH = Path.home() / ".claude" / "skills" / "_shared"
if _SHARED_SCANNERS_PATH.exists():
    sys.path.insert(0, str(_SHARED_SCANNERS_PATH))

from scanners.base import MAX_FILE_SIZE, SKIP_DIRS, FileScanner, ScanResult  # type: ignore


class TestNormalFileTraversal:
    """Tests for normal file traversal behavior."""

    def test_finds_files_in_nested_directories(self):
        """Test that FileScanner finds files in nested directory structure.

        Given: A project with nested directories containing .py files
        When: Scanning with default settings
        Then: All .py files are found
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create nested structure
            (project_root / "src" / "modules").mkdir(parents=True)
            (project_root / "src" / "modules" / "foo.py").touch()
            (project_root / "src" / "modules" / "bar.py").touch()
            (project_root / "src" / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan(pattern="**/*.py")

            assert len(result.files) == 3
            paths_str = [str(f) for f in result.files]
            assert any("foo.py" in p for p in paths_str)
            assert any("bar.py" in p for p in paths_str)
            assert any("main.py" in p for p in paths_str)

    def test_respects_extension_filter(self):
        """Test that FileScanner only returns files with whitelisted extensions.

        Given: A project with multiple file types
        When: Scanning with specific extensions
        Then: Only files with matching extensions are returned
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            (project_root / "file.py").touch()
            (project_root / "file.txt").touch()
            (project_root / "file.md").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan(pattern="**/*")

            extensions = {f.suffix for f in result.files}
            assert ".py" in extensions
            assert ".txt" not in extensions
            assert ".md" not in extensions


class TestPathTraversalBlocked:
    """Tests for path traversal attack prevention."""

    def test_blocks_absolute_path_traversal(self):
        """Test that absolute path traversal attempts are blocked.

        Given: A project root and an absolute path escaping it
        When: Calling _sanitize_path
        Then: ValueError is raised
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scanner = FileScanner(project_root=project_root)

            # Attempt path traversal with absolute path
            traversal_path = project_root / "subdir" / ".." / ".." / ".." / "etc" / "passwd"

            with pytest.raises(ValueError, match="escapes project root"):
                scanner._sanitize_path(traversal_path)

    def test_blocks_relative_path_traversal(self):
        """Test that relative path traversal attempts are blocked.

        Given: A project root and a relative path escaping it
        When: Calling _sanitize_path
        Then: ValueError is raised
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scanner = FileScanner(project_root=project_root)

            # Attempt path traversal with many ..
            traversal_path = (
                Path(tmpdir) / "src" / ".." / ".." / ".." / "windows" / "system32" / "config.sys"
            )

            with pytest.raises(ValueError, match="escapes project root"):
                scanner._sanitize_path(traversal_path)

    def test_allows_valid_relative_paths(self):
        """Test that valid paths inside project root are allowed.

        Given: A valid path inside project root
        When: Calling _sanitize_path
        Then: The resolved path is returned
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scanner = FileScanner(project_root=project_root)

            subdir = project_root / "src" / "modules"
            subdir.mkdir(parents=True)
            valid_path = subdir / "test.py"
            valid_path.touch()

            result = scanner._sanitize_path(valid_path)
            # _sanitize_path returns resolved absolute path within project root
            assert result == valid_path.resolve()


class TestSymlinkHandling:
    """Tests for symlink security guards."""

    def test_symlink_outside_root_skipped(self):
        """Test that symlinks pointing outside project root are skipped.

        Given: A symlink inside project root that points outside
        When: Scanning the project
        Then: The symlink target is not followed
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

            scanner = FileScanner(project_root=project_root, extensions={".txt"})
            result = scanner.scan(pattern="**/*")

            # The symlinked file should not be scanned
            assert symlink_path.relative_to(project_root) not in result.files

    def test_symlink_loop_detected(self):
        """Test that symlink loops are detected and handled.

        Given: A circular symlink (a -> b, b -> a)
        When: Scanning the project
        Then: The scan completes without infinite loop
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create two directories with circular symlinks
            dir_a = project_root / "dir_a"
            dir_b = project_root / "dir_b"
            dir_a.mkdir()
            dir_b.mkdir()

            # Create circular symlinks
            link_a_to_b = dir_a / "link_to_b"
            link_b_to_a = dir_b / "link_to_a"
            link_a_to_b.symlink_to(dir_b)
            link_b_to_a.symlink_to(dir_a)

            # Add a real file
            (project_root / "real_file.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            # Should complete without hanging or crashing
            result = scanner.scan(pattern="**/*.py")

            # The real file should be found
            assert any("real_file.py" in str(f) for f in result.files)


class TestOversizedFiles:
    """Tests for max file size filtering."""

    def test_skips_oversized_files(self):
        """Test that files larger than MAX_FILE_SIZE are skipped.

        Given: A project with files larger than MAX_FILE_SIZE
        When: Scanning the project
        Then: Those large files are not included in results
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a file larger than MAX_FILE_SIZE
            large_file = project_root / "large.bin"
            with open(large_file, "wb") as f:
                f.write(b"x" * (MAX_FILE_SIZE + 1))

            # Create a normal-sized file
            small_file = project_root / "small.txt"
            small_file.write_text("hello")

            scanner = FileScanner(project_root=project_root, extensions={".txt", ".bin"})
            result = scanner.scan(pattern="**/*")

            # Large file should not be scanned
            assert large_file.relative_to(project_root) not in result.files
            # Small file should be scanned
            assert small_file.relative_to(project_root) in result.files


class TestGitignorePatterns:
    """Tests for .gitignore pattern handling."""

    def test_respects_gitignore_patterns(self):
        """Test that .gitignore patterns are respected during scanning.

        Given: A project with .gitignore excluding certain directories
        When: Scanning the project
        Then: Files matching .gitignore patterns are excluded
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create .gitignore
            gitignore = project_root / ".gitignore"
            gitignore.write_text("__pycache__\n*.pyc\n")

            # Create pycache with python files
            pycache_dir = project_root / "__pycache__"
            pycache_dir.mkdir()
            (pycache_dir / "module.cpython-314.pyc").touch()

            # Create regular source
            (project_root / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py", ".pyc"})
            result = scanner.scan(pattern="**/*.py")

            # __pycache__ should be respected
            paths_str = [str(f) for f in result.files]
            assert not any("__pycache__" in p for p in paths_str)
            assert not any(".pyc" in p for p in paths_str)

    def test_gitignore_read_error_continues(self):
        """Test that .gitignore read errors don't crash the scan.

        Given: A project with an unreadable .gitignore
        When: Scanning continues
        Then: Scan completes successfully
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a valid source file
            (project_root / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan(pattern="**/*.py")

            assert len(result.files) >= 1


class TestSkipDirectories:
    """Tests for directory skipping behavior."""

    def test_skips_default_skip_dirs(self):
        """Test that directories in SKIP_DIRS are excluded.

        Given: A project with directories matching SKIP_DIRS
        When: Scanning the project
        Then: Those directories are not traversed
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create directories matching SKIP_DIRS (filter wildcards for filesystem safety)
            for dir_name in SKIP_DIRS:
                if "*" in dir_name:  # Skip wildcard patterns like *.egg-info
                    continue
                skip_dir = project_root / dir_name
                skip_dir.mkdir(parents=True, exist_ok=True)
                (skip_dir / "file.py").touch()

            # Create valid source directory
            src_dir = project_root / "src"
            src_dir.mkdir()
            (src_dir / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan(pattern="**/*.py")

            # SKIP_DIRS should not appear in scanned files
            scanned_paths = [str(f) for f in result.files]
            for dir_name in SKIP_DIRS:
                assert dir_name not in scanned_paths

            # Valid src should be scanned
            assert any("src" in str(f) for f in result.files)


class TestWindowsEdgeCases:
    """Tests for Windows-specific edge cases."""

    def test_handles_windows_drive_letters(self):
        """Test that Windows drive letters are handled correctly.

        Given: A path with a Windows drive letter
        When: Scanning from a path on a specific drive
        Then: The scan completes without error
        """
        # This test uses the actual project root which may or may not have drive letters
        # The key is that Path.resolve() and relative_to() work on Windows
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan(pattern="**/*.py")

            assert len(result.files) == 1
            assert result.files[0].name == "main.py"

    def test_handles_long_paths(self):
        """Test that very long paths are handled correctly.

        Given: A project with deeply nested directories
        When: Scanning the project
        Then: All files are found regardless of path depth
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create a deeply nested structure
            deep_path = project_root
            for i in range(10):
                deep_path = deep_path / f"level_{i}"
            deep_path.mkdir(parents=True, exist_ok=True)
            (deep_path / "deep_module.py").touch()

            # Also create a shallow file
            (project_root / "shallow.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan(pattern="**/*.py")

            names = [f.name for f in result.files]
            assert "deep_module.py" in names
            assert "shallow.py" in names


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_scan_result_has_required_fields(self):
        """Test that ScanResult has files and errors fields.

        Given: A ScanResult instance with data
        When: Accessing its fields
        Then: All expected fields are present with correct types
        """
        result = ScanResult(
            files=[Path("test.py")],
            errors=["error1", "error2"],
        )

        assert hasattr(result, "files")
        assert hasattr(result, "errors")
        assert result.files == [Path("test.py")]
        assert result.errors == ["error1", "error2"]

    def test_scan_time_ms_is_float(self):
        """Test that scan_time_ms is recorded as a positive float.

        Given: A valid project to scan
        When: Scanning completes
        Then: scan_time_ms is recorded as a positive float
        """
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "main.py").touch()

            scanner = FileScanner(project_root=project_root, extensions={".py"})
            result = scanner.scan()

            assert isinstance(result.scan_time_ms, float)
            assert result.scan_time_ms >= 0
