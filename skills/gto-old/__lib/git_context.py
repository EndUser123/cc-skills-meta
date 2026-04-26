"""GitContext - Detect git branch and worktree information for GTO.

Priority: P2 (informational, displayed in output)
Purpose: Show current git branch and worktree context in GTO output
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitContext:
    """Git context information."""

    branch: str | None
    is_detached: bool
    is_worktree: bool
    worktree_path: Path | None
    worktree_count: int = 0
    error: str | None = None

    @property
    def branch_display(self) -> str:
        """Human-readable branch display."""
        if self.error:
            return "unknown"
        if self.is_detached:
            return f"detached ({self.branch or 'HEAD'})"
        return self.branch or "unknown"


def detect_git_context(project_root: Path) -> GitContext:
    """Detect current git branch and worktree information.

    Args:
        project_root: Project root directory

    Returns:
        GitContext with branch and worktree information
    """
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5,
        )

        if branch_result.returncode == 0:
            branch = branch_result.stdout.strip()
            is_detached = False
        else:
            # Try detached HEAD
            head_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=5,
            )
            branch = head_result.stdout.strip() if head_result.returncode == 0 else None
            is_detached = True

        # Check if in worktree (has .git file with gitdir reference)
        git_file = project_root / ".git"
        is_worktree = False
        worktree_path: Path | None = None

        if git_file.exists() and git_file.is_file():
            content = git_file.read_text().strip()
            if content.startswith("gitdir:"):
                is_worktree = True
                # gitdir points to .git file in worktree, worktree root is its parent
                gitdir_path = Path(content.split(":", 1)[1].strip())
                if gitdir_path.exists():
                    worktree_path = gitdir_path.parent

        # Count total worktrees
        worktree_count = 0
        list_result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5,
        )
        if list_result.returncode == 0:
            for line in list_result.stdout.split("\n"):
                if line.startswith("worktree "):
                    worktree_count += 1

        return GitContext(
            branch=branch,
            is_detached=is_detached,
            is_worktree=is_worktree,
            worktree_path=worktree_path,
            worktree_count=worktree_count,
            error=None,
        )

    except subprocess.TimeoutExpired:
        return GitContext(
            branch=None,
            is_detached=False,
            is_worktree=False,
            worktree_path=None,
            error="git command timed out",
        )
    except OSError as e:
        return GitContext(
            branch=None,
            is_detached=False,
            is_worktree=False,
            worktree_path=None,
            error=str(e),
        )


__all__ = ["GitContext", "detect_git_context"]
