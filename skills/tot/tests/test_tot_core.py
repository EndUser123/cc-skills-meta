#!/usr/bin/env python3
"""
Unit tests for Tree-of-Thoughts core module.

Tests cover:
- ThoughtBranch dataclass
- TreeOfThoughts.explore_branches()
- TreeOfThoughts.evaluate_branches()
- Agent tool integration
- Async execution

TDD Discipline: RED → GREEN → REFACTOR
"""

import asyncio

# Import tot_core module
import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tot_core import ThoughtBranch, TreeOfThoughts, create_tot_engine


class TestThoughtBranchDataclass:
    """Test ThoughtBranch dataclass functionality."""

    def test_thought_branch_creation_with_all_fields(self):
        """Test creating a ThoughtBranch with all required fields."""
        branch = ThoughtBranch(
            branch_id="branch_0_analytical",
            approach="Analytical Step-by-Step",
            reasoning="Step 1: Analyze the problem. Step 2: Break down components.",
            confidence=0.85,
            conclusion="Recommendation: Proceed with analytical approach.",
            metadata={"branch_type": "analytical"},
        )

        assert branch.branch_id == "branch_0_analytical"
        assert branch.approach == "Analytical Step-by-Step"
        assert branch.reasoning.startswith("Step 1:")
        assert branch.confidence == 0.85
        assert branch.conclusion.startswith("Recommendation:")
        assert branch.metadata == {"branch_type": "analytical"}

    def test_thought_branch_creation_with_minimal_fields(self):
        """Test creating a ThoughtBranch with only required fields."""
        branch = ThoughtBranch(
            branch_id="branch_1",
            approach="Creative Lateral Thinking",
            reasoning="Think outside the box.",
            confidence=0.7,
            conclusion="Try unconventional approach.",
        )

        # metadata should default to empty dict
        assert branch.metadata == {}
        assert branch.branch_id == "branch_1"

    def test_thought_branch_confidence_within_bounds(self):
        """Test that confidence values are clamped to 0-1 range during parsing."""
        # Note: This is tested via _parse_branch_response, not direct validation
        # The dataclass itself doesn't enforce bounds
        branch = ThoughtBranch(
            branch_id="test",
            approach="Test",
            reasoning="Test",
            confidence=1.5,  # This is allowed in dataclass
            conclusion="Test",
        )

        # Dataclass doesn't auto-clamp, but parse_branch_response does
        assert branch.confidence == 1.5

    def test_thought_branch_immutability_is_not_enforced(self):
        """Test that ThoughtBranch is mutable (frozen=True not set)."""
        branch = ThoughtBranch(
            branch_id="test", approach="Test", reasoning="Test", confidence=0.5, conclusion="Test"
        )

        # Modify fields (dataclass is mutable by default)
        branch.confidence = 0.9
        assert branch.confidence == 0.9

    def test_thought_branch_to_dict_conversion(self):
        """Test converting ThoughtBranch to dict using asdict."""
        branch = ThoughtBranch(
            branch_id="test",
            approach="Test Approach",
            reasoning="Test reasoning",
            confidence=0.75,
            conclusion="Test conclusion",
            metadata={"key": "value"},
        )

        branch_dict = asdict(branch)
        assert branch_dict["branch_id"] == "test"
        assert branch_dict["approach"] == "Test Approach"
        assert branch_dict["confidence"] == 0.75
        assert branch_dict["metadata"] == {"key": "value"}


class TestTreeOfThoughtsInit:
    """Test TreeOfThoughts initialization."""

    def test_init_with_agent_tool_func(self):
        """Test initialization with Agent tool function."""
        mock_func = MagicMock()
        tot = TreeOfThoughts(agent_tool_func=mock_func)

        assert tot.agent_tool_func == mock_func
        assert len(tot.approaches) == 5  # analytical, creative, skeptical, pragmatic, synthesis

    def test_init_without_agent_tool_func(self):
        """Test initialization without Agent tool function (simulation mode)."""
        tot = TreeOfThoughts(agent_tool_func=None)

        assert tot.agent_tool_func is None
        assert len(tot.approaches) == 5

    def test_approaches_configuration(self):
        """Test that all expected approaches are configured."""
        tot = TreeOfThoughts()

        expected_approaches = ["analytical", "creative", "skeptical", "pragmatic", "synthesis"]
        for approach in expected_approaches:
            assert approach in tot.approaches
            assert "name" in tot.approaches[approach]
            assert "prompt_template" in tot.approaches[approach]

    def test_approach_prompt_templates_contain_placeholders(self):
        """Test that all prompt templates contain {task} placeholder."""
        tot = TreeOfThoughts()

        for approach_name, config in tot.approaches.items():
            template = config["prompt_template"]
            assert "{task}" in template, f"{approach_name} template missing {{task}} placeholder"


