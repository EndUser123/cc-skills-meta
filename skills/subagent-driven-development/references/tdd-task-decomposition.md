# TDD Task Decomposition Reference

## Task Size Heuristics (Aligned with TDD Hooks)

| Duration | Assessment | Action |
|----------|------------|--------|
| < 10 min | Too granular | Group related TDD steps |
| **10 - 30 minutes** | Sweet spot | One TDD cycle (RED, GREEN, or REFACTOR) |
| 30 - 60 min | Caution | Only if single cohesive feature |
| > 60 min | Too large | Break it down immediately |

**Rule of thumb**: One TDD cycle = one task. If a task spans RED->GREEN->REFACTOR, split it.

## Alignment with TDD Hooks

This skill works with the TDD enforcement system (`.claude/hooks/PreToolUse_tdd_gate.py`):

| TDD Hook Behavior | Task Model |
|-------------------|------------|
| Blocks impl before test failure | RED phase = separate task |
| Blocks test edits during RED | GREEN phase = separate task |
| Tracks by test file path | One test file per task |
| 5-minute approval window | Checkpoint between tasks |
| NOTDD comment exemption | Use for non-implementation tasks |

**Critical**: TDD operates at the method/function level. Tasks must be sized accordingly.

## Decomposition Signals

A task needs splitting when you see:
- Multiple test files involved (TDD isolates to one)
- Multiple TDD phases in one description
- >2 implementation files to modify
- Both implementation AND integration in one task
- "And then..." or "After that..." in description
- Estimated >30 minutes

## TDD-Specific Decomposition

**One TDD phase = one task**. Each RED, GREEN, or REFACTOR phase is a separate subagent dispatch.

```
Bad: "Implement QualityChecker with check_ruff, check_mypy, check_pytest" (2 hours, mixed phases)

Good - Decomposed into TDD-aligned tasks:
  Task 1: "Write test for check_ruff()" [RED] (10 min)
  Task 2: "Implement check_ruff()" [GREEN] (15 min)
  Task 3: "Write test for check_mypy()" [RED] (10 min)
  Task 4: "Implement check_mypy()" [GREEN] (15 min)
  Task 5: "Write test for check_pytest()" [RED] (10 min)
  Task 6: "Implement check_pytest()" [GREEN] (15 min)
  Task 7: "Refactor: extract subprocess helper" [REFACTOR] (20 min)
```

**TDD Phase = Task Boundary**:

| TDD Phase | Task Scope | Duration |
|-----------|------------|----------|
| RED | Write ONE test or test method | 5-15 min |
| GREEN | Implement ONE method to pass | 10-20 min |
| REFACTOR | Extract/clean ONE thing | 10-20 min |
| INTEGRATION | Connect TWO existing pieces | 15-30 min |

**Never mix phases in one task**:
- Bad: "Write tests and implement method" (mixes RED+GREEN)
- Bad: "Implement and then refactor" (mixes GREEN+REFACTOR)
- Good: "Write test for X.method()" [RED only]
- Good: "Implement X.method()" [GREEN only]
