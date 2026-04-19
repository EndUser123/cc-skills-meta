"""
Agent Heartbeat System

Tracks agent progress during execution to:
- Detect stuck/hung agents early
- Record partial work done before timeout
- Enable work recovery and resume

Design:
- Agents report heartbeat every N seconds
- Heartbeat contains: progress %, current operation, files modified
- On timeout, we know what work was completed
- Enables "incremental progress" vs "all-or-nothing"
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque
import time


@dataclass
class Heartbeat:
    """Single heartbeat from an agent."""
    agent_id: str
    timestamp: str
    progress_percent: float  # 0.0 to 100.0
    current_operation: str  # e.g., "reading file", "writing tests"
    files_modified: List[str]
    files_read: List[str]
    error_message: str | None = None
    notes: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Heartbeat":
        """Parse from dict."""
        return cls(**data)


class HeartbeatMonitor:
    """
    Monitors agent heartbeats to detect stalled execution.

    Usage:
        monitor = HeartbeatMonitor()
        monitor.start_tracking("agent-123")

        # Agent sends heartbeats during execution
        monitor.record_heartbeat(Heartbeat(
            agent_id="agent-123",
            timestamp=datetime.now().isoformat(),
            progress_percent=25.0,
            current_operation="analyzing code",
            files_modified=[],
            files_read=["src/main.py"]
        ))

        # Check if agent is stalled
        if monitor.is_stalled("agent-123", timeout_seconds=60):
            print("Agent appears stuck")
    """

    HEARTBEAT_FILE = Path("P:/.claude/session_data/agent_heartbeats.jsonl")

    def __init__(self, stall_timeout_seconds: int = 120) -> None:
        """
        Initialize the heartbeat monitor.

        Args:
            stall_timeout_seconds: Seconds without heartbeat before considering stalled
        """
        self.stall_timeout_seconds = stall_timeout_seconds
        self._lock = threading.RLock()  # Reentrant lock: allows same thread to acquire multiple times
        self._active_monitors: Dict[str, float] = {}  # agent_id -> last_heartbeat_time
        self._heartbeat_history: Dict[str, deque] = {}  # agent_id -> deque of recent heartbeats

        # Ensure directory exists
        self.HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)

    def start_tracking(self, agent_id: str) -> None:
        """Start monitoring a new agent."""
        with self._lock:
            self._active_monitors[agent_id] = time.monotonic()
            self._heartbeat_history[agent_id] = deque(maxlen=100)  # Keep last 100 heartbeats

    def stop_tracking(self, agent_id: str) -> None:
        """Stop monitoring an agent."""
        with self._lock:
            self._active_monitors.pop(agent_id, None)
            self._heartbeat_history.pop(agent_id, None)

    def record_heartbeat(self, heartbeat: Heartbeat) -> None:
        """
        Record a heartbeat from an agent.

        Args:
            heartbeat: Heartbeat data from agent
        """
        with self._lock:
            # Update last seen time
            self._active_monitors[heartbeat.agent_id] = time.monotonic()

            # Add to history
            if heartbeat.agent_id not in self._heartbeat_history:
                self._heartbeat_history[heartbeat.agent_id] = deque(maxlen=100)
            self._heartbeat_history[heartbeat.agent_id].append(heartbeat)

            # Persist to file
            self._persist_heartbeat(heartbeat)

    def is_stalled(self, agent_id: str, timeout_seconds: int | None = None) -> bool:
        """
        Check if an agent has stalled (no recent heartbeat).

        Args:
            agent_id: Agent to check
            timeout_seconds: Custom timeout (default: self.stall_timeout_seconds)

        Returns:
            True if agent appears stalled
        """
        timeout = timeout_seconds or self.stall_timeout_seconds

        with self._lock:
            last_heartbeat = self._active_monitors.get(agent_id)
            if last_heartbeat is None:
                return False  # Not being tracked

            return (time.monotonic() - last_heartbeat) > timeout

    def get_progress_summary(self, agent_id: str) -> Dict[str, Any]:
        """
        Get progress summary for an agent.

        Args:
            agent_id: Agent to query

        Returns:
            Summary with latest progress, files touched, etc.
        """
        with self._lock:
            history = self._heartbeat_history.get(agent_id)
            if not history or len(history) == 0:
                return {
                    "agent_id": agent_id,
                    "status": "not_started",
                    "progress_percent": 0.0,
                    "files_modified": [],
                    "files_read": [],
                }

            latest = history[-1]

            # Get all unique files touched
            all_files_modified = set()
            all_files_read = set()
            for hb in history:
                all_files_modified.update(hb.files_modified)
                all_files_read.update(hb.files_read)

            # NOTE: This calls is_stalled() while holding self._lock.
            # Requires RLock (reentrant lock) to avoid deadlock.
            return {
                "agent_id": agent_id,
                "status": "running" if not self.is_stalled(agent_id) else "stalled",
                "progress_percent": latest.progress_percent,
                "current_operation": latest.current_operation,
                "files_modified": list(all_files_modified),
                "files_read": list(all_files_read),
                "total_heartbeats": len(history),
                "last_heartbeat": latest.timestamp,
                "error_message": latest.error_message,
            }

    def get_partial_work(self, agent_id: str) -> Dict[str, Any]:
        """
        Get summary of work done before agent stalled/timed out.

        This enables "incremental progress" vs "all-or-nothing".

        Args:
            agent_id: Agent to query

        Returns:
            Summary of partial work completed
        """
        summary = self.get_progress_summary(agent_id)

        if summary["status"] == "not_started":
            return {
                "agent_id": agent_id,
                "work_completed": False,
                "message": "Agent never started",
            }

        # Calculate work value
        files_modified_count = len(summary["files_modified"])
        files_read_count = len(summary["files_read"])
        progress = summary["progress_percent"]

        # Estimate work value based on progress and files touched
        work_value = self._calculate_work_value(
            progress=progress,
            files_modified=files_modified_count,
            files_read=files_read_count,
        )

        return {
            "agent_id": agent_id,
            "work_completed": True,
            "progress_percent": progress,
            "files_modified": summary["files_modified"],
            "files_read": summary["files_read"],
            "estimated_work_value": work_value,
            "can_resume": files_modified_count > 0,  # Can resume if files were modified
            "recommendation": self._get_resume_recommendation(summary),
        }

    def _calculate_work_value(self, progress: float, files_modified: int, files_read: int) -> str:
        """Estimate the value of partial work done."""
        if progress >= 80:
            return "high - mostly complete"
        elif progress >= 50:
            return "medium - significant progress"
        elif files_modified > 0:
            return "low - some files modified"
        elif files_read > 0:
            return "minimal - analysis phase"
        else:
            return "none - no progress"

    def _get_resume_recommendation(self, summary: Dict[str, Any]) -> str:
        """Get recommendation for resuming from partial work."""
        progress = summary["progress_percent"]
        files_modified = summary["files_modified"]

        if not files_modified:
            return "No files modified - safe to restart from scratch"

        if progress >= 80:
            return f"Nearly complete - review {len(files_modified)} modified files and complete manually"

        if progress >= 50:
            return f"Significant progress - consider incremental approach on modified files"

        return f"Early stage - {len(files_modified)} files modified, consider reviewing before restart"

    def _persist_heartbeat(self, heartbeat: Heartbeat) -> None:
        """Append heartbeat to file for recovery."""
        try:
            with open(self.HEARTBEAT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(heartbeat.to_dict()) + "\n")
        except Exception as e:
            # Don't fail on write errors
            print(f"Warning: Could not persist heartbeat: {e}")

    def cleanup_old_heartbeats(self, hours: int = 24) -> int:
        """
        Remove old heartbeat records.

        Args:
            hours: Keep heartbeats from last N hours

        Returns:
            Number of records removed
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=hours)
        removed = 0

        if not self.HEARTBEAT_FILE.exists():
            return 0

        try:
            # Read and filter
            new_records = []
            with open(self.HEARTBEAT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        if timestamp > cutoff:
                            new_records.append(line)
                        else:
                            removed += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed lines
                        new_records.append(line)

            # Rewrite file
            with open(self.HEARTBEAT_FILE, "w", encoding="utf-8") as f:
                for record in new_records:
                    f.write(record + "\n")

        except Exception as e:
            print(f"Warning: Could not cleanup heartbeats: {e}")

        return removed


# Singleton instance
heartbeat_monitor = HeartbeatMonitor()


@dataclass
class PartialWorkResult:
    """Result of partial work assessment."""
    agent_id: str
    task_type: str
    progress_percent: float
    files_modified: List[str]
    files_read: List[str]
    work_value: str  # "high", "medium", "low", "none"
    can_resume: bool
    recommendation: str
    recovery_steps: List[str]


def assess_partial_work(agent_id: str, task_type: str) -> PartialWorkResult:
    """
    Assess work completed by an agent before it stalled/timed out.

    Args:
        agent_id: Agent that was executing
        task_type: Type of task being executed

    Returns:
        PartialWorkResult with assessment and recovery steps
    """
    monitor = heartbeat_monitor
    summary = monitor.get_partial_work(agent_id)

    # Generate recovery steps
    recovery_steps = _generate_recovery_steps(summary, task_type)

    return PartialWorkResult(
        agent_id=agent_id,
        task_type=task_type,
        progress_percent=summary["progress_percent"],
        files_modified=summary["files_modified"],
        files_read=summary["files_read"],
        work_value=summary["estimated_work_value"].split(" -")[0].strip(),
        can_resume=summary["can_resume"],
        recommendation=summary["recommendation"],
        recovery_steps=recovery_steps,
    )


def _generate_recovery_steps(summary: Dict[str, Any], task_type: str) -> List[str]:
    """Generate recovery steps based on partial work done."""
    steps = []
    files_modified = summary["files_modified"]
    progress = summary["progress_percent"]

    if not files_modified:
        return [
            f"1. No files were modified - safe to restart {task_type} task from scratch",
            "2. Consider increasing timeout if task is large",
        ]

    steps.append(f"1. Review {len(files_modified)} modified file(s):")
    for f in files_modified[:5]:  # Show first 5
        steps.append(f"   - {f}")
    if len(files_modified) > 5:
        steps.append(f"   - ... and {len(files_modified) - 5} more")

    if progress >= 80:
        steps.append("2. Task is nearly complete - finish manually or resume with higher timeout")
    elif progress >= 50:
        steps.append("2. Significant progress made - review changes and continue incrementally")
    else:
        steps.append("2. Early stage progress - review if direction is correct before continuing")

    steps.append("3. Run tests to validate partial work")
    steps.append("4. Commit partial work if valid: git add ... && git commit -m 'wip: partial work'")

    return steps