class TestParseBranchResponse:
    """Test _parse_branch_response method."""

    def test_parse_complete_response(self):
        """Test parsing a complete branch response with all fields."""
        tot = TreeOfThoughts()
        response_text = """
APPROACH: Analytical breakdown of the problem
REASONING: First, I'll analyze the components. Then, I'll evaluate dependencies.
CONFIDENCE: 0.85
CONCLUSION: Proceed with systematic approach.
"""

        branch = tot._parse_branch_response("analytical", response_text, "branch_0")

        assert branch.branch_id == "branch_0"
        assert branch.approach == "Analytical breakdown of the problem"
        assert "First, I'll analyze" in branch.reasoning
        assert branch.confidence == 0.85
        assert branch.conclusion == "Proceed with systematic approach."
        assert branch.metadata["branch_type"] == "analytical"

    def test_parse_minimal_response(self):
        """Test parsing a response with missing fields."""
        tot = TreeOfThoughts()
        response_text = "APPROACH: Quick analysis\nNo other fields here."

        branch = tot._parse_branch_response("creative", response_text, "branch_1")

        assert branch.approach == "Quick analysis"
        assert branch.reasoning == ""
        assert branch.confidence == 0.5  # Default value
        assert branch.conclusion == "No conclusion provided"  # Default value

    def test_parse_clamps_confidence_to_0_1(self):
        """Test that confidence values are clamped to valid range."""
        tot = TreeOfThoughts()

        # Test high confidence
        response_high = "APPROACH: Test\nCONFIDENCE: 1.5\nCONCLUSION: Test"
        branch_high = tot._parse_branch_response("test", response_high, "branch_high")
        assert branch_high.confidence == 1.0  # Clamped to 1.0

        # Test low confidence
        response_low = "APPROACH: Test\nCONFIDENCE: -0.5\nCONCLUSION: Test"
        branch_low = tot._parse_branch_response("test", response_low, "branch_low")
        assert branch_low.confidence == 0.0  # Clamped to 0.0

    def test_parse_with_invalid_confidence(self):
        """Test parsing with non-numeric confidence value."""
        tot = TreeOfThoughts()
        response_text = "APPROACH: Test\nCONFIDENCE: invalid\nCONCLUSION: Test"

        branch = tot._parse_branch_response("test", response_text, "branch_invalid")

        assert branch.confidence == 0.5  # Default value on error

    def test_parse_truncates_long_reasoning(self):
        """Test that long reasoning text is truncated to 1000 chars."""
        tot = TreeOfThoughts()
        long_reasoning = "X" * 2000
        response_text = (
            f"APPROACH: Test\nREASONING: {long_reasoning}\nCONFIDENCE: 0.5\nCONCLUSION: Test"
        )

        branch = tot._parse_branch_response("test", response_text, "branch_truncate")

        assert len(branch.reasoning) == 1000  # Truncated
        assert branch.reasoning == "X" * 1000

    def test_parse_truncates_long_conclusion(self):
        """Test that long conclusion text is truncated to 500 chars."""
        tot = TreeOfThoughts()
        long_conclusion = "Y" * 1000
        response_text = (
            f"APPROACH: Test\nREASONING: Test\nCONFIDENCE: 0.5\nCONCLUSION: {long_conclusion}"
        )

        branch = tot._parse_branch_response("test", response_text, "branch_truncate")

        assert len(branch.conclusion) == 500  # Truncated
        assert branch.conclusion == "Y" * 500

    def test_parse_multiline_fields(self):
        """Test parsing single-line APPROACH and multiline REASONING/CONCLUSION fields."""
        tot = TreeOfThoughts()
        response_text = """
APPROACH: Single-line approach description
REASONING: Reasoning line 1
Reasoning line 2
CONFIDENCE: 0.8
CONCLUSION: Multi-line
conclusion here.
"""

        branch = tot._parse_branch_response("test", response_text, "branch_multi")

        # APPROACH is single-line per format spec
        assert branch.approach == "Single-line approach description"
        # REASONING and CONCLUSION support multiline
        assert "Reasoning line 1" in branch.reasoning
        assert "Reasoning line 2" in branch.reasoning
        assert "Multi-line" in branch.conclusion
        assert "conclusion here." in branch.conclusion


