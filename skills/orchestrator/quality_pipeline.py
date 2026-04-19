"""
Quality Pipeline for Master Skill Orchestrator

Phase 2 integration for quality-focused workflows.
Routes quality skills through structured stages: test → validate → comply → qa
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any


class QualityStage(Enum):
    """Quality workflow stages in order of execution."""

    TEST = "test"           # /t - Context-aware adaptive testing with risk scoring
    VALIDATE = "validate"   # /validate_spec - Spec validation
    COMPLY = "comply"       # /comply - Standards compliance
    QA = "qa"               # /qa - Full certification

    # Analysis stages (parallel to main pipeline)
    DEBUG = "debug"         # /debug - Systematic debugging
    RCA = "rca"             # /rca - Root cause analysis
    NSE = "nse"             # /nse - Next steps
    OPTS = "opts"           # /q - Code quality monitoring
    REFACTOR = "refactor"   # /refactor - Refactoring suggestions


class QualityPipeline:
    """
    Orchestrates quality workflows through structured stages.

    Responsibilities:
    - Define quality skill sequences
    - Validate quality transitions
    - Track quality metrics
    - Provide quality-specific routing
    """

    # Quality skills by category
    QUALITY_SKILLS = {
        'testing': ['/t', '/qa', '/tdd'],
        'validation': ['/comply', '/validate_spec'],
        'analysis': ['/debug', '/rca', '/nse', '/analyze'],
        'optimization': ['/refactor', '/q', '/evolve']
    }

    # Recommended quality workflows
    QUALITY_WORKFLOWS = {
        'standard': ['/t', '/comply', '/qa'],
        'deep': ['/t', '/analyze', '/comply', '/debug', '/qa'],
        'regression': ['/t', '/rca', '/debug', '/fix'],
        'optimization': ['/t', '/q', '/refactor', '/comply', '/qa'],
        'spec_validation': ['/validate_spec', '/comply', '/t'],
        'quick_check': ['/t', '/comply']
    }

    # Quality stage transitions (valid sequences)
    STAGE_TRANSITIONS: dict[QualityStage, list[QualityStage]] = {
        QualityStage.TEST: [QualityStage.VALIDATE, QualityStage.COMPLY, QualityStage.QA],
        QualityStage.VALIDATE: [QualityStage.COMPLY, QualityStage.QA],
        QualityStage.COMPLY: [QualityStage.QA, QualityStage.OPTS],
        QualityStage.QA: [QualityStage.REFACTOR, QualityStage.NSE],

        # Analysis branches
        QualityStage.DEBUG: [QualityStage.RCA, QualityStage.NSE],
        QualityStage.RCA: [QualityStage.NSE, QualityStage.DEBUG],
        QualityStage.NSE: [QualityStage.TEST, QualityStage.COMPLY],
        QualityStage.OPTS: [QualityStage.REFACTOR, QualityStage.COMPLY],
        QualityStage.REFACTOR: [QualityStage.TEST, QualityStage.COMPLY, QualityStage.QA]
    }

    def __init__(self) -> None:
        """Initialize quality pipeline with metrics tracking."""
        self.metrics: dict[str, dict[str, Any]] = {}
        self.pipeline_history: list[dict[str, Any]] = []

    def get_quality_skills(self) -> dict[str, list[str]]:
        """Get all quality skills by category."""
        return self.QUALITY_SKILLS.copy()

    def get_recommended_workflow(self, workflow_type: str = 'standard') -> list[str]:
        """
        Get recommended workflow for a given type.

        Args:
            workflow_type: Type of workflow (standard, deep, regression, etc.)

        Returns:
            List of skills in recommended order
        """
        return self.QUALITY_WORKFLOWS.get(workflow_type, self.QUALITY_WORKFLOWS['standard']).copy()

    def is_quality_skill(self, skill_name: str) -> bool:
        """Check if a skill is a quality-related skill."""
        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        for skills in self.QUALITY_SKILLS.values():
            if skill_name in skills:
                return True
        return False

    def get_quality_category(self, skill_name: str) -> str | None:
        """Get the quality category for a skill."""
        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        for category, skills in self.QUALITY_SKILLS.items():
            if skill_name in skills:
                return category
        return None

    def get_stage_from_skill(self, skill_name: str) -> QualityStage | None:
        """Map skill name to quality stage."""
        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        # Direct skill to stage mapping
        skill_to_stage = {
            '/t': QualityStage.TEST,
            '/validate_spec': QualityStage.VALIDATE,
            '/comply': QualityStage.COMPLY,
            '/qa': QualityStage.QA,
            '/debug': QualityStage.DEBUG,
            '/rca': QualityStage.RCA,
            '/nse': QualityStage.NSE,
            '/q': QualityStage.OPTS,
            '/refactor': QualityStage.REFACTOR
        }

        return skill_to_stage.get(skill_name)

    def is_valid_quality_transition(self, from_skill: str, to_skill: str) -> bool:
        """
        Check if transition between quality skills is valid.

        Args:
            from_skill: Source skill
            to_skill: Destination skill

        Returns:
            True if transition is valid per quality pipeline stages
        """
        from_stage = self.get_stage_from_skill(from_skill)
        to_stage = self.get_stage_from_skill(to_skill)

        if from_stage is None or to_stage is None:
            # Not quality skills or unknown mapping
            return True  # Allow non-quality transitions

        valid_next = self.STAGE_TRANSITIONS.get(from_stage, [])
        return to_stage in valid_next

    def validate_quality_workflow(self, workflow: list[str]) -> dict[str, Any]:
        """
        Validate a quality workflow sequence.

        Args:
            workflow: List of skill names in order

        Returns:
            Validation result with issues and recommendations
        """
        issues = []
        warnings = []
        recommendations = []

        # Check if all skills are quality skills
        non_quality = [s for s in workflow if not self.is_quality_skill(s)]
        if non_quality:
            warnings.append(f"Non-quality skills in workflow: {non_quality}")

        # Validate transitions
        for i in range(len(workflow) - 1):
            from_skill = workflow[i]
            to_skill = workflow[i + 1]

            # Normalize skill names
            if not from_skill.startswith('/'):
                from_skill = f'/{from_skill}'
            if not to_skill.startswith('/'):
                to_skill = f'/{to_skill}'

            from_category = self.get_quality_category(from_skill)
            to_category = self.get_quality_category(to_skill)

            # Check for valid quality stage transitions
            if not self.is_valid_quality_transition(from_skill, to_skill):
                issues.append({
                    "step": i,
                    "from": from_skill,
                    "to": to_skill,
                    "from_category": from_category,
                    "to_category": to_category,
                    "reason": "Invalid quality pipeline transition"
                })

        # Generate recommendations
        if issues:
            recommendations.append("Consider using a standard quality workflow:")
            for name, wf in self.QUALITY_WORKFLOWS.items():
                recommendations.append(f"  - {name}: {' -> '.join(wf)}")

        return {
            "workflow": workflow,
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendations": recommendations
        }

    def get_next_quality_skills(self, current_skill: str) -> list[str]:
        """
        Get recommended next skills in quality pipeline.

        Args:
            current_skill: Current skill in workflow

        Returns:
            List of recommended next skills
        """
        current_stage = self.get_stage_from_skill(current_skill)

        if current_stage is None:
            # Not a quality skill, return entry points
            return ['/t', '/analyze', '/comply']

        valid_next = self.STAGE_TRANSITIONS.get(current_stage, [])

        # Map stages back to skills
        stage_to_skills = {
            QualityStage.TEST: ['/t', '/tdd'],
            QualityStage.VALIDATE: ['/validate_spec'],
            QualityStage.COMPLY: ['/comply'],
            QualityStage.QA: ['/qa'],
            QualityStage.DEBUG: ['/debug'],
            QualityStage.RCA: ['/rca'],
            QualityStage.NSE: ['/nse'],
            QualityStage.OPTS: ['/q'],
            QualityStage.REFACTOR: ['/refactor']
        }

        next_skills = []
        for stage in valid_next:
            next_skills.extend(stage_to_skills.get(stage, []))

        return next_skills

    def record_quality_metrics(
        self,
        skill_name: str,
        metrics: dict[str, Any]
    ) -> None:
        """
        Record quality metrics for a skill execution.

        Args:
            skill_name: Skill that was executed
            metrics: Metrics data (tests passed, coverage, issues found, etc.)
        """
        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        if skill_name not in self.metrics:
            self.metrics[skill_name] = {
                "executions": [],
                "total_runs": 0,
                "aggregate": {}
            }

        execution = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }

        self.metrics[skill_name]["executions"].append(execution)
        self.metrics[skill_name]["total_runs"] += 1

        # Update aggregate metrics
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if key not in self.metrics[skill_name]["aggregate"]:
                    self.metrics[skill_name]["aggregate"][key] = {
                        "sum": 0,
                        "count": 0,
                        "min": value,
                        "max": value
                    }

                agg = self.metrics[skill_name]["aggregate"][key]
                agg["sum"] += value
                agg["count"] += 1
                agg["min"] = min(agg["min"], value)
                agg["max"] = max(agg["max"], value)

    def get_quality_metrics(self, skill_name: str | None = None) -> dict[str, Any]:
        """
        Get quality metrics for a skill or all skills.

        Args:
            skill_name: Specific skill to query, or None for all

        Returns:
            Metrics data
        """
        if skill_name:
            # Normalize skill name
            if not skill_name.startswith('/'):
                skill_name = f'/{skill_name}'

            if skill_name in self.metrics:
                # Calculate averages
                for key, agg in self.metrics[skill_name]["aggregate"].items():
                    if agg["count"] > 0:
                        agg["avg"] = agg["sum"] / agg["count"]

                return self.metrics[skill_name]
            else:
                return {"error": f"No metrics recorded for {skill_name}"}
        else:
            # Return summary of all quality metrics
            summary = {
                "skills_tracked": len(self.metrics),
                "total_executions": sum(m["total_runs"] for m in self.metrics.values()),
                "by_skill": {}
            }

            for skill, data in self.metrics.items():
                summary["by_skill"][skill] = {
                    "total_runs": data["total_runs"],
                    "last_execution": data["executions"][-1]["timestamp"] if data["executions"] else None
                }

            return summary

    def record_pipeline_execution(
        self,
        workflow: list[str],
        results: dict[str, Any]
    ) -> None:
        """
        Record a complete quality pipeline execution.

        Args:
            workflow: List of skills executed
            results: Overall results from pipeline
        """
        execution = {
            "timestamp": datetime.now().isoformat(),
            "workflow": workflow,
            "results": results
        }

        self.pipeline_history.append(execution)

    def get_pipeline_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent quality pipeline executions.

        Args:
            limit: Maximum number of histories to return

        Returns:
            List of pipeline execution records
        """
        return self.pipeline_history[-limit:]

    def get_quality_summary(self) -> dict[str, Any]:
        """
        Get comprehensive quality pipeline summary.

        Returns:
            Summary of all quality pipeline data
        """
        return {
            "quality_skills": self.QUALITY_SKILLS,
            "recommended_workflows": self.QUALITY_WORKFLOWS,
            "metrics": self.get_quality_metrics(),
            "pipeline_executions": len(self.pipeline_history),
            "recent_executions": self.get_pipeline_history(5)
        }


# Singleton instance
quality_pipeline = QualityPipeline()
