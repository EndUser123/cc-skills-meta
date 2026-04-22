---
name: reason
description: Intelligent reasoning orchestrator. Use when the user wants stronger analysis, review, diagnosis, design thinking, optimization, or when something feels off.
enforcement: advisory
workflow_steps:
  - id: route
    description: Classify reasoning mode and depth from user prompt
  - id: execute
    description: Run local/targeted/tribunal path based on depth
  - id: synthesize
    description: Normalize output to standard contract shape
---

# /reason

Use this skill when the user wants better thinking rather than just a direct answer.

This skill does four things:
1. Diagnoses what kind of reasoning is needed.
2. Chooses an escalation depth.
3. Routes to the best available existing skill(s).
4. Returns a standard synthesis shape.

## When to use

Invoke `/reason` when the user:
- wants a stronger review of an answer, design, patch, or plan
- is unhappy with the current solution
- wants help choosing between options
- wants root-cause analysis
- wants optimization advice
- says something feels off

## Reasoning modes

### review
Use when there is an existing answer, solution, patch, or plan that needs critique.

### design
Use when the user needs options, architecture, or solution creation.

### diagnose
Use when something is broken and the cause is unclear.

### optimize
Use when the system works but should be improved.

### off
Use when the user has vague distrust, uncertainty, or discomfort with the current direction.

## Escalation depths

### depth 0: local
Run only the local THINK-style route.

### depth 1: targeted
Run local reasoning plus one or two specialists.

### depth 2: tribunal
Run local reasoning plus the parallel multi-model path.

## Standard output contract

Always return:
- Route chosen
- Best current conclusion
- Strongest challenge
- Biggest uncertainty
- Best next action

Include `Minority warning` when available.

## Execution

Run the router:

```bash
python3 ~/.claude/skills/reason/reason_router.py --prompt "$ARGUMENTS"

If no explicit arguments are provided, the router should still inspect context and produce a best-effort result.