class TestExploreBranches:
    """Test explore_branches method."""

    @pytest.mark.asyncio
    async def test_explore_branches_in_simulation_mode(self):
        """Test explore_branches without Agent tool (simulation mode)."""
        tot = TreeOfThoughts(agent_tool_func=None)
        task = "Solve 2 + 2 = 4"

        branches = await tot.explore_branches(task, num_branches=3)

        assert len(branches) == 3
        assert all(isinstance(b, ThoughtBranch) for b in branches)
        assert all(b.confidence == 0.7 for b in branches)  # Simulation default

    @pytest.mark.asyncio
    async def test_explore_branches_respects_num_branches(self):
        """Test that num_branches parameter controls branch count."""
        tot = TreeOfThoughts(agent_tool_func=None)

        # Test with 2 branches
        branches_2 = await tot.explore_branches("test task", num_branches=2)
        assert len(branches_2) == 2

        # Test with 5 branches
        branches_5 = await tot.explore_branches("test task", num_branches=5)
        assert len(branches_5) == 5

    @pytest.mark.asyncio
    async def test_explore_branches_branch_types_selection(self):
        """Test that correct branch types are selected."""
        tot = TreeOfThoughts(agent_tool_func=None)

        branches = await tot.explore_branches("test", num_branches=3)

        # Should select first 3: analytical, creative, skeptical
        branch_types = [b.metadata.get("branch_type") for b in branches]
        assert branch_types == ["analytical", "creative", "skeptical"]

    @pytest.mark.asyncio
    async def test_explore_branches_with_agent_tool(self):
        """Test explore_branches with Agent tool function."""

        # Create mock agent function
        async def mock_agent_func(prompt, branch_type, branch_id):
            return f"""
APPROACH: Mock response for {branch_type}
REASONING: Mock reasoning for {branch_id}
CONFIDENCE: 0.9
CONCLUSION: Mock conclusion
"""

        tot = TreeOfThoughts(agent_tool_func=mock_agent_func)
        branches = await tot.explore_branches("test task", num_branches=2)

        assert len(branches) == 2
        assert all(b.confidence == 0.9 for b in branches)

    @pytest.mark.asyncio
    async def test_explore_branches_handles_agent_exceptions(self):
        """Test that Agent tool exceptions are handled gracefully."""

        async def failing_agent_func(prompt, branch_type, branch_id):
            raise Exception("Agent failed")

        tot = TreeOfThoughts(agent_tool_func=failing_agent_func)
        branches = await tot.explore_branches("test", num_branches=2)

        assert len(branches) == 2
        # Failed branches should have confidence 0.0
        assert all(b.confidence == 0.0 for b in branches)
        assert all("failed" in b.reasoning.lower() for b in branches)

    @pytest.mark.asyncio
    async def test_explore_branches_timeout_handling(self):
        """Test that timeout is handled correctly."""

        async def slow_agent_func(prompt, branch_type, branch_id):
            await asyncio.sleep(10)  # Longer than timeout
            return "Response"

        tot = TreeOfThoughts(agent_tool_func=slow_agent_func)

        # Should timeout after 1 second
        branches = await tot.explore_branches("test", num_branches=1, timeout=1)

        assert len(branches) == 1
        assert branches[0].confidence == 0.0
        assert "timed out" in branches[0].reasoning.lower()


class TestExploreSimulation:
    """Test _explore_simulation method."""

    def test_explore_simulation_returns_correct_branches(self):
        """Test simulation mode returns expected ThoughtBranch objects."""
        tot = TreeOfThoughts()
        branch_types = ["analytical", "creative"]
        task = "Test task"

        branches = tot._explore_simulation(task, branch_types)

        assert len(branches) == 2
        assert branches[0].metadata["branch_type"] == "analytical"
        assert branches[1].metadata["branch_type"] == "creative"
        assert all(b.confidence == 0.7 for b in branches)

    def test_explore_simulation_includes_task_in_response(self):
        """Test that simulation includes task in reasoning."""
        tot = TreeOfThoughts()
        task = "Solve complex problem"

        branches = tot._explore_simulation(task, ["analytical"])

        assert task[:50] in branches[0].approach


