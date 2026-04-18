# Output Template

This file defines the standard output format for GTO analysis results.

## Sections

1. **Summary**: High-level health score and key metrics
2. **Gaps Detected**: List of errors and issues found
3. **Unfinished Business**: Open tasks, questions, deferred items
4. **Code Markers**: TODO, FIXME, HACK markers found
5. **Recommended Next Actions**: Prioritized action items
6. **Evidence**: Links to detailed analysis artifacts

## Format Example

```markdown
# GTO Analysis Summary

**Health Score**: 75/100 (Good)

## Gaps Detected (3)

1. [HIGH] Import error in module_x.py:42
2. [MEDIUM] Undefined variable 'result'
3. [LOW] Missing type hint for function parameter

## Unfinished Business (5)

- [TASK] Implement feature Y
- [QUESTION] How to handle edge case Z?
- [DEFERRED] Performance optimization postponed

## Code Markers (2)

- `TODO: Refactor this function` (main.py:123)
- `FIXME: Race condition possible` (utils.py:45)

## Recommended Next Actions

1. [CRITICAL] Fix import error in module_x.py
2. [HIGH] Resolve undefined variable issue
3. [MEDIUM] Implement feature Y
```
