# GTO Hooks Discovery Report

**Date:** 2026-03-23
**Purpose:** Identify existing hooks infrastructure before proposing enhancements

---

## Summary

GTO has 5 hook files in `P:\.claude\skills\gto\hooks\`:

| File | Type | Purpose | Integration |
|------|------|---------|--------------|
| `gto_failure_capture.py` | PostToolUseFailure | Classify GTO failures and log structured patterns | ❌ Standalone (not registered) |
| `checklist_gate.py` | Script | Validate pre-flight checklist items | ❌ Standalone |
| `session_summary.py` | Script | Generate session summaries from artifacts | ❌ Standalone |
| `validate_format.py` | Script | Validate artifact JSON/Markdown format | ❌ Standalone |
| `gto_verify_wrapper.py` | Stop | Platform-aware verification wrapper with scope guard | ✅ Registered in main hooks |

## Key Finding: GTO Hooks Are NOT Integrated

**Most GTO hooks are standalone scripts, NOT integrated into the Claude Code hook system.**

Only `gto_verify_wrapper.py` is actually registered and executed as a hook. The others are utility scripts that must be manually invoked.

## Main Hooks Infrastructure

The main hooks directory (`P:\.claude\hooks\`) has comprehensive infrastructure:

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **Hook Base** | `__lib/hook_base.py` | `@hook_main` decorator, error logging, context management |
| **Terminal ID** | `__lib/terminal_id.py` | Canonical terminal ID normalization |
| **Hook Platform** | `__lib/hook_platform.py` | Platform detection, scope guard checks |
| **Router System** | `PreToolUse.py`, `Stop.py` | Consolidated dispatch chains |

### Hook Events

| Event | Trigger | Capability |
|-------|---------|------------|
| SessionStart | Session begins | Initialize context, restore state |
| UserPromptSubmit | Before prompt processing | Inject context, validate input |
| PreToolUse | Before tool execution | **Block** actions, enforce prerequisites |
| PostToolUse | After tool completion | Analyze output, detect failures |
| Stop | Response complete | Validate success claims, enforce verification |

### In-Process Hook Protocol

Modern hooks support direct in-process calling via `run(data) -> dict | None`:

```python
def run(data: dict) -> dict | None:
    """In-process callable.

    Returns:
        {"block": True, "reason": "..."} to block
        {"allow": True} or None to allow
    """
    prompt = data.get("response", "")
    if "TODO" in prompt:
        return {"block": True, "reason": "TODO detected"}
    return None
```

## GTO Hook Integration Status

### ✅ Integrated: `gto_verify_wrapper.py`

**Purpose:** Stop hook that verifies GTO analysis completion with scope guard.

**Features:**
- Scope guard: Checks if GTO was actually used (skips if no GTO artifacts)
- Platform detection: Runs platform-specific verification script
- Terminal ID normalization: Multi-terminal isolation
- Exit code 2 on failure (blocks), 0 on pass

**Integration:** Registered as Stop hook in main hooks system.

### ❌ Not Integrated: Other GTO Hooks

**`gto_failure_capture.py`** (PostToolUseFailure):
- Classifies GTO failures into categories
- Logs structured entries to `.claude/failure-patterns/`
- **NOT registered** - must be added to settings.json manually
- Should be integrated into PostToolUse router

**`checklist_gate.py`**:
- Validates pre-flight checklist items
- Standalone script with `if __name__ == "__main__"`
- **NOT a hook** - utility script only
- Could be integrated as PreToolUse gate

**`session_summary.py`**:
- Generates session summaries from artifacts
- Standalone script
- **NOT a hook** - utility script only
- Could be integrated as SessionStart or PostToolUse hook

**`validate_format.py`**:
- Validates artifact JSON/Markdown format
- Standalone script
- **NOT a hook** - utility script only
- Could be integrated as PostToolUse hook

## Integration Opportunities

### Priority 1: Register `gto_failure_capture.py`

**Current State:** PostToolUseFailure hook exists but is NOT registered.

**Action Required:** Add to `P:\.claude\settings.json`:

```json
{
  "hooks": {
    "PostToolUseFailure": [
      {
        "matcher": ".*gto.*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:\\.claude\\skills\\gto\\hooks\\gto_failure_capture.py"
          }
        ]
      }
    ]
  }
}
```

**Rationale:** Failure capture is already implemented, just not wired into the system.

### Priority 2: Convert Utility Scripts to Hooks

**`checklist_gate.py`** → PreToolUse Hook:
- Block GTO execution if checklist has unchecked items
- Integrate with PreToolUse router
- Add bypass flag: `--allow-incomplete-checklist`

**`session_summary.py`** → SessionStart Hook:
- Auto-generate session summary on session start
- Show summary of previous GTO analysis
- Integrate into SessionStart router

**`validate_format.py`** → PostToolUse Hook:
- Validate GTO artifact format after Write/Edit
- Warn on malformed JSON/Markdown
- Integrate into PostToolUse router

## Patterns to Follow

### Hook Registration Pattern

For new GTO hooks, follow this pattern:

1. **Export `run()` function** (in-process protocol):
   ```python
   def run(data: dict) -> dict | None:
       # Hook logic
       return {"block": True, "reason": "..."}  # or None
   ```

2. **Register in router**:
   ```python
   # In PreToolUse.py, Stop.py, or PostToolUse.py
   "gto_checklist_gate": {
       "module": "gto_hooks.checklist_gate",
       "runner": run_checklist_gate,
       "priority": 8.0
   }
   ```

3. **Add `@hook_main` decorator** (for subprocess mode):
   ```python
   from __lib.hook_base import hook_main

   @hook_main
   def main():
       data = json.loads(sys.stdin.read())
       # Hook logic
   ```

### Multi-Terminal Isolation

All GTO hooks MUST use terminal-scoped state:

```python
from __lib.hook_base import get_terminal_id

