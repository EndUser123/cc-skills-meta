---
name: evolve
version: 1.0.3
description: Unified modernization workflow to transform working code into high-standard systems.
category: evolution
domain: evolution
triggers:
  - 'evolve this'
  - 'modernize this'
  - 'technical debt'
  - 'refactor for quality'
  - 'code smell'
  - 'outdated patterns'
  - 'Python 2025 migration'
argument-hint: <target_directory_or_file>
context: main
user-invocable: True
status: stable
owner: you
estimated_tokens: 1000-5000
typical_response_time: 45-90s
context_required: codebase structure, complexity metrics, project standards, performance baseline
depends_on_skills: ['/debug', '/rca', '/analysis-profile', '/analysis-audit', '/learn', '/llm-debate', '/brainstorm', '/tdd', '/aid']
requires_tools: ['python', 'radon', 'lizard', 'git', 'uv']
aliases:
  - '/evolve'

suggest:
  - /comply
  - /test
  - /refactor
---


# /evolve - Modernization Mission Control

## Purpose

Unified modernization workflow to transform working code into high-standard systems. Unifies diagnostic and transformation tools into a 4-phase process to eliminate technical debt and apply project standards.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **No enterprise patterns**: Filter out monitoring layers, circuit breakers, microservices, scalability requirements
- **Constitutional filter required**: All recommendations must pass SoloDevConstitutionalFilter
- **CC threshold applies to ALL code**: No distinction between new and legacy — if CC > 10, refactor it

### Technical Context
- **4-phase process**: AUDIT (measure debt) → STRATEGY (design abstraction) → EXECUTE (transform code) → HARDEN (certify excellence)
- **Key tools**: /complexity, /analyze, /profile, /design, /refactor, /aid, /checkpoint, //p-2025, /verify, /learn
- **Success criteria**: All CC > 10 functions refactored, Python 2025 compliance, performance measured, dead-code purged, CKS updated
- **Flow spec**: flows/modernize.md

### Architecture Alignment
- Integrates with /debug (triage), /rca (systemic flaws), /analysis-profile (baseline/verification)
- Links to /comply (standards), /test (coverage), /refactor (multi-file changes)
- Part of code quality and modernization ecosystem

## Your Workflow

1. **READ FLOW** — Load flows/modernize.md for detailed workflow
2. **AUDIT (Phase 1)** — Measure debt: /complexity, /analyze --focus quality, /profile --baseline
3. **STRATEGY (Phase 2)** — Design abstraction: /design, /plan, ADR auto-draft
4. **EXECUTE (Phase 3)** — Transform code: /refactor, /aid refactor, /checkpoint, /analyze --focus dead-code
5. **HARDEN (Phase 4)** — Certify excellence: //p-2025, /verify, /audit, /profile --compare, /learn
6. **PRESENT NEXT STEPS** — Show completion markers for finished phases

## Validation Rules

- **Before modernization**: Run baseline (complexity, profile) to measure debt
- **Before recommendations**: Apply SoloDevConstitutionalFilter check
- **Before claiming complete**: Verify CC > 10 functions are refactored (ALL code, not just "new")
- **After changes**: Run /verify to check regressions, /profile --compare for performance

### Prohibited Actions
- Refactoring without baseline (run complexity/profile FIRST)
- Only refactoring "new code" (CC threshold applies to ALL code)
- Guessing the new pattern (use /design to validate strategy)
- Editing without /checkpoint safety for multi-file changes

## ⚡ ALLOCATION DIRECTIVE

**When `/evolve` or `/modernize` is invoked:**

1.  **Read [Modernization Flow](flows/modernize.md)**.
2.  **Execute Phase 1 (AUDIT)** automatically.
    - _For large codebases (>50 files), consider running audit in a subagent via `context: fork` to preserve main context tokens._
3.  **Present findings** and ask to proceed to Phase 2 (STRATEGY).

---

## The 4-Phase Core

| Phase           | Goal               | Key Tools                                                                 |
| --------------- | ------------------ | ------------------------------------------------------------------------- |
| **1. AUDIT**    | Measure Debt       | `/complexity`, `/analyze --focus quality`, `/profile --baseline`          |
| **2. STRATEGY** | Design Abstraction | `/design`, `/plan`, ADR Auto-draft                                          |
| **3. EXECUTE**  | Transform Code     | `/refactor`, `/aid refactor`, `/checkpoint`, `/analyze --focus dead-code` |
| **4. HARDEN**   | Certify Excellence | `//p-2025`, `/verify`, `/audit`, `/profile --compare`, `/learn`  |

