# Master Skill Orchestrator - Handover Document

**Date:** 2025-01-18
**Status:** Complete - All 4 Phases Implemented
**Test Coverage:** 92 tests passing

---

## Overview

The Master Skill Orchestrator is a central routing and workflow management system for 193 skills in the CSF NIP ecosystem. It provides intelligent skill recommendations, validates workflow sequences, and maintains state across sessions.

### What Was Built

| Phase | Component | Files | Tests | Description |
|-------|-----------|-------|-------|-------------|
| **Phase 1** | Core Orchestrator | 4 modules | 25 + 12 CLI | Skill routing, workflow state, suggest field parsing |
| **Phase 2** | Quality Pipeline | 1 module | 14 | Quality workflow orchestration for 9 skills |
| **Phase 3** | Decision Engine | 2 modules | 15 | Multi-branch workflows, alternative paths |
| **Phase 4** | Error Recovery | 2 modules | 26 | Error classification, git operation routing |
| **Tools** | Suggest Field Analyzer | 1 module | - | Auto-discovers missing suggest fields |

**Total:** 9 Python modules, ~2500 LOC, 92 tests

---

## File Structure

```
P:/.claude/skills/orchestrator/
├── __init__.py                      # Public API exports
├── orchestrator.py                  # MasterSkillOrchestrator class (Phase 1)
├── suggest_parser.py                # SuggestFieldParser class (Phase 1)
├── workflow_state.py                # WorkflowStateMachine class (Phase 1)
├── skill_router.py                  # SkillRouter class (Phase 1)
├── quality_pipeline.py              # QualityPipeline class (Phase 2)
├── decision_engine.py               # DecisionEngine class (Phase 3)
├── phase3_decision_engine.py        # DecisionEngineMixin (Phase 3)
├── error_recovery.py                # ErrorRecoveryEngine class (Phase 4)
├── phase4_error_recovery.py         # ErrorRecoveryMixin (Phase 4)
├── suggest_field_analyzer.py        # Suggest field analyzer tool
├── cli.py                           # CLI interface
├── SKILL.md                         # Orchestrator skill documentation
├── WORKFLOWS.md                     # Canonical workflow documentation
└── Tests:
    ├── test_orchestrator.py         # 25 tests (Phase 1)
    ├── test_quality_pipeline.py     # 14 tests (Phase 2)
    ├── test_decision_engine.py      # 15 tests (Phase 3)
    ├── test_phase4_error_recovery.py # 26 tests (Phase 4)
    └── test_cli.py                  # 12 tests (CLI)
```

---

## Running Tests

### Run All Tests (pytest)
```bash
cd P:/.claude/skills/orchestrator
python -m pytest *.py -v
```

### Run Specific Phase Tests
```bash
# Phase 1: Core
python -m pytest test_orchestrator.py -v

# Phase 2: Quality Pipeline
python -m pytest test_quality_pipeline.py -v

# Phase 3: Decision Engine
python -m pytest test_decision_engine.py -v

# Phase 4: Error Recovery
python -m pytest test_phase4_error_recovery.py -v
```

### Run CLI Tests (standalone)
```bash
cd P:/.claude/skills/orchestrator
python test_cli.py
```

### Test Results Summary
```
test_orchestrator.py .................. 25 passed
test_quality_pipeline.py ............... 14 passed
test_decision_engine.py ................ 15 passed
test_phase4_error_recovery.py ............. 26 passed
test_cli.py (standalone) ................ 12 passed

Total: 92 tests, 0 failed
```

---

## API Usage

### Basic Usage

```python
from orchestrator import (
    invoke_skill,
    get_suggestions,
    get_audit_trail,
    get_stats,
    get_skill_info,
    validate_workflow
)

# Invoke a skill
result = invoke_skill("/nse", {"query": "what's next?"})

# Get suggested next skills
next_skills = get_suggestions("/nse")
# Returns: ['/analyze', '/search', '/r', '/design', '/r', ...]

# Get skill information
info = get_skill_info("/nse")
# Returns: {skill, suggests, suggested_by, metadata, ...}

# Validate a workflow
validation = validate_workflow(["/analyze", "/nse", "/design"])
# Returns: {valid: True, valid_transitions: [...], issues: []}

# Get statistics
stats = get_stats()
# Returns: {total_executions: ..., current_workflow: ..., ...}
```

