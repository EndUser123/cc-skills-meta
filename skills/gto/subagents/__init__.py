"""GTO v3 subagents.

This module contains AI-driven subagents for enhanced gap detection and analysis.
"""

from __future__ import annotations

__all__ = [
    "GapFinding",
    "HealthCalculatorSubagent",
    "calculate_health",
    "HealthMetric",
    "HealthReport",
]

from .health_calculator_subagent import (
    HealthCalculatorSubagent,
    HealthMetric,
    HealthReport,
    calculate_health,
)

# GapFinding shared dataclass (no subagent dependency)
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GapFinding:
    file_path: Path
    line_number: int
    pattern: str
    severity: str
    message: str
