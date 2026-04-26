"""UnfinishedBusinessDetector - Pattern matching for open tasks/questions.

Priority: P1 (runs during gap detection)
Purpose: Detect unfinished work from transcript patterns

Patterns detected:
- Open tasks (TODO, FIXME, checkbox markers)
- Open questions (question marks, uncertainty phrases)
- Deferred items (later, defer, postpone)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class UnfinishedItem:
    """A single unfinished item found in transcript."""

    category: Literal["task", "question", "deferred"]
    content: str
    turn_number: int
    confidence: float  # 0.0 to 1.0


@dataclass
class UnfinishedBusinessResult:
    """Result of unfinished business detection."""

    tasks: list[UnfinishedItem]
    questions: list[UnfinishedItem]
    deferred: list[UnfinishedItem]
    total_count: int

    @property
    def items(self) -> list[UnfinishedItem]:
        """All unfinished items combined."""
        return self.tasks + self.questions + self.deferred


class UnfinishedBusinessDetector:
    """
    Detect unfinished work from transcript patterns.

    Scans transcript for:
    - Open tasks (TODO, FIXME, checkbox markers)
    - Open questions (question marks, uncertainty phrases)
    - Deferred items (later, defer, postpone)
    """

    # Task patterns
    TASK_PATTERNS = [
        (r"TODO:\s*(.+)", 0.9),
        (r"FIXME:\s*(.+)", 0.9),
        (r"HACK:\s*(.+)", 0.7),
        (r"- \[ \]\s*(.+)", 0.8),
        (r"\[ \]\s*(.+)", 0.8),
    ]

    # Question patterns
    QUESTION_PATTERNS = [
        (r"\?(?:\s*$)", 0.5),  # Low confidence, filter by context
        (r"(?:not sure|maybe|need to check|uncertain)", 0.7),
        (r"(?:don't know|can you tell|how do I)", 0.7),
    ]

    # Deferred patterns
    DEFERRED_PATTERNS = [
        (r"(?:later|defer|postpone)", 0.6),
        (r"(?:for now|for the moment)", 0.5),
        (r"(?:skip|come back to)", 0.5),
    ]

    def __init__(self, project_root: Path | None = None):
        """Initialize detector with project root.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()

    def detect(self, transcript_path: Path) -> UnfinishedBusinessResult:
        """
        Detect unfinished business from transcript.

        Args:
            transcript_path: Path to transcript JSONL file

        Returns:
            UnfinishedBusinessResult with all detected items
        """
        tasks = []
        questions = []
        deferred = []

        if not transcript_path.exists():
            return UnfinishedBusinessResult(tasks=[], questions=[], deferred=[], total_count=0)

        try:
            with open(transcript_path) as f:
                lines = f.readlines()
        except (OSError, PermissionError):
            return UnfinishedBusinessResult(tasks=[], questions=[], deferred=[], total_count=0)

        for turn_num, line in enumerate(lines, start=1):
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue

            content = message.get("content", "")
            role = message.get("role", "")

            # Only check user and assistant messages (skip system messages)
            if role == "system":
                continue

            # Detect tasks
            for pattern, confidence in self.TASK_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    tasks.append(
                        UnfinishedItem(
                            category="task",
                            content=match.group(1).strip(),
                            turn_number=turn_num,
                            confidence=confidence,
                        )
                    )

            # Detect questions
            for pattern, confidence in self.QUESTION_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    question_content = match.group(0).strip()
                    # Filter trivially short content (e.g. bare "?" is noise)
                    if len(question_content) < 2:
                        continue
                    questions.append(
                        UnfinishedItem(
                            category="question",
                            content=question_content,
                            turn_number=turn_num,
                            confidence=confidence,
                        )
                    )

            # Detect deferred items
            for pattern, confidence in self.DEFERRED_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    deferred.append(
                        UnfinishedItem(
                            category="deferred",
                            content=match.group(0).strip(),
                            turn_number=turn_num,
                            confidence=confidence,
                        )
                    )

        return UnfinishedBusinessResult(
            tasks=tasks,
            questions=questions,
            deferred=deferred,
            total_count=len(tasks) + len(questions) + len(deferred),
        )


# Convenience function
def detect_unfinished_business(
    transcript_path: Path, project_root: Path | None = None
) -> UnfinishedBusinessResult:
    """
    Quick unfinished business detection.

    Args:
        transcript_path: Path to transcript file
        project_root: Project root directory

    Returns:
        UnfinishedBusinessResult with detected items
    """
    detector = UnfinishedBusinessDetector(project_root)
    return detector.detect(transcript_path)