**⚠️ MISSING TOOL**: `/profile` command is referenced throughout this workflow but **does not exist**. Current workaround: Use `/perf` (detects anti-patterns) or manual timing. The `/profile` command should provide:
- `/profile <target> --baseline` - Establish performance baseline (resource usage, timing)
- `/profile <target> --compare` - Compare before/after modernization metrics

This is a **gap in tooling** that prevents complete workflow execution.

---

## Success Criteria

- [ ] **ALL** high-complexity functions (CC > 10) are extracted or simplified.
  - **No distinction between new and legacy code** — if `radon cc` reports CC > 10, it gets refactored.
  - Do NOT skip "old code" or "code I didn't write" — CC threshold applies to the entire codebase.
- [ ] Code complies with `/p-2025` production standards.
- [ ] Performance delta (L3 metrics) is measured and verified.
- [ ] Orphaned dead-code is purged post-refactor.
- [ ] Project Constitution and CKS are updated (/learn).

## Failure Modes

| Failure            | Symptom                                    | Recovery                                        |
| ------------------ | ------------------------------------------ | ----------------------------------------------- |
| **Bloat**          | Refactor suggests too many changes at once | Use `/plan` to chunk the evolution.             |
| **Regressions**    | `/verify` fails or performance drops       | Roll back via `/checkpoint-restore`.            |
| **Logic Mismatch** | AI misunderstands legacy intent            | Use `/aid refactor` for deep semantic analysis. |

## Integration

- **`/debug`** — Use for triage if modernization reveals hidden bugs.
- **`/rca`** — Use if a hotspot reveals a systemic flaw.
- **`/analysis-profile`** — Used for baseline and verification gains.
- **`/learn`** — The final "Seal" to update the CKS.

## Anti-Patterns

| Don't                       | Do Instead                                                   |
| --------------------------- | ------------------------------------------------------------ |
| Refactor without a baseline | Run `/complexity` and `/profile --baseline` FIRST (Phase 1). |
| **Only refactor "new code"** | **CC threshold applies to ALL code — legacy functions with CC > 10 must also be refactored.** |
| Guess the new pattern       | Use `/design` to validate Strategy (Phase 2).                  |
| Edit without safety         | Run `/checkpoint` BEFORE any multi-file change.              |

## Constitutional Compliance (REQUIRED)

**CRITICAL:** All modernization recommendations MUST be filtered against solo-dev constitutional constraints.

### Prohibited Patterns (Auto-Filter)

Before suggesting any modernization, check against these prohibited patterns (CLAUDE.md:240-262):

| Pattern | Filter Because | Alternative |
|---------|---------------|-------------|
| `lock ordering`, `acquisition order` | Enterprise bloat | Use single RLock per object |
| `continuous monitoring` | Background service prohibited | Use on-demand `/health` |
| `real-time metrics` | Background service prohibited | Use query-based metrics |
| `self-healing` | Autonomous execution prohibited | Manual fix with approval |
| `scalability requirement` | Enterprise pattern prohibited | Optimize when needed |
| `enterprise-grade` | Enterprise pattern prohibited | Use simple solution |

### Required Filter Step

**Before generating recommendations, ALWAYS run:**

```python
# Import the constitutional filter
from src.core.solo_dev_constitutional_filter import SoloDevConstitutionalFilter

filter_obj = SoloDevConstitutionalFilter()

# Check each proposed modernization
for action in proposed_modernizations:
    result = filter_obj.check_action_item(action)
    if result.violates_constitution:
        # Skip this action - don't suggest it
        continue
```

### Why This Matters

Modernization suggestions are high-risk for enterprise bloat:
- "Add monitoring layer" → continuous tracking (prohibited)
- "Design for horizontal scalability" → unnecessary complexity
- "Implement circuit breaker pattern" → enterprise pattern
- "Extract to microservice" → over-engineering for solo dev

---

## NEXT STEPS

1. `/complexity` — Find hotspots
2. `/profile --baseline` — Establish baseline
3. `/design` — Validate patterns (if CC > 10)
4. `/refactor` — Apply synergies (if CC > 10)
5. `/analyze --focus dead-code` — Purge orphans
6. `/verify` — Validation
7. `/learn` — Knowledge sync

*After audit, show updated block with completion markers:*

**AUDIT COMPLETE**
Highest CC: [value] | Average: [value]

---
## NEXT STEPS
1. `/complexity` — Find hotspots ✓
2. `/profile --baseline` — Establish baseline
3. `/design` — Validate patterns (if CC > 10)
4. `/refactor` — Apply synergies (if CC > 10)
5. `/analyze --focus dead-code` — Purge orphans
6. `/verify` — Validation (recommend)
7. `/learn` — Knowledge sync (recommend)

**If completed:**

```

✅ Modernization complete. Code is production-grade, future-proof, and debt-free.

```

---

**Version:** 1.0.3
**Updated:** 2026-01-13
