"""Tests for state_manager module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from __lib.state_manager import StateFile, StateManager, get_state_manager


class TestStateManager:
    """Smoke tests for StateManager."""

    def test_get_state_manager(self, tmp_path: Path) -> None:
        """Test getting state manager instance."""
        manager = get_state_manager(tmp_path, "test_terminal")
        assert isinstance(manager, StateManager)
        assert manager.terminal_id == "test_terminal"


class TestStateFile:
    """Tests for StateFile dataclass."""

    def test_dataclass(self) -> None:
        """Test StateFile can be constructed."""
        sf = StateFile(
            version="3.0.0",
            terminal_id="test",
            timestamp="2026-01-01T00:00:00",
            session_id=None,
            gaps=[],
            metadata={},
        )
        assert sf.version == "3.0.0"
        assert sf.terminal_id == "test"
        assert len(sf.gaps) == 0
