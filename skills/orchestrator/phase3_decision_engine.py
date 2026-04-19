"""
Phase 3: Decision Engine Integration

Extends MasterSkillOrchestrator with decision engine capabilities.
This is loaded as a separate module to avoid file locking issues.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from decision_engine import DecisionEngine, get_decision_engine


class DecisionEngineMixin:
    """
    Mixin class that adds Phase 3 Decision Engine capabilities
    to the MasterSkillOrchestrator.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize decision engine with suggest graph
        graph = self.suggest_parser.load_all_skills()
        self.decision_engine = get_decision_engine(graph)

    def analyze_workflow_branches(self, workflow: List[str]) -> Dict[str, Any]:
        """Analyze a workflow to identify which lifecycle branches it uses."""
        return self.decision_engine.analyze_workflow_branches(workflow)

    def get_alternative_paths(
        self,
        from_skill: str,
        to_skill: str,
        max_paths: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate alternative workflow paths from one skill to another."""
        alternatives = self.decision_engine.get_alternative_paths(
            from_skill, to_skill, max_paths
        )
        return [alt.to_dict() for alt in alternatives]

    def get_branch_points(self, workflow: List[str]) -> List[Dict[str, Any]]:
        """Identify decision points (branch points) in a workflow."""
        return self.decision_engine.get_branch_points(workflow)

    def validate_cross_branch_workflow(self, workflow: List[str]) -> Dict[str, Any]:
        """Validate a workflow that spans multiple lifecycle branches."""
        return self.decision_engine.validate_cross_branch_workflow(workflow)

    def build_decision_tree(self, start_skill: str, max_depth: int = 3) -> Dict[str, Any]:
        """Build a decision tree from a starting skill."""
        return self.decision_engine.build_decision_tree(start_skill, max_depth)

    def recommend_optimal_path(
        self,
        from_skill: str,
        goal_category: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend optimal path based on context and goal category."""
        return self.decision_engine.recommend_optimal_path(
            from_skill, goal_category, context
        )

    def resolve_decision_conflict(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts when suggest fields disagree."""
        return self.decision_engine.resolve_decision_conflict(context)

    def plan_workflow_with_decisions(self, workflow_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a workflow that includes decision points."""
        return self.decision_engine.plan_workflow_with_decisions(workflow_plan)

    def select_branch_based_on_conditions(
        self,
        from_skill: str,
        conditions: Dict[str, Any]
    ) -> Optional[List[str]]:
        """Select branch based on conditions."""
        return self.decision_engine.select_branch_based_on_conditions(
            from_skill, conditions
        )

    def execute_decision_workflow(
        self,
        start: str,
        goal: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a decision-driven workflow."""
        return self.decision_engine.execute_decision_workflow(start, goal, context)

    def optimize_for_multiple_goals(
        self,
        start: str,
        goals: List[str]
    ) -> Dict[str, Any]:
        """Optimize workflow for multiple goals."""
        return self.decision_engine.optimize_for_multiple_goals(start, goals)

    def record_decision(
        self,
        from_skill: str,
        to_skill: str,
        context: Dict[str, Any],
        alternatives: List[str]
    ) -> None:
        """Record a decision for audit trail."""
        self.decision_engine.record_decision(from_skill, to_skill, context, alternatives)

    def get_decision_history(self) -> List[Dict[str, Any]]:
        """Get all recorded decisions."""
        return self.decision_engine.get_decision_history()


# Factory function to create enhanced orchestrator
def create_decision_orchestrator(base_orchestrator_class):
    """
    Create an orchestrator class with decision engine capabilities.

    Usage:
        from orchestrator import MasterSkillOrchestrator
        from phase3_decision_engine import create_decision_orchestrator

        DecisionOrchestrator = create_decision_orchestrator(MasterSkillOrchestrator)
        orchestrator = DecisionOrchestrator()
    """
    class DecisionOrchestrator(DecisionEngineMixin, base_orchestrator_class):
        """Orchestrator with Phase 3 Decision Engine capabilities."""
        pass

    return DecisionOrchestrator
