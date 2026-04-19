---
name: subagent-driven-development
description: Execute implementation plans by dispatching specialized subagents with two-stage review.
version: "1.0.0"
status: stable
category: strategy
triggers:
  - 'implement this plan'
  - 'execute the plan'
  - 'work through these tasks'
  - 'break this down and implement'
aliases:
  - '/subagent-driven-development'

suggest:
  - /build
  - /tdd
  - /qa
---


# Subagent-Driven Development

**Primary Directive**: Execute implementation plans by dispatching fresh subagents for each task with systematic review checkpoints.

## Purpose

Execute implementation plans by dispatching specialized subagents with two-stage review.

## When This Skill Activates

Use when:
- User provides an implementation plan with multiple steps
- User asks to "execute this plan" or "implement these tasks"
- Work requires multiple files or coordinated changes
- Task would benefit from specialized agent expertise

## Project Context

### Constitution/Constraints
- TDD compliance enforced via hooks (PreToolUse_tdd_gate.py)
- One TDD cycle = one task (RED, GREEN, or REFACTOR)
- Tasks estimated >30 minutes must be decomposed
- TaskMaster integration for complexity assessment

### Technical Context
- Task size: 10-30 minutes sweet spot
- One TDD phase per task (RED OR GREEN OR REFACTOR)
- Single method/function per task
- TaskMaster complexity scoring: 1-3 (dispatch), 4+ (decompose)

### Architecture Alignment
- Part of subagent delegation strategy
- Works with subagent-first skill
- Integrates with TaskMaster for tracking
- Aligns with /tdd PARALLEL delegation enforcement

## Core Workflow

### Phase 1: Plan Analysis
1. **Read the plan** - Identify all tasks, dependencies, and acceptance criteria
2. **Verify prerequisites** - Ensure all context is available
3. **Identify task types** - Categorize by required expertise
4. **Check complexity with /tm** - For each unclear or broad task
5. **Decompose if needed** - Use `/tm expand` for tasks with complexity >3

### Phase 2: Task Execution Loop

For each task:
1. **Dispatch Subagent** - Select specialist, provide context (see `references/task-format-and-examples.md` for dispatch template)
2. **Review 1: Spec Compliance** - Complete? Acceptance criteria met?
3. **Review 2: Code Quality** - Readable? No bugs? Tests pass?
4. **Verification & Checkpoint** - Run tests, present result, await confirmation

### Phase 3: Completion & Synthesis
1. Verify integration - All pieces work together
2. Run full test suite - Catch regressions
3. Summary report - Document changes
4. Next steps - Identify follow-up work

## Validation Rules

### Prohibited Actions
- Dispatching tasks estimated >30 minutes without decomposition
- Mixing TDD phases (RED+GREEN+REFACTOR in one task)
- Assigning multiple methods in one task
- Skipping verification to save time
- Proceeding without user checkpoint for significant changes
- Using vague task descriptions ("implement the module")
- Returning subagent output inline instead of writing to disk with Result Envelope
- Running high-output tasks in parallel (stagger sequentially)
- Passing entire plan documents into subagent prompts
- Reading entire files when only a function or block is needed

### Task Decomposition Required When
- Multiple test files involved
- Multiple TDD phases in one description
- >2 implementation files to modify
- Both implementation AND integration in one task
- Estimated >30 minutes

## Subagent Output Routing

See `references/output-routing.md` for Result Envelope spec, routing tiers, and context management rules.

**Key rule**: Orchestrator context overflow is the primary failure mode. Subagents write to disk, return only envelopes.

## Task Size Quick Reference

| Duration | Assessment | Action |
|----------|------------|--------|
| < 10 min | Too granular | Group related TDD steps |
| **10-30 min** | Sweet spot | One TDD cycle (RED, GREEN, or REFACTOR) |
| 30-60 min | Caution | Only if single cohesive feature |
| > 60 min | Too large | Break it down immediately |

