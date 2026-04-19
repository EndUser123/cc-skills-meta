---
name: cwo
description: CWO 16-step unified orchestration with CKS handoff, ML health check, and step validation
version: "1.0.0"
status: "stable"
category: orchestration
triggers:
  - /cwo
aliases:
  - /cwo

suggest:
  - /nse
  - /workflow
  - /quadlet
---

# /cwo — CWO 16-Step Unified Orchestration

## Purpose

CWO 16-step unified orchestration with CKS handoff, ML health check, and step validation. Comprehensive workflow orchestrator for implementation tasks, from pre-execution checklist through post-completion cleanup.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **CLI wired**: Python CWO engine runs directly via `features.cwo` module
- **Evidence-based**: RWV Protocol (Read-before-write), pre-discovery, validation at each step
- **Type-fixing mode**: Auto-detected for mypy/type errors (skips TDD, focuses on validation)

### Technical Context
- **16 steps**: 5 phases — Pre-Execution (0.1-0.6), Discovery (1-3), Planning (4-6), Execution (7-9), Completion (10-12), Post-Completion (13-16)
- **Modes**: comprehensive (16 steps), type_fixing (Phase 0+4), phase-specific (0-5 only)
- **Ralph Loop**: Auto-enabled for implementation/refactoring/bugs, disabled for research/analysis/docs
- **Outputs**: specify.md, requirements.md, research.md, arch.md, plan.md, tasks.json, synthesis.md, metrics.md, closure.json

### Architecture Alignment
- Integrates with /nse (next steps), /workflow (status), /quadlet (atomic operations)
- Links to /cwo-orchestrator (terminal monitoring), /workflow-status (progress display)
- Part of orchestration ecosystem

## Your Workflow

1. **PHASE 0 (Pre-Execution)** — TaskMaster resolution, ML health check, context usage, RWV protocol, pre-discovery, Ralph assessment
2. **PHASE 1 (Discovery)** — Input validation, requirements analysis, research intelligence
3. **PHASE 2 (Planning)** — Architecture analysis, implementation planning, task decomposition, UAF subagent plan
4. **PHASE 3 (Execution)** — Implementation with TDD, quality gate validation, metrics performance analysis
5. **PHASE 4 (Completion)** — Results synthesis with adversarial critique, documentation generation, task registry update
6. **PHASE 5 (Post-Completion)** — Final quality gate, command registry update, skills/agents sync, documentation cleanup

## Validation Rules

- **Before execution**: Complete Phase 0 pre-execution checklist
- **Before each step**: Validate step prerequisites, health checks
- **During execution**: Ralph loop for implementation tasks (auto-enable based on task type)
- **After completion**: Final quality gate, registry sync, cleanup

### Prohibited Actions

- Skipping Phase 0 pre-execution checklist
- Bypassing RWV protocol (read-before-write)
- Running implementation without Ralph loop when appropriate
- Skipping step validation and health checks
- Accumulating subagent return values in orchestrator context instead of writing to disk and returning a Result Envelope
- Running high-output steps in parallel — stagger so only one large artifact is produced at a time
- Reading entire files when only a section is needed

## Subagent Output Routing Rules

### Subagent Result Envelope

Every subagent writes results to disk and returns only a small envelope. See canonical spec: `.claude/skills/shared/result-envelope.md`.

```json
{
  "status": "done" | "blocked" | "retry",
  "artifact": "relative/path/to/output/file.ext",
  "summary": "≤3 short lines — no code, no diffs, no large analysis",
  "metrics": { "artifact_bytes": 4821, "files_read": 3 }
}
```

The orchestrator consumes only Result Envelopes plus selective reads of artifacts; it never inlines full artifact content into its own context.

### Output Routing Tiers

| Tier | Name | Contains | Access |
|------|------|----------|--------|
| 0 | Orchestrator Window | Envelopes, decisions, IDs, file paths, short summaries | Active LLM context |
| 1 | Artifact Store | Full analyses, diffs, logs, tool outputs, phase summaries | Read via path from envelope |
| 2 | History Archive | Old handoff chains, prior session histories | Explicit retrieve only |

### Routing rules

- **Phase boundaries = context resets** — use the handoff system between phases; new session reads phase summary, not full conversation history.
- **Sequential by default within a phase** — tasks that produce large artifacts (diffs, full analyses, complete implementations) are high-output and must run sequentially. Tasks that produce only metadata or short structured JSON are low-output and may run in parallel.
- **Targeted file reads** — use `Grep` + `offset`/`limit`; when only part of a file is relevant, read only that part. If a full read is genuinely needed and the file is clearly large, write a summary artifact and return a pointer.
- **Spike before high-output steps** — when a step would produce a large artifact, produce signatures/interfaces only first and review before full implementation.

## Usage

