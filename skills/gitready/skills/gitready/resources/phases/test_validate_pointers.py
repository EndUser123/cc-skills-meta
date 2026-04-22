#!/usr/bin/env python
"""Tests for validate_pointers.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

from resources.phases.validate_pointers import validate_pointers


class TestValidatePointers:
    """Test validate_pointers function."""

    def test_valid_pointers_in_skill_md(self) -> None:
        """All current > READ: pointers in SKILL.md resolve to existing, non-empty files."""
        errors = validate_pointers()
        assert errors == [], f"Broken pointers found: {errors}"

    def test_missing_skill_md(self) -> None:
        """Non-existent SKILL.md returns error."""
        errors = validate_pointers("/nonexistent/path/SKILL.md")
        assert len(errors) == 1
        assert "not found" in errors[0]

    def test_broken_pointer_nonexistent_file(self) -> None:
        """Pointer to non-existent file produces error with correct line number."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("Line 1\nLine 2\n> READ: nonexistent/file.md\n")
            temp_path = f.name

        try:
            errors = validate_pointers(temp_path)
            assert len(errors) == 1
            assert "non-existent" in errors[0]
            assert "nonexistent/file.md" in errors[0]
        finally:
            Path(temp_path).unlink()

    def test_broken_pointer_empty_file(self) -> None:
        """Pointer to empty file (0 bytes) produces error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write("Line 1\n> READ: empty.md\n")
            temp_dir = Path(f.name).parent

        empty_file = temp_dir / "empty.md"
        empty_file.touch()
        assert empty_file.stat().st_size == 0

        try:
            errors = validate_pointers(f.name)
            assert len(errors) == 1
            assert "empty" in errors[0]
            assert "empty.md" in errors[0]
        finally:
            empty_file.unlink()
            Path(f.name).unlink()

    def test_valid_pointer(self) -> None:
        """Valid pointer to existing non-empty file produces no errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            skill_md = tmpdir / "SKILL.md"
            target_md = tmpdir / "valid.md"
            target_md.write_text("# Valid content\n", encoding="utf-8")
            skill_md.write_text("Line 1\n> READ: valid.md\nLine 3\n", encoding="utf-8")

            errors = validate_pointers(skill_md)
            assert errors == []

    def test_multiple_pointers_all_valid(self) -> None:
        """Multiple valid pointers produce no errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            skill_md = tmpdir / "SKILL.md"
            target1 = tmpdir / "file1.md"
            target2 = tmpdir / "file2.md"
            target1.write_text("Content 1\n", encoding="utf-8")
            target2.write_text("Content 2\n", encoding="utf-8")
            skill_md.write_text("> READ: file1.md\n> READ: file2.md\n", encoding="utf-8")

            errors = validate_pointers(skill_md)
            assert errors == []

    def test_multiple_pointers_one_broken(self) -> None:
        """One broken pointer among valid ones produces one error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            skill_md = tmpdir / "SKILL.md"
            target1 = tmpdir / "good.md"
            target1.write_text("Good content\n", encoding="utf-8")
            skill_md.write_text("> READ: good.md\n> READ: missing.md\n", encoding="utf-8")

            errors = validate_pointers(skill_md)
            assert len(errors) == 1
            assert "missing.md" in errors[0]
