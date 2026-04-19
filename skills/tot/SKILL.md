---
name: tot
description: Tree-of-thoughts reasoning - explore multiple branches of thought and evaluate different perspectives.
version: "1.0.0"
status: stable
category: reasoning
triggers:
  - "/tot"
  - "tree of thoughts"
  - "explore multiple approaches"
  - "consider different perspectives"
aliases:
  - /tot
workflow_steps:
  - parse_input
  - spawn_branches
  - evaluate_branches
  - return_recommendation
---

# Tree-of-Thoughts Reasoning

## When to Use
- Complex problems requiring multiple approaches
- High-stakes decisions where single-point reasoning is risky
- Creative tasks where lateral thinking helps
- Architectural decisions with competing constraints
- Debugging complex issues where multiple hypotheses exist

## Instructions

**Just tell me what you want to reason about.** I'll spawn multiple subagents to explore different approaches in parallel, then evaluate which branch is most reliable.

## Workflow

### Step 1: Parse Input
Extract the core problem or question from your request.

### Step 2: Spawn Branches
Create 3-5 parallel subagents, each exploring a different reasoning approach:
- **Analytical Branch**: Step-by-step logical decomposition
- **Creative Branch**: Lateral thinking, novel solutions
- **Skeptical Branch**: Critique-first, find flaws in assumptions
- **Pragmatic Branch**: Focus on practical implementation
- **Synthesis Branch**: Integrate multiple perspectives

### Step 3: Evaluate Branches
Each branch returns:
- Approach description
- Key insights
- Confidence score (0-1)
- Recommendations

I evaluate using:
- Self-consistency (do branches converge?)
- Evidence quality (backed by verification?)
- Risk assessment (what could go wrong?)

### Step 4: Return Recommendation
Synthesize the highest-confidence approach and present:
- Recommended path with rationale
- Alternative considerations
- Confidence score
- Next steps

## Research Basis

Based on "Can AIs Like ChatGPT Think?" (ai-consciousness.org):
- 18× improvement on Game of 24 (4% → 74% success)
- Parallel branch exploration + self-consistency evaluation
- Outperforms single-threaded chain-of-thought

## Configuration

**Environment Variables**:
- `TOT_ENABLED=true` - Enable/disable Tree-of-Thoughts (default: true)
- `TOT_BRANCHES=3` - Number of parallel branches (default: 3)
- `TOT_TIMEOUT=300` - Timeout per branch in seconds (default: 300)

## Examples

**User**: `/tot Should I use Redis or Memcached for caching?`

**Response**:
```
Exploring 3 reasoning branches in parallel...

Branch 1 (Analytical): Performance comparison...
Branch 2 (Pragmatic): Implementation complexity...
Branch 3 (Skeptical): Operational overhead...

RECOMMENDATION: Redis (confidence: 0.8)
- Reasons: Data structures, persistence, ecosystem
- Alternative: Memcached for pure read-heavy workloads
- Next step: Prototype Redis connection pooling
```

## Implementation Notes

This skill uses the tot_core.py module for the Tree-of-Thoughts reasoning engine. The core module provides:

- `ThoughtBranch` dataclass for branch representation
- `TreeOfThoughts` class with `explore_branches()` and `evaluate_branches()` methods
- Agent tool integration for parallel subagent spawning
- Async/await support for parallel execution

## See Also

- Self-reflection gate (Phase 1): Detects low-confidence claims
- Chain-of-Draft (Phase 3): Optimizes verbose reasoning
