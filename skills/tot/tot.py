#!/usr/bin/env python3
"""
Tree-of-Thoughts Reasoning Implementation

Research basis: "Can AIs Like ChatGPT Think?" (ai-consciousness.org)
- 18× improvement on Game of 24 (4% → 74% success)
- Parallel branch exploration + self-consistency evaluation

Usage: /tot "your complex question or problem"
"""

import os
import sys
from typing import Any

# Configuration
TOT_ENABLED = os.environ.get("TOT_ENABLED", "true").lower() == "true"
TOT_BRANCHES = int(os.environ.get("TOT_BRANCHES", "3"))
TOT_TIMEOUT = int(os.environ.get("TOT_TIMEOUT", "300"))

# Branch configurations
BRANCH_TYPES = {
    "analytical": {
        "name": "Analytical",
        "prompt_template": """
You are the ANALYTICAL branch of Tree-of-Thoughts reasoning.

Your role: Provide step-by-step logical decomposition of the problem.

Problem: {problem}

Instructions:
1. Break down the problem into logical components
2. Analyze each component systematically
3. Use deductive reasoning to reach conclusions
4. Identify dependencies and constraints

Format your response as:
- Approach: [Your analytical approach]
- Key insights: [3-5 bullet points]
- Confidence: [0-1 score]
- Recommendations: [Actionable next steps]
""",
    },
    "creative": {
        "name": "Creative",
        "prompt_template": """
You are the CREATIVE branch of Tree-of-Thoughts reasoning.

Your role: Explore novel, unconventional solutions using lateral thinking.

Problem: {problem}

Instructions:
1. Question assumptions and constraints
2. Consider wild or unconventional ideas
3. Use analogies and metaphors to reframe the problem
4. Combine concepts from different domains

Format your response as:
- Approach: [Your creative approach]
- Key insights: [3-5 bullet points]
- Confidence: [0-1 score]
- Recommendations: [Actionable next steps]
""",
    },
    "skeptical": {
        "name": "Skeptical",
        "prompt_template": """
You are the SKEPTICAL branch of Tree-of-Thoughts reasoning.

Your role: Critique assumptions, find flaws, identify risks.

Problem: {problem}

Instructions:
1. Identify hidden assumptions in the problem
2. Find potential failure modes
3. Question whether the problem is well-formed
4. Consider what could go wrong

Format your response as:
- Approach: [Your skeptical analysis]
- Key insights: [3-5 bullet points of critiques/risks]
- Confidence: [0-1 score]
- Recommendations: [Risk mitigation strategies]
""",
    },
    "pragmatic": {
        "name": "Pragmatic",
        "prompt_template": """
You are the PRAGMATIC branch of Tree-of-Thoughts reasoning.

Your role: Focus on practical, implementable solutions.

Problem: {problem}

Instructions:
1. Consider implementation complexity
2. Evaluate resource requirements
3. Identify quick wins vs long-term solutions
4. Assess operational feasibility

Format your response as:
- Approach: [Your pragmatic approach]
- Key insights: [3-5 bullet points]
- Confidence: [0-1 score]
- Recommendations: [Implementation steps]
""",
    },
    "synthesis": {
        "name": "Synthesis",
        "prompt_template": """
You are the SYNTHESIS branch of Tree-of-Thoughts reasoning.

Your role: Integrate multiple perspectives and find common ground.

Problem: {problem}

Instructions:
1. Consider how different approaches might complement each other
2. Look for hybrid solutions that combine strengths
3. Identify trade-offs between different approaches
4. Seek consensus or compromise positions

Format your response as:
- Approach: [Your synthesis approach]
- Key insights: [3-5 bullet points]
- Confidence: [0-1 score]
- Recommendations: [Integrated solution]
""",
    },
}


def parse_branch_response(response_text: str) -> dict[str, Any]:
    """
    Parse a branch response into structured data.

    Args:
        response_text: Raw response from a branch

    Returns:
        Dict with approach, insights, confidence, recommendations
    """
    import re

    result = {
        "approach": "",
        "insights": [],
        "confidence": 0.5,
        "recommendations": "",
    }

    # Extract approach
    approach_match = re.search(
        r"[-:]?\s*Approach:\s*(.+?)(?:\n|$)", response_text, re.IGNORECASE | re.DOTALL
    )
    if approach_match:
        result["approach"] = approach_match.group(1).strip()[:500]

    # Extract insights (bullet points)
    insight_pattern = r"[-\*•]\s+(.+?)(?:\n[-\*•]|\n\n|$)"
    insights = re.findall(insight_pattern, response_text, re.MULTILINE)
    result["insights"] = [i.strip() for i in insights[:10]]

    # Extract confidence
    confidence_match = re.search(r"[-:]?\s*Confidence:\s*([0-9.]+)", response_text, re.IGNORECASE)
    if confidence_match:
        try:
            result["confidence"] = float(confidence_match.group(1))
            result["confidence"] = max(0, min(1, result["confidence"]))  # Clamp to 0-1
        except ValueError:
            pass

    # Extract recommendations
    rec_match = re.search(
        r"[-:]?\s*Recommendations?:\s*(.+?)(?:\n\n|$)", response_text, re.IGNORECASE | re.DOTALL
    )
    if rec_match:
        result["recommendations"] = rec_match.group(1).strip()[:500]

    return result


