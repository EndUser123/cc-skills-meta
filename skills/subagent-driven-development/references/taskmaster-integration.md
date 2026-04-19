# TaskMaster Integration Reference

## When to Use TaskMaster

- Task description is vague or broad
- Unsure if task needs splitting
- Want AI-assisted decomposition
- Need to track subtasks

## Workflow

```bash
# 1. Add the task to TaskMaster
/tm add Implement shared quality modules

# 2. Check complexity
/tm complexity task_123
# Output: task_123: 4 subtasks - medium complexity, multiple components

# 3. Get expansion prompt (if complexity > 3)
/tm expand task_123
# Output: AI-ready prompt for breaking down the task

# 4. Create subtasks manually or use the expansion prompt
/tm subtask task_123 Write test for QualityChecker.check_ruff [RED]
/tm subtask task_123 Implement check_ruff method [GREEN]
/tm subtask task_123 Write test for check_mypy [RED]
/tm subtask task_123 Implement check_mypy method [GREEN]
```

## Complexity Thresholds

| Score | Action |
|-------|--------|
| 1-3 | Keep atomic, dispatch directly |
| 4-5 | Break into 2 subtasks |
| 6-7 | Break into 3-4 subtasks |
| 8-10 | Break into 5+ subtasks |

## Pre-dispatch with TaskMaster

```
For any task:
  1. /tm add "<task description>"
  2. /tm complexity <task_id>
  3. If score <= 3: Dispatch to subagent
  4. If score > 3: /tm expand <task_id>, create subtasks, dispatch each
```
