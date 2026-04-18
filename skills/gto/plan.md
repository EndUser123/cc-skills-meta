# Three-Layer Prevention/Detection System Implementation

## Overview

Implement a three-layer system to encode practices so issues don't happen, and when they do, are detected and fixed.

**Layer 1 (PreToolUse Auto-Fix)**: Catch issues before they enter codebase - formatting, imports, basic validation
**Layer 2 (GitHooks + GTO Assertions)**: Catch issues at commit time with binary assertions
**Layer 3 (GTO Periodic Analysis)**: Detect issues that slipped through via periodic GTO analysis with skill routing

---

## Architecture

### Layer 1: PreToolUse Auto-Fix Hooks

**Purpose**: Intercept tool calls and auto-fix common issues before they propagate

**Components**:
- `PreToolUse_auto_format.py` - Auto-format code on edit (ruff format)
- `PreToolUse_auto_import.py` - Auto-add missing imports on edit
- `PreToolUse_import_order.py` - Enforce import ordering standards

**Location**: `P:\.claude\hooks\PreToolUse_*.py`

**Behavior**:
- On `Edit` or `Write` tool calls, intercept and auto-fix formatting/imports
- Non-blocking (advisory) with explicit user notification
- Graceful degradation: if tool fails, allow original operation

### Layer 2: GitHooks + GTO Assertions

**Purpose**: Validate commit-time assertions using GTO binary assertions

**Components**:
- Git commit hook (pre-commit or via settings.json)
- Run `gto_assertions.py --project-root` before commit allowed
- Block commit if A1-A5 assertions fail

**Location**: `P:\.claude\hooks\` + git hooks configuration

**Behavior**:
- Before commit: run binary assertions
- Only allow commit if all assertions pass (exit code 0)
- Report which assertions failed if blocked

### Layer 3: GTO Periodic Analysis

**Purpose**: Periodic gap analysis with skill routing for issues that slipped through

**Components**:
- Existing GTO orchestrator already does this
- Add periodic scheduling (via cron or SessionStart)
- Integrate skill routing for detected gap types

**Location**: `P:\.claude\hooks\` + existing GTO infrastructure

**Behavior**:
- Run GTO analysis on session start or periodically
- Map gaps to relevant skills via gap_skill_mapper
- Surface findings in RSN format

---

## Data Flow

```
User Edits Code
      ↓
Layer 1: PreToolUse Hooks (auto-fix formatting/imports)
      ↓
Git Commit Triggered
      ↓
Layer 2: GitHook runs gto_assertions.py
      ↓ (if pass)
Commit Succeeds
      ↓
SessionStart / Periodic
      ↓
Layer 3: GTO Analysis → Skill Routing → RNS
```

---

## Error Handling

| Layer | Failure Mode | Handling |
|-------|--------------|----------|
| L1 | Auto-fix tool fails | Allow operation to proceed, warn user |
| L2 | Assertions fail | Block commit, show failure details |
| L3 | GTO analysis fails | Log error, continue without analysis |

---

## Test Strategy

1. **Layer 1 Tests**:
   - Test auto-format hook on Python files
   - Test auto-import hook detects missing imports
   - Test graceful degradation when tool unavailable

2. **Layer 2 Tests**:
   - Test assertion script runs correctly
   - Test commit blocked when assertions fail
   - Test commit succeeds when assertions pass

3. **Layer 3 Tests**:
   - Test GTO analysis produces valid artifact
   - Test skill routing maps gaps correctly
   - Test RNS output format

---

## Standards Compliance

- Python: ruff, pydantic-settings, asyncio patterns
- Hooks: Local-only operations (no external API calls)
- Graceful degradation: Fall back to original behavior on failure

---

## Ramifications

- **New files**: 3-5 PreToolUse hook files for Layer 1
- **Modified files**: Git hooks configuration, GTO integration
- **Breaking changes**: None - all layers are additive
- **Backward compatibility**: Existing GTO behavior unchanged
