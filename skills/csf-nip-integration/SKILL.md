---
name: csf-nip-integration
description: Guide Claude in working with CSF NIP architecture, commands, patterns, and conventions
version: "1.0.0"
status: "stable"
category: strategy
triggers:
  - '/csf-nip-integration'
aliases:
  - '/csf-nip-integration'

suggest:
  - /nse
  - /orchestrator
  - /build
---


# CSF NIP Integration Skill

Teaches Claude how to effectively work within the CSF NIP (Constitutional Software Foundation - New Integration Protocol) ecosystem.

## Purpose

Guide Claude in working with CSF NIP architecture, commands, patterns, and conventions.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- Evidence-first, verification-required
- Anti-sycophancy enforced

### Technical Context
- CKS (Cognitive Knowledge System) for persistent learning
- CHS (Chat History Search) for conversation retrieval
- Hooks for pre/post processing
- Registry for command discovery and workflow routing
- SLC (Session Learning & Context) auto-loaded on session start

### Architecture Alignment
- Part of CSF NIP governance framework
- Integrates with quality gates and standards
- Command-first workflow for complex orchestration
- Progressive disclosure (load details only when needed)

## Your Workflow

1. Read core documentation (statusline_spec.md, CLAUDE.md, COMMANDS_REFERENCE.md)
2. Use slash commands for complex orchestration
3. Follow READ Before WRITE (RBW-001) pattern
4. Apply evidence-based decisions (verify before asserting)
5. Use forward slashes in bash commands
6. Follow TDD: RED -> GREEN -> REFACTOR

## Validation Rules

- All claims must cite file:line evidence
- Present-tense claims require present-state evidence
- Verify path existence before referencing
- Use /search for queries, not grep

### Prohibited Actions

- Import modules without registering in QualityOrchestrator
- Assume imports will auto-register
- Use sl from P:\ root (use git instead)
- Use sl push (use git push instead)
- Speculate without investigation

## Core Principles

1. **Constitutional compliance** - All code follows CLAUDE.md constitution
2. **Command-first workflow** - Use slash commands for complex orchestration
3. **Progressive disclosure** - Load details only when needed
4. **Evidence-based decisions** - Verify before asserting

## Architecture Overview

### Directory Structure

```
P:/
+-- __csf/               # Core system
|   +-- commands/            # Slash command implementations
|   |   +-- nip/             # Main orchestration (/main, /exec)
|   |   +-- co/              # Command orchestration
|   |   +-- <category>/      # Domain-specific commands
|   +-- .data/               # Knowledge base (CKS, CHS)
|   +-- hooks/               # Pre/post processing hooks
|   +-- tools/               # Third-party tools (sapling, sqlite3)
|   +-- logs/                # System logs
+-- .claude/                 # Claude Code configuration
|   +-- skills/              # Skill definitions
|   +-- registry/            # Command registry
|   +-- hooks/               # Session hooks
+-- projects/                # Project workspaces
```

### Key Systems

| System | Purpose | Entry Point |
|--------|---------|-------------|
| **CKS** | Cognitive Knowledge System - persistent learning | `import cognitive_keystone` |
| **CHS** | Chat History Search - conversation retrieval | `/chs <query>` |
| **Hooks** | Pre/post processing for operations | `P:/.claude/hooks/` |
| **Registry** | Command discovery and workflow routing | `skill_registry` |
| **SLC** | Session Learning & Context system | Auto-loaded on session start |

### Key Documentation

| Document | Path | Purpose |
|----------|------|---------|
| **Statusline Spec** | `__csf/docs/statusline_spec.md` | All status indicators, state files, TTLs |
| **Constitution** | `__csf/docs/CLAUDE.md` | Constitutional constraints and operating principles |
| **Commands Reference** | `__csf/docs/COMMANDS_REFERENCE.md` | Complete command catalog |

## Essential Commands (Quick Reference)

