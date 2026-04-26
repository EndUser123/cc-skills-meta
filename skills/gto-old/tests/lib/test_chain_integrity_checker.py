"""Tests for chain_integrity_checker module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.chain_integrity_checker import (
    ChainIntegrityChecker,
    ChainIntegrityResult,
    check_chain_integrity,
)


class TestChainIntegrityChecker:
    """Smoke tests for ChainIntegrityChecker."""

    def test_checker_instantiation(self, tmp_path: Path) -> None:
        """Test checker can be instantiated."""
        checker = ChainIntegrityChecker(tmp_path)
        assert checker is not None

    def test_check_chain_integrity_no_file(self, tmp_path: Path) -> None:
        """Test check with no transcript file."""
        result = check_chain_integrity(tmp_path / "nonexistent.jsonl")
        assert isinstance(result, ChainIntegrityResult)


class TestChainIntegrityResult:
    """Tests for ChainIntegrityResult dataclass."""

    def test_result_dataclass(self) -> None:
        """Test result can be constructed."""
        result = ChainIntegrityResult(
            paths=[],
            partial_scope=False,
            excluded=[],
            warnings=[],
        )
        assert result.paths == []
        assert result.partial_scope is False
