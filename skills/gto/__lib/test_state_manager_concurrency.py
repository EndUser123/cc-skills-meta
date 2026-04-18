"""Tests for state_manager.py Windows concurrency fixes.

Verifies:
- CAUSE-001: save() preserves temp file when os.replace fails
- CAUSE-002: lock file is never deleted on acquisition failure
- CAUSE-015: lock file is never deleted after lock release
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from __lib.state_manager import StateManager, get_state_manager


@pytest.fixture
def sm(tmp_path: Path) -> StateManager:
    """Create a StateManager with a temporary state directory."""
    manager = get_state_manager(terminal_id="test-conc", state_dir=tmp_path / "state")
    return manager


class TestSaveTempFilePreservation:
    """CAUSE-001: save() must not delete temp file when os.replace fails."""

    def test_temp_file_preserved_on_replace_failure(self, sm: StateManager, tmp_path: Path) -> None:
        """If os.replace fails, the temp file with valid data must survive."""
        state = sm.create_state(session_id="s1", gaps=[{"type": "test"}])
        # First save succeeds so state dir and file exist
        sm.save(state)
        assert sm.state_file_path.exists()

        # Second save: make os.replace fail
        state.gaps.append({"type": "new-gap"})
        with patch("os.replace", side_effect=PermissionError("replace denied")):
            with pytest.raises(PermissionError):
                sm.save(state)

        # Temp files should exist for recovery (orphaned cleanup handles later)
        tmp_files = list(sm.state_dir.glob("*.tmp"))
        assert len(tmp_files) >= 1, "Temp file should survive os.replace failure"
        # Verify temp file has valid data
        data = json.loads(tmp_files[0].read_text())
        assert len(data["gaps"]) == 2

    def test_successful_save_leaves_no_temp_files(self, sm: StateManager) -> None:
        """After a successful save, no orphaned temp files remain."""
        state = sm.create_state(session_id="s1")
        sm.save(state)
        tmp_files = list(sm.state_dir.glob("*.tmp"))
        assert len(tmp_files) == 0


class TestLockFilePreservation:
    """CAUSE-002/015: Lock files must never be deleted."""

    def test_lock_file_not_deleted_on_acquire_failure(self, sm: StateManager) -> None:
        """append_history: lock file survives failed lock acquisition."""
        lock_path = sm.state_dir / ".history.lock"
        # Pre-create the lock file and hold it open
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        holder = open(lock_path, "w")
        try:
            import msvcrt
            msvcrt.locking(holder.fileno(), msvcrt.LK_NBLCK, 1)
        except (ImportError, OSError):
            # fcntl path or lock not supported — create file so path exists
            pass

        try:
            with pytest.raises(OSError):
                sm.append_history({"run": 1})
        finally:
            try:
                import msvcrt
                msvcrt.locking(holder.fileno(), msvcrt.LK_UNLCK, 1)
            except (ImportError, OSError):
                pass
            holder.close()

        # Lock file must still exist
        assert lock_path.exists(), "Lock file must survive failed acquisition"

    def test_lock_file_not_deleted_after_release(self, sm: StateManager) -> None:
        """append_history: lock file survives successful lock-release cycle."""
        lock_path = sm.state_dir / ".history.lock"
        sm.append_history({"run": 1, "status": "ok"})
        assert lock_path.exists(), "Lock file must survive release"

    def test_skill_usage_lock_not_deleted_after_release(self, sm: StateManager) -> None:
        """log_skill_run: lock file survives successful lock-release cycle."""
        lock_path = sm.project_root / ".evidence" / ".skill_usage.lock"
        sm.log_skill_run({
            "type": "skill_run",
            "skill": "gto",
            "timestamp": "2026-04-17T00:00:00",
            "status": "complete",
        })
        assert lock_path.exists(), "Lock file must survive release"

    def test_concurrent_append_history_no_lock_corruption(self, sm: StateManager) -> None:
        """Two sequential append_history calls both succeed."""
        # Clear any prior history
        if sm.history_file_path.exists():
            sm.history_file_path.unlink()
        sm.append_history({"run": 1})
        sm.append_history({"run": 2})
        history = sm.get_history(last_n=10)
        assert len(history) == 2
        assert history[0]["run"] == 2  # most recent first


class TestOrphanedTempFileCleanup:
    """Verify orphaned temp files are cleaned up on load()."""

    def test_orphaned_temp_cleaned_on_load(self, sm: StateManager) -> None:
        """_cleanup_orphaned_temp_files runs during load()."""
        sm.state_dir.mkdir(parents=True, exist_ok=True)
        # Create an orphaned temp file
        orphan = sm.state_dir / ".state_test-conc_orphan.tmp"
        orphan.write_text('{"orphan": true}')
        # Age it past the 60-second cleanup threshold
        old_time = time.time() - 120
        os.utime(orphan, (old_time, old_time))

        sm.load()
        assert not orphan.exists()

    def test_valid_temp_preserved_until_replace(self, sm: StateManager) -> None:
        """Temp file from failed replace is preserved for one cycle."""
        state = sm.create_state(session_id="s1")
        sm.save(state)

        # Inject a failed-replace temp file
        state.gaps.append({"type": "recovery-gap"})
        with patch("os.replace", side_effect=PermissionError("denied")):
            with pytest.raises(PermissionError):
                sm.save(state)

        tmp_files = list(sm.state_dir.glob("*.tmp"))
        assert len(tmp_files) >= 1

        # Age temp files past the 60-second cleanup threshold
        old_time = time.time() - 120
        for tf in tmp_files:
            os.utime(tf, (old_time, old_time))

        # load() cleans them up
        sm.load()
        tmp_files_after = list(sm.state_dir.glob("*.tmp"))
        assert len(tmp_files_after) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
