"""
Agent Performance Logger

Tracks agent execution outcomes to build performance profiles.
Enables adaptive routing decisions and circuit breaker patterns.

Data is stored in append-only JSONL format for:
- Simple parsing (no database overhead)
- Easy inspection (text-editable)
- Git-friendly (line-oriented)
"""

from __future__ import annotations

import json
import threading
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AgentExecutionRecord:
    """Single agent execution record."""
    timestamp: str
    agent_type: str  # e.g., "tdd-implementer", "general-purpose"
    task_type: str  # e.g., "refactor", "implement", "analyze"
    file_path: str
    lines_of_code: int
    file_count: int
    outcome: str  # "success", "timeout", "error", "partial"
    duration_seconds: float
    timeout_limit: int | None
    strategy_used: str  # "agent", "direct", "hybrid"
    error_message: str | None = None
    notes: str | None = None

    def to_jsonl(self) -> str:
        """Convert to JSONL line."""
        return json.dumps(asdict(self))

    @classmethod
    def from_jsonl(cls, line: str) -> AgentExecutionRecord:
        """Parse from JSONL line."""
        data = json.loads(line)
        return cls(**data)


class AgentPerformanceLogger:
    """
    Append-only logger for agent performance tracking.

    Usage:
        logger = AgentPerformanceLogger()
        logger.log_execution(
            agent_type="tdd-implementer",
            task_type="refactor",
            file_path="src/large_file.py",
            lines_of_code=3520,
            file_count=1,
            outcome="timeout",
            duration_seconds=300.0,
            timeout_limit=300,
            strategy_used="agent"
        )
    """

    DEFAULT_LOG_PATH = Path("P:/.claude/session_data/agent_performance.jsonl")

    def __init__(self, log_path: Path | None = None) -> None:
        """
        Initialize the logger.

        Args:
            log_path: Path to JSONL log file (default: ~/.claude/session_data/agent_performance.jsonl)
        """
        self.log_path = log_path or self.DEFAULT_LOG_PATH
        self._lock = threading.Lock()

        # Ensure directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_execution(
        self,
        agent_type: str,
        task_type: str,
        file_path: str,
        lines_of_code: int,
        file_count: int,
        outcome: str,
        duration_seconds: float,
        timeout_limit: int | None = None,
        strategy_used: str = "agent",
        error_message: str | None = None,
        notes: str | None = None,
    ) -> None:
        """
        Log an agent execution result.

        Args:
            agent_type: Type of agent (e.g., "tdd-implementer")
            task_type: Type of task (e.g., "refactor", "implement")
            file_path: Path to file being worked on
            lines_of_code: Lines of code in file
            file_count: Number of files involved
            outcome: "success", "timeout", "error", "partial"
            duration_seconds: How long the execution took
            timeout_limit: Timeout limit (if any)
            strategy_used: "agent", "direct", or "hybrid"
            error_message: Error message if failed
            notes: Additional notes
        """
        record = AgentExecutionRecord(
            timestamp=datetime.now().isoformat(),
            agent_type=agent_type,
            task_type=task_type,
            file_path=file_path,
            lines_of_code=lines_of_code,
            file_count=file_count,
            outcome=outcome,
            duration_seconds=duration_seconds,
            timeout_limit=timeout_limit,
            strategy_used=strategy_used,
            error_message=error_message,
            notes=notes,
        )

        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(record.to_jsonl() + "\n")

    def get_all_records(self) -> list[AgentExecutionRecord]:
        """Read all records from log."""
        if not self.log_path.exists():
            return []

        records = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(AgentExecutionRecord.from_jsonl(line))
        return records

    def get_performance_stats(self) -> dict[str, Any]:
        """
        Get aggregated performance statistics.

        Returns:
            Dict with stats by agent-task pattern, file size, etc.
        """
        records = self.get_all_records()

        if not records:
            return {
                "total_executions": 0,
                "by_agent": {},
                "by_task": {},
                "by_agent_task": {},
                "by_size_range": {},
                "outcomes": {},
            }

        # Stats containers
        outcomes = defaultdict(int)
        by_agent = defaultdict(lambda: defaultdict(int))
        by_task = defaultdict(lambda: defaultdict(int))
        by_agent_task = defaultdict(lambda: defaultdict(int))
        by_size_range = defaultdict(lambda: defaultdict(int))

        for record in records:
            outcomes[record.outcome] += 1

            # By agent
            by_agent[record.agent_type]["count"] += 1
            by_agent[record.agent_type][f"{record.outcome}"] += 1
            by_agent[record.agent_type]["total_duration"] += record.duration_seconds

            # By task
            by_task[record.task_type]["count"] += 1
            by_task[record.task_type][f"{record.outcome}"] += 1
            by_task[record.task_type]["total_duration"] += record.duration_seconds

            # By agent-task combination
            key = f"{record.agent_type}:{record.task_type}"
            by_agent_task[key]["count"] += 1
            by_agent_task[key][f"{record.outcome}"] += 1
            by_agent_task[key]["total_duration"] += record.duration_seconds

            # By size range
            size_range = self._get_size_range(record.lines_of_code)
            by_size_range[size_range]["count"] += 1
            by_size_range[size_range][f"{record.outcome}"] += 1
            by_size_range[size_range]["total_duration"] += record.duration_seconds

        # Compute averages and success rates
        def compute_stats(stats: dict) -> dict:
            return {
                "count": stats["count"],
                "success": stats["success"],
                "timeout": stats["timeout"],
                "error": stats["error"],
                "success_rate": stats["success"] / stats["count"] if stats["count"] > 0 else 0,
                "avg_duration": stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0,
            }

        return {
            "total_executions": len(records),
            "by_agent": {k: compute_stats(v) for k, v in by_agent.items()},
            "by_task": {k: compute_stats(v) for k, v in by_task.items()},
            "by_agent_task": {k: compute_stats(v) for k, v in by_agent_task.items()},
            "by_size_range": {k: compute_stats(v) for k, v in by_size_range.items()},
            "outcomes": dict(outcomes),
        }

    def _get_size_range(self, lines: int) -> str:
        """Categorize file size into ranges."""
        if lines < 100:
            return "small (<100)"
        elif lines < 500:
            return "medium (100-500)"
        elif lines < 1000:
            return "large (500-1000)"
        elif lines < 2000:
            return "xlarge (1000-2000)"
        else:
            return "xxlarge (2000+)"

    def get_bad_patterns(self, min_count: int = 2, timeout_threshold: float = 0.5) -> list[dict[str, Any]]:
        """
        Identify patterns with high timeout/failure rates.

        Args:
            min_count: Minimum executions before flagging as bad pattern
            timeout_threshold: Timeout rate above which to flag (0.5 = 50%)

        Returns:
            List of bad patterns with recommendations
        """
        stats = self.get_performance_stats()
        bad_patterns = []

        for pattern, stat in stats["by_agent_task"].items():
            if stat["count"] >= min_count:
                timeout_rate = stat["timeout"] / stat["count"]
                if timeout_rate >= timeout_threshold:
                    agent_type, task_type = pattern.split(":")
                    bad_patterns.append({
                        "pattern": pattern,
                        "agent_type": agent_type,
                        "task_type": task_type,
                        "timeout_rate": timeout_rate,
                        "success_rate": stat["success_rate"],
                        "count": stat["count"],
                        "avg_duration": stat["avg_duration"],
                        "recommendation": self._get_recommendation(
                            agent_type, task_type, stat, timeout_rate
                        ),
                    })

        # Also check size-based patterns
        for size_range, stat in stats["by_size_range"].items():
            if stat["count"] >= min_count:
                timeout_rate = stat["timeout"] / stat["count"]
                if timeout_rate >= timeout_threshold:
                    bad_patterns.append({
                        "pattern": f"size:{size_range}",
                        "size_range": size_range,
                        "timeout_rate": timeout_rate,
                        "success_rate": stat["success_rate"],
                        "count": stat["count"],
                        "avg_duration": stat["avg_duration"],
                        "recommendation": self._get_size_recommendation(size_range, timeout_rate),
                    })

        return bad_patterns

    def _get_recommendation(
        self,
        agent_type: str,
        task_type: str,
        stat: dict,
        timeout_rate: float
    ) -> str:
        """Generate recommendation for a bad pattern."""
        if timeout_rate >= 0.8:
            return f"CRITICAL: {agent_type} fails {timeout_rate*100:.0f}% on {task_type}. Use alternative agent or DIRECT strategy."
        elif timeout_rate >= 0.5:
            return f"WARNING: {agent_type} times out {timeout_rate*100:.0f}% on {task_type}. Consider increasing timeout or using DIRECT."
        else:
            return f"Monitor: {agent_type} has {timeout_rate*100:.0f}% timeout rate on {task_type}."

    def _get_size_recommendation(self, size_range: str, timeout_rate: float) -> str:
        """Generate size-based recommendation."""
        if "xxlarge" in size_range or "xlarge" in size_range:
            return f"Files {size_range} frequently timeout. Use DIRECT strategy for large files (>{1000 if 'xlarge' in size_range else 2000} lines)."
        return f"Monitor {size_range} file performance."

    def recommend_strategy(
        self,
        task_type: str,
        lines_of_code: int,
        file_count: int = 1,
        preferred_agent: str | None = None,
    ) -> dict[str, Any]:
        """
        Recommend execution strategy based on historical performance.

        Args:
            task_type: Type of task (e.g., "refactor", "implement")
            lines_of_code: Lines of code in target file
            file_count: Number of files involved
            preferred_agent: Preferred agent type (if any)

        Returns:
            Recommendation dict with strategy, agent, timeout, and rationale
        """
        stats = self.get_performance_stats()
        size_range = self._get_size_range(lines_of_code)

        # Check for bad patterns with preferred agent
        if preferred_agent:
            pattern_key = f"{preferred_agent}:{task_type}"
            if pattern_key in stats["by_agent_task"]:
                pattern_stat = stats["by_agent_task"][pattern_key]
                timeout_rate = pattern_stat["timeout"] / pattern_stat["count"]
                if timeout_rate > 0.5 and pattern_stat["count"] >= 2:
                    return {
                        "strategy": "direct",
                        "agent": None,
                        "timeout": None,
                        "confidence": "high",
                        "rationale": f"Circuit breaker: {preferred_agent} has {timeout_rate*100:.0f}% timeout rate on {task_type}. Using DIRECT strategy instead.",
                        "historical_data": {
                            "pattern": pattern_key,
                            "timeout_rate": timeout_rate,
                            "sample_count": pattern_stat["count"],
                        }
                    }

        # Size-based recommendation
        if lines_of_code >= 1000:
            # Check if agents have historically failed on large files
            size_stat = stats["by_size_range"].get(size_range, {})
            if size_stat.get("count", 0) >= 2:
                timeout_rate = size_stat["timeout"] / size_stat["count"]
                if timeout_rate > 0.5:
                    return {
                        "strategy": "direct",
                        "agent": None,
                        "timeout": None,
                        "confidence": "medium",
                        "rationale": f"Size-based recommendation: Files {size_range} have {timeout_rate*100:.0f}% timeout rate with agents. Using DIRECT strategy.",
                        "historical_data": {
                            "size_range": size_range,
                            "timeout_rate": timeout_rate,
                            "sample_count": size_stat["count"],
                        }
                    }

        # Default: use task size classifier
        from task_size_classifier import TaskSizeClassifier
        classifier = TaskSizeClassifier()
        classification = classifier.classify(
            file_path="",
            lines_of_code=lines_of_code,
            description=task_type,
            file_count=file_count,
        )

        return {
            "strategy": classification.strategy.value,
            "agent": preferred_agent if classification.strategy.value == "agent" else None,
            "timeout": 600 if classification.strategy.value == "agent" else None,  # 10 min for large tasks
            "confidence": "low",
            "rationale": classification.reason,
            "classification": {
                "complexity": classification.complexity.value,
                "estimated_duration_minutes": classification.estimated_duration_minutes,
            }
        }

    def clear_old_records(self, days: int = 30) -> int:
        """
        Remove records older than specified days.

        Args:
            days: Keep records from last N days

        Returns:
            Number of records removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        records = self.get_all_records()

        # Filter to keep only recent records
        recent_records = [
            r for r in records
            if datetime.fromisoformat(r.timestamp) > cutoff
        ]

        removed = len(records) - len(recent_records)

        # Rewrite file with only recent records
        with self._lock:
            with open(self.log_path, "w", encoding="utf-8") as f:
                for record in recent_records:
                    f.write(record.to_jsonl() + "\n")

        return removed


# Singleton instance
agent_performance_logger = AgentPerformanceLogger()
