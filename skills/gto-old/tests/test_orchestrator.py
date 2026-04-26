"""Tests for GTO v3 orchestrator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gto_orchestrator import (
    GTOOrchestrator,
    OrchestratorConfig,
    OrchestratorResult,
    run_gto_analysis,
)


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = OrchestratorConfig()

        assert config.project_root is None
        assert config.terminal_id == "unknown"
        assert config.transcript_path is None
        assert config.enable_subagents is False  # Disabled: gap types route to dedicated skills
        assert config.verbose is False


class TestGTOOrchestrator:
    """Tests for GTOOrchestrator."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test orchestrator initialization."""
        config = OrchestratorConfig(project_root=tmp_path, terminal_id="test")
        orchestrator = GTOOrchestrator(config)

        assert orchestrator.config == config
        assert orchestrator.project_root == tmp_path
        assert orchestrator.state_manager is not None

    def test_run_with_viability_failure(self, tmp_path: Path) -> None:
        """Test run with viability check failure."""
        config = OrchestratorConfig(project_root=tmp_path, terminal_id="test")
        orchestrator = GTOOrchestrator(config)

        result = orchestrator.run()

        assert isinstance(result, OrchestratorResult)
        # Non-git directory should fail viability

    def test_format_output(self, tmp_path: Path) -> None:
        """Test output formatting."""
        config = OrchestratorConfig(project_root=tmp_path, terminal_id="test")
        orchestrator = GTOOrchestrator(config)

        # Create a mock result
        from __lib import ConsolidatedResults, Gap

        mock_results = ConsolidatedResults(
            gaps=[
                Gap(
                    gap_id="GAP-001",
                    type="test",
                    severity="high",
                    message="Add tests",
                    file_path="src/module.py",
                    line_number=10,
                    source="TestPresenceChecker",
                    theme="testing",
                )
            ],
            total_gap_count=1,
            critical_count=0,
            high_count=1,
            medium_count=0,
            low_count=0,
            timestamp="2026-03-21T10:00:00",
        )

        result = OrchestratorResult(
            success=True,
            viability_passed=True,
            results=mock_results,
            health_report=None,
            error=None,
        )

        output = orchestrator.format_output(result)

        assert isinstance(output, str)
        assert "GTO Gap Analysis Results" in output
        assert "Add tests" in output  # gap message rendered

    def test_save_json_artifact(self, tmp_path: Path) -> None:
        """Test JSON artifact saving."""
        config = OrchestratorConfig(project_root=tmp_path, terminal_id="test")
        orchestrator = GTOOrchestrator(config)

        # Create a mock result
        from __lib import ConsolidatedResults, Gap

        mock_results = ConsolidatedResults(
            gaps=[
                Gap(
                    gap_id="GAP-001",
                    type="test",
                    severity="high",
                    message="Add tests",
                    file_path="src/module.py",
                    line_number=10,
                    source="TestPresenceChecker",
                )
            ],
            total_gap_count=1,
            critical_count=0,
            high_count=1,
            medium_count=0,
            low_count=0,
            timestamp="2026-03-21T10:00:00",
        )

        result = OrchestratorResult(
            success=True,
            viability_passed=True,
            results=mock_results,
            health_report=None,
            error=None,
        )

        output_path = tmp_path / "output.json"
        orchestrator.save_json_artifact(result, output_path)

        assert output_path.exists()

        with open(output_path) as f:
            data = json.load(f)

        assert data["total_gap_count"] == 1
        assert len(data["gaps"]) == 1


class TestRunGTOAnalysis:
    """Tests for run_gto_analysis convenience function."""

    def test_convenience_function(self, tmp_path: Path) -> None:
        """Test run_gto_analysis convenience function."""
        result = run_gto_analysis(project_root=tmp_path, terminal_id="test")

        assert isinstance(result, OrchestratorResult)
