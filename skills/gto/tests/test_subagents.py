"""Tests for GTO v3 subagents."""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from subagents import (
    HealthMetric,
    HealthReport,
    calculate_health,
)


class TestHealthCalculatorSubagent:
    """Tests for HealthCalculatorSubagent."""

    def test_calculate_health_basic(self, tmp_path: Path) -> None:
        """Test basic health calculation."""
        # Create a simple project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "module.py").write_text('"""Module."""\n\ndef foo(): pass\n')
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_module.py").write_text("def test_foo(): pass\n")

        result = calculate_health(tmp_path)

        assert isinstance(result, HealthReport)
        assert 0.0 <= result.overall_score <= 1.0
        assert result.status in ("healthy", "warning", "critical")
        assert isinstance(result.metrics, list)
        assert len(result.metrics) >= 4  # test_coverage, documentation, dependencies, code_quality

    def test_health_score_thresholds(self, tmp_path: Path) -> None:
        """Test health score status thresholds."""
        result = calculate_health(tmp_path)

        # Verify status thresholds
        if result.overall_score >= 0.8:
            assert result.status == "healthy"
        elif result.overall_score >= 0.5:
            assert result.status == "warning"
        else:
            assert result.status == "critical"

    def test_health_metrics_structure(self, tmp_path: Path) -> None:
        """Test health metric structure."""
        result = calculate_health(tmp_path)

        for metric in result.metrics:
            assert isinstance(metric, HealthMetric)
            assert hasattr(metric, "name")
            assert hasattr(metric, "score")
            assert hasattr(metric, "weight")
            assert 0.0 <= metric.score <= 1.0
            assert 0.0 <= metric.weight <= 1.0