### Phase 2: Quality Pipeline

```python
from orchestrator import master_orchestrator

# Get quality skills by category
quality_skills = master_orchestrator.get_quality_skills()

# Get recommended quality workflow
workflow = master_orchestrator.get_recommended_quality_workflow('standard')
# Returns: ['/t', '/comply', '/qa']

# Validate quality workflow
validation = master_orchestrator.validate_quality_workflow(['/t', '/qa'])

# Record quality metrics
master_orchestrator.record_quality_metrics('/t', {
    'tests_passed': 42,
    'tests_failed': 3,
    'coverage_percent': 85.5
})
```

### Phase 3: Decision Engine

```python
from phase3_decision_engine import create_decision_orchestrator
from orchestrator import MasterSkillOrchestrator

# Create enhanced orchestrator
DecisionOrchestrator = create_decision_orchestrator(MasterSkillOrchestrator)
orchestrator = DecisionOrchestrator()

# Analyze workflow branches
analysis = orchestrator.analyze_workflow_branches(["/analyze", "/nse", "/t"])
# Returns: {branches: ['STRATEGY', 'QUALITY'], is_multi_branch: True}

# Get alternative paths
alternatives = orchestrator.get_alternative_paths("/analyze", "/qa")
# Returns: [{path: [...], reasoning: "...", branches: [...]}]

# Build decision tree
tree = orchestrator.build_decision_tree("/nse", max_depth=3)
```

### Phase 4: Error Recovery

```python
from phase4_error_recovery import create_full_orchestrator
from orchestrator import MasterSkillOrchestrator

# Create full orchestrator with all phases
FullOrchestrator = create_full_orchestrator(MasterSkillOrchestrator)
orchestrator = FullOrchestrator()

# Classify error
category = orchestrator.classify_error("SyntaxError: invalid syntax")
# Returns: 'SYNTAX'

# Get recovery path
recovery = orchestrator.select_recovery_path({
    "type": "SyntaxError",
    "message": "invalid syntax"
})
# Returns: {path: [...], skill: "/fix", reasoning: "..."}

# Record error for tracking
orchestrator.record_error(
    error_type="SyntaxError",
    message="invalid syntax",
    recovery_attempted="/fix",
    success=True
)
```

---

## Suggest Field Analyzer

### Usage

```bash
# Full analysis
cd P:/.claude/skills/orchestrator
python suggest_field_analyzer.py --analyze

# Get suggestions for a specific skill
python suggest_field_analyzer.py --suggest-for /nse

# Show fixes for missing suggest fields
python suggest_field_analyzer.py --fix-missing
```

### What It Does

1. **Text Analysis** - Parses SKILL.md files for `/skill` mentions
2. **Category Clustering** - Groups skills by category field
3. **Usage Patterns** - Identifies high-traffic skills
4. **Recommendations** - Suggests additions to improve coverage

### Results Applied

- Added suggestions to 5 high-traffic skills (`/nse`, `/comply`, `/analyze`, `/search`, `/design`)
- Fixed 5 skills missing suggest fields
- **193/193 skills now have suggest fields (100% coverage)**

---

## Workflow Documentation

See `WORKFLOWS.md` for canonical workflow patterns:

### Common Workflows

| Workflow | Path |
|----------|------|
| Development | `/analyze → /nse → /design → /r` |
| Quality | `/build → /t → /comply → /qa` |
| Bug Fix | `/debug → /fix → /t → /comply` |
| Research | `/search → /research → /cks → /chs` |
| Error Recovery | `/r → /rca → /debug → /fix` |

### Hub Skills (Most Referenced)

