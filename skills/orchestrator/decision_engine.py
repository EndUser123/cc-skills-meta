"""
Decision Engine - Phase 3 Implementation

Handles complex multi-branch workflows, alternative path handling,
and decision branching for STRATEGY + QUALITY skill integration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LifecycleBranch(Enum):
    """SDLC lifecycle branches from the tech tree."""
    STRATEGY = "STRATEGY"
    EXECUTION = "EXECUTION"
    QUALITY = "QUALITY"
    EVOLUTION = "EVOLUTION"
    CONTROL = "CONTROL"


@dataclass
class DecisionNode:
    """A node in the decision tree."""
    skill: str
    alternatives: list[str]
    branch: LifecycleBranch
    depth: int = 0
    children: list['DecisionNode'] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "alternatives": self.alternatives,
            "branch": self.branch.value,
            "depth": self.depth,
            "children": [child.to_dict() for child in self.children]
        }


@dataclass
class AlternativePath:
    """An alternative workflow path."""
    path: list[str]
    reasoning: str
    branches: list[str]
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "reasoning": self.reasoning,
            "branches": self.branches,
            "confidence": self.confidence
        }


@dataclass
class DecisionRecord:
    """A recorded decision for audit trail."""
    from_skill: str
    to_skill: str
    context: dict[str, Any]
    alternatives: list[str]
    timestamp: str
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_skill,
            "to": self.to_skill,
            "context": self.context,
            "alternatives": self.alternatives,
            "timestamp": self.timestamp,
            "reasoning": self.reasoning
        }


class DecisionEngine:
    """
    Decision Engine for complex multi-branch workflows.

    Handles:
    - Multi-branch workflow detection (STRATEGY + QUALITY)
    - Alternative path generation
    - Decision branch point identification
    - Conditional branch selection
    """

    # Phase 3 skills categorization
    PHASE_3_STRATEGY = {"/design", "/nse", "/r"}
    PHASE_3_ANALYSIS = {"/analyze", "/llm-brainstorm", "/s"}
    PHASE_3_RCA = {"/rca"}

    # Quality branch skills (from Phase 2)
    # Note: /t now handles both /test and /test-bisect functionality
    QUALITY_BRANCH = {"/t", "/qa", "/tdd", "/comply", "/validate_spec", "/q", "/refactor"}

    # Strategy branch skills
    STRATEGY_BRANCH = {"/search", "/research", "/chs", "/cks", "/analyze", "/design", "/nse", "/r"}

    # Lifecycle branch mapping
    SKILL_TO_BRANCH = {}
    _initialized = False

    @classmethod
    def initialize_branch_mapping(cls, suggest_graph: dict[str, list[str]]) -> None:
        """Initialize skill to branch mapping."""
        if cls._initialized:
            return

        # Add known skills to their branches
        for skill in cls.STRATEGY_BRANCH:
            cls.SKILL_TO_BRANCH[skill] = LifecycleBranch.STRATEGY
        for skill in cls.QUALITY_BRANCH:
            cls.SKILL_TO_BRANCH[skill] = LifecycleBranch.QUALITY

        # Also add EXECUTION and CONTROL
        execution_skills = {"/git", "/commit", "/push", "/fix"}
        control_skills = {"/orchestrate", "/workflow", "/cwo_orchestrator"}

        for skill in execution_skills:
            cls.SKILL_TO_BRANCH[skill] = LifecycleBranch.EXECUTION
        for skill in control_skills:
            cls.SKILL_TO_BRANCH[skill] = LifecycleBranch.CONTROL

        cls._initialized = True

    def __init__(self, suggest_graph: dict[str, list[str]] = None):
        self.suggest_graph = suggest_graph or {}
        self.initialize_branch_mapping(suggest_graph)
        self.decision_history: list[DecisionRecord] = []

    def analyze_workflow_branches(self, workflow: list[str]) -> dict[str, Any]:
        """Analyze a workflow to identify which lifecycle branches it uses."""
        branches = []
        for skill in workflow:
            branch = self.SKILL_TO_BRANCH.get(skill)
            if branch and branch.value not in branches:
                branches.append(branch.value)

        return {
            "branches": branches,
            "is_multi_branch": len(branches) > 1,
            "branch_count": len(branches)
        }

    def get_alternative_paths(
        self,
        from_skill: str,
        to_skill: str,
        max_paths: int = 5
    ) -> list[AlternativePath]:
        """Generate alternative workflow paths from one skill to another."""
        if not from_skill.startswith('/'):
            from_skill = f'/{from_skill}'
        if not to_skill.startswith('/'):
            to_skill = f'/{to_skill}'

        alternatives = []

        # Direct path if available
        if from_skill in self.suggest_graph:
            direct_suggestions = self.suggest_graph[from_skill]
            if to_skill in direct_suggestions:
                alternatives.append(AlternativePath(
                    path=[from_skill, to_skill],
                    reasoning="Direct path available via suggest field",
                    branches=self._get_path_branches([from_skill, to_skill])
                ))

        # Find paths through intermediate skills
        for intermediate, suggestions in self.suggest_graph.items():
            if intermediate == from_skill:
                continue
            if to_skill in suggestions and from_skill in self.suggest_graph.get(intermediate, []):
                # Reverse path exists
                alternatives.append(AlternativePath(
                    path=[from_skill, intermediate, to_skill],
                    reasoning=f"Path via {intermediate}",
                    branches=self._get_path_branches([from_skill, intermediate, to_skill]),
                    confidence=0.8
                ))

        # Forward paths through intermediate
        if from_skill in self.suggest_graph:
            for intermediate in self.suggest_graph[from_skill]:
                if intermediate in self.suggest_graph and to_skill in self.suggest_graph[intermediate]:
                    alternatives.append(AlternativePath(
                        path=[from_skill, intermediate, to_skill],
                        reasoning=f"Forward path via {intermediate}",
                        branches=self._get_path_branches([from_skill, intermediate, to_skill]),
                        confidence=0.9
                    ))

        return alternatives[:max_paths]

    def get_branch_points(self, workflow: list[str]) -> list[dict[str, Any]]:
        """Identify decision points (branch points) in a workflow."""
        branch_points = []

        for skill in workflow:
            if skill in self.suggest_graph:
                alternatives = self.suggest_graph[skill]
                if len(alternatives) > 1:
                    # Check if alternatives aren't already in workflow
                    new_alternatives = [a for a in alternatives if a not in workflow]
                    if new_alternatives:
                        branch_points.append({
                            "skill": skill,
                            "alternatives": new_alternatives,
                            "all_options": alternatives,
                            "branch": self.SKILL_TO_BRANCH.get(skill, LifecycleBranch.STRATEGY).value
                        })

        return branch_points

    def validate_cross_branch_workflow(self, workflow: list[str]) -> dict[str, Any]:
        """Validate a workflow that spans multiple lifecycle branches."""
        analysis = self.analyze_workflow_branches(workflow)

        issues = []
        # Check if transitions between branches are valid
        for i in range(len(workflow) - 1):
            from_skill = workflow[i]
            to_skill = workflow[i + 1]

            from_branch = self.SKILL_TO_BRANCH.get(from_skill)
            to_branch = self.SKILL_TO_BRANCH.get(to_skill)

            if from_branch and to_branch and from_branch != to_branch:
                # Cross-branch transition - check if valid
                if not self._is_valid_cross_branch_transition(from_branch, to_branch):
                    issues.append({
                        "step": i,
                        "from": from_skill,
                        "to": to_skill,
                        "from_branch": from_branch.value,
                        "to_branch": to_branch.value,
                        "reason": "Invalid cross-branch transition"
                    })

        return {
            "valid": len(issues) == 0,
            "branches": analysis["branches"],
            "is_multi_branch": analysis["is_multi_branch"],
            "issues": issues
        }

    def build_decision_tree(self, start_skill: str, max_depth: int = 3) -> dict[str, Any]:
        """Build a decision tree from a starting skill."""
        if not start_skill.startswith('/'):
            start_skill = f'/{start_skill}'

        branch_enum = self.SKILL_TO_BRANCH.get(start_skill, LifecycleBranch.STRATEGY)
        root = DecisionNode(
            skill=start_skill,
            alternatives=self.suggest_graph.get(start_skill, []),
            branch=branch_enum,
            depth=0
        )

        # Build tree recursively
        self._build_tree_recursive(root, max_depth, {start_skill})

        return {
            "root": root.skill,
            "branch": root.branch.value,
            "branches": root.alternatives,
            "tree": root.to_dict()
        }

    def _build_tree_recursive(
        self,
        node: DecisionNode,
        max_depth: int,
        visited: set[str]
    ) -> None:
        """Recursively build decision tree."""
        if node.depth >= max_depth or not node.alternatives:
            return

        for skill in node.alternatives[:3]:  # Limit to 3 alternatives per node
            if skill in visited:
                continue

            visited.add(skill)
            child_branch = self.SKILL_TO_BRANCH.get(skill, LifecycleBranch.STRATEGY)
            child = DecisionNode(
                skill=skill,
                alternatives=self.suggest_graph.get(skill, []),
                branch=child_branch,
                depth=node.depth + 1
            )

            self._build_tree_recursive(child, max_depth, visited.copy())
            node.children.append(child)

    def recommend_optimal_path(
        self,
        from_skill: str,
        goal_category: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Recommend optimal path based on context and goal category."""
        if not from_skill.startswith('/'):
            from_skill = f'/{from_skill}'

        # Map goal category to target branch
        goal_branch = self._category_to_branch(goal_category)

        # Find paths to skills in the target branch
        target_skills = [
            s for s, b in self.SKILL_TO_BRANCH.items()
            if b == goal_branch
        ][:3]  # Limit to 3 targets

        best_path = None
        best_score = 0

        for target in target_skills:
            alternatives = self.get_alternative_paths(from_skill, target)
            for alt in alternatives:
                score = self._score_path(alt, context)
                if score > best_score:
                    best_score = score
                    best_path = alt

        if best_path:
            return {
                "path": best_path.path,
                "reasoning": best_path.reasoning,
                "score": best_score,
                "goal_category": goal_category,
                "target_branch": goal_branch.value
            }

        # Fallback: direct suggestions
        return {
            "path": [from_skill] + self.suggest_graph.get(from_skill, [])[:3],
            "reasoning": "Using direct suggest fields",
            "score": 0.5,
            "goal_category": goal_category
        }

    def resolve_decision_conflict(self, context: dict[str, Any]) -> dict[str, Any]:
        """Resolve conflicts when suggest fields disagree."""
        # Simple resolution: prioritize by context
        priority_skills = []

        if context.get("urgency") == "high":
            priority_skills.extend(["/debug", "/fix", "/rca"])
        elif context.get("domain") == "architecture":
            priority_skills.extend(["/design", "/nse", "/r"])
        elif context.get("priority") == "quality":
            priority_skills.extend(["/t", "/comply", "/qa"])

        chosen = priority_skills[0] if priority_skills else "/nse"

        return {
            "resolved": True,
            "chosen_skill": chosen,
            "reasoning": f"Selected {chosen} based on context: {context.get('domain', context.get('urgency', 'default'))}",
            "alternatives_considered": priority_skills
        }

    def plan_workflow_with_decisions(self, workflow_plan: dict[str, Any]) -> dict[str, Any]:
        """Plan a workflow that includes decision points."""
        start = workflow_plan.get("start", "/analyze")
        goals = workflow_plan.get("goals", [])
        decision_points = workflow_plan.get("decision_points", [])

        # Build the path
        current = start
        steps = [current]

        for goal in goals:
            # Find path to goal
            alternatives = self.get_alternative_paths(current, goal, max_paths=1)
            if alternatives:
                path = alternatives[0].path[1:]  # Skip current
                steps.extend(path)
                current = goal

        return {
            "steps": steps,
            "decision_points": [
                {"name": dp, "at": step, "options": self.suggest_graph.get(step, [])}
                for dp in decision_points
                for step in steps if dp.lower() in step.lower()
            ],
            "goals_achieved": goals
        }

    def select_branch_based_on_conditions(
        self,
        from_skill: str,
        conditions: dict[str, Any]
    ) -> list[str] | None:
        """Select branch based on conditions."""
        if not from_skill.startswith('/'):
            from_skill = f'/{from_skill}'

        alternatives = self.suggest_graph.get(from_skill, [])
        if not alternatives:
            return None

        # Score each alternative based on conditions
        scored = []
        for alt in alternatives:
            score = 0
            alt_lower = alt.lower()

            if conditions.get("test_coverage") == "low":
                if "/t" in alt_lower or "/qa" in alt_lower or "/tdd" in alt_lower:
                    score += 3

            if conditions.get("complexity") == "high":
                if "/design" in alt_lower or "/nse" in alt_lower or "/r" in alt_lower:
                    score += 2

            if conditions.get("time_constraint") == "none":
                # No time pressure, can do thorough analysis
                if "/analyze" in alt_lower or "/llm-brainstorm" in alt_lower:
                    score += 1

            scored.append((alt, score))

        # Return highest scored path
        best = scored[0]
        if best[1] > 0:
            return [from_skill, best[0]]

        return [from_skill, alternatives[0]]  # Fallback to first

    def record_decision(
        self,
        from_skill: str,
        to_skill: str,
        context: dict[str, Any],
        alternatives: list[str]
    ) -> None:
        """Record a decision for audit trail."""
        from datetime import datetime

        record = DecisionRecord(
            from_skill=from_skill,
            to_skill=to_skill,
            context=context,
            alternatives=alternatives,
            timestamp=datetime.now().isoformat()
        )

        self.decision_history.append(record)

    def get_decision_history(self) -> list[dict[str, Any]]:
        """Get all recorded decisions."""
        return [r.to_dict() for r in self.decision_history]

    def execute_decision_workflow(
        self,
        start: str,
        goal: str,
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a decision-driven workflow."""
        if not start.startswith('/'):
            start = f'/{start}'

        # Build path using decision engine
        path = [start]
        current = start
        decisions_made = []

        max_steps = 10
        step = 0

        while current != goal and step < max_steps:
            alternatives = self.get_alternative_paths(current, goal, max_paths=1)
            if not alternatives:
                break

            # Choose based on conditions
            selected = alternatives[0]
            path.extend(selected.path[1:])
            decisions_made.append({
                "from": current,
                "to": selected.path[1] if len(selected.path) > 1 else goal,
                "reasoning": selected.reasoning
            })

            current = selected.path[-1]
            step += 1

        return {
            "workflow": path,
            "decisions_made": decisions_made,
            "goal_reached": current == goal,
            "steps": len(path)
        }

    def optimize_for_multiple_goals(
        self,
        start: str,
        goals: list[str]
    ) -> dict[str, Any]:
        """Optimize workflow for multiple goals."""
        if not start.startswith('/'):
            start = f'/{start}'

        all_paths = []
        for goal in goals:
            alternatives = self.get_alternative_paths(start, goal, max_paths=2)
            all_paths.extend(alternatives)

        # Score paths by goal coverage
        scored_paths = []
        for path in all_paths:
            score = len(path.path)  # Prefer shorter paths
            scored_paths.append((path, score))


        if scored_paths:
            best = scored_paths[0][0]
            return {
                "recommended_path": best.path,
                "reasoning": best.reasoning,
                "goal_scores": [
                    {"goal": g, "score": 1.0}
                    for g in goals
                ]
            }

        return {
            "recommended_path": [start],
            "goal_scores": []
        }

    def _get_path_branches(self, path: list[str]) -> list[str]:
        """Get branches for a path."""
        branches = []
        for skill in path:
            branch = self.SKILL_TO_BRANCH.get(skill)
            if branch and branch.value not in branches:
                branches.append(branch.value)
        return branches

    def _is_valid_cross_branch_transition(
        self,
        from_branch: LifecycleBranch,
        to_branch: LifecycleBranch
    ) -> bool:
        """Check if cross-branch transition is valid."""
        # STRATEGY can go to any branch
        # QUALITY can go to STRATEGY (for re-analysis) or CONTROL
        # EXECUTION can go to QUALITY or CONTROL
        valid_transitions = {
            LifecycleBranch.STRATEGY: {LifecycleBranch.STRATEGY, LifecycleBranch.EXECUTION,
                                       LifecycleBranch.QUALITY, LifecycleBranch.EVOLUTION,
                                       LifecycleBranch.CONTROL},
            LifecycleBranch.EXECUTION: {LifecycleBranch.EXECUTION, LifecycleBranch.QUALITY,
                                         LifecycleBranch.CONTROL},
            LifecycleBranch.QUALITY: {LifecycleBranch.QUALITY, LifecycleBranch.STRATEGY,
                                       LifecycleBranch.CONTROL},
            LifecycleBranch.EVOLUTION: {LifecycleBranch.EVOLUTION, LifecycleBranch.STRATEGY},
            LifecycleBranch.CONTROL: {LifecycleBranch.STRATEGY, LifecycleBranch.EXECUTION,
                                       LifecycleBranch.QUALITY}
        }

        return to_branch in valid_transitions.get(from_branch, set())

    def _category_to_branch(self, category: str) -> LifecycleBranch:
        """Map goal category to lifecycle branch."""
        mapping = {
            "quality": LifecycleBranch.QUALITY,
            "quality_assurance": LifecycleBranch.QUALITY,
            "testing": LifecycleBranch.QUALITY,
            "strategy": LifecycleBranch.STRATEGY,
            "architecture": LifecycleBranch.STRATEGY,
            "execution": LifecycleBranch.EXECUTION,
            "optimization": LifecycleBranch.EVOLUTION,
            "control": LifecycleBranch.CONTROL
        }
        return mapping.get(category.lower(), LifecycleBranch.STRATEGY)

    def _score_path(self, path: AlternativePath, context: dict[str, Any]) -> float:
        """Score a path based on context."""
        score = path.confidence

        # Prefer paths that stay in fewer branches (more focused)
        score += 1.0 / (len(path.branches) + 1)

        # Prefer paths that match context priority
        if context.get("priority") == "thoroughness":
            score += len(path.path) * 0.1  # Longer paths are more thorough
        elif context.get("priority") == "speed":
            score += 1.0 / (len(path.path) + 1)

        return score


# Singleton instance
decision_engine = None


def get_decision_engine(suggest_graph: dict[str, list[str]] = None) -> DecisionEngine:
    """Get or create the decision engine singleton."""
    global decision_engine
    if decision_engine is None:
        decision_engine = DecisionEngine(suggest_graph)
    return decision_engine