class TestSpawnBranchAgent:
    """Test _spawn_branch_agent method."""

    @pytest.mark.asyncio
    async def test_spawn_branch_agent_success(self):
        """Test successful agent spawning."""

        async def mock_agent(prompt, branch_type, branch_id):
            return "Agent response"

        tot = TreeOfThoughts(agent_tool_func=mock_agent)

        result = await tot._spawn_branch_agent("test_prompt", "analytical", "branch_0", 10)

        assert result == "Agent response"

    @pytest.mark.asyncio
    async def test_spawn_branch_agent_timeout(self):
        """Test that timeout raises Exception."""

        async def slow_agent(prompt, branch_type, branch_id):
            await asyncio.sleep(5)
            return "Response"

        tot = TreeOfThoughts(agent_tool_func=slow_agent)

        with pytest.raises(Exception) as exc_info:
            await tot._spawn_branch_agent("test", "analytical", "branch_0", timeout=0.1)

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_spawn_branch_agent_exception_propagation(self):
        """Test that agent exceptions are wrapped."""

        async def failing_agent(prompt, branch_type, branch_id):
            raise ValueError("Agent error")

        tot = TreeOfThoughts(agent_tool_func=failing_agent)

        with pytest.raises(Exception) as exc_info:
            await tot._spawn_branch_agent("test", "analytical", "branch_0", 10)

        assert "failed" in str(exc_info.value).lower()


class TestEvaluateBranches:
    """Test evaluate_branches method."""

    def test_evaluate_empty_branch_list(self):
        """Test evaluation with empty branch list."""
        tot = TreeOfThoughts()
        result = tot.evaluate_branches([])

        assert result["best_branch"] is None
        assert result["confidence"] == 0
        assert result["consistency"] == 0
        assert result["reasoning"] == "No branches to evaluate"

    def test_evaluate_single_branch(self):
        """Test evaluation with single branch."""
        tot = TreeOfThoughts()
        branch = ThoughtBranch(
            branch_id="branch_0",
            approach="Test Approach",
            reasoning="Test reasoning",
            confidence=0.8,
            conclusion="Test conclusion",
            metadata={},
        )

        result = tot.evaluate_branches([branch])

        assert result["best_branch"] == branch
        assert result["confidence"] == 0.8
        assert result["avg_confidence"] == 0.8
        assert result["branch_count"] == 1

    def test_evaluate_selects_highest_confidence(self):
        """Test that highest confidence branch is selected."""
        tot = TreeOfThoughts()

        branches = [
            ThoughtBranch("b1", "Approach 1", "Reasoning 1", 0.5, "Conclusion 1", {}),
            ThoughtBranch("b2", "Approach 2", "Reasoning 2", 0.9, "Conclusion 2", {}),
            ThoughtBranch("b3", "Approach 3", "Reasoning 3", 0.7, "Conclusion 3", {}),
        ]

        result = tot.evaluate_branches(branches)

        assert result["best_branch"].branch_id == "b2"
        assert result["confidence"] == 0.9

    def test_evaluate_consistency_calculation(self):
        """Test consistency score calculation using Jaccard similarity."""
        tot = TreeOfThoughts()

        branches = [
            ThoughtBranch("b1", "A1", "R1", 0.8, "Conclusion X", {}),
            ThoughtBranch("b2", "A2", "R2", 0.9, "Conclusion Y", {}),
            ThoughtBranch("b3", "A3", "R3", 0.3, "Conclusion Z", {}),
        ]

        result = tot.evaluate_branches(branches)

        # 2 out of 3 branches have confidence > 0.7
        # Jaccard similarity: share "conclusion" keyword, differ on X/Y/Z
        # Intersection: {"conclusion"} = 1, Union: {"conclusion", "x", "y"} = 3
        # consistency = 1/3 ≈ 0.333
        assert result["consistency"] == pytest.approx(1 / 3, rel=1e-10)

    def test_evaluate_reasoning_summary_format(self):
        """Test that reasoning summary has correct format."""
        tot = TreeOfThoughts()

        branch = ThoughtBranch(
            "b1",
            "Analytical Approach",
            "Step-by-step analysis of the problem.",
            0.85,
            "Recommendation: Proceed with analytical method.",
            {},
        )

        result = tot.evaluate_branches([branch])

        reasoning = result["reasoning"]
        assert "**Best Approach**:" in reasoning
        assert "**Confidence**:" in reasoning
        assert "**Consistency**:" in reasoning
        assert "**Reasoning**:" in reasoning
        assert "**Conclusion**:" in reasoning

    def test_evaluate_all_branches_sorted(self):
        """Test that all_branches is sorted by confidence."""
        tot = TreeOfThoughts()

        branches = [
            ThoughtBranch("b1", "A1", "R1", 0.5, "C1", {}),
            ThoughtBranch("b2", "A2", "R2", 0.9, "C2", {}),
            ThoughtBranch("b3", "A3", "R3", 0.7, "C3", {}),
        ]

        result = tot.evaluate_branches(branches)

        all_branches = result["all_branches"]
        confidences = [b.confidence for b in all_branches]
        assert confidences == [0.9, 0.7, 0.5]  # Descending order

    def test_evaluate_average_confidence(self):
        """Test average confidence calculation."""
        tot = TreeOfThoughts()

        branches = [
            ThoughtBranch("b1", "A1", "R1", 0.5, "C1", {}),
            ThoughtBranch("b2", "A2", "R2", 0.7, "C2", {}),
            ThoughtBranch("b3", "A3", "R3", 0.9, "C3", {}),
        ]

        result = tot.evaluate_branches(branches)

        # (0.5 + 0.7 + 0.9) / 3 = 0.7
        assert result["avg_confidence"] == pytest.approx(0.7, rel=1e-10)