| Skill | Suggested By |
|-------|--------------|
| `/nse` | 83 skills |
| `/comply` | 44 skills |
| `/t` | 40 skills |
| `/build` | 39 skills |
| `/analyze` | 36 skills |

---

## Integration Points

### With Skills

The orchestrator reads suggest fields from skill `SKILL.md` files:

```yaml
---
name: my_skill
category: analysis
suggest:
  - /nse
  - /design
  - /r
---
```

### With Claude Code

Skills are invoked through Claude Code's `Skill()` tool. The orchestrator:
1. Validates transitions using suggest fields
2. Routes to Python imports or CLI invocation
3. Maintains workflow state
4. Returns suggestions for next skills

### State Persistence

State is stored at `P:/.claude/session_data/workflow_state.json`:
- Execution log
- Decision records (strategic skills)
- Workflow stack
- Current skill

---

## Key Design Decisions

### 1. Singleton Pattern
`master_orchestrator` is a singleton to maintain consistent state across imports.

### 2. Mixin Pattern for Phases
Phases 3 and 4 use mixins to extend the base orchestrator without modifying core files:
- `DecisionEngineMixin` - Phase 3
- `ErrorRecoveryMixin` - Phase 4

### 3. Quality Pipeline as Separate Module
Quality logic is isolated in `quality_pipeline.py` for clear separation of concerns.

### 4. Suggest Fields as Source of Truth
All workflow validation derives from the `suggest:` field in SKILL.md files.

---

## Known Limitations

1. **CLI Path Issue on Windows** - The suggest field analyzer has issues with `/nse` being interpreted as a path. Use Python API instead of CLI on Windows.

2. **State Not Shared Across Sessions** - Each Claude Code session creates a new orchestrator instance. State persists via JSON file but isn't shared.

3. **No Real-time Skill Discovery** - Skills are loaded at initialization. New skills require restart.

---

## Maintenance

### Adding a New Skill

1. Create skill directory with `SKILL.md`
2. Add `suggest:` field with next skills
3. Add `category:` for quality pipeline routing (optional)
4. Run suggest field analyzer to validate

### Adding a New Phase

1. Create new module with phase logic
2. Create mixin class for integration
3. Add factory function `create_phaseX_orchestrator()`
4. Write tests in `test_phaseX.py`
5. Update this handover document

---

## Quick Reference

### Public API Functions

| Function | Purpose |
|----------|---------|
| `invoke_skill(name, args, context)` | Invoke a skill |
| `get_suggestions(skill)` | Get next skill suggestions |
| `get_audit_trail()` | Get strategic decision records |
| `get_stats()` | Get workflow statistics |
| `get_skill_info(skill)` | Get comprehensive skill info |
| `validate_workflow(workflow)` | Validate workflow sequence |

### MasterSkillOrchestrator Methods

| Method | Purpose |
|--------|---------|
| `get_quality_skills()` | Get quality skills by category |
| `get_recommended_quality_workflow(type)` | Get quality workflow template |
| `validate_quality_workflow(workflow)` | Validate quality sequence |
| `get_quality_metrics(skill)` | Get metrics for skill |

### DecisionEngineMixin Methods

| Method | Purpose |
|--------|---------|
| `analyze_workflow_branches(workflow)` | Identify lifecycle branches |
| `get_alternative_paths(from, to)` | Find multiple routes |
| `build_decision_tree(skill, depth)` | Explore possible paths |
| `recommend_optimal_path(from, goal, context)` | Get context-aware recommendation |

### ErrorRecoveryMixin Methods

| Method | Purpose |
|--------|---------|
| `classify_error(message)` | Categorize error type |
| `select_recovery_path(error)` | Get recovery strategy |
| `detect_recovery_loop(history)` | Catch repeated errors |
| `record_error(...)` | Track errors for analysis |

---

## Contact & Support

For questions or issues:
1. Check `WORKFLOWS.md` for canonical patterns
2. Run tests to verify functionality
3. Review relevant phase documentation in SKILL.md
4. Check suggest field coverage with analyzer

---

**End of Handover Document**
