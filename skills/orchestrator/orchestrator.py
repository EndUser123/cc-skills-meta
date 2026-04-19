"""
Master Skill Orchestrator

Central orchestrator for skill routing and workflow management.

Works with:
- 3 Python-based skills (NSE, RCA, brainstorm)
- 189 CLI-based skills (invoked via Skill tool)
- 17+ skills with suggest fields (routing foundation)
- 35+ high-value skills for consolidation
- Phase 2: Quality Pipeline integration for 9 quality skills
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from suggest_parser import suggest_parser
from skill_router import skill_router
from workflow_state import workflow_state
from quality_pipeline import quality_pipeline
from timeout_guard import TimeoutGuard, DEFAULT_TIMEOUT
from agent_performance_logger import agent_performance_logger
import time


class MasterSkillOrchestrator:
    """
    Central orchestrator for skill routing and workflow management.

    Responsibilities:
    - Parse suggest fields from 192 skills
    - Validate workflow sequences
    - Route to appropriate skills
    - Persist workflow state
    - Record decision audit trail
    - Phase 2: Quality Pipeline orchestration
    """

    STATE_FILE = Path("P:/.claude/session_data/workflow_state.json")

    # Strategic skills that should be recorded in decision trail
    STRATEGIC_SKILLS = {
        '/nse', '/design', '/r', '/llm-brainstorm', '/rca',
        '/analyze', '/s', '/dne', '/refactor', '/evolve'
    }

    def __init__(self) -> None:
        self.suggest_parser = suggest_parser
        self.skill_router = skill_router
        self.workflow_state = workflow_state
        self.quality_pipeline = quality_pipeline
        self.agent_logger = agent_performance_logger
        self.decision_records: List[Dict[str, Any]] = []
        self.execution_log: List[Dict[str, Any]] = []

        # Load persisted state from previous sessions
        self._load_persisted_state()

        # Load suggest field relationships and build transition graph
        graph = self.suggest_parser.load_all_skills()
        self.workflow_state.load_transitions_from_graph(graph)

    def invoke_skill(
        self,
        skill_name: str,
        args: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: int | None = DEFAULT_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Invoke a skill with orchestration.

        Args:
            skill_name: Skill to invoke (e.g., '/nse', '/debug')
            args: Arguments for the skill
            context: Execution context
            timeout: Maximum seconds for skill execution (None for no limit)

        Returns:
            Skill result with post-action suggestions
        """

        if args is None:
            args = {}
        if context is None:
            context = {}

        # Normalize skill name
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        # Phase 1: Check workflow state validity
        if self.workflow_state.current_skill:
            if not self.workflow_state.is_valid_transition(
                self.workflow_state.current_skill,
                skill_name
            ):
                valid_next = list(self.workflow_state.get_valid_next_skills(
                    self.workflow_state.current_skill
                ))
                return {
                    "error": f"Invalid transition from {self.workflow_state.current_skill} to {skill_name}",
                    "valid_next_skills": valid_next,
                    "current_workflow": self.workflow_state.get_workflow_path(),
                    "blocked": True,
                    "suggestion": f"Valid next skills from {self.workflow_state.current_skill}: {valid_next}"
                }

        # Phase 1.5: Check quality pipeline validity (if quality skill)
        if self.quality_pipeline.is_quality_skill(skill_name):
            if self.workflow_state.current_skill:
                if not self.quality_pipeline.is_valid_quality_transition(
                    self.workflow_state.current_skill,
                    skill_name
                ):
                    quality_next = self.quality_pipeline.get_next_quality_skills(
                        self.workflow_state.current_skill
                    )
                    return {
                        "error": f"Invalid quality pipeline transition from {self.workflow_state.current_skill} to {skill_name}",
                        "quality_pipeline": True,
                        "valid_next_quality_skills": quality_next,
                        "current_workflow": self.workflow_state.get_workflow_path(),
                        "blocked": True,
                        "suggestion": f"Valid quality transitions from {self.workflow_state.current_skill}: {quality_next}"
                    }

        # Phase 2: Enter skill state
        if not self.workflow_state.enter_skill(skill_name):
            return {
                "error": f"Failed to enter skill state for {skill_name}",
                "status": "failed"
            }

        # Track execution start time for performance logging
        start_time = time.monotonic()
        outcome = "success"

        try:
            # Phase 3: Invoke skill
            result = self.skill_router.invoke_skill(skill_name, args, context)

            # Phase 4: Record if strategic decision
            if self._is_strategic_decision(skill_name):
                self._record_decision(skill_name, args, result)

            # Phase 5: Get suggested next skills
            suggestions = self.suggest_parser.get_suggestions(skill_name)
            result["suggested_next_skills"] = suggestions

            # Phase 5.5: Add quality pipeline suggestions for quality skills
            if self.quality_pipeline.is_quality_skill(skill_name):
                quality_suggestions = self.quality_pipeline.get_next_quality_skills(skill_name)
                result["quality_pipeline_suggestions"] = quality_suggestions
                result["quality_category"] = self.quality_pipeline.get_quality_category(skill_name)

            # Phase 6: Log execution
            self.execution_log.append({
                "skill": skill_name,
                "timestamp": datetime.now().isoformat(),
                "status": result.get("status", "unknown"),
                "suggestions": suggestions,
                "workflow_path": self.workflow_state.get_workflow_path(),
                "is_quality_skill": self.quality_pipeline.is_quality_skill(skill_name)
            })

            # Add timeout info to result
            if timeout is not None:
                result["timeout_seconds"] = timeout
            return result

        except Exception as e:
            outcome = "error"
            error_result = {
                "error": str(e),
                "skill": skill_name,
                "status": "failed"
            }
            self.execution_log.append({
                "skill": skill_name,
                "timestamp": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            })
            return error_result

        finally:
            # Phase 7: Exit skill state
            self.workflow_state.exit_skill()

            # Phase 8: Persist state
            self._persist_state()

            # Phase 9: Log to agent performance logger (for circuit breaker data)
            duration_seconds = time.monotonic() - start_time
            self._log_agent_performance(
                skill_name=skill_name,
                args=args,
                outcome=outcome,
                duration_seconds=duration_seconds,
                timeout_limit=timeout
            )

    def _log_agent_performance(
        self,
        skill_name: str,
        args: Dict[str, Any],
        outcome: str,
        duration_seconds: float,
        timeout_limit: int | None
    ) -> None:
        """
        Log agent execution performance for circuit breaker analysis.

        Only logs subagent invocations (via Task tool), not CLI skills.
        """
        # Determine if this was a subagent invocation
        # Subagents are invoked via Task tool, which we can detect from context
        agent_type = args.get("subagent_type", "unknown")
        if agent_type == "unknown":
            # Try to infer from skill name
            if skill_name.startswith("/"):
                # CLI skill - not logged as agent performance
                return

        # Extract task info from args
        task_type = args.get("task_type", "unknown")
        file_path = args.get("file_path", args.get("target_file", ""))
        lines_of_code = args.get("lines_of_code", 0)
        file_count = args.get("file_count", 1)

        # Determine strategy used
        strategy_used = args.get("strategy", "agent")

        # Map outcome from status
        if outcome == "success":
            outcome = "success"
        elif outcome == "error":
            # Check if it was a timeout
            if duration_seconds >= (timeout_limit or float('inf')):
                outcome = "timeout"
            else:
                outcome = "error"
        else:
            outcome = outcome

        # Only log if we have meaningful data
        if agent_type != "unknown" and lines_of_code > 0:
            self.agent_logger.log_execution(
                agent_type=agent_type,
                task_type=task_type,
                file_path=file_path,
                lines_of_code=lines_of_code,
                file_count=file_count,
                outcome=outcome,
                duration_seconds=duration_seconds,
                timeout_limit=timeout_limit,
                strategy_used=strategy_used,
                error_message=args.get("error_message") if outcome != "success" else None,
            )

    def _is_strategic_decision(self, skill_name: str) -> bool:
        """Check if skill is a strategic decision that should be recorded."""
        return skill_name in self.STRATEGIC_SKILLS

    def _record_decision(
        self,
        skill_name: str,
        args: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Record strategic decision for audit trail."""
        self.decision_records.append({
            "skill": skill_name,
            "timestamp": datetime.now().isoformat(),
            "args": args,
            "result": result.get("result", result),
            "workflow_path": self.workflow_state.get_workflow_path()
        })

    def _load_persisted_state(self) -> None:
        """Load workflow state from previous sessions."""
        if not self.STATE_FILE.exists():
            return

        try:
            with open(self.STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # Restore execution log
            self.execution_log = state_data.get('execution_log', [])

            # Restore decision records
            self.decision_records = state_data.get('decision_records', [])

            # Restore workflow stack
            workflow_stack = state_data.get('workflow_stack', [])
            if workflow_stack:
                self.workflow_state.stack = workflow_stack
                self.workflow_state.current_skill = workflow_stack[-1] if workflow_stack else None

        except Exception as e:
            print(f"Warning: Could not load persisted state: {e}")

    def _persist_state(self) -> None:
        """Save workflow state to file for next session."""
        # Ensure directory exists
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        state_data = {
            "execution_log": self.execution_log,
            "decision_records": self.decision_records,
            "workflow_stack": self.workflow_state.stack,
            "current_skill": self.workflow_state.current_skill,
            "timestamp": datetime.now().isoformat()
        }

        try:
            with open(self.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not persist state: {e}")

    # ==================== PUBLIC API ====================

    def get_workflow_suggestions(self, current_skill: str) -> List[str]:
        """Get suggested next skills based on skill's suggest field."""
        return self.suggest_parser.get_suggestions(current_skill)

    def get_skill_metadata(self, skill_name: str) -> Dict[str, Any]:
        """Get metadata for a skill (from SKILL.md)."""
        return self.suggest_parser.get_skill_metadata(skill_name)

    def get_decision_audit_trail(self) -> List[Dict[str, Any]]:
        """Get audit trail of all strategic decisions."""
        return self.decision_records

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get complete execution log."""
        return self.execution_log

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        return {
            "total_executions": len(self.execution_log),
            "total_decisions": len(self.decision_records),
            "current_workflow": self.workflow_state.get_workflow_path(),
            "workflow_state": self.workflow_state.get_state_summary(),
            "invocation_stats": self.skill_router.get_invocation_stats(),
            "skills_with_suggest_fields": len(self.suggest_parser.get_graph())
        }

    def get_all_suggestions(self) -> Dict[str, List[str]]:
        """Get all suggest field relationships."""
        return self.suggest_parser.get_graph()

    def validate_workflow(self, workflow: List[str]) -> Dict[str, Any]:
        """
        Validate a proposed workflow sequence.

        Returns validation result with any issues found.
        """
        issues = []
        valid_transitions = []

        for i in range(len(workflow) - 1):
            from_skill = workflow[i]
            to_skill = workflow[i + 1]

            if not from_skill.startswith('/'):
                from_skill = f'/{from_skill}'
            if not to_skill.startswith('/'):
                to_skill = f'/{to_skill}'

            if self.workflow_state.is_valid_transition(from_skill, to_skill):
                valid_transitions.append((from_skill, to_skill))
            else:
                issues.append({
                    "step": i,
                    "from": from_skill,
                    "to": to_skill,
                    "reason": "Transition not found in suggest fields"
                })

        return {
            "workflow": workflow,
            "valid": len(issues) == 0,
            "valid_transitions": valid_transitions,
            "issues": issues
        }

    def suggest_workflow(
        self,
        starting_skill: str,
        max_depth: int = 3
    ) -> List[List[str]]:
        """
        Generate possible workflows starting from a given skill.

        Args:
            starting_skill: Skill to start from
            max_depth: Maximum depth to explore

        Returns:
            List of possible workflow paths
        """
        if not starting_skill.startswith('/'):
            starting_skill = f'/{starting_skill}'

        def explore(current: str, depth: int, path: List[str]) -> List[List[str]]:
            if depth >= max_depth:
                return [path]

            next_skills = self.suggest_parser.get_suggestions(current)
            workflows = []

            for next_skill in next_skills:
                new_path = path + [next_skill]
                workflows.extend(explore(next_skill, depth + 1, new_path))

            return workflows if workflows else [path]

        return explore(starting_skill, 0, [starting_skill])

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a skill."""
        if not skill_name.startswith('/'):
            skill_name = f'/{skill_name}'

        metadata = self.suggest_parser.get_skill_metadata(skill_name)
        suggestions = self.suggest_parser.get_suggestions(skill_name)

        # Find what skills suggest this skill
        reverse_suggestions = []
        for from_skill, to_skills in self.suggest_parser.get_graph().items():
            if skill_name in to_skills:
                reverse_suggestions.append(from_skill)

        return {
            "skill": skill_name,
            "metadata": metadata,
            "suggests": suggestions,
            "suggested_by": reverse_suggestions,
            "is_python_orchestrator": skill_name in self.skill_router.PYTHON_ORCHESTRATORS,
            "is_strategic": skill_name in self.STRATEGIC_SKILLS,
            "is_quality_skill": self.quality_pipeline.is_quality_skill(skill_name),
            "quality_category": self.quality_pipeline.get_quality_category(skill_name)
        }

    # ==================== QUALITY PIPELINE API (Phase 2) ====================

    def get_quality_skills(self) -> Dict[str, List[str]]:
        """Get all quality skills by category."""
        return self.quality_pipeline.get_quality_skills()

    def get_recommended_quality_workflow(self, workflow_type: str = 'standard') -> List[str]:
        """
        Get recommended quality workflow for a given type.

        Args:
            workflow_type: Type of workflow (standard, deep, regression, optimization, etc.)

        Returns:
            List of skills in recommended order
        """
        return self.quality_pipeline.get_recommended_workflow(workflow_type)

    def validate_quality_workflow(self, workflow: List[str]) -> Dict[str, Any]:
        """
        Validate a quality workflow sequence.

        Args:
            workflow: List of skill names in order

        Returns:
            Validation result with issues and recommendations
        """
        return self.quality_pipeline.validate_quality_workflow(workflow)

    def get_quality_pipeline_summary(self) -> Dict[str, Any]:
        """Get comprehensive quality pipeline summary."""
        return self.quality_pipeline.get_quality_summary()

    def record_quality_metrics(
        self,
        skill_name: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Record quality metrics for a skill execution.

        Args:
            skill_name: Skill that was executed
            metrics: Metrics data (tests passed, coverage, issues found, etc.)
        """
        self.quality_pipeline.record_quality_metrics(skill_name, metrics)

    def get_quality_metrics(self, skill_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quality metrics for a skill or all skills.

        Args:
            skill_name: Specific skill to query, or None for all

        Returns:
            Metrics data
        """
        return self.quality_pipeline.get_quality_metrics(skill_name)

    def get_next_quality_skills(self, current_skill: str) -> List[str]:
        """
        Get recommended next skills in quality pipeline.

        Args:
            current_skill: Current skill in workflow

        Returns:
            List of recommended next skills
        """
        return self.quality_pipeline.get_next_quality_skills(current_skill)

    # ==================== AGENT PERFORMANCE API (Circuit Breaker) ====================

    def get_agent_performance_stats(self) -> Dict[str, Any]:
        """Get aggregated agent performance statistics."""
        return self.agent_logger.get_performance_stats()

    def get_bad_agent_patterns(self, min_count: int = 2, timeout_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Get agent-task patterns with high timeout/failure rates.

        Args:
            min_count: Minimum executions before flagging as bad pattern
            timeout_threshold: Timeout rate above which to flag (0.5 = 50%)

        Returns:
            List of bad patterns with recommendations
        """
        return self.agent_logger.get_bad_patterns(min_count=min_count, timeout_threshold=timeout_threshold)

    def recommend_agent_strategy(
        self,
        task_type: str,
        lines_of_code: int,
        file_count: int = 1,
        preferred_agent: str | None = None,
    ) -> Dict[str, Any]:
        """
        Recommend execution strategy based on historical performance.

        Args:
            task_type: Type of task (e.g., "refactor", "implement")
            lines_of_code: Lines of code in target file
            file_count: Number of files involved
            preferred_agent: Preferred agent type (if any)

        Returns:
            Recommendation dict with strategy, agent, timeout, and rationale
        """
        return self.agent_logger.recommend_strategy(
            task_type=task_type,
            lines_of_code=lines_of_code,
            file_count=file_count,
            preferred_agent=preferred_agent,
        )


# Singleton instance
master_orchestrator = MasterSkillOrchestrator()
