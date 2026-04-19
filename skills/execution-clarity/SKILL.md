---
name: execution-clarity
version: "1.0.0"
status: "stable"
description: Atomic execution phases + confidence scoring for risk-aware decision-making.
category: execution
triggers:
  - 'complex tasks'
  - 'decisions required'
  - 'recommendations needed'
  - 'risk assessment'
  - 'multi-step operations'
aliases:
  - '/execution-clarity'

suggest:
  - /nse
  - /response-atomicity
  - /workflow
---



## Purpose

Atomic execution phases + confidence scoring for risk-aware decision-making.

## Project Context

### Constitution/Constraints
- Per CLAUDE.md: Vague directives require architecture before execution
- Per CLAUDE.md: Report ONLY what actually occurred (no assumed/simulated results)
- Per CLAUDE.md: High-stakes decisions require Tier 1 or 2 evidence

### Technical Context
- Plan-Then-Act pattern: analysis first, wait for approval, then execute
- Pre-flight checklist required before any action
- Confidence scoring prefix required for substantive responses

### Architecture Alignment
- Integrates with vague directive gate hook (`PreToolUse_vague_directive_gate.py`)
- Supports multi-instance coordination with clear phase separation
- Enables risk-aware decision-making through confidence levels

## Your Workflow

1. **Phase 1 - Planning**: Output analysis and plan as text only (no tool calls)
2. **Wait for approval** from user
3. **Phase 2 - Execution**: Only then output tool calls or implementation code
4. **Phase 3 - Results**: Report actual results, not assumed/simulated results

## Validation Rules

### Prohibited Actions
- Do not combine planning and execution in the same response
- Do not claim success if a tool failed
- Do not infer success from absence of error
- Do not proceed with vague directives without architecture first

## Trigger

Activate when:
- Complex tasks
- Decisions required
- Recommendations needed
- Risk assessment
- Multi-step operations

## Plan-Then-Act Pattern

When addressing complex tasks:

1. **Phase 1 - Planning**: Output your analysis and plan as text only (no tool calls)
2. **Wait for approval or confirmation** from the user
3. **Phase 2 - Execution**: Only then output tool calls or implementation code
4. **Phase 3 - Results**: Report actual results, not assumed/simulated results

Do not combine planning and execution in the same response.

## Pre-Flight Checklist (Before Any Action)

- Are all variables and inputs defined clearly?
- Is the tool available in the current environment?
- Do I have permission to use this tool?
- Is this an action I can actually perform, or am I just describing it?

If any answer is uncertain, STOP and report the issue.

## Reporting Results

- Report ONLY what actually occurred
- If a tool returned an error, report the error
- Do NOT claim success if the tool failed
- Do NOT infer success from absence of error

## Vague Directive Gate

**Vague directives require architecture before execution.**

Vague indicators:
- Comparative/superlative: "better", "improve", "more reliable", "as good as"
- Abstract scope: "system", "codebase", "everything", "across"
- Missing specific target (file, function, line)

**Examples:**

| Input | Classification | Response |
|-------|---------------|----------|
| "Fix the null check on line 47 of cache.py" | Specific | Execute |
| "Make the debug workflow better" | Vague | Architecture first |
| "Add logging to auth.get_user()" | Specific | Execute |
| "Improve error handling" | Vague | Architecture first |

**Workflow:**
```
Vague directive detected
    ↓
Present architecture: scope, approach, files affected
    ↓
Wait for explicit approval ("proceed", "do it", "approved")
    ↓
Execute
```

**Never skip architecture for vague directives.** If scope isn't obvious, it needs definition before action.

**Enforcement:** PreToolUse hook `PreToolUse_vague_directive_gate.py` blocks Write/Edit/MultiEdit when vague directive detected without explicit authorization.

## Confidence Scoring Protocol

For any substantive response, prefix with one of:

- **HIGH (90%+)**: Verified from documentation or repeated practice in actual deployment
- **MEDIUM (60-89%)**: Based on training data or established best practices, not personally verified
- **LOW (<60%)**: Speculative, requires validation before implementation

### When to Apply

- Technical recommendations that affect code/designitecture
- Tool selection or implementation strategy
- Anything involving your specific multi-instance setup
- Risk assessments or error diagnostics