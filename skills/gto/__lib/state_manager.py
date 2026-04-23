"""StateManager - Terminal-isolated state management for GTO v3.

Priority: P0 (core infrastructure)
Purpose: Manage state persistence with multi-terminal isolation and atomic writes

Features:
- Terminal-isolated state directories (no shared mutable state)
- Atomic state writes (temp-file + replace pattern)
- Schema versioning for migration support
- Corruption recovery with fallback
- Orphaned temp file cleanup
- Cross-session recurrence tracking
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Terminal ID sanitization: allow only safe characters
_TERMINAL_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

# Cross-platform file locking
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

# Windows file locking
try:
    import msvcrt

    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


@dataclass
class StateFile:
    """GTO state file schema."""

    version: str
    terminal_id: str
    timestamp: str
    session_id: str | None
    gaps: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "terminal_id": self.terminal_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "gaps": self.gaps,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateFile:
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0.0"),
            terminal_id=data.get("terminal_id", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            session_id=data.get("session_id"),
            gaps=data.get("gaps", []),
            metadata=data.get("metadata", {}),
        )


CURRENT_VERSION = "3.0.0"


class StateManager:
    """
    Manage GTO state with terminal isolation and atomic writes.

    Each terminal writes to its own state directory. No shared mutable state.
    """

    @staticmethod
    def _resolve_project_root(project_root: Path | None) -> Path:
        r"""Resolve project root, routing workspace root to .claude/.

        When cwd is the workspace root (P:\), .claude/ exists and is the canonical
        home for Claude Code state. This prevents dot-directories at workspace root.
        """
        if project_root:
            return Path(project_root).resolve()
        cwd = Path.cwd().resolve()
        # Workspace root detection: cwd.name == '' means we're at a drive root
        # and .claude existence confirms it's the Claude Code workspace root
        if cwd.name == "" and (cwd / ".claude").exists():
            return cwd / ".claude"
        return cwd

    def __init__(self, project_root: Path | None = None, terminal_id: str | None = None):
        """Initialize state manager.

        Args:
            project_root: Project root directory
            terminal_id: Terminal identifier for isolation

        Raises:
            ValueError: If terminal_id contains unsafe characters
        """
        self.project_root = self._resolve_project_root(project_root)
        self.terminal_id = terminal_id if terminal_id is not None else self._resolve_terminal_id()

        # CRITICAL: Validate terminal_id to prevent path traversal
        if not _TERMINAL_ID_PATTERN.match(self.terminal_id):
            raise ValueError(
                f"Invalid terminal_id: {self.terminal_id!r}. "
                f"Must match {_TERMINAL_ID_PATTERN.pattern}"
            )

        # State directory: .claude-state/gto-state-{terminal_id}/
        self.state_dir = self.project_root / ".claude-state" / f"gto-state-{self.terminal_id}"
        self.state_file_path = self.state_dir / "state.json"

        # History file: .claude-state/gto-history-{terminal}.jsonl (terminal-isolated)
        self.history_file_path = (
            self.project_root / ".claude-state" / f"gto-history-{self.terminal_id}.jsonl"
        )

        # Shared skill-usage log: .claude-state/skill-usage.jsonl (shared across terminals)
        # Append-only, multi-terminal safe via file locking
        self.skill_usage_log_path = self.project_root / ".claude-state" / "skill-usage.jsonl"

        # Current version
        self.current_version = CURRENT_VERSION

    def _resolve_terminal_id(self) -> str:
        """Resolve terminal ID from environment or generate default.

        Returns:
            Terminal identifier string
        """
        # Try to get terminal ID from environment
        term_id = os.environ.get("CLAUDE_TERMINAL_ID")
        if term_id:
            return term_id

        # Fallback: hostname-based
        import socket

        hostname = socket.gethostname()
        pid = os.getpid()
        return f"{hostname}-{pid}"

    def _ensure_state_dir(self) -> None:
        """Ensure state directory exists."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _cleanup_orphaned_temp_files(self) -> None:
        """Clean up orphaned .tmp files from incomplete writes.

        Only removes files older than 60 seconds to avoid deleting
        temp files from concurrent terminals mid-write.
        """
        if not self.state_dir.exists():
            return

        import time
        now = time.time()
        for tmp_file in self.state_dir.glob("*.tmp"):
            try:
                if now - tmp_file.stat().st_mtime > 60:
                    tmp_file.unlink()
            except OSError:
                pass

    def _validate_schema(self, data: dict[str, Any]) -> bool:
        """Validate state file schema.

        Args:
            data: Dictionary to validate

        Returns:
            True if valid schema
        """
        required_fields = ["version", "terminal_id", "timestamp"]
        return all(field in data for field in required_fields)

    def _migrate_schema(self, data: dict[str, Any]) -> dict[str, Any]:
        """Migrate state data to current version.

        Args:
            data: State data to migrate

        Returns:
            Migrated state data
        """
        version = data.get("version", "1.0.0")

        # Parse version string
        try:
            major, minor, patch = map(int, version.split("."))
            current_major, current_minor, current_patch = map(int, self.current_version.split("."))
        except ValueError:
            # Invalid version format, return as-is
            return data

        # Handle newer version (graceful degradation)
        if (major, minor, patch) > (current_major, current_minor, current_patch):
            # Log warning but continue with partial load
            import warnings

            warnings.warn(
                f"State file from newer version {version}, "
                f"some fields may be ignored (current: {self.current_version})"
            )
            return data

        # Migration logic for older versions
        if version == "1.0.0":
            # Migrate to 2.0.0: add session_id field
            data["session_id"] = data.get("session_id")
            data["version"] = "2.0.0"

        if version in ["1.0.0", "2.0.0"]:
            # Migrate to 3.0.0: restructure gaps array
            # (add recurrence_count if missing)
            for gap in data.get("gaps", []):
                if "recurrence_count" not in gap:
                    gap["recurrence_count"] = 1
            data["version"] = "3.0.0"

        return data

    def load(self) -> StateFile:
        """Load state from disk with corruption recovery.

        Returns:
            StateFile with loaded data or empty default

        Raises:
            OSError: If state directory is not accessible
        """
        self._ensure_state_dir()
        self._cleanup_orphaned_temp_files()

        # If state file doesn't exist, return empty state
        if not self.state_file_path.exists():
            return StateFile(
                version=self.current_version,
                terminal_id=self.terminal_id,
                timestamp=datetime.now().isoformat(),
                session_id=None,
                gaps=[],
                metadata={},
            )

        # Try to load and parse state file
        try:
            with open(self.state_file_path) as f:
                data = json.load(f)

            # Validate schema
            if not self._validate_schema(data):
                # Invalid schema, start fresh
                return self._get_empty_state()

            # Migrate if needed
            if data.get("version") != self.current_version:
                data = self._migrate_schema(data)

            return StateFile.from_dict(data)

        except (OSError, json.JSONDecodeError):
            # Corrupted or unreadable, return empty state
            return self._get_empty_state()

    def _get_empty_state(self) -> StateFile:
        """Get empty state file.

        Returns:
            Empty StateFile with current version
        """
        return StateFile(
            version=self.current_version,
            terminal_id=self.terminal_id,
            timestamp=datetime.now().isoformat(),
            session_id=None,
            gaps=[],
            metadata={},
        )

    def create_state(
        self,
        session_id: str | None = None,
        gaps: list[dict] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateFile:
        """Create a new StateFile.

        Args:
            session_id: Optional session identifier
            gaps: Optional list of gap dictionaries
            metadata: Optional metadata dictionary

        Returns:
            New StateFile instance
        """
        return StateFile(
            version=self.current_version,
            terminal_id=self.terminal_id,
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            gaps=gaps or [],
            metadata=metadata or {},
        )

    def save(self, state: StateFile) -> None:
        """Save state with atomic write (temp-file + replace).

        Args:
            state: StateFile to save

        Raises:
            OSError: If state directory is not writable
        """
        self._ensure_state_dir()

        # Update timestamp
        state.timestamp = datetime.now().isoformat()

        # Serialize to JSON
        data = state.to_dict()
        json_content = json.dumps(data, indent=2)

        # Atomic write: temp file + rename
        # Use terminal-specific prefix to avoid conflicts between terminals
        tmp_path = None
        write_succeeded = False
        try:
            # Create temp file with terminal-specific prefix to avoid cross-terminal conflicts
            tmp_prefix = f".state_{self.terminal_id}_"
            fd, tmp_path = tempfile.mkstemp(dir=self.state_dir, prefix=tmp_prefix, suffix=".tmp")

            # Write content
            with os.fdopen(fd, "w") as f:
                f.write(json_content)

            # Atomic rename (overwrites existing if any)
            os.replace(tmp_path, self.state_file_path)
            write_succeeded = True
        except BaseException:
            # Keep temp file for recovery if os.replace failed.
            # Orphaned temp files are cleaned up on next load().
            if tmp_path is not None and not write_succeeded:
                # Write failed - temp file may contain partial data for recovery
                # Leave temp file for manual recovery.
                pass
            raise
        finally:
            # Clean up temp file if write succeeded
            if tmp_path is not None and write_succeeded:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    # Temp file already cleaned up or replaced
                    pass

    def append_history(self, run_summary: dict[str, Any]) -> None:
        """Append run summary to history file with file locking for thread-safety.

        Args:
            run_summary: Dictionary with run summary data

        Raises:
            OSError: If lock cannot be acquired (caller should fail closed)
        """
        self._ensure_state_dir()

        # Add timestamp if not present
        if "timestamp" not in run_summary:
            run_summary["timestamp"] = datetime.now().isoformat()

        # Lock file path
        lock_path = self.state_dir / ".history.lock"

        # Acquire exclusive lock first — fail closed if lock is busy
        # Use single try-finally to ensure lock is always released
        lock_file_obj = None
        try:
            # Open lock file
            lock_file_obj = open(lock_path, "w")

            # Acquire lock
            if HAS_FCNTL:
                # Non-blocking: fail with EWOULDBLOCK if lock is held
                fcntl.flock(lock_file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif HAS_MSVCRT:
                # Windows non-blocking: raises OSError (Win32 Error 33) if busy
                msvcrt.locking(lock_file_obj.fileno(), msvcrt.LK_NBLCK, 1)

            # Lock acquired — write operation
            with open(self.history_file_path, "a") as f:
                f.write(json.dumps(run_summary) + "\n")
        except (OSError, IOError):
            # Lock busy or unavailable — fail closed, do NOT write unprotected
            raise  # Caller must decide: fail or skip
        finally:
            # Always release lock if it was acquired
            if lock_file_obj is not None:
                try:
                    if HAS_FCNTL:
                        fcntl.flock(lock_file_obj.fileno(), fcntl.LOCK_UN)
                    elif HAS_MSVCRT:
                        msvcrt.locking(lock_file_obj.fileno(), msvcrt.LK_UNLCK, 1)
                except (OSError, IOError):
                    # Ignore errors during lock release
                    pass
                lock_file_obj.close()
                # Do NOT delete lock file: another terminal may acquire it next.

    def get_history(self, last_n: int = 10) -> list[dict[str, Any]]:
        """Get last N run summaries from history.

        Args:
            last_n: Number of recent runs to retrieve

        Returns:
            List of run summary dictionaries (most recent first)
        """
        if not self.history_file_path.exists():
            return []

        history = []
        try:
            with open(self.history_file_path) as f:
                for line in f:
                    try:
                        history.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
        except OSError:
            # File not readable, return empty
            return []

        # Return last N entries in reverse order (most recent first)
        return list(reversed(history[-last_n:]))

    def update_gap_recurrence(self, gaps: list[dict]) -> list[dict]:
        """Update recurrence counts for gaps based on history.

        Args:
            gaps: Current gaps to check for recurrence

        Returns:
            Updated gaps with recurrence counts
        """
        # Build map of gap signatures to recurrence counts
        signature_counts: dict[str, int] = {}

        # Count occurrences in history
        for run in self.get_history(last_n=10):
            for gap in run.get("gaps", []):
                # Create signature: type + message (normalized)
                sig = self._gap_signature(gap)
                signature_counts[sig] = signature_counts.get(sig, 0) + 1

        # Update current gaps
        for gap in gaps:
            sig = self._gap_signature(gap)
            gap["recurrence_count"] = signature_counts.get(sig, 1)

        return gaps

    def _gap_signature(self, gap: dict) -> str:
        """Create signature for gap recurrence tracking.

        Args:
            gap: Gap dictionary

        Returns:
            Signature string for matching
        """
        # Use type + message (normalized) as signature
        gap_type = gap.get("type", "")
        message = gap.get("message", "").lower().strip()
        # Remove common variations
        message = message.replace(" ", "").replace("\t", "")
        return f"{gap_type}:{message}"

    def get_state_path(self) -> Path:
        """Get state file path.

        Returns:
            Path to state file
        """
        return self.state_file_path

    def get_history_path(self) -> Path:
        """Get history file path.

        Returns:
            Path to history file
        """
        return self.history_file_path

    def log_skill_run(self, skill_run: dict[str, Any]) -> None:
        """Append skill run record to shared skill-usage log.

        The skill-usage log is shared across all terminals (unlike GTO's
        terminal-isolated history). Uses file locking for multi-terminal safety.

        Args:
            skill_run: Dictionary with skill run data. Required fields:
                - type: "skill_run"
                - skill: skill name (e.g., "gto")
                - timestamp: ISO timestamp
                - status: "complete" | "failed" | "skipped"
                Optional fields:
                - gaps_detected: int
                - delta_from: ISO timestamp (for incremental runs)
                - metadata: dict
        """
        self._ensure_state_dir()

        # Validate required fields
        required = ["type", "skill", "timestamp", "status"]
        if not all(field in skill_run for field in required):
            raise ValueError(f"skill_run missing required fields: {required}")

        # Add lock path for shared log
        lock_path = self.project_root / ".evidence" / ".skill_usage.lock"

        # Acquire exclusive lock first — fail closed if lock is busy
        # Use single try-finally to ensure lock is always released
        lock_file_obj = None
        try:
            # Open lock file
            lock_file_obj = open(lock_path, "w")

            # Acquire lock
            if HAS_FCNTL:
                fcntl.flock(lock_file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif HAS_MSVCRT:
                msvcrt.locking(lock_file_obj.fileno(), msvcrt.LK_NBLCK, 1)

            # Lock acquired — write operation
            with open(self.skill_usage_log_path, "a") as f:
                f.write(json.dumps(skill_run) + "\n")
        except (OSError, IOError):
            # Lock busy or unavailable — fail closed, do NOT write unprotected
            raise  # Caller must decide: fail or skip
        finally:
            # Always release lock if it was acquired
            if lock_file_obj is not None:
                try:
                    if HAS_FCNTL:
                        fcntl.flock(lock_file_obj.fileno(), fcntl.LOCK_UN)
                    elif HAS_MSVCRT:
                        msvcrt.locking(lock_file_obj.fileno(), msvcrt.LK_UNLCK, 1)
                except (OSError, IOError):
                    # Ignore errors during lock release
                    pass
                lock_file_obj.close()
                # Do NOT delete lock file: another terminal may acquire it next.

    def get_skill_usage(self, skill: str | None = None, last_n: int = 50) -> list[dict[str, Any]]:
        """Query skill usage log.

        Args:
            skill: Optional skill name to filter by. If None, returns all skills.
            last_n: Number of recent records to retrieve (default 50)

        Returns:
            List of skill run records, most recent first
        """
        if not self.skill_usage_log_path.exists():
            return []

        records = []
        try:
            with open(self.skill_usage_log_path) as f:
                for line in f:
                    try:
                        record = json.loads(line.strip())
                        if skill is None or record.get("skill") == skill:
                            records.append(record)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return []

        # Return last N records (most recent first)
        return list(reversed(records[-last_n:]))


# Convenience function
def get_state_manager(
    project_root: Path | None = None,
    terminal_id: str | None = None,
    state_dir: Path | None = None,
) -> StateManager:
    """
    Quick state manager instantiation.

    Args:
        project_root: Project root directory
        terminal_id: Terminal identifier
        state_dir: Optional custom state directory (for testing)

    Returns:
        StateManager instance
    """
    manager = StateManager(project_root, terminal_id)
    # Override state_dir if provided (for testing)
    if state_dir is not None:
        manager.state_dir = state_dir
        manager.state_file_path = state_dir / "state.json"
        manager.history_file_path = state_dir / f"gto-history-{manager.terminal_id}.jsonl"
        manager.skill_usage_log_path = state_dir / "skill-usage.jsonl"
    return manager
