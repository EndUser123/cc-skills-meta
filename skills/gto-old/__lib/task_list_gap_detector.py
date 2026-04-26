"""TaskListGapDetector - Surface pending tasks from shared task list.

Priority: P0 (runs first, before other detectors)
Purpose: Bridge GTO's gap analysis with the shared TaskList so that
pending tasks surface as a list for LLM-native relevance evaluation.

This detector reads the shared task list from ~/.claude/tasks/project-main-tasks/
and returns all pending tasks as gaps for the RNS "YOUR TASKS" section.

Relevance filtering is done natively by the LLM — not by Python filtering.
Python reads the raw task list; LLM evaluates semantic relevance.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TaskListGapResult:
    """Result of task list gap detection."""

    gaps: list[dict[str, Any]]
    total_tasks_checked: int
    pending_count: int


class TaskListGapDetector:
    """
    Read all pending tasks from the shared task list.

    Returns ALL pending (non-completed, non-deleted) tasks as gaps
    for the RNS "YOUR TASKS" section. The LLM evaluates relevance
    semantically — Python does no filtering.
    """

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize detector.

        Args:
            project_root: Project root (unused, for interface consistency)
        """
        self.task_list_dir = Path.home() / ".claude" / "tasks" / "project-main-tasks"

    def check(self) -> TaskListGapResult:
        """
        Read all pending tasks from task list.

        Returns:
            TaskListGapResult with all pending tasks as gaps
        """
        gaps: list[dict[str, Any]] = []

        if not self.task_list_dir.exists():
            return TaskListGapResult(
                gaps=[],
                total_tasks_checked=0,
                pending_count=0,
            )

        task_files = list(self.task_list_dir.glob("*.json"))
        pending_count = 0

        for task_file in task_files:
            try:
                with open(task_file, encoding="utf-8") as f:
                    task_data: dict[str, Any] = json.load(f)
            except (OSError, json.JSONDecodeError, ValueError):
                continue

            subject = task_data.get("subject", "")
            status = task_data.get("status", "")
            task_id = task_file.stem  # filename without .json

            # Only process pending/in_progress items
            if status in ("completed", "deleted"):
                continue

            pending_count += 1

            gap = {
                "type": "pending_task",
                "severity": "low",  # LLM re-prioritizes semantically
                "message": subject,
                "file_path": str(task_file),
                "line_number": None,
                "source": "TaskListGapDetector",
                "confidence": 0.95,
                "effort_estimate_minutes": task_data.get("effort_minutes", 15),
                "gap_id": f"TASK-{task_id}",
                "task_status": status,
            }
            gaps.append(gap)

        return TaskListGapResult(
            gaps=gaps,
            total_tasks_checked=len(task_files),
            pending_count=pending_count,
        )


# Convenience function
def detect_task_list_gaps(project_root: Path | None = None) -> TaskListGapResult:
    """
    Quick task list gap detection.

    Args:
        project_root: Project root (unused, for interface consistency)

    Returns:
        TaskListGapResult with all pending tasks
    """
    detector = TaskListGapDetector(project_root)
    return detector.check()
