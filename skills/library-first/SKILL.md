---
name: library-first
description: Check for existing solutions before generating new code
version: 1.0.0
status: stable
category: quality
triggers:
  - /library-first
aliases:
  - /library-first

suggest:
  - /comply
  - /slc
---

# /library-first - Existing Solutions First

## Purpose

Prevent code reinvention by checking for existing solutions before generating new code.

## Workflow

1. **Check Known Solutions Registry**
   - Search codebase for similar implementations
   - Check standard library first
   - Look for established patterns

2. **Standard Library Check**
   - Python: `import this; help(this)` - always check stdlib
   - JavaScript: MDN Web Docs for built-ins
   - Node.js: `node --help` and docs

3. **Codebase Pattern Reuse**
   - Glob/Grep for similar code patterns
   - Extract common patterns to shared modules
   - Flag "why new instead of reuse?"

4. **Justification Required**
   - If creating new implementation:
     - Document why existing solution doesn't fit
     - Explain what's different about this use case
     - Get explicit approval for reinvention

## Rules

- Always check standard library first
- Always search codebase before implementing
- Never reinvent without justification
- Prefer extraction over duplication

## Usage

```
/library-first "implement X"     # Check before implementing
/library-first --audit           # Audit current codebase for reinvention
```

## Anti-Patterns

- ❌ Implementing sorted() when stdlib has it
- ❌ Copying error handling pattern 5 times instead of shared module
- ❌ Writing new CLI parser when argparse/Click exists
- ❌ Creating "utility" functions that duplicate stdlib

## Version

**Version:** 1.0.0
**Updated:** 2026-02-16