terminal_id = get_terminal_id()
state_file = Path(f".claude/gto-state-{terminal_id}/state.json")
```

### Scope Guard Pattern

For hooks that should only run when GTO is active:

```python
from __lib.hook_platform import scope_guard_check

should_skip, reason = scope_guard_check(
    project_root,
    "gto-state-{terminal_id}",
    terminal_id
)

if should_skip:
    return None  # Skip this hook
```

## Architectural Recommendations

### 1. Consolidate GTO Hook Registration

Create `P:\.claude\skills\gto\hooks\router.py` to register all GTO hooks:

```python
GTO_HOOKS = {
    "PreToolUse": [
        "checklist_gate",
        "viability_gate",
    ],
    "PostToolUse": [
        "format_validator",
        "failure_capture",
    ],
    "Stop": [
        "verify_wrapper",
    ],
}
```

### 2. Use In-Process Protocol

Convert standalone scripts to in-process hooks:

**Before (standalone):**
```python
if __name__ == "__main__":
    checklist_path = Path(sys.argv[1])
    passed = run_checklist_gate(checklist_path)
    sys.exit(0 if passed else 1)
```

**After (in-process):**
```python
def run(data: dict) -> dict | None:
    checklist_path = Path(".claude/gto-checklist.md")
    passed = run_checklist_gate(checklist_path)
    if not passed:
        return {"block": True, "reason": "Checklist has unchecked items"}
    return None

if __name__ == "__main__":
    # For standalone execution
    import json, sys
    data = json.loads(sys.stdin.read())
    result = run(data)
    print(json.dumps(result or {"allow": True}))
```

### 3. Add Scope Guards

All GTO hooks should skip when GTO is not active:

```python
from __lib.hook_platform import scope_guard_check

def run(data: dict) -> dict | None:
    # Scope guard: Skip if GTO not active
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    should_skip, reason = scope_guard_check(
        project_root,
        "gto-state-{terminal_id}",
        get_terminal_id()
    )

    if should_skip:
        return None  # GTO not active, skip hook

    # Hook logic continues...
```

## Related Documentation

- **Hook Architecture:** `P:\.claude\hooks\CLAUDE.md`
- **Hook Protocol:** `P:\.claude\hooks\PROTOCOL.md`
- **Hook Base:** `P:\.claude\hooks\__lib\hook_base.py`
- **Platform Detection:** `P:\.claude\hooks\__lib\hook_platform.py`

## Next Steps

Based on this discovery:

1. **Register `gto_failure_capture.py`** - Already implemented, just needs registration
2. **Convert utility scripts to hooks** - Leverage existing infrastructure
3. **Create GTO hook router** - Centralized registration for all GTO hooks
4. **Add scope guards** - Ensure hooks only run when GTO is active
5. **Use in-process protocol** - Better performance than subprocess mode

---

**Conclusion:** GTO has comprehensive hook logic but poor integration. The main hooks directory has robust infrastructure that GTO should leverage rather than maintaining standalone scripts.
