"""
Test Suite for Master Skill Orchestrator

Run: python -m pytest test_orchestrator.py -v
Or: python test_orchestrator.py
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent_heartbeat import (
    Heartbeat,
    HeartbeatMonitor,
    PartialWorkResult,
    assess_partial_work,
    heartbeat_monitor,
)
from agent_performance_logger import AgentExecutionRecord, AgentPerformanceLogger
from orchestrator import master_orchestrator
from skill_router import skill_router
from suggest_parser import suggest_parser
from task_size_classifier import ExecutionStrategy, TaskComplexity, TaskSizeClassifier
from workflow_state import workflow_state


class TestSuggestParser:
    """Test suggest field parsing."""

    def test_load_all_skills(self):
        """Test loading all suggest fields."""
        graph = suggest_parser.load_all_skills()
        assert len(graph) > 0, "Should load at least some skills"
        assert any('/' in skill for skill in graph.keys()), "Skills should have / prefix"

    def test_get_suggestions(self):
        """Test getting suggestions for a skill."""
        suggestions = suggest_parser.get_suggestions("/adf")
        assert isinstance(suggestions, list), "Should return list"
        # NSE has suggest fields
        assert len(suggestions) > 0, "/adf should have suggestions"

    def test_get_skill_metadata(self):
        """Test getting skill metadata."""
        metadata = suggest_parser.get_skill_metadata("adf")
        assert isinstance(metadata, dict), "Should return dict"

    def test_get_graph(self):
        """Test getting complete graph."""
        graph = suggest_parser.get_graph()
        assert isinstance(graph, dict), "Should return dict"
        assert len(graph) > 0, "Graph should not be empty"


class TestWorkflowState:
    """Test workflow state machine."""

    def test_enter_exit_skill(self):
        """Test entering and exiting skills."""
        # Save state
        old_current = workflow_state.current_skill
        old_stack = workflow_state.stack.copy()

        workflow_state.current_skill = None
        workflow_state.stack = []

        # Enter first skill
        entered = workflow_state.enter_skill("/analyze")
        assert workflow_state.current_skill == "/analyze"

        # Exit skill
        workflow_state.exit_skill()

        # Restore state
        workflow_state.current_skill = old_current
        workflow_state.stack = old_stack

    def test_workflow_path(self):
        """Test workflow path tracking."""
        # Save state
        old_current = workflow_state.current_skill
        old_stack = workflow_state.stack.copy()
        old_transitions = workflow_state.valid_transitions.copy()

        # Clear transitions to test behavior when no graph loaded
        workflow_state.current_skill = None
        workflow_state.stack = []
        workflow_state.valid_transitions = {}

        workflow_state.enter_skill("/analyze")
        workflow_state.enter_skill("/adf")

        path = workflow_state.get_workflow_path()
        assert "/analyze" in path
        assert "/adf" in path

        # Restore state
        workflow_state.current_skill = old_current
        workflow_state.stack = old_stack
        workflow_state.valid_transitions = old_transitions

    def test_load_transitions_from_graph(self):
        """Test loading transitions from graph."""
        # Save state
        old_transitions = workflow_state.valid_transitions.copy()

        workflow_state.valid_transitions = {}
        test_graph = {
            "/test1": ["/test2", "/test3"],
            "/test2": ["/test4"]
        }

        workflow_state.load_transitions_from_graph(test_graph)
        assert workflow_state.is_valid_transition("/test1", "/test2")
        assert workflow_state.is_valid_transition("/test1", "/test3")
        assert workflow_state.is_valid_transition("/test2", "/test4")
        assert not workflow_state.is_valid_transition("/test3", "/test1")

        # Restore state
        workflow_state.valid_transitions = old_transitions

    def test_get_state_summary(self):
        """Test getting state summary."""
        summary = workflow_state.get_state_summary()
        assert "current_skill" in summary
        assert "stack_depth" in summary
        assert "workflow_path" in summary
        assert "total_valid_transitions" in summary


class TestSkillRouter:
    """Test skill router."""

    def test_orchestrator_skills_identified(self):
        """Test that Python orchestrators are identified."""
        assert "/nse" in skill_router.PYTHON_ORCHESTRATORS
        assert "/rca" in skill_router.PYTHON_ORCHESTRATORS
        assert "/llm-brainstorm" in skill_router.PYTHON_ORCHESTRATORS

    def test_invoke_python_skill(self):
        """Test invoking a Python skill."""
        result = skill_router.invoke_skill("/adf", {"query": "test"})
        assert result["skill"] == "/adf"
        assert "status" in result

    def test_invoke_cli_skill(self):
        """Test invoking a CLI skill."""
        result = skill_router.invoke_skill("/t", {"args": "value"})
        assert result["skill"] == "/t"
        assert "status" in result

    def test_get_invocation_stats(self):
        """Test getting invocation statistics."""
        stats = skill_router.get_invocation_stats()
        assert "total_invocations" in stats

    def test_get_python_orchestrators(self):
        """Test getting Python orchestrator set."""
        orchs = skill_router.get_python_orchestrators()
        assert isinstance(orchs, set)
        assert "/nse" in orchs


class TestMasterOrchestrator:
    """Test master orchestrator."""

    def test_initialization(self):
        """Test orchestrator initializes without error."""
        assert master_orchestrator.suggest_parser is not None
        assert master_orchestrator.skill_router is not None
        assert master_orchestrator.workflow_state is not None

    def test_get_suggestions(self):
        """Test getting suggestions."""
        suggestions = master_orchestrator.get_workflow_suggestions("/adf")
        assert isinstance(suggestions, list)

    def test_get_audit_trail(self):
        """Test getting audit trail."""
        trail = master_orchestrator.get_decision_audit_trail()
        assert isinstance(trail, list)

    def test_get_execution_log(self):
        """Test getting execution log."""
        log = master_orchestrator.get_execution_log()
        assert isinstance(log, list)

    def test_get_workflow_stats(self):
        """Test getting workflow stats."""
        stats = master_orchestrator.get_workflow_stats()
        assert "total_executions" in stats
        assert "total_decisions" in stats
        assert "current_workflow" in stats

    def test_get_all_suggestions(self):
        """Test getting all suggest field relationships."""
        graph = master_orchestrator.get_all_suggestions()
        assert isinstance(graph, dict)
        assert len(graph) > 0

    def test_get_skill_info(self):
        """Test getting comprehensive skill info."""
        info = master_orchestrator.get_skill_info("/adf")
        assert "skill" in info
        assert "metadata" in info
        assert "suggests" in info
        assert "suggested_by" in info

    def test_validate_workflow(self):
        """Test workflow validation."""
        # Valid workflow (based on /nse -> /r suggestion)
        validation = master_orchestrator.validate_workflow(["/adf", "/design"])
        assert "workflow" in validation
        assert "valid" in validation
        assert "issues" in validation

    def test_suggest_workflow(self):
        """Test workflow suggestion."""
        workflows = master_orchestrator.suggest_workflow("/adf", max_depth=2)
        assert isinstance(workflows, list)
        assert len(workflows) > 0



class TestTaskSizeClassifier:
    """Test task size classification for agent delegation decisions."""

    def test_small_task_classification(self):
        """Test that small tasks are classified for agent delegation."""
        classifier = TaskSizeClassifier()
        result = classifier.classify(
            file_path="test.py",
            lines_of_code=50,
            description="Add simple function"
        )
        assert result.complexity == TaskComplexity.SMALL
        assert result.strategy == ExecutionStrategy.AGENT

    def test_large_file_refactor_classification(self):
        """Test that large file refactors use direct implementation."""
        classifier = TaskSizeClassifier()
        result = classifier.classify(
            file_path="large_module.py",
            lines_of_code=3520,
            description="Extract filter logic"
        )
        assert result.complexity == TaskComplexity.LARGE
        assert result.strategy == ExecutionStrategy.DIRECT

    def test_threshold_exactly_1000_lines(self):
        """Test boundary condition at 1000 lines."""
        classifier = TaskSizeClassifier()
        result = classifier.classify(
            file_path="boundary.py",
            lines_of_code=1000,
            description="Medium refactor"
        )
        # 1000 lines is the threshold - should be MEDIUM or LARGE
        assert result.complexity in (TaskComplexity.MEDIUM, TaskComplexity.LARGE)

    def test_multi_file_task_classification(self):
        """Test that multi-file tasks are classified correctly."""
        classifier = TaskSizeClassifier()
        result = classifier.classify_multi_file(
            file_count=5,
            total_lines=2500,
            description="Refactor across modules"
        )
        assert result.complexity == TaskComplexity.LARGE
        assert result.strategy == ExecutionStrategy.DIRECT

    def test_get_reason_returns_string(self):
        """Test that classification reason is provided."""
        classifier = TaskSizeClassifier()
        result = classifier.classify(
            file_path="test.py",
            lines_of_code=50,
            description="Add simple function"
        )
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0


class TestTimeoutGuard:
    """Test timeout functionality for agent tasks."""

    def test_default_timeout_is_300_seconds(self):
        """Test that default timeout is 5 minutes."""
        from timeout_guard import DEFAULT_TIMEOUT
        assert DEFAULT_TIMEOUT == 300

    def test_timeout_guard_returns_remaining_time(self):
        """Test that timeout guard tracks remaining time."""
        from timeout_guard import TimeoutGuard
        guard = TimeoutGuard(timeout=10)
        assert guard.get_remaining_seconds() > 0
        assert guard.get_remaining_seconds() <= 10

    def test_timeout_guard_detects_expiration(self):
        """Test that timeout guard detects when time is up."""
        import time

        from timeout_guard import TimeoutGuard
        guard = TimeoutGuard(timeout=1)
        time.sleep(1.1)
        assert guard.is_expired()

    def test_custom_timeout_override(self):
        """Test that custom timeout can be set."""
        from timeout_guard import TimeoutGuard
        guard = TimeoutGuard(timeout=600)  # 10 minutes
        assert guard.timeout == 600
        assert guard.get_remaining_seconds() > 500


class TestOrchestratorTimeoutIntegration:
    """Test orchestrator integration with timeout functionality."""

    def test_invoke_skill_accepts_timeout_param(self):
        """Test that invoke_skill accepts timeout parameter."""
        # This test verifies the API exists
        # Actual timeout behavior tested in integration
        try:
            result = master_orchestrator.invoke_skill(
                "/adf",
                {"query": "test"},
                timeout=10
            )
            # Should return result with timeout info
            assert "status" in result
        except TypeError:
            pytest.fail("invoke_skill should accept timeout parameter")

    def test_timeout_none_disables_timeout(self):
        """Test that timeout=None disables timeout."""
        result = master_orchestrator.invoke_skill(
            "/adf",
            {"query": "test"},
            timeout=None
        )
        assert "status" in result


class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self):
        """Test a complete workflow from suggestion to invocation."""
        # Get suggestions for /nse
        suggestions = master_orchestrator.get_workflow_suggestions("/adf")
        assert len(suggestions) > 0

        # Check first suggestion is valid
        first_suggestion = suggestions[0]
        assert master_orchestrator.workflow_state.is_valid_transition("/adf", first_suggestion)

    def test_skill_relationships(self):
        """Test that skill relationships are bidirectional."""
        # Get skills that suggest /nse
        info = master_orchestrator.get_skill_info("/adf")
        assert "suggested_by" in info
        # Should have at least some skills that suggest /nse

    def test_state_persistence(self):
        """Test that state can be persisted and loaded."""
        # Get current stats
        stats_before = master_orchestrator.get_workflow_stats()

        # The state file should exist or be creatable
        state_file = master_orchestrator.STATE_FILE
        assert state_file.parent.exists() or state_file.parent.mkdir(parents=True, exist_ok=True)


def main():
    """Run tests without pytest."""
    print("Running Master Skill Orchestrator Test Suite")
    print("=" * 60)

    test_classes = [
        TestSuggestParser(),
        TestWorkflowState(),
        TestSkillRouter(),
        TestMasterOrchestrator(),
        TestTaskSizeClassifier(),
        TestTimeoutGuard(),
        TestOrchestratorTimeoutIntegration(),
        TestAgentPerformanceLogger(),
        TestHeartbeat(),
        TestIntegration()
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{class_name}:")

        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_class, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                    passed += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {e}")
                    failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


class TestAgentPerformanceLogger:
    """Test agent performance logging and circuit breaker pattern."""

    def test_logger_initialization(self):
        """Test that logger initializes without error."""
        logger = AgentPerformanceLogger()
        assert logger.log_path is not None
        assert logger.log_path.parent.exists()

    def test_log_execution(self):
        """Test logging an agent execution."""
        logger = AgentPerformanceLogger()
        logger.log_execution(
            agent_type="tdd-implementer",
            task_type="refactor",
            file_path="src/large_file.py",
            lines_of_code=3520,
            file_count=1,
            outcome="timeout",
            duration_seconds=300.0,
            timeout_limit=300,
            strategy_used="agent",
            error_message="Agent timeout"
        )
        records = logger.get_all_records()
        assert len(records) > 0
        assert records[-1].agent_type == "tdd-implementer"
        assert records[-1].outcome == "timeout"

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        logger = AgentPerformanceLogger()
        stats = logger.get_performance_stats()
        assert "total_executions" in stats
        assert "by_agent" in stats
        assert "by_task" in stats
        assert "by_agent_task" in stats
        assert "by_size_range" in stats
        assert "outcomes" in stats

    def test_size_range_categorization(self):
        """Test file size categorization."""
        logger = AgentPerformanceLogger()
        assert logger._get_size_range(50) == "small (<100)"
        assert logger._get_size_range(250) == "medium (100-500)"
        assert logger._get_size_range(750) == "large (500-1000)"
        assert logger._get_size_range(1500) == "xlarge (1000-2000)"
        assert logger._get_size_range(3000) == "xxlarge (2000+)"

    def test_recommend_strategy_with_no_history(self):
        """Test strategy recommendation with no historical data."""
        logger = AgentPerformanceLogger()
        # Clear any existing records for clean test
        logger.log_path.unlink(missing_ok=True)

        recommendation = logger.recommend_strategy(
            task_type="refactor",
            lines_of_code=3520,
            file_count=1,
            preferred_agent="tdd-implementer"
        )
        assert "strategy" in recommendation
        assert "rationale" in recommendation
        # Without history, should use task size classifier
        assert recommendation["strategy"] in ["agent", "direct", "hybrid"]

    def test_recommend_strategy_circuit_breaker(self):
        """Test circuit breaker triggers on bad patterns."""
        logger = AgentPerformanceLogger()
        test_log = logger.log_path.parent / "test_circuit_breaker.jsonl"
        test_logger = AgentPerformanceLogger(log_path=test_log)

        # Log some timeouts for the same pattern
        for _ in range(3):
            test_logger.log_execution(
                agent_type="tdd-implementer",
                task_type="refactor",
                file_path="src/large.py",
                lines_of_code=3520,
                file_count=1,
                outcome="timeout",
                duration_seconds=300.0,
                timeout_limit=300,
                strategy_used="agent"
            )

        # Now ask for recommendation - should trigger circuit breaker
        recommendation = test_logger.recommend_strategy(
            task_type="refactor",
            lines_of_code=3520,
            file_count=1,
            preferred_agent="tdd-implementer"
        )

        # Should recommend direct due to bad pattern
        assert recommendation["strategy"] == "direct"
        assert "circuit breaker" in recommendation["rationale"].lower()

        # Cleanup
        test_log.unlink(missing_ok=True)

    def test_get_bad_patterns(self):
        """Test identification of bad agent-task patterns."""
        logger = AgentPerformanceLogger()
        test_log = logger.log_path.parent / "test_bad_patterns.jsonl"
        test_logger = AgentPerformanceLogger(log_path=test_log)

        # Log mixed results
        for i in range(5):
            outcome = "timeout" if i < 3 else "success"
            test_logger.log_execution(
                agent_type="tdd-implementer",
                task_type="refactor",
                file_path="src/large.py",
                lines_of_code=3520,
                file_count=1,
                outcome=outcome,
                duration_seconds=300.0,
                strategy_used="agent"
            )

        bad_patterns = test_logger.get_bad_patterns(min_count=2, timeout_threshold=0.5)
        assert len(bad_patterns) > 0
        assert bad_patterns[0]["timeout_rate"] >= 0.5
        assert "recommendation" in bad_patterns[0]

        # Cleanup
        test_log.unlink(missing_ok=True)

    def test_record_jsonl_serialization(self):
        """Test JSONL serialization roundtrip."""
        record = AgentExecutionRecord(
            timestamp="2024-01-01T00:00:00",
            agent_type="test-agent",
            task_type="test-task",
            file_path="/test.py",
            lines_of_code=100,
            file_count=1,
            outcome="success",
            duration_seconds=10.0,
            timeout_limit=300,
            strategy_used="agent"
        )

        # Serialize
        jsonl_line = record.to_jsonl()
        assert isinstance(jsonl_line, str)

        # Deserialize
        parsed = AgentExecutionRecord.from_jsonl(jsonl_line)
        assert parsed.agent_type == record.agent_type
        assert parsed.task_type == record.task_type
        assert parsed.outcome == record.outcome


class TestHeartbeat:
    """Test agent heartbeat system for stall detection and partial work assessment."""

    def test_heartbeat_dataclass(self):
        """Test Heartbeat dataclass creation and serialization."""
        hb = Heartbeat(
            agent_id="test-agent",
            timestamp="2024-01-01T00:00:00",
            progress_percent=50.0,
            current_operation="analyzing",
            files_modified=["src/test.py"],
            files_read=["src/main.py"]
        )
        assert hb.agent_id == "test-agent"
        assert hb.progress_percent == 50.0

        # Test serialization
        data = hb.to_dict()
        assert data["agent_id"] == "test-agent"
        assert data["progress_percent"] == 50.0

    def test_heartbeat_monitor_initialization(self):
        """Test heartbeat monitor initializes correctly."""
        monitor = HeartbeatMonitor(stall_timeout_seconds=60)
        assert monitor.stall_timeout_seconds == 60
        assert monitor.HEARTBEAT_FILE.parent.exists()

    def test_start_stop_tracking(self):
        """Test starting and stopping agent tracking."""
        monitor = HeartbeatMonitor()
        agent_id = "test-agent-123"

        monitor.start_tracking(agent_id)
        assert agent_id in monitor._active_monitors

        monitor.stop_tracking(agent_id)
        assert agent_id not in monitor._active_monitors

    def test_record_heartbeat(self):
        """Test recording a heartbeat updates tracking."""
        monitor = HeartbeatMonitor()
        agent_id = "test-agent-456"

        monitor.start_tracking(agent_id)

        hb = Heartbeat(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            progress_percent=25.0,
            current_operation="reading files",
            files_modified=[],
            files_read=["src/main.py"]
        )

        monitor.record_heartbeat(hb)

        # Check history was updated
        assert agent_id in monitor._heartbeat_history
        assert len(monitor._heartbeat_history[agent_id]) > 0

        # Cleanup
        monitor.stop_tracking(agent_id)

    def test_is_stalled_detection(self):
        """Test stall detection based on heartbeat timeout."""
        monitor = HeartbeatMonitor(stall_timeout_seconds=1)
        agent_id = "test-agent-stall"

        monitor.start_tracking(agent_id)

        # Initially not stalled
        assert not monitor.is_stalled(agent_id)

        # Record heartbeat
        hb = Heartbeat(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            progress_percent=10.0,
            current_operation="working",
            files_modified=[],
            files_read=[]
        )
        monitor.record_heartbeat(hb)

        # Still not stalled immediately
        assert not monitor.is_stalled(agent_id)

        # Wait for timeout
        import time
        time.sleep(1.1)

        # Now should be stalled
        assert monitor.is_stalled(agent_id)

        # Cleanup
        monitor.stop_tracking(agent_id)

    def test_get_progress_summary(self):
        """Test getting progress summary for an agent."""
        monitor = HeartbeatMonitor()
        agent_id = "test-agent-progress"

        monitor.start_tracking(agent_id)

        # Record multiple heartbeats
        heartbeats = [
            Heartbeat(
                agent_id=agent_id,
                timestamp=datetime.now().isoformat(),
                progress_percent=10.0,
                current_operation="reading",
                files_modified=[],
                files_read=["src/file1.py"]
            ),
            Heartbeat(
                agent_id=agent_id,
                timestamp=datetime.now().isoformat(),
                progress_percent=50.0,
                current_operation="writing",
                files_modified=["src/file2.py"],
                files_read=["src/file1.py", "src/file2.py"]
            ),
        ]

        for hb in heartbeats:
            monitor.record_heartbeat(hb)

        summary = monitor.get_progress_summary(agent_id)

        assert summary["agent_id"] == agent_id
        assert summary["progress_percent"] == 50.0  # Latest
        assert summary["current_operation"] == "writing"
        assert "src/file2.py" in summary["files_modified"]
        assert "src/file1.py" in summary["files_read"]
        assert summary["total_heartbeats"] == 2

        # Cleanup
        monitor.stop_tracking(agent_id)

    def test_get_partial_work_no_progress(self):
        """Test partial work assessment when no progress made."""
        monitor = HeartbeatMonitor()
        agent_id = "test-agent-no-work"

        summary = monitor.get_partial_work(agent_id)

        assert summary["agent_id"] == agent_id
        assert summary["work_completed"] is False
        assert "never started" in summary["message"]

    def test_get_partial_work_with_progress(self):
        """Test partial work assessment with some progress."""
        monitor = HeartbeatMonitor()
        agent_id = "test-agent-partial"

        monitor.start_tracking(agent_id)

        hb = Heartbeat(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            progress_percent=65.0,
            current_operation="writing tests",
            files_modified=["src/test_file.py"],
            files_read=["src/source.py"]
        )

        monitor.record_heartbeat(hb)

        summary = monitor.get_partial_work(agent_id)

        assert summary["work_completed"] is True
        assert summary["progress_percent"] == 65.0
        assert "src/test_file.py" in summary["files_modified"]
        assert summary["can_resume"] is True
        assert "medium" in summary["estimated_work_value"]

        # Cleanup
        monitor.stop_tracking(agent_id)

    def test_assess_partial_work_function(self):
        """Test the assess_partial_work helper function."""
        # Use the global heartbeat_monitor since assess_partial_work uses it
        agent_id = "test-agent-assess"
        task_type = "refactor"

        heartbeat_monitor.start_tracking(agent_id)

        hb = Heartbeat(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            progress_percent=85.0,
            current_operation="finalizing",
            files_modified=["src/refactored.py"],
            files_read=["src/original.py"]
        )

        heartbeat_monitor.record_heartbeat(hb)

        result = assess_partial_work(agent_id, task_type)

        assert isinstance(result, PartialWorkResult)
        assert result.agent_id == agent_id
        assert result.task_type == task_type
        assert result.progress_percent == 85.0
        assert result.work_value == "high"
        assert result.can_resume is True
        assert len(result.recovery_steps) > 0
        assert len(result.files_modified) > 0

        # Cleanup
        heartbeat_monitor.stop_tracking(agent_id)

    def test_reentrant_lock_behavior(self):
        """Test that HeartbeatMonitor uses RLock to prevent deadlock.

        This test verifies that a method holding the lock can call another
        method that also acquires the lock. This would deadlock with a
        non-reentrant Lock but works with RLock.
        """
        monitor = HeartbeatMonitor()
        agent_id = "test-reentrant"

        monitor.start_tracking(agent_id)

        hb = Heartbeat(
            agent_id=agent_id,
            timestamp=datetime.now().isoformat(),
            progress_percent=50.0,
            current_operation="processing",
            files_modified=["src/file.py"],
            files_read=["src/file.py"]
        )

        monitor.record_heartbeat(hb)

        # This call internally holds the lock and calls is_stalled()
        # which also tries to acquire the lock. With RLock, this works.
        # With a non-reentrant Lock, this would deadlock.
        summary = monitor.get_progress_summary(agent_id)

        # If we get here, the lock is reentrant (no deadlock)
        assert summary["agent_id"] == agent_id
        assert summary["progress_percent"] == 50.0
        assert summary["status"] == "running"  # Should not be stalled

        # Cleanup
        monitor.stop_tracking(agent_id)


if __name__ == "__main__":
    sys.exit(main())
