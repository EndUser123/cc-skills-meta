"""Tests for git_context module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.git_context import GitContext, detect_git_context


class TestGitContext:
    """Smoke tests for GitContext."""

    def test_detect_git_context_no_repo(self, tmp_path: Path) -> None:
        """Test detecting git context when no repo exists."""
        result = detect_git_context(tmp_path)
        assert isinstance(result, GitContext)


class TestGitContextDataclass:
    """Tests for GitContext dataclass."""

    def test_dataclass(self) -> None:
        """Test GitContext can be constructed."""
        ctx = GitContext(
            branch="main",
            is_detached=False,
            is_worktree=False,
            worktree_path=None,
            worktree_count=0,
            error=None,
        )
        assert ctx.branch == "main"
        assert ctx.is_detached is False
        assert ctx.error is None
