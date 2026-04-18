"""HealthCalculatorSubagent - Calculate project health metrics.

Priority: P2 (subagent for health calculation)
Purpose: Calculate health scores across multiple dimensions

Features:
- Test coverage health calculation
- Documentation coverage calculation
- Dependency health calculation
- Code quality metrics
- Overall health score aggregation
"""

from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class HealthMetric:
    """A single health metric."""

    name: str
    score: float  # 0.0 to 1.0
    weight: float = 1.0
    description: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "score": self.score,
            "weight": self.weight,
            "description": self.description,
            "details": self.details,
        }


@dataclass
class HealthReport:
    """Overall health report."""

    overall_score: float  # 0.0 to 1.0
    metrics: list[HealthMetric]
    status: str  # "healthy", "warning", "critical"
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "status": self.status,
            "metrics": [m.to_dict() for m in self.metrics],
            "timestamp": self.timestamp,
        }


class HealthCalculatorSubagent:
    """
    Calculate project health metrics.

    Aggregates health scores across multiple dimensions
    for overall project health assessment.
    """

    # Health thresholds
    HEALTHY_THRESHOLD = 0.8
    WARNING_THRESHOLD = 0.5

    # Metric weights (must sum to 1.0)
    METRIC_WEIGHTS = {
        "test_coverage": 0.3,
        "documentation": 0.2,
        "dependencies": 0.2,
        "code_quality": 0.3,
    }

    def __init__(self, project_root: Path | None = None):
        """Initialize health calculator.

        Args:
            project_root: Project root directory
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def _calculate_test_coverage(self) -> HealthMetric:
        """Calculate test coverage health.

        Returns:
            HealthMetric for test coverage
        """
        # Count source and test files
        source_files = [
            p
            for p in self.project_root.rglob("*.py")
            if p.name != "__init__.py" and not p.name.startswith("test_") and "tests" not in p.parts
        ]

        test_files = list(self.project_root.rglob("test_*.py")) + list(
            self.project_root.rglob("tests/test_*.py")
        )

        # Calculate coverage ratio
        if len(source_files) == 0:
            return HealthMetric(
                name="test_coverage",
                score=1.0,  # No source files = perfect coverage
                weight=self.METRIC_WEIGHTS["test_coverage"],
                description="Test coverage (no source files)",
                details={"source_files": 0, "test_files": 0, "ratio": 1.0},
            )

        coverage_ratio = len(test_files) / len(source_files)
        score = min(1.0, coverage_ratio)  # Cap at 1.0

        return HealthMetric(
            name="test_coverage",
            score=score,
            weight=self.METRIC_WEIGHTS["test_coverage"],
            description="Test coverage ratio",
            details={
                "source_files": len(source_files),
                "test_files": len(test_files),
                "ratio": round(coverage_ratio, 2),
            },
        )

    def _calculate_documentation_coverage(self) -> HealthMetric:
        """Calculate documentation coverage health.

        Returns:
            HealthMetric for documentation coverage
        """
        source_files = [
            p
            for p in self.project_root.rglob("*.py")
            if p.name != "__init__.py" and not p.name.startswith("test_") and "tests" not in p.parts
        ]

        documented_count = 0
        for source_file in source_files:
            try:
                with open(source_file) as f:
                    content = f.read()
                    tree = ast.parse(content)
                    if ast.get_docstring(tree):
                        documented_count += 1
            except (OSError, UnicodeDecodeError, SyntaxError):
                # Skip problematic files
                pass

        if len(source_files) == 0:
            return HealthMetric(
                name="documentation",
                score=1.0,
                weight=self.METRIC_WEIGHTS["documentation"],
                description="Documentation coverage (no source files)",
                details={"source_files": 0, "documented": 0, "ratio": 1.0},
            )

        doc_ratio = documented_count / len(source_files)

        return HealthMetric(
            name="documentation",
            score=doc_ratio,
            weight=self.METRIC_WEIGHTS["documentation"],
            description="Documentation coverage",
            details={
                "source_files": len(source_files),
                "documented": documented_count,
                "ratio": round(doc_ratio, 2),
            },
        )

    def _calculate_dependency_health(self) -> HealthMetric:
        """Calculate dependency health.

        Returns:
            HealthMetric for dependency health
        """
        # Check for requirements file
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            "setup.py",
        ]

        has_requirements = any((self.project_root / f).exists() for f in requirements_files)

        # Try to get installed packages
        installed_packages = {}
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for pkg in json.loads(result.stdout):
                    installed_packages[pkg.get("name", "").lower()] = pkg.get("version", "")
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        # Parse requirements if exists
        declared_packages = set()
        if (self.project_root / "requirements.txt").exists():
            try:
                with open(self.project_root / "requirements.txt") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name
                            pkg_name = (
                                line.split(">")[0].split("<")[0].split("=")[0].strip().lower()
                            )
                            declared_packages.add(pkg_name)
            except OSError:
                pass

        # Calculate health based on dependency management
        score = 0.5  # Base score

        if has_requirements:
            score += 0.3

        if declared_packages:
            score += 0.2

        return HealthMetric(
            name="dependencies",
            score=min(1.0, score),
            weight=self.METRIC_WEIGHTS["dependencies"],
            description="Dependency management health",
            details={
                "has_requirements": has_requirements,
                "declared_packages": len(declared_packages),
                "installed_packages": len(installed_packages),
            },
        )

    def _calculate_code_quality(self) -> HealthMetric:
        """Calculate code quality health.

        Returns:
            HealthMetric for code quality
        """
        # Scan for code quality indicators
        source_files = list(self.project_root.rglob("*.py"))

        # Count quality markers
        todo_count = 0
        hack_count = 0
        fixme_count = 0
        xxx_count = 0
        type_ignore_count = 0

        for source_file in source_files:
            try:
                with open(source_file) as f:
                    content = f.read()
                    lines = content.split("\n")

                    for line in lines:
                        line_lower = line.lower().strip()
                        if "# todo:" in line_lower:
                            todo_count += 1
                        if "# hack:" in line_lower:
                            hack_count += 1
                        if "# fixme:" in line_lower:
                            fixme_count += 1
                        if "# xxx:" in line_lower:
                            xxx_count += 1
                        if "# type: ignore" in line_lower:
                            type_ignore_count += 1

            except (OSError, UnicodeDecodeError):
                # Skip problematic files
                pass

        # Calculate quality score (fewer markers = better)
        total_markers = todo_count + hack_count + fixme_count + xxx_count
        max_acceptable = len(source_files) * 2  # Allow 2 markers per file

        if max_acceptable == 0:
            quality_score = 1.0
        else:
            quality_score = max(0.0, 1.0 - (total_markers / max_acceptable))

        return HealthMetric(
            name="code_quality",
            score=quality_score,
            weight=self.METRIC_WEIGHTS["code_quality"],
            description="Code quality (fewer TODO/HACK markers)",
            details={
                "files_scanned": len(source_files),
                "todo_count": todo_count,
                "hack_count": hack_count,
                "fixme_count": fixme_count,
                "xxx_count": xxx_count,
                "type_ignore_count": type_ignore_count,
                "total_markers": total_markers,
            },
        )

    def _determine_status(self, overall_score: float) -> str:
        """Determine health status from overall score.

        Args:
            overall_score: Overall health score (0.0 to 1.0)

        Returns:
            Status string: "healthy", "warning", or "critical"
        """
        if overall_score >= self.HEALTHY_THRESHOLD:
            return "healthy"
        elif overall_score >= self.WARNING_THRESHOLD:
            return "warning"
        else:
            return "critical"

    def calculate_health(self) -> HealthReport:
        """
        Calculate overall project health.

        Returns:
            HealthReport with all metrics and overall score
        """
        from datetime import datetime

        # Calculate individual metrics
        metrics = [
            self._calculate_test_coverage(),
            self._calculate_documentation_coverage(),
            self._calculate_dependency_health(),
            self._calculate_code_quality(),
        ]

        # Calculate weighted overall score
        weighted_sum = sum(m.score * m.weight for m in metrics)
        overall_score = weighted_sum

        # Determine status
        status = self._determine_status(overall_score)

        return HealthReport(
            overall_score=round(overall_score, 2),
            metrics=metrics,
            status=status,
            timestamp=datetime.now().isoformat(),
        )


# Convenience function
def calculate_health(project_root: Path | None = None) -> HealthReport:
    """
    Quick health calculation.

    Args:
        project_root: Project root directory

    Returns:
        HealthReport with all metrics and overall score
    """
    calculator = HealthCalculatorSubagent(project_root)
    return calculator.calculate_health()
