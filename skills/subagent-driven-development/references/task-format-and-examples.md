# Task Format and Examples Reference

## Task Format Template for Subagents

When dispatching, provide:

```
You are executing task [N/M] of an implementation plan.

**Task**: [method_name] - [one line action]
**Estimated**: [X minutes, max 30]
**Phase**: [RED | GREEN | REFACTOR]

**Context**: [Relevant background - 1-2 sentences]

**Acceptance Criteria**:
- [ ] [Criterion 1 - specific/testable]
- [ ] [Criterion 2]

**Files**:
- Read: [file paths]
- Write: [file path]

**Verification**:
```bash
[exact command]
```
Expected: [PASSED/FAILED]

**Constraints**:
- One method/function only
- Follow existing patterns
- Stop if exceeding estimate

**Output**:
- [Specific: one method, one test, etc.]

Begin.
```

## Checkpoint Template

After each task (or batch of 2-3 related tasks):

```
## Checkpoint: Task [N/M] Complete

**Completed**: [task description]
**Files Modified**: [list]
**Verification**: [tests run, results]

**Ready to proceed to next task?**
Next: [brief description of task N+1]
```

## Good vs Bad Task Examples

### Bad: Too Large

```
Task: "Implement shared quality and verification modules for /cwo, /analyze, and /verify"
Estimated: 4 hours
Files: src/features/quality/shared/*.py, tests/quality/*.py, src/features/cwo/*.py
```

**Problems**:
- Multiple modules, multiple test files
- Integration mixed with implementation
- No clear TDD phase
- Cannot verify in isolation

### Good: Atomic TDD Task (RED)

```
Task: "Write test for check_ruff() method"
Estimated: 10 minutes
Phase: RED

Context: Creating QualityChecker class for unified quality checking.
Need to test check_ruff() method before implementation exists.

Acceptance Criteria:
- Test file: tests/quality/test_shared_quality_checker.py
- Add method: test_check_ruff_returns_result()
- Asserts: result is QualityResult with passed, errors, warnings attributes

Files:
- Write: tests/quality/test_shared_quality_checker.py

Verification:
```bash
pytest tests/quality/test_shared_quality_checker.py::TestQualityChecker::test_check_ruff_returns_result -v
```
Expected: FAILED (implementation doesn't exist)

Constraints:
- Write test FIRST
- One test method only
- Follow existing test patterns

Output:
- Test method that fails
```

### Good: Implementation Task (GREEN)

```
Task: "Implement check_ruff() to pass tests"
Estimated: 15 minutes
Phase: GREEN

Context: Test already written. Need to implement check_ruff() method.

Acceptance Criteria:
- Method signature: def check_ruff(self, target_path: Path | None = None) -> QualityResult
- Runs: ruff check --output-format=json
- Returns: QualityResult with parsed errors

Files:
- Read: tests/quality/test_shared_quality_checker.py
- Write: src/features/quality/shared/quality_checker.py

Verification:
```bash
pytest tests/quality/test_shared_quality_checker.py::TestQualityChecker::test_check_ruff_returns_result -v
```
Expected: PASSED

Constraints:
- One method only
- Don't refactor yet
- Match test expectations exactly

Output:
- Working check_ruff() method
```

## Task Smell Checklist

If you see any of these, **STOP and decompose**:

| Smell | Example | Fix |
|-------|---------|-----|
| Estimated > 30 min | "This will take ~45 minutes" | Split into 3-4 tasks |
| Multiple methods | "Implement check_ruff, check_mypy" | One method per task |
| Mixed phases | "Write tests and implement" | RED task + GREEN task |
| Implementation + integration | "Implement and integrate" | Separate tasks |
| "And then..." in description | "Add field and then update UI" | Two separate tasks |
| >2 files to modify | src/*.py (5 files) | Group by related changes |
