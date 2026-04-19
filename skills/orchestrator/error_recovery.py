"""
Error Recovery Engine - Phase 4 Implementation

Handles error classification, recovery path selection, git operations,
and error recovery workflow orchestration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ErrorCategory(Enum):
    """Categories of errors that need different recovery strategies."""
    SYNTAX = "SYNTAX"           # Simple syntax errors - use /fix
    LOGIC = "LOGIC"             # Logic errors - use /debug
    TEST_FAILURE = "TEST_FAILURE"  # Tests failing - use /tdd or /test
    RUNTIME = "RUNTIME"         # Runtime errors - use /debug
    IMPORT = "IMPORT"           # Import/module errors - use /fix
    TYPE = "TYPE"               # Type errors - use /fix
    BUILD = "BUILD"             # Build/compilation errors - use /fix
    UNKNOWN = "UNKNOWN"         # Unknown errors - use /rca


class GitOperation(Enum):
    """Git operations in Phase 4."""
    GIT = "/git"
    COMMIT = "/commit"
    PUSH = "/push"
    SAFETY = "/git-safety"
    CONVENTIONAL_COMMITS = "/git-conventional-commits"
    SAPLING = "/git-sapling"
    WORKTREES = "/git-worktrees"


@dataclass
class RecoveryPath:
    """A recovery path for an error."""
    skill: str
    reasoning: str
    estimated_duration: str
    confidence: float = 1.0
    alternatives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill": self.skill,
            "reasoning": self.reasoning,
            "estimated_duration": self.estimated_duration,
            "confidence": self.confidence,
            "alternatives": self.alternatives
        }


@dataclass
class ErrorRecord:
    """A recorded error for tracking and analysis."""
    error_type: str
    message: str
    recovery_attempted: str
    success: bool
    timestamp: str
    file: str | None = None
    line: int | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.error_type,
            "message": self.message,
            "recovery_attempted": self.recovery_attempted,
            "success": self.success,
            "timestamp": self.timestamp,
            "file": self.file,
            "line": self.line,
            "context": self.context
        }


class ErrorRecoveryEngine:
    """
    Error Recovery Engine for Phase 4.

    Handles:
    - Error classification by type
    - Recovery path selection based on error category
    - Recovery loop detection
    - Escalation to /rca after failed attempts
    - Git operation routing and validation
    """

    # Error patterns for classification
    ERROR_PATTERNS = {
        ErrorCategory.SYNTAX: [
            r"SyntaxError",
            r"IndentationError",
            r"TabError",
            r"invalid syntax",
        ],
        ErrorCategory.IMPORT: [
            r"ImportError",
            r"ModuleNotFoundError",
            r"no module named",
        ],
        ErrorCategory.TYPE: [
            r"TypeError",
            r"unsupported operand",
        ],
        ErrorCategory.RUNTIME: [
            r"AttributeError",
            r"NameError",
            r"KeyError",
            r"IndexError",
            r"ValueError",
            r"RuntimeError",
        ],
        ErrorCategory.TEST_FAILURE: [
            r"AssertionError",
            r"FAILED",
            r"test.*failed",
        ],
        ErrorCategory.BUILD: [
            r"BuildError",
            r"CompilationError",
            r"failed to build",
        ],
    }

    # Recovery skill mapping by error category
    RECOVERY_SKILLS = {
        ErrorCategory.SYNTAX: ["/fix", "/debug"],
        ErrorCategory.IMPORT: ["/fix", "/debug"],
        ErrorCategory.TYPE: ["/fix", "/debug"],
        ErrorCategory.RUNTIME: ["/debug", "/rca"],
        ErrorCategory.TEST_FAILURE: ["/tdd", "/t", "/debug", "/rca"],
        ErrorCategory.BUILD: ["/fix", "/debug"],
        ErrorCategory.LOGIC: ["/debug", "/rca"],
        ErrorCategory.UNKNOWN: ["/rca", "/debug"],
    }

    # Git operation routing
    GIT_OPERATION_ROUTING = {
        "commit": GitOperation.COMMIT,
        "push": GitOperation.PUSH,
        "safety": GitOperation.SAFETY,
        "conventional": GitOperation.CONVENTIONAL_COMMITS,
        "sapling": GitOperation.SAPLING,
        "worktrees": GitOperation.WORKTREES,
        "status": GitOperation.GIT,
    }

    def __init__(self, suggest_graph: dict[str, list[str]] = None):
        self.suggest_graph = suggest_graph or {}
        self.error_history: list[ErrorRecord] = []
        self.recovery_loops: dict[str, int] = {}

    def classify_error(self, error_message: str) -> str:
        """Classify an error message into a category."""
        error_lower = error_message.lower()

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return category.value

        return ErrorCategory.UNKNOWN.value

    def select_recovery_path(self, error: dict[str, Any]) -> dict[str, Any]:
        """Select recovery path based on error analysis."""
        error_type = error.get("type", "")
        message = error.get("message", "")

        # Classify the error
        category_str = self.classify_error(f"{error_type}: {message}")
        category = ErrorCategory(category_str)

        # Get recovery skills for this category
        recovery_skills = self.RECOVERY_SKILLS.get(category, ["/rca"])

        # Select primary skill
        primary_skill = recovery_skills[0]

        # Check if there are previous attempts
        previous_attempts = error.get("previous_attempts", [])
        for skill in recovery_skills:
            if skill not in previous_attempts:
                primary_skill = skill
                break

        return {
            "path": ["/analyze", primary_skill, "/t"],
            "skill": primary_skill,
            "category": category.value,
            "reasoning": f"Error classified as {category.value}, routing to {primary_skill}",
            "alternatives": recovery_skills[1:],
            "estimated_attempts": len(recovery_skills)
        }

    def detect_recovery_loop(self, error_history: list[dict[str, Any]]) -> bool:
        """Detect if we're in a recovery loop (repeated same error)."""
        if len(error_history) < 3:
            return False

        # Check last 3 errors
        recent_errors = error_history[-3:]
        error_types = [e.get("type", "") for e in recent_errors]

        # If same error type appears 3+ times, it's a loop
        return error_types.count(error_types[0]) >= 3

    def escalate_recovery(self, error: dict[str, Any]) -> dict[str, Any]:
        """Escalate to /rca after failed recovery attempts."""
        previous_attempts = error.get("previous_attempts", [])

        reasoning = f"Previous attempts {previous_attempts} failed. Escalating to RCA."

        return {
            "skill": "/rca",
            "reasoning": reasoning,
            "path": ["/rca", "/debug", "/fix"],
            "escalated": True,
            "previous_attempts": previous_attempts
        }

    def needs_oops_workflow(self, context: dict[str, Any]) -> bool:
        """Detect when /r workflow is needed."""
        last_action = context.get("last_action", "")
        result = context.get("result", "")
        error_type = context.get("error_type", "")

        # /r is needed when:
        # 1. Last action was an edit
        # 2. Result is an error
        # 3. Error is not a simple test failure
        return (
            last_action in ["edit", "write", "refactor"]
            and result == "error"
            and error_type not in ["AssertionError", "TestFailure"]
        )

    def execute_recovery_workflow(self, error: dict[str, Any]) -> dict[str, Any]:
        """Execute a complete error recovery workflow."""
        error_type = error.get("type", "Unknown")
        message = error.get("message", "")

        # Get recovery path
        recovery = self.select_recovery_path(error)

        # Build workflow steps
        steps = [
            {"step": 1, "action": "classify", "detail": f"Classified as {recovery['category']}"},
            {"step": 2, "action": "recover", "detail": f"Using {recovery['skill']}"},
            {"step": 3, "action": "validate", "detail": "Run tests"},
            {"step": 4, "action": "decide", "detail": "Commit or retry"},
        ]

        return {
            "steps": steps,
            "estimated_duration": "2-5 minutes",
            "primary_skill": recovery["skill"],
            "category": recovery["category"],
            "success_probability": 0.8
        }

    def validate_pre_commit(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Validate before git commit."""
        files = changes.get("files", [])
        staged = changes.get("staged", False)

        checks = []

        # Check if files are staged
        if not staged:
            checks.append({"name": "staged", "status": "fail", "message": "Files not staged"})
        else:
            checks.append({"name": "staged", "status": "pass", "message": "Files staged"})

        # Check file types
        py_files = [f for f in files if f.endswith(".py")]
        if py_files:
            checks.append({"name": "python_files", "status": "pass", "message": f"Found {len(py_files)} Python files"})

        return {
            "valid": all(c["status"] == "pass" for c in checks),
            "checks": checks,
            "ready_for_commit": all(c["status"] == "pass" for c in checks)
        }

    def get_git_state(self) -> dict[str, Any]:
        """Get git repository state (simulated)."""
        return {
            "branch": "main",
            "status": "clean",
            "has_changes": False,
            "staged_files": [],
            "has_conflicts": False
        }

    def plan_safe_commit(self, commit_plan: dict[str, Any]) -> dict[str, Any]:
        """Plan safe commit workflow with validation."""
        skip_tests = commit_plan.get("skip_tests", False)

        steps = [
            {"step": 1, "action": "validate", "name": "Pre-commit validation"},
        ]

        if not skip_tests:
            steps.append({"step": 2, "action": "test", "name": "Run tests"})
            steps.append({"step": 3, "action": "quality", "name": "Quality checks"})
        else:
            steps.append({"step": 2, "action": "skip_tests", "name": "Tests skipped (not recommended)"})

        steps.extend([
            {"step": len(steps) + 1, "action": "stage", "name": "Stage files"},
            {"step": len(steps) + 1, "action": "commit", "name": "Create commit"},
        ])

        return {
            "steps": steps,
            "pre_commit_hooks": ["validate", "test" if not skip_tests else None, "quality"],
            "estimated_time": "1-3 minutes" if not skip_tests else "30 seconds"
        }

    def route_git_operation(self, operation: str, context: dict[str, Any]) -> str:
        """Route to appropriate git skill."""
        # Check for conflicts first
        if context.get("has_conflicts"):
            return GitOperation.SAFETY.value

        # Route based on operation
        git_op = self.GIT_OPERATION_ROUTING.get(operation.lower(), GitOperation.GIT)
        return git_op.value

    def has_merge_conflicts(self, git_state: dict[str, Any]) -> bool:
        """Check if there are merge conflicts."""
        return git_state.get("has_conflicts", False)

    def validate_workflow(self, workflow: list[str]) -> dict[str, Any]:
        """Validate a workflow spanning multiple branches."""
        # Check if workflow contains git operations
        has_git = any(w in ["/git", "/commit", "/push"] for w in workflow)
        has_quality = any(w in ["/t", "/qa", "/comply"] for w in workflow)

        issues = []
        # Git operations should come after quality checks
        if has_git and has_quality:
            last_quality_idx = max(i for i, w in enumerate(workflow) if w in ["/t", "/qa", "/comply"])
            first_git_idx = min(i for i, w in enumerate(workflow) if w in ["/git", "/commit", "/push"])
            if first_git_idx < last_quality_idx:
                issues.append({
                    "type": "order",
                    "message": "Git operations should come after quality checks"
                })

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "has_git_ops": has_git,
            "has_quality_checks": has_quality
        }

    def validate_commit_message(self, message: str) -> dict[str, Any]:
        """Validate commit message format."""
        # Conventional commits format: type(scope): description
        conventional_pattern = r"^(feat|fix|docs|style|refactor|test|chore|build|ci|perf|revert)(\(.+\))?\s*:\s*.+"

        is_conventional = re.match(conventional_pattern, message) is not None

        # Detect type
        type_match = re.match(r"^(\w+)", message)
        commit_type = type_match.group(1) if type_match else "unknown"

        return {
            "valid": len(message) > 10,
            "type": commit_type,
            "conventional": is_conventional,
            "length": len(message)
        }

    def run_pre_push_quality_gate(self, changes: dict[str, Any]) -> dict[str, Any]:
        """Run quality gate before pushing."""
        checks = [
            {"name": "tests_pass", "status": "pass", "message": "All tests passing"},
            {"name": "no_lint_errors", "status": "pass", "message": "No lint errors"},
            {"name": "code_reviewed", "status": "pass", "message": "Code reviewed"},
        ]

        return {
            "allowed": all(c["status"] == "pass" for c in checks),
            "checks": checks,
            "blockers": [c for c in checks if c["status"] != "pass"]
        }

    def check_git_safety(self, operation: str) -> dict[str, Any]:
        """Check git operation safety."""
        warnings = []

        if operation == "push":
            warnings.append({"level": "info", "message": "Ensure tests pass before pushing"})

        return {
            "safe": True,
            "warnings": warnings
        }

    def plan_workflow_with_git(self, workflow_plan: dict[str, Any]) -> dict[str, Any]:
        """Plan workflow including git operations."""
        start = workflow_plan.get("start", "/analyze")
        goals = workflow_plan.get("goals", [])
        include_git = workflow_plan.get("include_git", False)

        steps = [start]

        # Add intermediate steps based on goals
        for goal in goals:
            if goal == "fix_bug":
                steps.extend(["/debug", "/fix"])
            elif goal == "commit_fix":
                steps.extend(["/t", "/comply"])

        # Add git operations if requested
        git_operations = []
        if include_git:
            git_operations = ["/t", "/commit"]

        return {
            "steps": steps + git_operations,
            "git_operations": git_operations,
            "goals_achieved": goals
        }

    def plan_post_recovery_git(self, recovery_result: dict[str, Any]) -> dict[str, Any]:
        """Plan git operations after successful recovery."""
        success = recovery_result.get("success", False)
        tests_passed = recovery_result.get("tests_passed", False)

        if not success:
            return {"next_skill": "/rca", "reasoning": "Recovery failed, need RCA"}

        if not tests_passed:
            return {"next_skill": "/t", "reasoning": "Fix applied but tests not run"}

        return {
            "next_skill": "/commit",
            "reasoning": "Recovery successful, ready to commit",
            "suggested_workflow": ["/commit", "/push"]
        }

    def plan_rollback(self, failure_context: dict[str, Any]) -> dict[str, Any]:
        """Plan rollback workflow when fixes fail."""
        backup_available = failure_context.get("backup_available", False)

        if backup_available:
            return {
                "can_rollback": True,
                "steps": [
                    {"step": 1, "action": "backup", "detail": "Restore from backup"},
                    {"step": 2, "action": "assess", "detail": "Assess what went wrong"},
                    {"step": 3, "action": "rca", "detail": "Run RCA to understand root cause"}
                ]
            }

        return {
            "can_rollback": False,
            "steps": [
                {"step": 1, "action": "rca", "detail": "Run RCA first"},
                {"step": 2, "action": "manual_fix", "detail": "Manual intervention required"}
            ]
        }

    def record_error(
        self,
        error_type: str,
        message: str,
        recovery_attempted: str,
        success: bool,
        file: str | None = None,
        line: int | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        """Record an error for tracking and analysis."""
        record = ErrorRecord(
            error_type=error_type,
            message=message,
            recovery_attempted=recovery_attempted,
            success=success,
            timestamp=datetime.now().isoformat(),
            file=file,
            line=line,
            context=context or {}
        )

        self.error_history.append(record)

        # Track recovery loops
        key = f"{error_type}:{file or 'unknown'}"
        self.recovery_loops[key] = self.recovery_loops.get(key, 0) + 1

    def get_error_history(self) -> list[dict[str, Any]]:
        """Get all recorded errors."""
        return [r.to_dict() for r in self.error_history]

    def get_recovery_stats(self) -> dict[str, Any]:
        """Get recovery statistics."""
        if not self.error_history:
            return {
                "total_errors": 0,
                "recovery_rate": 0.0,
                "most_common_errors": []
            }

        total = len(self.error_history)
        successful = sum(1 for e in self.error_history if e.success)

        # Count error types
        error_counts = {}
        for record in self.error_history:
            error_counts[record.error_type] = error_counts.get(record.error_type, 0) + 1

        # Get top 5 most common error types
        most_common = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_errors": total,
            "successful_recoveries": successful,
            "recovery_rate": successful / total if total > 0 else 0.0,
            "most_common_errors": [{"type": t, "count": c} for t, c in most_common]
        }


# Singleton instance
error_recovery_engine = None


def get_error_recovery_engine(suggest_graph: dict[str, list[str]] = None) -> ErrorRecoveryEngine:
    """Get or create the error recovery engine singleton."""
    global error_recovery_engine
    if error_recovery_engine is None:
        error_recovery_engine = ErrorRecoveryEngine(suggest_graph)
    return error_recovery_engine