class TestCreateTotEngine:
    """Test create_tot_engine factory function."""

    def test_create_tot_engine_without_agent_func(self):
        """Test factory without agent function."""
        engine = create_tot_engine()

        assert isinstance(engine, TreeOfThoughts)
        assert engine.agent_tool_func is None

    def test_create_tot_engine_with_agent_func(self):
        """Test factory with agent function."""
        mock_func = MagicMock()
        engine = create_tot_engine(agent_tool_func=mock_func)

        assert isinstance(engine, TreeOfThoughts)
        assert engine.agent_tool_func == mock_func


class TestIntegrationScenarios:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_tot_workflow_simulation(self):
        """Test complete ToT workflow in simulation mode."""
        tot = create_tot_engine()
        task = "Should I use Redis or Memcached for caching?"

        # Explore branches
        branches = await tot.explore_branches(task, num_branches=3)

        # Evaluate branches
        result = tot.evaluate_branches(branches)

        # Verify workflow completed
        assert len(branches) == 3
        assert result["best_branch"] is not None
        assert result["confidence"] > 0
        assert result["branch_count"] == 3

    @pytest.mark.asyncio
    async def test_full_tot_workflow_with_mock_agent(self):
        """Test complete ToT workflow with mocked Agent tool."""
        call_count = 0

        async def mock_agent(prompt, branch_type, branch_id):
            nonlocal call_count
            call_count += 1
            return f"""
APPROACH: {branch_type} analysis
REASONING: Detailed {branch_type} reasoning
CONFIDENCE: 0.{80 + call_count * 5}
CONCLUSION: {branch_type} recommendation
"""

        tot = create_tot_engine(agent_tool_func=mock_agent)
        task = "Optimize database query performance"

        branches = await tot.explore_branches(task, num_branches=3)
        result = tot.evaluate_branches(branches)

        # Verify all agents were called
        assert call_count == 3
        assert len(branches) == 3
        assert result["best_branch"] is not None

    @pytest.mark.asyncio
    async def test_concurrent_branch_execution(self):
        """Test that branches execute concurrently, not sequentially."""
        execution_order = []

        async def tracking_agent(prompt, branch_type, branch_id):
            execution_order.append(branch_id)
            await asyncio.sleep(0.1)  # Simulate work
            return f"Response from {branch_id}"

        tot = create_tot_engine(agent_tool_func=tracking_agent)

        start_time = asyncio.get_event_loop().time()
        branches = await tot.explore_branches("test", num_branches=3)
        elapsed = asyncio.get_event_loop().time() - start_time

        # Concurrent execution should be much faster than sequential
        # Sequential: 3 * 0.1 = 0.3 seconds minimum
        # Concurrent: ~0.1 seconds (overhead adds some)
        assert elapsed < 0.25  # Should complete in under 0.25 seconds
        assert len(branches) == 3