## TDD Phase Boundaries

| TDD Phase | Task Scope | Duration |
|-----------|------------|----------|
| RED | Write ONE test or test method | 5-15 min |
| GREEN | Implement ONE method to pass | 10-20 min |
| REFACTOR | Extract/clean ONE thing | 10-20 min |
| INTEGRATION | Connect TWO existing pieces | 15-30 min |

**Never mix phases in one task**. One TDD cycle = one task.

## Pre-Dispatch Checklist

Before assigning ANY subagent task, verify:

- [ ] **Single TDD phase** (RED OR GREEN OR REFACTOR, never mixed)
- [ ] **Single method/function** (one test method or one implementation method)
- [ ] **Estimated ≤ 30 minutes** (decompose if larger)
- [ ] **Specific acceptance criteria** (testable, not vague)
- [ ] **Exact file paths** listed
- [ ] **Verification command** specified with expected result

If any checkbox fails → **decompose first**.

## Subagent Selection Guide

| Task Type | Recommended Specialist |
|-----------|----------------------|
| Backend/API | python-core, python-web |
| Frontend/UI | react-specialist, ui-ux-expert |
| Testing | qa-engineer, code-reviewer |
| Architecture | architect |
| Security | bug-scan |
| Performance | ml-engineer (for optimization) |
| Documentation | technical-writer (generic) |
| General | general-purpose |

## Anti-Patterns

Do NOT:
- Dispatch a task estimated >30 minutes (decompose first)
- Mix TDD phases (RED+GREEN+REFACTOR in one task)
- Assign multiple methods in one task
- Skip verification to save time
- Proceed without user checkpoint for significant changes
- Use vague task descriptions ("implement the module")

Instead:
- One TDD phase per task (RED OR GREEN OR REFACTOR)
- One method/function per implementation task
- Integration as separate task after implementation
- Verify each task before proceeding
- Specific: "Implement check_ruff() method"

## Integration with CSF NIP Skills

Works alongside:
- **read-before-write** - Subagents must read before editing
- **debug-triage** - Use if subagent encounters errors
- **architecture-decision-framework** - For architectural decisions
- **git-workflow** - Follow for commit practices

## User Override

User can override this workflow by:
- Saying "skip checkpoint" to continue without pause
- Providing explicit task order: "do tasks 1, 3, 5 then 2, 4"
- Saying "stop" to halt execution and review progress

## Plan Generation

When user asks to implement something but no plan exists, first generate a plan using granular-plan-writing skill.

### Plan Generation Triggers

| User Says | Action |
|-----------|--------|
| "implement X" | Generate plan → Execute |
| "create a plan for X" | Generate plan only |
| "plan and implement X" | Generate plan → Execute |
| "break this down and implement" | Generate plan → Execute |
| "work through these tasks" | Skip to execution (plan provided) |

### Plan Quality Checklist

Before executing a generated plan, verify:
- [ ] All tasks have exact file paths
- [ ] Each task is 2-5 minutes
- [ ] Acceptance criteria are specific
- [ ] Verification steps exist
- [ ] Dependencies are handled
- [ ] Total time estimate is reasonable

If any criteria fail, revise the plan before execution.

## Success Criteria

- Plan executed with all tasks complete
- All acceptance criteria met
- Tests passing, no regressions
- User satisfied with results

## Reference Files

| File | Contents |
|------|----------|
| `references/output-routing.md` | Result Envelope spec, routing tiers, context management |
| `references/task-format-and-examples.md` | Dispatch template, good/bad examples, task smell checklist, checkpoint template |
| `references/tdd-task-decomposition.md` | TDD size heuristics, decomposition signals, TDD hook alignment |
| `references/taskmaster-integration.md` | TaskMaster workflow, complexity thresholds, pre-dispatch flow |
| `references/workflow-examples.md` | Full workflow walkthrough, plan generation example, integration patterns |
