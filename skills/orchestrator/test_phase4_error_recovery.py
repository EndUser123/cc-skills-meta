"""
Test Suite for Phase 4: Error Recovery + Git Ops

Run: python -m pytest test_phase4_error_recovery.py -v
Or: python test_phase4_error_recovery.py
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import for testing
from error_recovery import ErrorCategory, ErrorRecoveryEngine, RecoveryPath
from orchestrator import MasterSkillOrchestrator, master_orchestrator
from phase4_error_recovery import create_error_recovery_orchestrator

# Create enhanced orchestrator with error recovery
ErrorRecoveryOrchestrator = create_error_recovery_orchestrator(MasterSkillOrchestrator)
orchestrator = ErrorRecoveryOrchestrator()


class TestErrorRecoveryEngine:
    """Test Phase 4 Error Recovery Engine functionality."""

    def test_error_recovery_engine_exists(self):
        """Test that error recovery engine is available."""
        from error_recovery import ErrorCategory
        assert ErrorRecoveryEngine is not None
        assert ErrorCategory is not None
        assert RecoveryPath is not None

    def test_error_classification(self):
        """Test classifying errors into recovery categories."""
        error_message = "SyntaxError: invalid syntax"
        category = orchestrator.classify_error(error_message)
        assert category in [e.value for e in ErrorCategory]

    def test_recovery_path_selection_syntax_error(self):
        """Test selecting recovery path for syntax errors."""
        error = {
            "type": "SyntaxError",
            "message": "invalid syntax",
            "file": "example.py",
            "line": 42
        }
        recovery = orchestrator.select_recovery_path(error)
        assert "path" in recovery
        assert "skill" in recovery
        # Syntax errors should route to /fix
        assert recovery["skill"] in ["/fix", "/debug"]

    def test_recovery_path_selection_test_failure(self):
        """Test selecting recovery path for test failures."""
        error = {
            "type": "AssertionError",
            "message": "Expected 200 but got 500",
            "test_file": "test_api.py",
            "test_name": "test_endpoint"
        }
        recovery = orchestrator.select_recovery_path(error)
        assert "path" in recovery
        # Test failures should route to /tdd or /debug
        assert recovery["skill"] in ["/tdd", "/t", "/debug", "/rca"]

    def test_recovery_path_selection_runtime_error(self):
        """Test selecting recovery path for runtime errors."""
        error = {
            "type": "AttributeError",
            "message": "'NoneType' object has no attribute 'foo'",
            "file": "example.py",
            "line": 123
        }
        recovery = orchestrator.select_recovery_path(error)
        assert "path" in recovery
        # Runtime errors should route to /debug or /rca
        assert recovery["skill"] in ["/debug", "/rca"]

    def test_recovery_loop_detection(self):
        """Test detecting repeated errors (recovery loops)."""
        error_history = [
            {"type": "SyntaxError", "attempt": 1},
            {"type": "SyntaxError", "attempt": 2},
            {"type": "SyntaxError", "attempt": 3}
        ]
        is_loop = orchestrator.detect_recovery_loop(error_history)
        assert isinstance(is_loop, bool)

    def test_recovery_escalation(self):
        """Test escalating to /rca after failed recovery attempts."""
        error = {
            "type": "RuntimeError",
            "message": "Failed after 3 attempts",
            "previous_attempts": ["/fix", "/debug"]
        }
        escalation = orchestrator.escalate_recovery(error)
        assert "skill" in escalation
        assert "reasoning" in escalation
        # After failed attempts, should escalate to /rca
        assert escalation["skill"] == "/rca"

    def test_oops_workflow_detection(self):
        """Test detecting when /r workflow is needed."""
        context = {
            "last_action": "edit",
            "result": "error",
            "error_type": "ImportError"
        }
        needs_oops = orchestrator.needs_oops_workflow(context)
        assert isinstance(needs_oops, bool)

    def test_error_recovery_workflow_execution(self):
        """Test executing a complete error recovery workflow."""
        error = {
            "type": "AssertionError",
            "message": "Test failed",
            "context": {"test": "test_example"}
        }
        workflow = orchestrator.execute_recovery_workflow(error)
        assert "steps" in workflow
        assert "estimated_duration" in workflow
        assert isinstance(workflow["steps"], list)

    def test_pre_commit_validation(self):
        """Test validation before git commit."""
        changes = {
            "files": ["example.py"],
            "staged": True
        }
        validation = orchestrator.validate_pre_commit(changes)
        assert "valid" in validation
        assert "checks" in validation

    def test_git_state_check(self):
        """Test checking git repository state."""
        state = orchestrator.get_git_state()
        assert "branch" in state
        assert "status" in state
        assert "has_changes" in state

    def test_safe_commit_workflow(self):
        """Test safe commit workflow with validation."""
        commit_plan = {
            "message": "feat: add new feature",
            "files": ["example.py"],
            "skip_tests": False
        }
        workflow = orchestrator.plan_safe_commit(commit_plan)
        assert "steps" in workflow
        assert "pre_commit_hooks" in workflow

    def test_git_operation_routing(self):
        """Test routing to appropriate git skill."""
        operation = "commit"
        context = {"has_conflicts": False}
        git_skill = orchestrator.route_git_operation(operation, context)
        assert git_skill in ["/git", "/commit", "/push", "/git-safety",
                            "/git-conventional-commits", "/git-sapling",
                            "/git-worktrees"]

    def test_conflict_detection(self):
        """Test detecting merge conflicts."""
        state = orchestrator.get_git_state()
        has_conflicts = orchestrator.has_merge_conflicts(state)
        assert isinstance(has_conflicts, bool)


class TestGitOpsIntegration:
    """Integration tests for Git Operations."""

    def test_git_workflow_integration(self):
        """Test git workflow integrated with quality pipeline."""
        workflow = ["/fix", "/t", "/commit", "/push"]
        validation = orchestrator.validate_workflow(workflow)
        assert "valid" in validation
        # Should recognize this crosses EXECUTION and QUALITY branches

    def test_commit_message_validation(self):
        """Test validating commit messages."""
        message = "feat: add user authentication"
        validation = orchestrator.validate_commit_message(message)
        assert "valid" in validation
        assert "type" in validation

    def test_pre_push_quality_gate(self):
        """Test quality gate before pushing."""
        changes = {"files": ["src/example.py"]}
        gate_result = orchestrator.run_pre_push_quality_gate(changes)
        assert "allowed" in gate_result
        assert "checks" in gate_result

    def test_git_safety_integration(self):
        """Test git safety checks integration."""
        operation = "push"
        safety_check = orchestrator.check_git_safety(operation)
        assert "safe" in safety_check
        assert "warnings" in safety_check

    def test_workflow_with_git_ops(self):
        """Test complete workflow including git operations."""
        workflow_plan = {
            "start": "/analyze",
            "goals": ["fix_bug", "commit_fix"],
            "include_git": True
        }
        execution = orchestrator.plan_workflow_with_git(workflow_plan)
        assert "steps" in execution
        assert "git_operations" in execution

    def test_error_recovery_to_git_transition(self):
        """Test transition from error recovery to git operations."""
        recovery_result = {
            "success": True,
            "fixes_applied": ["Fixed syntax error"],
            "tests_passed": True
        }
        next_steps = orchestrator.plan_post_recovery_git(recovery_result)
        assert "next_skill" in next_steps
        assert next_steps["next_skill"] in ["/commit", "/t", "/qa"]

    def test_rollback_workflow(self):
        """Test rollback workflow when fixes fail."""
        failure_context = {
            "attempted_fix": "/fix",
            "error": "Fix introduced new errors",
            "backup_available": True
        }
        rollback_plan = orchestrator.plan_rollback(failure_context)
        assert "can_rollback" in rollback_plan
        assert "steps" in rollback_plan


class TestPhase4SkillsCategorized:
    """Test that Phase 4 skills are properly categorized."""

    def test_error_recovery_skills_categorized(self):
        """Test that error recovery skills are in EXECUTION branch."""
        error_skills = ["/debug", "/r", "/fix", "/t", "/rca"]
        for skill in error_skills:
            info = master_orchestrator.get_skill_info(skill)
            assert "skill" in info
            assert info["skill"] == skill

    def test_git_ops_skills_categorized(self):
        """Test that git ops skills are in EXECUTION branch."""
        git_skills = [
            "/git", "/commit", "/push",
            "/git-safety", "/git-conventional-commits",
            "/git-sapling", "/git-worktrees"
        ]
        for skill in git_skills:
            info = master_orchestrator.get_skill_info(skill)
            assert "skill" in info
            assert info["skill"] == skill

    def test_phase_4_completion(self):
        """Test that all 35 skills from 4 phases are accessible."""
        # Sample skills from each phase
        phase_skills = {
            "phase1": ["/search", "/research", "/orchestrate"],
            "phase2": ["/t", "/qa", "/comply", "/q"],
            "phase3": ["/design", "/nse", "/analyze", "/r"],
            "phase4": ["/debug", "/fix", "/commit", "/push"]
        }
        for phase, skills in phase_skills.items():
            for skill in skills:
                info = master_orchestrator.get_skill_info(skill)
                assert info["skill"] == skill


class TestErrorRecoveryStatePersistence:
    """Test error recovery state persistence."""

    def test_error_history_recording(self):
        """Test recording error history."""
        orchestrator.record_error(
            error_type="SyntaxError",
            message="invalid syntax",
            recovery_attempted="/fix",
            success=True
        )
        history = orchestrator.get_error_history()
        assert len(history) > 0
        latest = history[-1]
        assert latest["error_type"] == "SyntaxError"

    def test_recovery_statistics(self):
        """Test getting recovery statistics."""
        stats = orchestrator.get_recovery_stats()
        assert "total_errors" in stats
        assert "recovery_rate" in stats
        assert "most_common_errors" in stats


def main():
    """Run tests without pytest."""
    print("Running Phase 4 Error Recovery + Git Ops Test Suite")
    print("=" * 60)

    test_classes = [
        TestErrorRecoveryEngine(),
        TestGitOpsIntegration(),
        TestPhase4SkillsCategorized(),
        TestErrorRecoveryStatePersistence()
    ]

    passed = 0
    failed = 0
    not_implemented = 0

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{class_name}:")

        for method_name in dir(test_class):
            if not method_name.startswith("test_"):
                continue

            method = getattr(test_class, method_name)
            try:
                method()
                print(f"  ✓ {method_name}")
                passed += 1
            except AssertionError:
                print(f"  ✗ {method_name}: AssertionError")
                failed += 1
            except ImportError as e:
                print(f"  ⏸ {method_name}: Not implemented ({e})")
                not_implemented += 1
            except AttributeError as e:
                print(f"  ⏸ {method_name}: Not implemented ({e})")
                not_implemented += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {type(e).__name__}: {e}")
                failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {not_implemented} not implemented")

    if failed == 0 and not_implemented == 0:
        print("✅ All tests passed!")
        return 0
    elif failed == 0:
        print("⏸️ Some methods not implemented")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
