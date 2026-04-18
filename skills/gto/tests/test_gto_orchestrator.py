"""Tests for gto_orchestrator module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.gto.gto_orchestrator import (
    GTOOrchestrator,
    OrchestratorConfig,
    OrchestratorResult,
    _auto_detect_transcript_path,
    _get_default_terminal_id,
    _get_transcript_fingerprint,
)


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test OrchestratorConfig can be constructed."""
        config = OrchestratorConfig(project_root=Path("/tmp/test"))
        assert config.project_root == Path("/tmp/test")
        assert config.enable_subagents is True
        assert config.enable_health_check is True

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = OrchestratorConfig()
        assert config.project_root is None
        assert config.terminal_id is not None
        assert isinstance(config.terminal_id, str)


class TestOrchestratorResult:
    """Tests for OrchestratorResult dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test OrchestratorResult can be constructed."""
        result = OrchestratorResult(
            success=True,
            viability_passed=True,
            results=None,
            health_report=None,
        )
        assert result.success is True
        assert result.viability_passed is True
        assert result.results is None

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        result = OrchestratorResult(
            success=True,
            viability_passed=True,
            results=None,
            health_report={"score": 85},
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["success"] is True
        assert d["health_report"]["score"] == 85


class TestGTOOrchestrator:
    """Smoke tests for GTOOrchestrator class."""

    def test_instantiation(self, tmp_path: Path) -> None:
        """Test GTOOrchestrator can be instantiated."""
        config = OrchestratorConfig(project_root=tmp_path)
        orchestrator = GTOOrchestrator(config)
        assert orchestrator.project_root == tmp_path.resolve()

    def test_run_returns_orchestrator_result(self, tmp_path: Path) -> None:
        """Test run returns OrchestratorResult."""
        config = OrchestratorConfig(project_root=tmp_path, enable_subagents=False)
        orchestrator = GTOOrchestrator(config)
        result = orchestrator.run()
        assert isinstance(result, OrchestratorResult)


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_default_terminal_id(self) -> None:
        """Test _get_default_terminal_id returns a string."""
        result = _get_default_terminal_id()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_auto_detect_transcript_path(self) -> None:
        """Test _auto_detect_transcript_path returns Path or None."""
        result = _auto_detect_transcript_path()
        # Result can be Path or None depending on system state
        assert result is None or isinstance(result, Path)

    def test_get_transcript_fingerprint_with_none(self) -> None:
        """Test _get_transcript_fingerprint with None input."""
        result = _get_transcript_fingerprint(None)
        assert result is None

    def test_get_transcript_fingerprint_with_nonexistent_path(self, tmp_path: Path) -> None:
        """Test _get_transcript_fingerprint with nonexistent path."""
        result = _get_transcript_fingerprint(tmp_path / "nonexistent.jsonl")
        assert result is None
