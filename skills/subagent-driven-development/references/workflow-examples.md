# Workflow Examples Reference

## Complete Workflow Example: TaskMaster + Subagent Dispatch

**User request**: "Implement shared quality checker module"

**Step 1: Add to TaskMaster and check complexity**
```bash
/tm add Implement shared quality checker module for ruff, mypy, pytest
# Returns: task_20250108_143000_abc

/tm complexity task_20250108_143000_abc
# Returns: task_20250108_143000_abc: 5 subtasks - medium complexity, multiple components
```

**Step 2: Get expansion prompt**
```bash
/tm expand task_20250108_143000_abc
# Returns AI-ready prompt for decomposition
```

**Step 3: Create subtasks using /tm**
```bash
/tm subtask task_20250108_143000_abc Write test for QualityChecker.check_ruff [RED]
/tm subtask task_20250108_143000_abc Implement check_ruff method [GREEN]
/tm subtask task_20250108_143000_abc Write test for check_mypy [RED]
/tm subtask task_20250108_143000_abc Implement check_mypy method [GREEN]
/tm subtask task_20250108_143000_abc Write test for check_pytest [RED]
/tm subtask task_20250108_143000_abc Implement check_pytest method [GREEN]
```

**Step 4: Dispatch subagents for each subtask**
```
For each subtask in order:
  1. Read subtask details: /tm task <subtask_id>
  2. Dispatch to appropriate specialist
  3. Verify completion
  4. Mark complete: /tm complete <subtask_id>
  5. Move to next subtask
```

**Result**: 6 atomic tasks, each 10-20 minutes, all tracked in TaskMaster.

## Plan Generation Example

**User request**: "Implement user email verification"

**Phase 1: Plan Generation**
```
[granular-plan-writing activates]

# Implementation Plan: User Email Verification

### Task 1: Add email_verified field to User model (~2 min)
**File**: `src/features/models/user.py`
**Action**: Add `email_verified: bool = False` field
**Verification**: `python -c "from src.models.user import User; assert User.email_verified == False"`

### Task 2: Write test for email sending (~2 min) [RED]
**File**: `tests/test_auth.py`
**Action**: Write test_send_verification_email() expecting success
**Verification**: `pytest tests/test_auth.py::test_send_verification_email -v` -> FAILED

### Task 3: Implement email sending (~3 min) [GREEN]
**File**: `src/auth/email.py`
**Action**: Create send_verification_email() function
**Verification**: `pytest tests/test_auth.py::test_send_verification_email -v` -> PASSED

[... full plan ...]

**Does this plan look correct? Any adjustments needed?**
```

**User**: "Yes, looks good. Proceed."

**Phase 2: Task Execution**
```
[Subagents execute each task sequentially with checkpoints]
```

### Integration with granular-plan-writing

When plan generation is needed:
1. **Implicit activation**: User says "implement X" -> activate granular-plan-writing first
2. **Explicit activation**: User says "create a plan for X" -> just create plan, don't execute
3. **Combined activation**: User says "plan and implement X" -> create then execute

### Plan Generation Triggers

| User Says | Action |
|-----------|--------|
| "implement X" | Generate plan -> Execute |
| "create a plan for X" | Generate plan only |
| "plan and implement X" | Generate plan -> Execute |
| "break this down and implement" | Generate plan -> Execute |
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
