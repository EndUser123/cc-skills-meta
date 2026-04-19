"""
Phase 4: Error Recovery + Git Ops Integration

Extends MasterSkillOrchestrator with error recovery and git operations capabilities.
This is loaded as a separate module to avoid file locking issues.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from error_recovery import (
    ErrorRecoveryEngine,
    ErrorCategory,
    GitOperation,
    get_error_recovery_engine
)


class ErrorRecoveryMixin:
    """
    Mixin class that adds Phase 4 Error Recovery + Git Ops capabilities
    to the MasterSkillOrchestrator.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize error recovery engine with suggest graph
        graph = self.suggest_parser.load_all_skills()
        self.error_recovery = get_error_recovery_engine(graph)

    # Error Classification
    def classify_error(self, error_message: str) -> str:
        """Classify an error message into a recovery category."""
        return self.error_recovery.classify_error(error_message)

    # Recovery Path Selection
    def select_recovery_path(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """Select recovery path based on error analysis."""
        return self.error_recovery.select_recovery_path(error)

    # Recovery Loop Detection
    def detect_recovery_loop(self, error_history: List[Dict[str, Any]]) -> bool:
        """Detect if we're in a recovery loop."""
        return self.error_recovery.detect_recovery_loop(error_history)

    # Recovery Escalation
    def escalate_recovery(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate to /rca after failed recovery attempts."""
        return self.error_recovery.escalate_recovery(error)

    # Oops Workflow Detection
    def needs_oops_workflow(self, context: Dict[str, Any]) -> bool:
        """Detect when /r workflow is needed."""
        return self.error_recovery.needs_oops_workflow(context)

    # Recovery Workflow Execution
    def execute_recovery_workflow(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a complete error recovery workflow."""
        return self.error_recovery.execute_recovery_workflow(error)

    # Pre-commit Validation
    def validate_pre_commit(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate before git commit."""
        return self.error_recovery.validate_pre_commit(changes)

    # Git State
    def get_git_state(self) -> Dict[str, Any]:
        """Get git repository state."""
        return self.error_recovery.get_git_state()

    # Safe Commit Planning
    def plan_safe_commit(self, commit_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Plan safe commit workflow with validation."""
        return self.error_recovery.plan_safe_commit(commit_plan)

    # Git Operation Routing
    def route_git_operation(self, operation: str, context: Dict[str, Any]) -> str:
        """Route to appropriate git skill."""
        return self.error_recovery.route_git_operation(operation, context)

    # Merge Conflict Detection
    def has_merge_conflicts(self, git_state: Dict[str, Any]) -> bool:
        """Check if there are merge conflicts."""
        return self.error_recovery.has_merge_conflicts(git_state)

    # Commit Message Validation
    def validate_commit_message(self, message: str) -> Dict[str, Any]:
        """Validate commit message format."""
        return self.error_recovery.validate_commit_message(message)

    # Pre-push Quality Gate
    def run_pre_push_quality_gate(self, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Run quality gate before pushing."""
        return self.error_recovery.run_pre_push_quality_gate(changes)

    # Git Safety Check
    def check_git_safety(self, operation: str) -> Dict[str, Any]:
        """Check git operation safety."""
        return self.error_recovery.check_git_safety(operation)

    # Workflow with Git Planning
    def plan_workflow_with_git(self, workflow_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Plan workflow including git operations."""
        return self.error_recovery.plan_workflow_with_git(workflow_plan)

    # Post-Recovery Git Planning
    def plan_post_recovery_git(self, recovery_result: Dict[str, Any]) -> Dict[str, Any]:
        """Plan git operations after successful recovery."""
        return self.error_recovery.plan_post_recovery_git(recovery_result)

    # Rollback Planning
    def plan_rollback(self, failure_context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan rollback workflow when fixes fail."""
        return self.error_recovery.plan_rollback(failure_context)

    # Error Recording
    def record_error(
        self,
        error_type: str,
        message: str,
        recovery_attempted: str,
        success: bool,
        file: Optional[str] = None,
        line: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record an error for tracking."""
        self.error_recovery.record_error(
            error_type, message, recovery_attempted, success, file, line, context
        )

    # Error History
    def get_error_history(self) -> List[Dict[str, Any]]:
        """Get all recorded errors."""
        return self.error_recovery.get_error_history()

    # Recovery Statistics
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        return self.error_recovery.get_recovery_stats()


# Factory function to create orchestrator with Phase 4 capabilities
def create_error_recovery_orchestrator(base_orchestrator_class):
    """
    Create an orchestrator class with Phase 4 Error Recovery + Git Ops capabilities.

    Usage:
        from orchestrator import MasterSkillOrchestrator
        from phase4_error_recovery import create_error_recovery_orchestrator

        ErrorRecoveryOrchestrator = create_error_recovery_orchestrator(MasterSkillOrchestrator)
        orchestrator = ErrorRecoveryOrchestrator()
    """
    class ErrorRecoveryOrchestrator(ErrorRecoveryMixin, base_orchestrator_class):
        """Orchestrator with Phase 4 Error Recovery + Git Ops capabilities."""
        pass

    return ErrorRecoveryOrchestrator


# Factory function for Phase 3 + 4 combined orchestrator
def create_full_orchestrator(base_orchestrator_class):
    """
    Create an orchestrator with both Phase 3 Decision Engine and Phase 4 Error Recovery.

    Usage:
        from orchestrator import MasterSkillOrchestrator
        from phase4_error_recovery import create_full_orchestrator

        FullOrchestrator = create_full_orchestrator(MasterSkillOrchestrator)
        orchestrator = FullOrchestrator()
    """
    # Import Phase 3 mixin
    from phase3_decision_engine import DecisionEngineMixin

    class FullOrchestrator(ErrorRecoveryMixin, DecisionEngineMixin, base_orchestrator_class):
        """Orchestrator with Phase 3 Decision Engine and Phase 4 Error Recovery capabilities."""
        pass

    return FullOrchestrator