See `references/commands-and-patterns.md` for full command details, git workflow, health check interpretation, session continuity, and file conventions.

| Category | Key Commands |
|----------|-------------|
| **Health & Status** | `/main`, `python P:/.claude/hooks/hook_health_check.py` |
| **Knowledge** | `/chs "query"`, `cks.ingest_learning(...)`, `/ask "question"` |
| **Development** | `/debug "what went wrong"`, `/research "topic"`, `/analyze <path> --focus quality` |
| **Planning** | `/breakdown`, `/exec <task>`, `/cwo12` |

## Constitutional Patterns

### Singular Dev Authority

This is a solo-dev environment:
- **Allowed**: Any architectural pattern the developer chooses
- **Prohibited**: Patterns requiring others' permission (consensus, multi-team approval)

### Anti-Sycophancy

- **Do NOT** use excessive praise or agree with incorrect premises
- **DO** correct false assumptions directly
- **DO** provide objective technical assessment

### READ Before WRITE (RBW-001)

Before any implementation:
1. **S**earch codebase (Glob/Grep)
2. **R**ead working implementations
3. **P**lan minimal change
4. **I**mplement using Edit/Write

### Real-Time Measurement

For time-sensitive metrics (memory, performance):
- **USE**: `psutil.Process().memory_info().rss` for current memory
- **DO NOT USE**: Cached JSON values (stale data creates false positives)

## Knowledge Context Auto-Injection

The CKS Knowledge Layer provides automatic context injection for implementation/debugging questions. See `references/knowledge-context.md` for AST-based chunking, incremental indexing, and auto-injection hook details.

## Neural Cache Lessons

**86 lessons migrated to CKS vector database** (2026-01-05). Full context searchable via CKS.

See `references/neural-cache-lessons.md` for the complete lesson archive covering:

- Core Reflexes (L1): git index.lock, datetime.utcnow(), Glob-then-Grep, RELAY pattern, TDD
- Async & Performance: TaskGroup, health check timeout, Rich Progress anti-pattern
- FAISS & GPU: GPU speedup by dataset size, troubleshooting flow, INT8 quantization
- PowerShell & Windows: Where-Object, UTF-8 BOM, notification scoping
- Search Optimization: Pipeline stages, RRF fusion, SQLite threading
- Hooks & Notifications: DUF dismissal, sloppiness signals, hook stdin format
- Import & Module Patterns: `src.module.name` imports, cross-directory traversal
- Vector Search: HNSW vs FAISS, Qdrant migration, file lock contention
- CHS Architecture: Path inconsistency, real-time indexing, Qdrant backend
- RCA Workflow: Preflight checks, mental model selector, ADF evaluation
- Subagent Architecture: Task tool vs subagents, expertise-based splitting

**Core Reflexes (L1 - quick reference):**
- **git index.lock**: `rm -f .git/index.lock` when git operations fail
- **datetime.utcnow()**: Use `datetime.now(timezone.utc)` instead (Python 3.12+)
- **Glob first, then Grep**: Search for files with Glob, then content with Grep
- **RELAY Pattern**: Hook stdout -> system-reminder -> LLM must relay to user
- **TDD**: RED (write failing test) -> GREEN (implement) -> REFACTOR (improve)

## When to Use This Skill

Activate this skill when:
- Working with CSF NIP command system
- Interpreting health check results
- Using CKS/CHS knowledge systems
- Following constitutional patterns
- Navigating the codebase structure
- Understanding hook behavior

## Integration Notes

This skill works with:
- **health-monitor** - Real-time system health
- **debug-triage** - Structured problem-solving
- **git-workflow** - Version control patterns
- **session-handoff** - Cross-session continuity

## Metadata

**Version:** 1.0.1
**Created:** 2025-12-27
**Updated:** 2026-01-10 (search optimization retro)
**Purpose:** Reduce repetitive explanations of CSF NIP patterns
