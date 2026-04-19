#!/usr/bin/env python3
"""
Tree-of-Thoughts Core Module

Research basis: "Can AIs Like ChatGPT Think?" (ai-consciousness.org)
- 18× improvement on Game of 24 (4% → 74% success)
- Parallel branch exploration + self-consistency evaluation

This module implements the ToT reasoning engine with Agent tool integration.
"""

import asyncio
from dataclasses import dataclass, field
from collections.abc import Callable


@dataclass
class ThoughtBranch:
    """A single reasoning branch in Tree-of-Thoughts."""

    branch_id: str
    approach: str
    reasoning: str
    confidence: float
    conclusion: str
    metadata: dict = field(default_factory=dict)


class TreeOfThoughts:
    """
    Tree-of-Thoughts reasoning with parallel branch exploration.

    This class orchestrates parallel reasoning branches, evaluates their
    outputs, and returns the most reliable recommendation.
    """

    def __init__(self, agent_tool_func: Callable | None = None):
        """
        Initialize ToT engine.

        Args:
            agent_tool_func: Function to spawn subagents (Agent tool wrapper)
                           If None, runs in simulation mode for testing
        """
        self.agent_tool_func = agent_tool_func
        self.approaches = {
            "analytical": {
                "name": "Analytical Step-by-Step",
                "prompt_template": """You are the ANALYTICAL reasoning branch.

Your task: {task}

Instructions:
1. Break down the problem into logical components
2. Analyze each component systematically
3. Use deductive reasoning to reach conclusions
4. Identify dependencies and constraints

Format your response:
APPROACH: [Your analytical approach in 1-2 sentences]
REASONING: [Step-by-step reasoning]
CONFIDENCE: [0-1 score]
CONCLUSION: [Final recommendation]
""",
            },
            "creative": {
                "name": "Creative Lateral Thinking",
                "prompt_template": """You are the CREATIVE reasoning branch.

Your task: {task}

Instructions:
1. Question assumptions and constraints
2. Consider wild or unconventional ideas
3. Use analogies and metaphors to reframe the problem
4. Combine concepts from different domains

Format your response:
APPROACH: [Your creative approach in 1-2 sentences]
REASONING: [Lateral thinking insights]
CONFIDENCE: [0-1 score]
CONCLUSION: [Final recommendation]
""",
            },
            "skeptical": {
                "name": "Skeptical Critique-First",
                "prompt_template": """You are the SKEPTICAL reasoning branch.

Your task: {task}

Instructions:
1. Identify hidden assumptions in the problem
2. Find potential failure modes
3. Question whether the problem is well-formed
4. Consider what could go wrong

Format your response:
APPROACH: [Your skeptical analysis in 1-2 sentences]
REASONING: [Critique and risk assessment]
CONFIDENCE: [0-1 score]
CONCLUSION: [Risk-mitigated recommendation]
""",
            },
            "pragmatic": {
                "name": "Pragmatic Implementation",
                "prompt_template": """You are the PRAGMATIC reasoning branch.

Your task: {task}

Instructions:
1. Consider implementation complexity
2. Evaluate resource requirements
3. Identify quick wins vs long-term solutions
4. Assess operational feasibility

Format your response:
APPROACH: [Your pragmatic approach in 1-2 sentences]
REASONING: [Implementation considerations]
CONFIDENCE: [0-1 score]
CONCLUSION: [Actionable recommendation]
""",
            },
            "synthesis": {
                "name": "Synthesis Integration",
                "prompt_template": """You are the SYNTHESIS reasoning branch.

Your task: {task}

Instructions:
1. Consider how different approaches might complement each other
2. Look for hybrid solutions that combine strengths
3. Identify trade-offs between different approaches
4. Seek consensus or compromise positions

Format your response:
APPROACH: [Your synthesis approach in 1-2 sentences]
REASONING: [Integration analysis]
CONFIDENCE: [0-1 score]
CONCLUSION: [Integrated solution]
""",
            },
        }

    def _parse_branch_response(
        self, branch_type: str, response_text: str, branch_id: str
    ) -> ThoughtBranch:
        """
        Parse a branch agent's response into a ThoughtBranch.

        Args:
            branch_type: Type of reasoning branch (analytical, creative, etc.)
            response_text: Raw response from the branch agent
            branch_id: Unique identifier for this branch

        Returns:
            ThoughtBranch with parsed data
        """
        import re

        # Extract APPROACH (single line, don't capture newlines)
        approach_match = re.search(r"APPROACH:\s*(.+?)(?:\n|$)", response_text)
        approach = approach_match.group(1).strip() if approach_match else f"{branch_type} reasoning"

        # Extract REASONING (multiline until next tag or end)
        reasoning_match = re.search(
            r"REASONING:\s*(.+?)(?=\nCONFIDENCE:|\nCONCLUSION:|\n\n|$)", response_text, re.DOTALL
        )
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

        # Extract CONFIDENCE (match negative numbers too)
        confidence_match = re.search(r"CONFIDENCE:\s*(-?[0-9.]+)", response_text)
        try:
            confidence = float(confidence_match.group(1)) if confidence_match else 0.5
            confidence = max(0, min(1, confidence))  # Clamp to 0-1
        except (ValueError, AttributeError):
            confidence = 0.5

        # Extract CONCLUSION
        conclusion_match = re.search(r"CONCLUSION:\s*(.+?)(?:\n\n|$)", response_text, re.DOTALL)
        conclusion = (
            conclusion_match.group(1).strip() if conclusion_match else "No conclusion provided"
        )

        return ThoughtBranch(
            branch_id=branch_id,
            approach=approach,
            reasoning=reasoning[:1000],  # Truncate long reasoning
            confidence=confidence,
            conclusion=conclusion[:500],  # Truncate long conclusions
            metadata={"branch_type": branch_type},
        )

    async def explore_branches(
        self, task: str, num_branches: int = 3, timeout: int = 300
    ) -> list[ThoughtBranch]:
        """
        Explore multiple reasoning branches in parallel.

        Args:
            task: The problem or question to reason about
            num_branches: Number of parallel branches (default: 3)
            timeout: Timeout per branch in seconds (default: 300)

        Returns:
            List of ThoughtBranch objects with reasoning results
        """
        # Select branch types
        branch_types = list(self.approaches.keys())[:num_branches]

        # If agent tool function is available, spawn parallel subagents
        if self.agent_tool_func:
            return await self._explore_with_agent_tool(task, branch_types, timeout)
        else:
            # Simulation mode for testing
            return self._explore_simulation(task, branch_types)

    async def _explore_with_agent_tool(
        self, task: str, branch_types: list[str], timeout: int
    ) -> list[ThoughtBranch]:
        """Explore branches using Agent tool for parallel subagent spawning."""
        # Create branch tasks
        branch_tasks = []
        for i, branch_type in enumerate(branch_types):
            branch_id = f"branch_{i}_{branch_type}"
            prompt = self.approaches[branch_type]["prompt_template"].format(task=task)

            # Create async task for each branch
            task_coro = self._spawn_branch_agent(branch_id, branch_type, prompt, timeout)
            branch_tasks.append(task_coro)

        # Execute all branches in parallel
        results = await asyncio.gather(*branch_tasks, return_exceptions=True)

        # Parse results
        branches = []
        for i, (branch_type, result) in enumerate(zip(branch_types, results)):
            if isinstance(result, Exception):
                # Branch failed
                branches.append(
                    ThoughtBranch(
                        branch_id=f"branch_{i}_{branch_type}",
                        approach=self.approaches[branch_type]["name"],
                        reasoning=f"Branch failed: {str(result)}",
                        confidence=0.0,
                        conclusion="Error occurred during reasoning",
                        metadata={"error": str(result), "branch_type": branch_type},
                    )
                )
            elif result:
                # Branch succeeded - parse response
                branches.append(
                    self._parse_branch_response(branch_type, result, f"branch_{i}_{branch_type}")
                )

        return branches

    async def _spawn_branch_agent(
        self, branch_id: str, branch_type: str, prompt: str, timeout: int
    ) -> str:
        """Spawn a single branch agent using Agent tool."""
        try:
            # Call agent tool function with branch-specific prompt
            result = await asyncio.wait_for(
                self.agent_tool_func(prompt, branch_type, branch_id), timeout=timeout
            )
            return str(result)
        except TimeoutError:
            raise Exception(f"Branch {branch_id} timed out after {timeout}s")
        except Exception as e:
            raise Exception(f"Branch {branch_id} failed: {e}")

    def _explore_simulation(self, task: str, branch_types: list[str]) -> list[ThoughtBranch]:
        """Simulation mode for testing without Agent tool."""
        branches = []
        for i, branch_type in enumerate(branch_types):
            # Simulated response for testing
            simulated_response = f"""
APPROACH: {self.approaches[branch_type]['name']} for task: {task[:50]}...
REASONING: Simulated reasoning for {branch_type} branch.
CONFIDENCE: 0.7
CONCLUSION: Simulated conclusion from {branch_type} perspective.
"""
            branches.append(
                self._parse_branch_response(
                    branch_type, simulated_response, f"branch_{i}_{branch_type}"
                )
            )
        return branches

    def evaluate_branches(self, branches: list[ThoughtBranch]) -> dict:
        """
        Select the best branch using self-consistency evaluation.

        Args:
            branches: List of ThoughtBranch objects to evaluate

        Returns:
            Evaluation summary with best branch and analysis
        """
        if not branches:
            return {
                "best_branch": None,
                "confidence": 0,
                "consistency": 0,
                "reasoning": "No branches to evaluate",
            }

        # Sort by confidence
        sorted_branches = sorted(branches, key=lambda b: b.confidence, reverse=True)

        # Calculate consistency (do high-confidence branches agree?)
        high_conf_branches = [b for b in branches if b.confidence > 0.7]
        consistency_score = 0.0
        if high_conf_branches:
            # Extract keywords from conclusions (remove common words)
            conclusions = [b.conclusion.lower() for b in high_conf_branches]
            stop_words = {
                "the",
                "a",
                "an",
                "is",
                "are",
                "was",
                "were",
                "be",
                "been",
                "use",
                "using",
                "to",
                "for",
                "with",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "by",
                "from",
                "as",
                "of",
                "that",
                "this",
                "it",
            }

            # Build keyword sets for each conclusion
            keyword_sets = []
            for conclusion in conclusions:
                words = {w.strip(".,!?;:") for w in conclusion.split()}
                keywords = words - stop_words
                keyword_sets.append(keywords)

            # Calculate average overlap between all pairs
            if len(keyword_sets) > 1:
                overlap_scores = []
                for i in range(len(keyword_sets)):
                    for j in range(i + 1, len(keyword_sets)):
                        set1, set2 = keyword_sets[i], keyword_sets[j]
                        if set1 or set2:
                            # Jaccard similarity: intersection / union
                            intersection = len(set1 & set2)
                            union = len(set1 | set2)
                            jaccard = intersection / union if union > 0 else 0.0
                            overlap_scores.append(jaccard)

                consistency_score = (
                    sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
                )
            else:
                # Single high-confidence branch = full consistency
                consistency_score = 1.0
        else:
            # No high-confidence branches = zero consistency
            consistency_score = 0.0

        best = sorted_branches[0]

        # Build reasoning summary
        # Calculate agreeing branches count based on consistency score
        agreeing_count = (
            int(len(high_conf_branches) * consistency_score) if high_conf_branches else 0
        )

        # Determine consistency level indicator
        if consistency_score >= 0.7:
            level_indicator = "high"
        elif consistency_score >= 0.4:
            level_indicator = "moderate"
        elif consistency_score > 0:
            level_indicator = "low"
        else:
            level_indicator = "no"

        reasoning_parts = [
            f"**Best Approach**: {best.approach}",
            f"**Confidence**: {best.confidence:.2f}",
            f"**Consistency**: {consistency_score:.2f} ({agreeing_count}/{len(high_conf_branches)} high-confidence branches agree) - {level_indicator} consistency",
            "",
            "**Reasoning**:",
            f"  {best.reasoning[:200]}...",
            "",
            "**Conclusion**:",
            f"  {best.conclusion[:300]}...",
        ]

        return {
            "best_branch": best,
            "confidence": best.confidence,
            "avg_confidence": sum(b.confidence for b in branches) / len(branches),
            "consistency": consistency_score,
            "branch_count": len(branches),
            "reasoning": "\n".join(reasoning_parts),
            "all_branches": sorted_branches,
        }


def create_tot_engine(agent_tool_func: Callable | None = None) -> TreeOfThoughts:
    """
    Factory function to create a TreeOfThoughts engine.

    Args:
        agent_tool_func: Optional function to spawn subagents via Agent tool

    Returns:
        Configured TreeOfThoughts instance
    """
    return TreeOfThoughts(agent_tool_func=agent_tool_func)
