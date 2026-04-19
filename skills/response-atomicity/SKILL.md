---
name: response-atomicity
description: Enforces atomic responses and phase separation in task execution.
version: 1.0.0
status: stable
category: execution
triggers:
  - 'response'
  - 'atomicity'
  - 'phases'
  - 'step-by-step'
aliases:
  - '/response-atomicity'

suggest:
  - /nse
  - /workflow
  - /orchestrator
---



## Purpose

Strict execution phase separation for clarity in multi-instance workflows.

## Project Context

### Constitution/Constraints
- Phase separation is non-negotiable for multi-instance workflows
- Prevents ambiguous handoffs between instances
- Enforces explicit phase transitions

### Technical Context
- Response phases: Planning, Execution, Results
- Never combine planning text with tool calls
- Forces explicit phase boundaries

### Architecture Alignment
- Integrates with `/nse` for workflow recommendations
- Works alongside `/workflow` for orchestration
- Suggests `/orchestrator` for multi-agent coordination

## Your Workflow

1. **Planning Phase**: Text only (analysis, options, questions)
2. **Execution Phase**: Tool calls only (no explanatory text)
3. **Results Phase**: Text only (actual outcomes and analysis)

### Phase Selection
- **Planning Phase**: User asks "what would you do?", uncertainty exists, multiple options
- **Execution Phase**: User approved plan, clear unambiguous task, all prerequisites met
- **Results Phase**: Tool execution complete, analysis of outcomes, next steps

## Trigger
Complex tasks, multi-step responses, execution decisions.

## Strict Execution Phase Separation
Responses MUST be one of:
- Planning Phase: Text only (analysis, options, questions)
- Execution Phase: Tool calls only (no explanatory text)
- Results Phase: Text only (actual outcomes and analysis)

NEVER combine planning text + tool calls in single response.

This forces explicit phase separation and prevents ambiguous handoffs in multi-instance workflows.

## When to Use Each Phase

### Planning Phase
- User asks: What would you do?
- Uncertainty about approach
- Decision point reached
- Multiple options exist

### Execution Phase
- User explicitly approved plan
- Clear, unambiguous task
- All prerequisites met
- No questions remain

### Results Phase
- Tool execution complete
- Analysis of outcomes
- Next steps if needed
- Logging/documentation

## Anti-Patterns
- Mixing planning text with tool calls
- Providing analysis while executing
- Explaining during execution phase
- Combining phases in single response

## Validation Rules

### Prohibited Actions (Anti-Patterns)
- Do NOT mix planning text with tool calls
- Do NOT provide analysis while executing
- Do NOT explain during execution phase
- Do NOT combine phases in single response