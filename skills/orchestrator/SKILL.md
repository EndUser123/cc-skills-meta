---
name: Master Skill Orchestrator
description: Intelligent central orchestrator for unified skill routing and workflow management across 192+ skills with Phase 2 Quality Pipeline integration
version: 1.0.0
status: stable
category: orchestration
aliases:
  - /orchestrate
  - /orchestrator
  - /route
  - /master-orchestrator
suggest:
  - /nse
  - /analyze
  - /design
  - /workflow
  - /cwo_orchestrator
tags:
  - orchestration
  - workflow
  - routing
  - state-management
  - skill-discovery
  - quality-pipeline
---

# Master Skill Orchestrator

## Purpose

Intelligent central orchestrator for unified skill routing and workflow management across 192+ skills with Phase 2 Quality Pipeline integration. Consolidates skill orchestration by parsing suggest fields, enforcing valid workflow sequences, routing to appropriate implementations, persisting workflow state, and maintaining decision audit trails.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **No enterprise patterns**: Simple orchestration, not complex workflow engines
- **State persistence**: JSON file storage survives session restarts
- **Quality pipeline**: Phase 2 integration for 9 quality skills (test, qa, tdd, comply, validate_spec, debug, rca, nse, refactor, opts)

### Technical Context
- **Python module**: `P:/.claude/skills/orchestrator/orchestrator.py`
- **Core components**: SuggestFieldParser, WorkflowStateMachine, SkillRouter, QualityPipeline
- **State storage**: `P:/.claude/session_data/workflow_state.json`
- **Skill routing**: Direct Python import for 3 orchestrator skills (/nse, /rca, /llm-brainstorm), Skill() tool for 189 CLI-based skills
- **Quality categories**: Testing (3 skills), Validation (2 skills), Analysis (3 skills), Optimization (2 skills)

### Architecture Alignment
- Integrates with /nse (next steps), /analyze (analysis), /design (architecture), /workflow (workflow management)
- Links to /cwo_orchestrator (CWO workflow)
- Central coordination point for skill ecosystem

## Your Workflow

1. **PARSE SUGGEST FIELDS** -- Read all 192 skill SKILL.md files, extract suggest field relationships
2. **BUILD ROUTING GRAPH** -- Dynamically build skill routing graph from suggest fields
3. **VALIDATE WORKFLOWS** -- Validate skill transition sequences based on suggest fields
4. **ROUTE SKILLS** -- Direct Python import for orchestrator skills, Skill() tool for CLI-based skills
5. **PERSIST STATE** -- Save workflow state to JSON for session recovery
6. **QUALITY PIPELINE** -- Phase 2: orchestrate quality skills with stage transitions and metrics

## Validation Rules

- **Before skill invocation**: Validate workflow sequence against suggest fields
- **Before quality transitions**: Ensure quality pipeline stage is valid
- **After routing**: Record decision in audit trail
- **State persistence**: Maintain complete execution audit trail

### Prohibited Actions
- Invalid workflow sequences (wrong order, e.g., /qa -> /t)
- Skipping quality pipeline stages
- Losing state across session restarts
- Blocking valid skill transitions

## Module Structure

```
P:/.claude/skills/orchestrator/
+-- __init__.py              # Public API exports
+-- orchestrator.py          # MasterSkillOrchestrator class
+-- suggest_parser.py        # SuggestFieldParser class
+-- workflow_state.py        # WorkflowStateMachine class
+-- skill_router.py          # SkillRouter class
+-- quality_pipeline.py      # QualityPipeline class (Phase 2)
+-- test_orchestrator.py     # Comprehensive test suite
+-- SKILL.md                 # This file
```

## Features

### Phase 1: Core Orchestration

| Feature | Description |
|---------|-------------|
| **Suggest Field Parsing** | Reads all 192 skill SKILL.md files, extracts suggest relationships, builds routing graph dynamically (17+ skills have suggest fields) |
| **Workflow State Machine** | Validates skill transitions dynamically, maintains call stack for nested invocations, reset capability |
| **Intelligent Skill Router** | Direct Python import for 3 orchestrator skills (/nse, /rca, /llm-brainstorm), Skill() tool for 189 CLI-based skills |
| **State Persistence** | JSON file storage, survives session restarts, complete execution audit trail |

### Phase 2: Quality Pipeline

9 quality skills organized into 4 categories with predefined workflow templates (standard, deep, regression, optimization, spec_validation, quick_check) and validated stage transitions.

See `references/quality-pipeline.md` for quality skills listing, workflow templates, stage transitions, metrics tracking, and pipeline behavior details.

## Strategic Skills

Recorded in decision audit trail:
- `/nse` - Next Step Engine
- `/design` - Ultimate Architectural Advisor
- `/r` - Deterministic Remember + Refine (pre-mortem ownership)
- `/llm-brainstorm` - Multi-provider brainstorming
- `/rca` - Root Cause Analysis
- `/analyze` - Unified analysis engine
- `/r` - Solution Optimization Review

## Testing

```bash
# Using pytest
python -m pytest test_orchestrator.py -v

# Standalone
python test_orchestrator.py

# Test quality pipeline specifically
python -m pytest test_orchestrator.py::test_quality_pipeline -v
```

## Reference Files

| File | Contents |
|------|----------|
| `references/api-reference.md` | Phase 1 and Phase 2 Python API examples |
| `references/cli-reference.md` | CLI commands for Phase 1 and Phase 2 |
| `references/designitecture.md` | Component architecture, backward compatibility, performance notes |
| `references/quality-pipeline.md` | Quality skills, workflow templates, stage transitions, metrics |
