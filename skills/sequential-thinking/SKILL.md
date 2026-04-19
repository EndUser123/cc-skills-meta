---
name: sequential-thinking
description: Apply Generate → Critique → Improve loop to make reasoning smarter through self-reflection
version: "1.0.0"
status: beta
category: reasoning

# Sequential Thinking with Self-Reflection

## Purpose

Wrap user prompts in a self-reflection loop to improve reasoning quality by 20-60%. No external LLM needed - uses Claude's own mode-switching capability.

## When To Use

Trigger this skill when:
- User wants structured reasoning ("think through this", "analyze carefully")
- Complex decisions requiring careful consideration
- User asks for "sequential thinking" or "step-by-step reasoning"
- Detecting potential gaps in quick answers

## Core Principle

**Make Claude smarter, not just show the work.**

The value is in the quality improvement, not in displaying reasoning steps to the user.

## Process

### Stage 1: Generate

Generate initial reasoning using direct approach:
- Answer the user's question directly
- Provide clear, structured thinking
- Don't hold back - give your best answer

### Stage 2: Self-Critique

Switch to **analysis mode** and critique your own reasoning:

```
You are now in ANALYSIS MODE. Review your previous reasoning for:

1. Logical gaps - Did you skip reasoning steps?
2. Missing alternatives - What options didn't you consider?
3. Overconfidence - Are you certain when you should be uncertain?
4. Contradictions - Do your statements conflict?

Provide specific feedback for improvement.
```

### Stage 3: Refine

Switch to **improvement mode** and address the critique:

```
You are now in IMPROVEMENT MODE. Based on the critique above:

1. Address each identified issue
2. Fill in missing reasoning steps
3. Consider alternatives you missed
4. Resolve contradictions
5. Reduce overconfidence where appropriate

Provide your refined, improved answer.
```

### Stage 4: Quality Gate

Check if refinement passes quality threshold:
- All 5 stages covered (Problem → Research → Analysis → Synthesis → Conclusion)
- Claims are supported by reasoning
- No obvious contradictions
- Actually answers the user's question

If quality gate fails, iterate once more (max 2 iterations total).

### Stage 5: Return

Return the final refined answer to the user. Do NOT show the intermediate steps - just the improved result.

## Implementation

Use the Agent tool for mode switching:

```python
# Stage 1: Generate (already done - user's prompt)
initial_answer = <your direct response>

# Stage 2: Critique
Agent(
    subagent_type="general-purpose",
    prompt=f"""You are in ANALYSIS MODE. Review this reasoning:
{initial_answer}

Check for: logical gaps, missing alternatives, overconfidence, contradictions."""
)

# Stage 3: Refine
Agent(
    subagent_type="general-purpose",
    prompt=f"""You are in IMPROVEMENT MODE. Based on this critique:
{critique}

Improve your original answer. Address all issues."""
)

# Stage 4: Quality gate (internal check)
# Stage 5: Return final answer
```

## Key Rules

1. **Don't show your work** - Return only the final improved answer
2. **Max 2 iterations** - Don't infinite loop
3. **Actually use Agent tool** - This is what enables mode switching
4. **Fallback gracefully** - If Agent tool fails, return initial answer
5. **Be concise** - This isn't a demonstration, it's a quality improvement

## Example

**User:** "What's the best cache invalidation strategy?"

**Without self-reflection:** "Use TTL-based caching with write-through invalidation."

**With self-reflection:**
1. Generate: Initial answer about TTL + write-through
2. Critique: "Didn't consider cache stampede, didn't mention write-back, didn't address read-heavy vs write-heavy workloads"
3. Refine: "For read-heavy: cache-aside with TTL. For write-heavy: write-through with immediate invalidation. Watch for stampede - use probabilistic early expiration..."

## Anti-Patterns

**Don't:**
- Show all 5 stages to the user (they just want the answer)
- Use external LLM APIs (Claude is smart enough)
- Skip the Agent tool (that's how mode switching works)
- Iterate more than 2 times (diminishing returns)

**Do:**
- Return only the final improved answer
- Use Agent tool for critique and refinement
- Stop after quality gate passes or 2 iterations
- Focus on making Claude smarter, not showing the process

## Quality Indicators

You'll know it's working when:
- Your refined answer has nuances the initial one missed
- You acknowledge uncertainty where you were previously overconfident
- You consider alternatives you didn't think of initially
- The answer is more comprehensive yet still concise

## Integration Notes

- No changes to `reasoning/` package needed
- Works standalone as a skill
- Uses existing Agent tool infrastructure
- No external dependencies
