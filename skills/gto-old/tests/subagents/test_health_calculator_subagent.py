"""Tests for health_calculator_subagent module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from subagents.health_calculator_subagent import (
    HealthCalculatorSubagent,
    HealthMetric,
    HealthReport,
    calculate_health,
)


class TestHealthMetric:
    """Tests for HealthMetric dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test HealthMetric can be constructed."""
        metric = HealthMetric(
            name="test_coverage",
            score=0.8,
            weight=0.3,
        )
        assert metric.name == "test_coverage"
        assert metric.score == 0.8
        assert metric.weight == 0.3

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        metric = HealthMetric(
            name="test_coverage",
            score=0.8,
            weight=0.3,
        )
        result = metric.to_dict()
        assert isinstance(result, dict)
        assert result["name"] == "test_coverage"
        assert result["score"] == 0.8


class TestHealthReport:
    """Tests for HealthReport dataclass."""

    def test_dataclass_construction(self) -> None:
        """Test HealthReport can be constructed."""
        metric = HealthMetric(name="test", score=0.8)
        report = HealthReport(
            overall_score=0.75,
            metrics=[metric],
            status="healthy",
            timestamp="2026-03-25T00:00:00Z",
        )
        assert report.overall_score == 0.75
        assert len(report.metrics) == 1
        assert report.status == "healthy"

    def test_to_dict(self) -> None:
        """Test to_dict method."""
        metric = HealthMetric(name="test", score=0.8)
        report = HealthReport(
            overall_score=0.75,
            metrics=[metric],
            status="healthy",
            timestamp="2026-03-25T00:00:00Z",
        )
        result = report.to_dict()
        assert isinstance(result, dict)
        assert result["overall_score"] == 0.75
        assert result["status"] == "healthy"


class TestHealthCalculatorSubagent:
    """Smoke tests for HealthCalculatorSubagent class."""

    def test_instantiation(self, tmp_path: Path) -> None:
        """Test HealthCalculatorSubagent can be instantiated."""
        calculator = HealthCalculatorSubagent(tmp_path)
        assert calculator.project_root == tmp_path.resolve()

    def test_calculate_health_returns_report(self, tmp_path: Path) -> None:
        """Test calculate_health returns HealthReport."""
        calculator = HealthCalculatorSubagent(tmp_path)
        result = calculator.calculate_health()
        assert isinstance(result, HealthReport)
        assert isinstance(result.overall_score, float)
        assert isinstance(result.metrics, list)
        assert result.status in ("healthy", "warning", "critical")

    def test_calculate_health_convenience_function(self, tmp_path: Path) -> None:
        """Test calculate_health convenience function."""
        result = calculate_health(tmp_path)
        assert isinstance(result, HealthReport)
