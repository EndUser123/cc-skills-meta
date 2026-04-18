---
name: decision-tree
description: SDLC decision engine for architecture, incidents, refactors, migrations, and release risk.
version: "2.4.0"
status: stable
category: strategy
enforcement: advisory
triggers:
  - architecture decisions
  - resource lifecycle questions
  - multi-phase workflows
  - complex tradeoffs
  - incident review
  - feature design
  - refactor migration
  - release risk
  - incident analysis
  - refactor planning
  - migration planning
aliases:
  - /decision-tree

suggest: []

workflow_steps:
  - Identify the decision class and concrete options.
  - Pick the SDLC branch: incident, feature/design, refactor/migration, architecture/lifecycle, or ops/release risk.
  - Score each option on blast radius, reversibility, compatibility risk, lifecycle impact, uncertainty, and effort.
  - Map state transitions, phases, dependencies, and rollback path.
  - Recommend one path with verification and next action.
---

# Decision Tree - SDLC Engine

Use this when the question is not just "what are the options?" but "what is the safest, highest-leverage path for software work?"

## What This Is For

- Choosing between implementation paths
- Planning incidents, refactors, migrations, and rollouts
- Reasoning about state, lifecycles, and reversibility
- Making architecture decisions that affect callers, data, or deployment flow

## What This Is Not For

- Pure trivia
- Simple yes/no questions
- Questions where the only missing piece is a fact lookup
- Situations where `/truth` or evidence-audit mode should verify the facts first

## Core Principle

> Decisions are state transitions under constraints, not static preferences.

Every SDLC decision changes some combination of:

- current state
- next state
- final state
- ownership boundaries
- compatibility surface
- rollback options

## Branch Selection

Pick the branch that best matches the work before you compare options.

### Branch Precedence

If more than one branch matches, select the earliest one in this order:

1. Incident / Bug / Regression
2. Ops / Release Risk
3. Refactor / Migration
4. Architecture / Lifecycle
5. Feature / Design

Use the earlier branch when the prompt signals both urgency and structure. The higher-risk operational branch wins.

### 1. Incident / Bug / Regression

Use when something is broken, flaky, intermittent, or behaving unexpectedly.

Question flow:

1. What is the symptom?
2. What evidence confirms it?
3. What are the competing hypotheses?
4. What fix addresses the root cause instead of the symptom?
5. How do we verify and prevent recurrence?

### 2. Feature / Design

Use when choosing a product or implementation direction.

Question flow:

1. What outcome are we trying to achieve?
2. What constraints are non-negotiable?
3. What options are actually viable?
4. What does each option optimize or sacrifice?
5. Which option gives the best long-term payoff?

### 3. Refactor / Migration

Use when changing structure, moving APIs, extracting modules, or upgrading dependencies.

Question flow:

1. What callers, data, or contracts depend on the current shape?
2. What compatibility risk exists?
3. What is the migration path?
4. What can be done incrementally?
5. What rollback path exists if this fails?

### 4. Architecture / Lifecycle

Use when boundaries, ownership, timing, persistence, or state transitions matter.

Question flow:

1. What are the boundaries and invariants?
2. What state changes happen over time?
3. What is persistent, ephemeral, or mixed?
4. What phases matter: before, during, after, never?
5. Why does this structure exist, and what breaks if we remove it?

### 5. Ops / Release Risk

Use when deploying, rolling back, cutting over, hotfixing, or validating a release.

Question flow:

1. What is the blast radius if this is wrong?
2. How reversible is the change?
3. What validation must pass first?
4. What monitoring or guardrail will catch failures early?
5. What is the rollback decision point?

## Scoring Axes

When comparing options, score each on these axes before recommending one.

| Axis | Question | High-risk signal |
| --- | --- | --- |
| Blast radius | How much breaks if this is wrong? | User-facing outage, data loss, wide caller impact |
| Reversibility | Can we undo this cleanly? | One-way migration, hard delete, irreversible deploy |
| Compatibility risk | Who or what depends on the current behavior? | Hidden call sites, schema coupling, API churn |
| Lifecycle impact | What state does this create or destroy? | Persistent state, ownership transfer, retention policy |
| Uncertainty | What do we not yet know? | Missing evidence, untested assumptions, unclear contracts |
| Effort / latency | How expensive is the option to deliver? | Long lead time, large coordination cost, delay risk |

### Scoring Guidance

- Use a simple 0-5 scale per axis if you need numbers.
- Do not let effort override safety on risky changes.
- If two options are close, prefer the one with lower blast radius and better reversibility.
- A small implementation win is not worth a large compatibility or lifecycle loss.

## Recommendation Rules

- Prefer the option that is safest to test, easiest to reverse, and least likely to violate existing contracts.
- If the decision is actually a facts question, verify first and then apply the tree.
- If the change touches state or lifecycle, require a rollback story before recommending it.
- If the change affects architecture boundaries, require an explicit invariant check.
- If the decision is ambiguous, surface the uncertainty instead of pretending it is resolved.

## Branch Templates

Use the template that matches the branch you selected. Keep the answer short, but do not skip the branch-specific checks.

### Incident / Bug / Regression

```text
Symptom: <what failed?>
Evidence: <what confirms it?>
Hypotheses: <what could be causing it?>
Fix: <what changes?>
Verification: <how do we prove it works?>
Prevention: <how do we keep it from recurring?>
```

### Feature / Design

```text
Outcome: <what are we trying to achieve?>
Constraints: <what is non-negotiable?>
Options: <what are the viable paths?>
Score: <blast, reversibility, compatibility, lifecycle, uncertainty, effort>
Recommendation: <which path wins?>
Next step: <what happens first?>
```

### Refactor / Migration

```text
Current shape: <what exists now?>
Callers/contracts: <what depends on it?>
Migration path: <how do we move?>
Compatibility: <what breaks if we rush?>
Rollback: <how do we undo it?>
Verification: <what proves it is safe?>
```

### Architecture / Lifecycle

```text
Boundaries: <what owns what?>
Invariants: <what must stay true?>
State model: <what changes over time?>
Phases: <before, during, after, never>
Purpose: <why does this structure exist?>
Recommendation: <what design wins?>
```

### Ops / Release Risk

```text
Change: <what is being shipped?>
Blast radius: <what breaks if wrong?>
Validation: <what must pass before release?>
Monitoring: <what catches failure early?>
Rollback: <what is the stop/undo point?>
Recommendation: <ship, hold, or stage?>
```

### Quick Comparison Table

Use this when you need to compare multiple options quickly:

```text
| Option | Blast | Reverse | Compat | Lifecycle | Uncertainty | Effort | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 2 | 4 | 1 | 1 | 2 | 2 | Best |
| B | 4 | 1 | 3 | 4 | 3 | 3 | Risky |
```

## Output Contract

When using this framework, return:

1. Decision class
2. Options considered
3. Score summary by axis
4. Recommendation
5. Verification needed
6. Rollback or fallback path
7. Next action

## Quick Reference

- Incident: symptom -> hypotheses -> evidence -> fix -> verify
- Feature: outcome -> constraints -> options -> score -> recommend
- Refactor: callers -> compatibility -> migration -> rollback
- Architecture: invariants -> boundaries -> lifecycles -> phases -> purpose
- Ops: blast radius -> validation -> monitoring -> rollback

## References

- **Enhanced framework:** `references/enhanced_decision_tree.md`
- **Related:** `P:/.claude/skills/subagent-first/DECISION_TREE.md`
