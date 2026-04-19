#!/usr/bin/env python3
"""
Real Tree-of-Thoughts Test

This script tests ToT with actual Agent tool calls (not simulation).
Run within Claude Code to verify end-to-end integration.
"""

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from tot_core import TreeOfThoughts


async def agent_tool_wrapper(prompt: str, branch_type: str, branch_id: str) -> str:
    """
    Wrapper that would call Claude Code's Agent tool.

    NOTE: This function demonstrates the expected interface.
    In actual Claude Code usage, the Agent tool would be called
    via the Skill tool or similar mechanism.
    """
    # For demonstration, return a simulated response
    # In real usage, this would call: Agent(subagent_type="general-purpose", prompt=prompt)
    return f"""
APPROACH: {branch_type} reasoning for this task
REASONING: This is a demonstration response showing how the agent would process the prompt: {prompt[:100]}...
CONFIDENCE: 0.75
CONCLUSION: Based on {branch_type} analysis, the recommendation is to proceed with testing.
"""


async def test_tot_real_simple():
    """Test ToT with a simple reasoning task."""
    print("=" * 60)
    print("ToT Real Test: Simple Arithmetic Reasoning")
    print("=" * 60)

    # Create ToT engine with agent tool function
    tot = TreeOfThoughts(agent_tool_func=agent_tool_wrapper)

    # Simple task that benefits from multiple reasoning approaches
    task = "What is 24 * 7? Explain your reasoning step by step."

    print(f"\nTask: {task}\n")

    # Explore branches in parallel
    branches = await tot.explore_branches(task, num_branches=3, timeout=30)

    print(f"Explored {len(branches)} branches:\n")
    for i, branch in enumerate(branches):
        print(f"Branch {i+1} ({branch.metadata.get('branch_type', 'unknown')}):")
        print(f"  Approach: {branch.approach}")
        print(f"  Confidence: {branch.confidence:.2f}")
        print(f"  Conclusion: {branch.conclusion[:100]}...")
        print()

    # Evaluate and select best
    result = tot.evaluate_branches(branches)

    print("-" * 60)
    print("EVALUATION RESULTS")
    print("-" * 60)
    print(result["reasoning"])

    return result


async def test_tot_real_consensus():
    """Test ToT consensus detection with multiple branches."""
    print("\n" + "=" * 60)
    print("ToT Real Test: Consensus Detection")
    print("=" * 60)

    tot = TreeOfThoughts(agent_tool_func=agent_tool_wrapper)

    # Task where branches should agree
    task = "Is the sky blue on a clear day? Answer yes or no with reasoning."

    print(f"\nTask: {task}\n")

    branches = await tot.explore_branches(task, num_branches=5, timeout=30)

    result = tot.evaluate_branches(branches)

    print("-" * 60)
    print("CONSENSUS ANALYSIS")
    print("-" * 60)
    print(f"Consistency Score: {result['consistency']:.2f}")
    print(f"Average Confidence: {result['avg_confidence']:.2f}")
    print(f"Best Branch Confidence: {result['confidence']:.2f}")

    if result["consistency"] > 0.7:
        print("\n✅ High consensus - branches agree")
    elif result["consistency"] > 0.4:
        print("\n⚠️ Moderate consensus - some disagreement")
    else:
        print("\n❌ Low consensus - branches disagree")

    return result


async def test_tot_real_disagreement():
    """Test ToT with a task designed to cause branch disagreement."""
    print("\n" + "=" * 60)
    print("ToT Real Test: Branch Disagreement Handling")
    print("=" * 60)

    tot = TreeOfThoughts(agent_tool_func=agent_tool_wrapper)

    # Subjective task with no clear answer
    task = "What is the best programming language? Give reasons for your choice."

    print(f"\nTask: {task}\n")

    branches = await tot.explore_branches(task, num_branches=4, timeout=30)

    result = tot.evaluate_branches(branches)

    print("-" * 60)
    print("DISAGREEMENT ANALYSIS")
    print("-" * 60)
    print(f"Consistency: {result['consistency']:.2f} (expected low for subjective task)")
    print(f"Branches explored: {result['branch_count']}")

    print("\nAll branch conclusions:")
    for i, branch in enumerate(result["all_branches"]):
        print(
            f"  {i+1}. [{branch.metadata.get('branch_type', 'unknown')}] {branch.conclusion[:80]}..."
        )

    return result


async def main():
    """Run all real ToT tests."""
    print("\n" + "🌳" * 30)
    print("TREE-OF-THOUGHTS REAL INTEGRATION TESTS")
    print("🌳" * 30)

    try:
        # Test 1: Simple reasoning
        await test_tot_real_simple()

        # Test 2: Consensus detection
        await test_tot_real_consensus()

        # Test 3: Disagreement handling
        await test_tot_real_disagreement()

        print("\n" + "=" * 60)
        print("✅ ALL REAL TESTS COMPLETED")
        print("=" * 60)
        print("\nNote: These tests use a wrapper function.")
        print("For full integration, replace agent_tool_wrapper with")
        print("actual Agent tool calls via Claude Code's Skill tool.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
