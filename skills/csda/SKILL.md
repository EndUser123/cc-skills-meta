---
name: csda
description: Code Structure-Documentation Architecture Pattern - 4-layer architecture for CSAF bundles
version: "1.0.0"
status: "stable"
category: development
triggers:
  - /csda
aliases:
  - /csda

suggest:
  - /csaf
  - /csf-nip-dev
  - /standards
---

# CSDA - Code Structure-Documentation Architecture

Generate CSAF bundles with proper CSDA pattern implementation.

## Purpose

4-layer architecture pattern for CSAF bundles (Command Interface, Interface Layer, Specification Layer, Documentation Layer).

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- Evidence-first, verification-required

### Technical Context
- Part of CSF NIP governance framework
- Integrates with CSAF behavioral framework
- Works with CWO orchestration

### Architecture Alignment
- Enforces structure through 4-layer separation
- Each layer has single responsibility
- Specification layer is deterministic and machine-enforceable

## Your Workflow

1. Analyze existing command structure
2. Identify missing layers
3. Create or update _spec.py with deterministic logic
4. Create or update _inst.md with orchestration
5. Ensure _help.md has complete documentation
6. Verify all 4 layers are present and consistent

## Validation Rules

- All 4 layers must be present (.md, _inst.md, _spec.py, _help.md)
- Specification layer must be 100% constitutional compliant
- When CSDA is applied to any component, entire workflow ecosystem must be refactored
- No layer mixing (each layer has distinct responsibility)

## Quick Start



## 4-Layer Architecture



### Layer Responsibilities

**Layer 1: Command Interface** (.md)
- Essential metadata for Claude Code discovery
- Minimal interface description only

**Layer 2: Interface Layer** (_inst.md)
- Command orchestration and workflow
- Error handling and user feedback

**Layer 3: Specification Layer** (_spec.py)
- Deterministic Python logic
- 100% constitutional compliance enforcement
- Real implementation with tool usage

**Layer 4: Documentation Layer** (_help.md)
- Complete documentation
- Constitutional principles and WHY
- Implementation procedures and HOW

## Execution Modes

**Standard Mode**: Refactors all components to CSDA compliance

**Dry Run Mode** (--dry-run): Analysis only, no file changes

## Scope Rule

**MANDATORY**: When CSDA is applied to any component, the entire workflow ecosystem must be refactored.