```bash
# Full workflow (creates TSK if needed)
/cwo "implement user authentication system"

# Continue existing workflow
/cwo --continue

# Phase-specific execution
/cwo "analyze requirements" mode=phase_1_only
/cwo "pre-flight checks" mode=phase_0_only

# Skip validation (use with caution)
/cwo "quick fix" --force

# Ralph Loop controls
/cwo "implement feature" --ralph-loop              # Force enable
/cwo "research topic" --no-ralph-loop              # Disable auto
/cwo "complex refactor" --ralph-max-iterations=50  # Custom limit
```

## Execution Modes

| Mode            | Steps       | Description                                                     |
| --------------- | ----------- | --------------------------------------------------------------- |
| `comprehensive` | 0.1-16      | Full 16-step workflow (default)                                 |
| `type_fixing`   | Phase 0 + 4 | Type error fixing: Setup + Validation (skips TDD)               |
| `phase_0_only`  | 0.1-0.5     | Pre-Execution Checklist                                         |
| `phase_1_only`  | 1-3         | Discovery: Input, Requirements, Research                        |
| `phase_2_only`  | 4-6         | Planning: Architecture, Implementation Plan, Task Decomposition |
| `phase_3_only`  | 7-9         | Execution: Implementation, Quality Gates, Metrics               |
| `phase_4_only`  | 10-12       | Completion: Synthesis, Documentation, Registry Update           |
| `phase_5_only`  | 13-16       | Post-Completion: Final Quality, Registry Sync, Cleanup          |

### Type-Fixing Mode

**Purpose:** Refactoring existing code to fix type errors (mypy strict mode compliance)

**Auto-Detection:** Automatically enabled when task description contains:
- `mypy`, `type error`, `type fixing`, `type-check`, `typing`, `annotation`
- `strict mode`, `type hints`, `pyright`, `pyre`, `type validation`

**Workflow:** FIX → VALIDATE → COMMIT

## The 16 Steps

### Phase 0: Pre-Execution Checklist (Steps 0.1-0.6)

| Step | Name                  | Output                       |
| ---- | --------------------- | ---------------------------- |
| 0.1  | TaskMaster Resolution | TSK directory                |
| 0.2  | ML Health Check       | Health status                |
| 0.3  | Context Usage Check   | Token budget                 |
| 0.4  | RWV Protocol          | Read-before-write            |
| 0.5  | Pre-Discovery         | `discovery_session.json`     |
| 0.6  | Ralph Loop Assessment | `ralph_loop_assessment.json` |

### Phase 1: Discovery (Steps 1-3)

| Step | Name                       | Output            |
| ---- | -------------------------- | ----------- | ----------------- |
| 1    | Input Validation & Quality | `specify.md`      |
| 2    | Requirements Analysis      | `requirements.md` |
| 3    | Research Intelligence      | `research.md`     |

### Phase 2: Planning (Steps 4-6)

| Step | Name                    | Output               |
| ---- | ----------------------- | ------------------- | -------------------- |
| 4    | Architecture Analysis   | `arch.md`            |
| 5    | Implementation Planning | `plan.md`            |
| 6    | Task Decomposition      | `tasks.json`         |
| 6.1  | UAF Subagent Plan       | `subagent_plan.json` |

### Phase 3: Execution (Steps 7-9)

| Step | Name                         | Output         |
| ---- | ---------------------------- | -------------------------------- | -------------- |
| 7    | Implementation Execution     | Code + TDD     |
| 8    | Quality Gate Validation      | `qual-gate.md` |
| 9    | Metrics Performance Analysis | `metrics.md`   |

### Phase 4: Completion (Steps 10-12)

| Step | Name                     | Output                  |
| ---- | ------------------------ | ------------------------- | ----------------------- |
| 10   | Results Synthesis        | `synthesis.md`          |
| 10.1 | Adversarial Critique     | `synthesis_critique.md` |
| 11   | Documentation Generation | `doc.md`                |
| 12   | Task Registry Update     | Task completion         |

### Phase 5: Post-Completion & Cleanup (Steps 13-16)

| Step | Name                    | Output               |
| ---- | ----------------------- | -------------------- | -------------------- |
| 13   | Final Quality Gate      | `qual-gate-final.md` |
| 14   | Command Registry Update | `skill_registry`     |
| 15   | Skills/Agents Sync      | Sync report          |
| 16   | Documentation & Cleanup | `closure.json`       |

## Ralph Loop Integration

**Auto-Enable Behavior:**

| Task Type      | Auto-Enable? | Examples                      |
| -------------- | ------------ | ----------------------------- |
| Implementation | ✅ Yes       | `implement auth system`       |
| Refactoring    | ✅ Yes       | `refactor database layer`     |
| Bug fixes      | ✅ Yes       | `fix authentication bug`      |
| Research       | ❌ No        | `research codebase patterns`  |
| Analysis       | ❌ No        | `analyze performance metrics` |
| Documentation  | ❌ No        | `document API endpoints`      |

## See Also

- `/cwo-orchestrator` - Terminal A monitoring for parallel subagent coordination
- `/workflow-status` - Display CWO12 workflow progress and recommendations
