"""
Task Size Classifier - Determines execution strategy based on task complexity.

Helps prevent agent timeout issues by routing large tasks to direct implementation
instead of delegation to subagents.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass


class TaskComplexity(Enum):
    """Task complexity levels."""
    SMALL = "small"       # < 100 lines, single file
    MEDIUM = "medium"     # 100-1000 lines, 1-3 files
    LARGE = "large"       # > 1000 lines, or 4+ files


class ExecutionStrategy(Enum):
    """Execution strategy recommendations."""
    AGENT = "agent"           # Use subagent delegation
    DIRECT = "direct"         # Use direct implementation
    HYBRID = "hybrid"         # Mix of both (decompose and parallelize)


@dataclass
class ClassificationResult:
    """Result of task classification."""
    complexity: TaskComplexity
    strategy: ExecutionStrategy
    reason: str
    estimated_duration_minutes: int


class TaskSizeClassifier:
    """
    Classifies tasks by size to determine appropriate execution strategy.
    
    Thresholds:
    - SMALL: < 100 lines → Agent delegation
    - MEDIUM: 100-1000 lines → Agent with monitoring
    - LARGE: > 1000 lines → Direct implementation
    
    This prevents the issue where large file refactoring tasks
    are delegated to agents that timeout or fail.
    """
    
    # Thresholds
    SMALL_MAX_LINES = 100
    MEDIUM_MAX_LINES = 1000
    MULTI_FILE_THRESHOLD = 4
    
    def __init__(self) -> None:
        self._classifications: list[ClassificationResult] = []
    
    def classify(
        self,
        file_path: str,
        lines_of_code: int,
        description: str,
        file_count: int = 1,
    ) -> ClassificationResult:
        """
        Classify a single-file task.
        
        Args:
            file_path: Path to the file being modified
            lines_of_code: Total lines in the file
            description: Task description
            file_count: Number of files involved (default 1)
        
        Returns:
            ClassificationResult with strategy recommendation
        """
        if file_count > 1:
            return self.classify_multi_file(file_count, lines_of_code, description)
        
        if lines_of_code < self.SMALL_MAX_LINES:
            result = ClassificationResult(
                complexity=TaskComplexity.SMALL,
                strategy=ExecutionStrategy.AGENT,
                reason=f"Small task ({lines_of_code} lines) - suitable for agent delegation",
                estimated_duration_minutes=2,
            )
        elif lines_of_code < self.MEDIUM_MAX_LINES:
            result = ClassificationResult(
                complexity=TaskComplexity.MEDIUM,
                strategy=ExecutionStrategy.AGENT,
                reason=f"Medium task ({lines_of_code} lines) - agent with monitoring",
                estimated_duration_minutes=5,
            )
        else:
            result = ClassificationResult(
                complexity=TaskComplexity.LARGE,
                strategy=ExecutionStrategy.DIRECT,
                reason=f"Large file ({lines_of_code} lines) - direct implementation recommended to avoid timeout",
                estimated_duration_minutes=15,
            )
        
        self._classifications.append(result)
        return result
    
    def classify_multi_file(
        self,
        file_count: int,
        total_lines: int,
        description: str,
    ) -> ClassificationResult:
        """
        Classify a multi-file task.
        
        Args:
            file_count: Number of files involved
            total_lines: Total lines across all files
            description: Task description
        
        Returns:
            ClassificationResult with strategy recommendation
        """
        avg_lines = total_lines // file_count if file_count > 0 else 0
        
        if file_count >= self.MULTI_FILE_THRESHOLD or total_lines > self.MEDIUM_MAX_LINES:
            result = ClassificationResult(
                complexity=TaskComplexity.LARGE,
                strategy=ExecutionStrategy.DIRECT,
                reason=f"Multi-file task ({file_count} files, ~{avg_lines} lines/file) - direct implementation",
                estimated_duration_minutes=20,
            )
        else:
            result = ClassificationResult(
                complexity=TaskComplexity.MEDIUM,
                strategy=ExecutionStrategy.HYBRID,
                reason=f"Multi-file task ({file_count} files) - decompose into parallel agents",
                estimated_duration_minutes=10,
            )
        
        self._classifications.append(result)
        return result
    
    def get_classification_history(self) -> list[ClassificationResult]:
        """Return history of all classifications."""
        return self._classifications.copy()
