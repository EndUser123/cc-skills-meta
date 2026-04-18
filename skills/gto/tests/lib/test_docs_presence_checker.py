"""Tests for docs_presence_checker module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.docs_presence_checker import (
    DocGap,
    DocPresenceResult,
    DocsPresenceChecker,
    check_docs_presence,
)


class TestDocsPresenceChecker:
    """Smoke tests for DocsPresenceChecker."""

    def test_checker_instantiation(self, tmp_path: Path) -> None:
        """Test checker can be instantiated."""
        checker = DocsPresenceChecker(tmp_path)
        assert checker is not None

    def test_check_docs_presence(self, tmp_path: Path) -> None:
        """Test checking docs presence."""
        result = check_docs_presence(tmp_path)
        assert isinstance(result, DocPresenceResult)


class TestDocPresenceResult:
    """Tests for DocPresenceResult dataclass."""

    def test_result_dataclass(self) -> None:
        """Test result can be constructed."""
        result = DocPresenceResult(
            gaps=[],
            modules_checked=0,
            modules_with_docs=0,
            modules_without_docs=0,
        )
        assert result.modules_checked == 0
        assert len(result.gaps) == 0


class TestDocGap:
    """Tests for DocGap dataclass."""

    def test_gap_dataclass(self) -> None:
        """Test gap can be constructed."""
        gap = DocGap(
            module_path="/fake/module.py",
            expected_doc_paths=["README.md"],
            any_doc_exists=False,
        )
        assert gap.module_path == "/fake/module.py"
        assert gap.any_doc_exists is False
