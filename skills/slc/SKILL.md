---
name: slc
description: Pragmatic Solo Dev Guidelines - lean development principles for solo developers
version: "1.0.0"
status: stable
category: quality
triggers:
  - /slc
aliases:
  - /slc

suggest:
  - //p-2025
  - /comply
---

# /slc - Solo Dev Compliance

## Purpose

Enforce pragmatic solo development constraints: prevent over-engineering, require evidence, ensure local/portable solutions.

## Director Model Context

> **Full philosophy:** See [memory/constitution.md](C:/Users/brsth/.claude/projects/P--/memory/constitution.md) for complete constitutional principles

When "SOLO DEVELOPMENT CONTEXT" appears:

When "SOLO DEVELOPMENT CONTEXT" appears:
- ✅ **ONE human director** (you) - no other humans
- ✅ **MULTIPLE AI agents** assist (planning, coding, testing)
- ✅ **Enterprise patterns ARE appropriate** for AI workflows
- ✅ **Observability, testing rigor ARE appropriate**
- ❌ **Team approval gates** - no other humans to coordinate with

## Constraints

- **Evidence Required**: Proofs shown for all claims (tests, logs, outputs)
- **Complete Solutions**: No dead code, no TODO placeholders, no partial implementations
- **Local/Portable**: No infra lock-in, no cloud dependencies for local dev
- **No Background Services (without approval)**: Commands must terminate; idle timeout applies
- **Director Approval Required**: Self-healing, auto-correction only with your explicit approval

## What's Appropriate (Director + AI Agents)

- ✅ Enterprise-grade patterns, scalability requirements (AI agents work in parallel)
- ✅ Observability, monitoring (track AI agent performance)
- ✅ Comprehensive testing (AI agents write tests)
- ✅ Abstract factories, DI containers (AI-maintained code)
- ✅ Continuous monitoring with idle timeout

## What's Not Appropriate

- ❌ Team approval gates (no other humans)
- ❌ Multi-human collaboration patterns
- ❌ Enterprise deployment operations (local dev environment)

## Checklist

### Complexity Justification
- Value > costs?
- Simple alternative considered and rejected?
- Over-engineering anti-patterns avoided?

### Complete Solutions
- No dead code or commented-out code
- No TODO/FIXME placeholders in shipped code
- All paths through code are reachable and tested

### Evidence Verification
- Tests demonstrate claimed behavior
- Logs/show outputs verify claims
- Before/after evidence for refactorings

### Local/Portable
- Runs without external services
- No cloud dependency for local development
- Self-contained verification

## Usage

```
/slc <target>     # Check compliance
/slc --strict     # Fail on warnings
```

## Version

**Version:** 1.0.0
**Updated:** 2026-02-16
