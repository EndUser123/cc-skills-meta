---
name: csaf
description: Cognitive Systems Architect Framework - machine-enforceable behavior for orchestrators
version: "1.0.0"
status: "stable"
category: framework
triggers:
  - /csaf
aliases:
  - /csaf

suggest:
  - /csda
  - /cwo
  - /orchestrator
---

# /csaf - Cognitive Systems Architect Framework

Protocol defining concrete, machine-enforceable behavior for orchestrators and automation systems.

## Purpose

Machine-enforceable behavior specification for orchestrators and automation systems.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- Evidence-first, verification-required

### Technical Context
- Integrates with CSDA 4-layer architecture
- Works with CWO orchestration
- Complements /csda and /orchestrator

### Architecture Alignment
- Part of CSF NIP governance framework
- Enforces behavior through structure, not documentation

## Your Workflow

1. Analyze orchestration requirements
2. Define concrete invariants
3. Specify state consistency rules
4. Document observability requirements
5. Define rollback procedures

## Validation Rules

- Invariants must be machine-enforceable
- State must have single source of truth
- All actions must be logged
- Recovery procedures must be defined

## Core Invariants

1. **Orchestration Boundary** - Planner/Executor separation
2. **State Consistency** - Single source of truth
3. **Observability** - All actions logged
4. **Recovery** - Defined rollback procedures