def evaluate_branches(branch_results: list[dict]) -> dict:
    """
    Evaluate all branches and determine the best approach.

    Args:
        branch_results: List of parsed branch responses

    Returns:
        Evaluation summary with best branch and confidence
    """
    if not branch_results:
        return {
            "best_branch": None,
            "confidence": 0,
            "reasoning": "No branches returned results",
        }

    # Calculate average confidence
    avg_confidence = sum(b["confidence"] for b in branch_results) / len(branch_results)

    # Find highest confidence branch
    best = max(branch_results, key=lambda b: b["confidence"])

    # Check self-consistency (do high-confidence branches agree?)
    high_conf_branches = [b for b in branch_results if b["confidence"] > 0.7]
    consistency = len(high_conf_branches) / len(branch_results) if branch_results else 0

    return {
        "best_branch": best,
        "confidence": best["confidence"],
        "avg_confidence": avg_confidence,
        "consistency": consistency,
        "branch_count": len(branch_results),
        "reasoning": _build_reasoning_summary(best, branch_results, consistency),
    }


def _build_reasoning_summary(best: dict, all_branches: list[dict], consistency: float) -> str:
    """Build a human-readable reasoning summary."""
    parts = []

    # Best branch
    parts.append(f"**BEST APPROACH**: {best.get('approach', 'Unknown')[:100]}")

    # Confidence
    parts.append(
        f"**Confidence**: {best['confidence']:.2f} (average: {sum(b['confidence'] for b in all_branches) / len(all_branches):.2f})"
    )

    # Consistency
    if consistency > 0.7:
        parts.append("**Consistency**: High - multiple branches agree")
    elif consistency > 0.4:
        parts.append("**Consistency**: Medium - partial agreement")
    else:
        parts.append("**Consistency**: Low - branches disagree")

    # Key insights from best branch
    if best.get("insights"):
        parts.append("**Key Insights**:")
        for insight in best["insights"][:5]:
            parts.append(f"  • {insight}")

    return "\n".join(parts)


def run_tot(problem: str) -> str:
    """
    Main Tree-of-Thoughts execution function.

    Args:
        problem: The problem or question to reason about

    Returns:
        Formatted recommendation with branch analysis
    """
    if not TOT_ENABLED:
        return "Tree-of-Thoughts is disabled. Set TOT_ENABLED=true to enable."

    # Select branch types based on configured count
    branch_names = list(BRANCH_TYPES.keys())[:TOT_BRANCHES]

    # Prepare branch prompts
    branch_prompts = []
    for branch_name in branch_names:
        branch_type = BRANCH_TYPES[branch_name]
        prompt = branch_type["prompt_template"].format(problem=problem)
        branch_prompts.append(
            {
                "name": branch_type["name"],
                "type": branch_name,
                "prompt": prompt,
            }
        )

    # In a real implementation, this would use the Agent tool to spawn parallel subagents
    # For now, we'll create a placeholder that shows the structure
    output_parts = [
        "# Tree-of-Thoughts Analysis",
        "",
        f"**Problem**: {problem[:200]}",
        "",
        f"Exploring {len(branch_prompts)} reasoning branches in parallel...",
        "",
    ]

    # Add branch placeholders
    for i, branch in enumerate(branch_prompts, 1):
        output_parts.append(f"**Branch {i}: {branch['name']}**")
        output_parts.append(f"  Type: {branch['type']}")
        output_parts.append("  (Branch execution via Agent tool - implementation pending)")
        output_parts.append("")

    # Note: In production, this would:
    # 1. Spawn parallel subagents using Agent tool
    # 2. Collect and parse responses
    # 3. Evaluate using evaluate_branches()
    # 4. Return best recommendation

    output_parts.append(
        "**Note**: Full Tree-of-Thoughts implementation requires Agent tool integration."
    )
    output_parts.append(
        "This structure demonstrates the workflow; parallel subagent spawning is pending."
    )

    return "\n".join(output_parts)


def main():
    """CLI entry point for /tot skill."""
    import json

    # Read problem from stdin or args
    try:
        input_data = json.loads(sys.stdin.read())
        problem = input_data.get("prompt") or input_data.get("query") or ""
    except json.JSONDecodeError:
        problem = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    if not problem:
        print("Usage: /tot <your complex question or problem>")
        sys.exit(1)

    result = run_tot(problem)
    print(result)


if __name__ == "__main__":
    main()
