Phase Examples

## Correct: Planning Phase

User: What would you do to fix this bug?

Claude: [Planning Phase - text only]
I would first analyze the error logs to identify the root cause, then check the affected code paths. Based on the error type, I would either fix the logic error or update the dependencies. After implementing, I would run tests to verify the fix.

## Correct: Execution Phase

User: Proceed with the plan.

Claude: [Execution Phase - tool calls only]
<read file>
<run tests>

## Incorrect: Mixed Phases

Claude: [WRONG - mixed text and tools]
I'll analyze the error now.
<read file>
Then I'll fix it.

## Correct: Results Phase

Claude: [Results Phase - text only]
Analysis complete. Found 3 issues:
1. Null pointer in line 42
2. Missing error handling
3. Test coverage gap

All have been fixed and tests pass.