---
name: csf-nip-dev
description: Development standards for the CSF/NIP ecosystem.
version: "1.0.0"
status: "stable"
category: strategy
triggers:
  - 'csf'
  - 'nip'
  - 'hooks'
  - 'internal scripts'
aliases:
  - '/csf-nip-dev'

suggest:
  - /comply
  - /standards
  - /test
---



## Purpose

Development patterns and lessons learned for CSF NIP (Constitutional Solo Framework - Numerically Indexed Projects).

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- Evidence-first, verification-required
- Fail fast, truthfulness > agreement

### Technical Context
- Quality Gates system with 8 phases
- Path management for Windows development
- TaskMaster integration for project tracking
- Vector Store & Qdrant for semantic search
- Hooks & Git integration with anti-bleed protection
- CKS Bridge & Serena integration

### Architecture Alignment
- Part of CSF NIP core system
- Integrates with CHS (Chat History Search)
- Uses SKILLS registry for command discovery
- Follows CSDA 4-layer architecture

## Your Workflow

1. When working on `__csf/` codebase, reference NEURAL CACHE first
2. Check for known patterns and fixes before implementing
3. Follow CLI unification patterns (positional [target] argument)
4. Verify path format (forward slashes in bash)
5. Always register analyzers explicitly after import
6. Use terminal-scoped notifications correctly

## Validation Rules

- Quality phase counts must match between docs and code
- Always explicitly register analyzers after import
- Use forward slashes in bash commands
- Verify SRC_ROOT definition matches actual project structure
- Hooks must be explicitly registered in settings.json

### Prohibited Actions

- Import modules without registering in QualityOrchestrator
- Use different CLI interfaces for similar commands
- Rename parameters without updating function body
- Rely on test environment paths for runtime behavior
- Use `git add .` or wildcard staging

## Triggers
- Working on `__csf/` codebase
- Quality gate system modifications
- Path management issues
- TaskMaster integration

## 🧠 NEURAL CACHE

### Quality Gates
- [FIX 2026-01-07] **QualityOrchestrator Auto-Discovery**: `_auto_discover_analyzers()` imported modules but never registered them - `orchestrator.py:73` - Must explicitly call `registry.register()` after imports
- [PATTERN 2026-01-07] **Architecture Mismatch**: qual-gate.md (6 phases) ≠ qual-gate.py (8 phases) - Keep documentation and code in sync

### Path Management
- [FIX 2026-01-07] **SRC_ROOT Definition**: Path manager had wrong `SRC_ROOT` definition causing validation failures - `path_manager.py` - Add Python path config to `main_code.py`
- [FIX 2026-01-08] **sys.path Pollution & Module Cache**: CHSBackend polluted `sys.path` with wrong paths (`src/modules/src`) and cached `src` module pointing to `core_utils/src/__init__.py` - `search.py:SerenaBackend` - Solution: (1) Clean problematic paths from `sys.path`, (2) Ensure project root before `src` in `sys.path`, (3) Detect and remove wrong cached `src` from `sys.modules` before importing

### TaskMaster Integration
- [FIX 2026-01-07] **Missing DAL Module**: CWO12TaskManager imports `taskmaster.db` but module doesn't exist - Import fails silently, `get_dal = None` - Create `taskmaster/db.py` Data Access Layer

### Import Consolidation
- [PATTERN 2026-01-07] **ImportConsolidator Auto-Detection**: Don't pass `imports_to_remove` - class has built-in duplicate detection - `import_consolidator.py`

### Parameter Renaming
- [FIX 2026-01-07] **ParameterRenamer Body Updates**: Only renamed signature, not function body - Set context on entry, not exit - Timing issue with AST traversal

### CLI Unification
- [SUCCESS 2026-01-07] **Target Interface**: `const-tree` now uses `[target]` positional arg matching `qual-check` - Keep `--path` for backward compat with deprecation warning

### Testing
- [PATTERN 2026-01-07] **Test Context Path**: DUF plugin discovery shows 0 in test context but 64 in real execution - Test environment path setup differs from runtime

### Vector Store & Qdrant
- [FIX 2026-01-09] **Qdrant Lock Recovery**: Stale `.lock` files blocked new clients - `vector_store.py:79-114` - Solution: Detect locks older than 60s, attempt removal, fall back to `:memory:` mode
- [FIX 2026-01-09] **atexit Not Registered**: `_register_cleanup()` defined but never called - `vector_store.py:72-76` - Added call in `__init__` to ensure cleanup on Python shutdown
- [FIX 2026-01-09] **Log Parameter Bug**: Used `storage_path` (None) instead of `self.storage_path` in log messages - `vector_store.py:176-188` - Always use instance attribute after assignment

### Search CLI Architecture
- [FIX 2026-01-09] **ProgressiveDisclosureSearcher Missing Backends**: `lsp_backend`, `code_backend`, `serena_backend`, `docs_backend`, `findings_backend` not in signature - `progressive_disclosure.py:73-95` - Added all backend parameters to match search.py usage
- [FIX 2026-01-09] **SerenaWrapper Module Location**: `serena_wrapper` exists as `src/modules/serena_wrapper/__init__.py` (package) - Tests verify: SerenaClient, CodeMemory, SerenaError all functional - `test_serena_wrapper.py`

### Hooks & Git Integration
- [PATTERN 2026-01-09] **Hooks NOT Auto-Discovered**: PreToolUse hooks must be explicitly registered in `settings.json` - Naming pattern `PreToolUse_*.py` alone is insufficient - Add entry under `hooks.PreToolUse` with `matcher: "^Bash$"` and command path
- [SUCCESS 2026-01-09] **Anti-Bleed Gate Implementation**: Created `PreToolUse_anti_bleed_gate.py` blocking `git add .`, `*`, `-A`, `--all` - Allows explicit paths, `-u` (tracked), `-p` (interactive) - Override via `ANTI_BLEED_OVERRIDE=1` or `--anti-bleed-override` flag
- [FIX 2026-01-09] **Directory Coherence Check**: Added `_check_directory_coherence()` to `smart_git_commit.py` - Detects commits spanning >3 top-level directories - Elevates risk to HIGH and warns for incoherent commits

### Statusline & Notifications
- [PATTERN 2026-01-09] **Terminal-Scoped Notifications**: Notifications are scoped to `terminal_id`, not global - Each terminal window has its own `terminal_id` from `Get-TerminalId()` - Notifications only appear in the terminal that created them - `statusline.ps1:49-53` filters: `session_id == ""` (global) OR matching session OR matching terminal_id
- [FIX 2026-01-09] **Gear Emoji ⚙️ Architecture**: Single responsibility restored - `capture_settings_baseline.ps1` writes Unix timestamp (not FILETIME) - `SessionStart_cks_restore.py` removed duplicate timestamp writing - Statusline compares: `settings_mtime > stored_session_start` - Per-terminal tracking via `cc_settings_mtime_<terminal_id>.txt` - `capture_settings_baseline.ps1:133-136`, `statusline.ps1:437-450`
- [PATTERN 2026-01-09] **Global Notifications**: To show in ALL terminals, use `session_id=""` when calling `add_notification()` - Empty string = global, appears in all terminals - `notification_queue.py:41`

### CKS Bridge & Serena Integration
- [SUCCESS 2026-01-09] **Serena Code Memories in CKS Bridge**: Integrated `SerenaClient` into `ClaudeCodeCKSBridge` - `claude_code_cks_bridge.py:54-107,423-531,866-900` - Added `enable_serena` parameter, `_search_serena()` helper, updated `search_memories()` and `hybrid_search()` to combine CKS + Serena results - Code memories now automatically injected via `user_prompt_submit_cks.py` hook
- [PATTERN 2026-01-09] **Multi-Pass Edit Collision**: Sequential edits for multi-method integration create duplicates - If feature requires >3 changes to one file, MUST apply as single atomic Edit operation - Dependency-first ordering: new methods → modify callers → update entry point
- [FIX 2026-01-09] **vector_search Exception Handling**: `DaemonUnavailable` referenced before assignment when import fails - `claude_code_cks_bridge.py:856-877` - Initialize `DaemonLauncher = None` and `DaemonUnavailable = None` before try block, use `isinstance()` check in except handler

## Anti-Patterns

### What NOT to do:
- Import modules without registering in QualityOrchestrator
- Assume imports will auto-register
- Use different CLI interfaces for similar commands
- Rename parameters without updating function body
- Rely on test environment paths for runtime behavior

## Best Practices

### Quality Gates
1. Always explicitly register analyzers after import
2. Keep phase counts consistent between docs and code
3. Verify analyzer discovery returns actual analyzers, not empty list

### Path Management
1. Add Python path configuration before path operations
2. Use forward slashes in bash: `"P:/__csf/path"` not `P:\path`
3. Validate SRC_ROOT definition matches actual project structure

### CLI Design
1. Use positional `[target]` argument for primary target
2. Keep `--path` as deprecated fallback with warning
3. Unify interfaces across related commands

### Session Context & Checkpoints
- [FIX 2026-01-10] **Stale Task Identity in CKS Restore**: SessionStart restored CWO12 checkpoints despite CWO12 being deprecated - Root cause: `session-task.json` had stale `task_name: "CWO12"`; CKS contained 148 old CWO12 checkpoints - Fix: Update `session-task.json` via TaskIdentityManager; delete stale checkpoints via `cks.delete_entity('SessionCheckpoint', entity_id)`
- [PATTERN 2026-01-10] **Task Validity Has No Single Source of Truth**: Task identity determined by 5-source chain: session-task.json → compact metadata → git branch → user prompt - No deprecation mechanism; old checkpoints accumulate indefinitely - Future: Add `get_active_tasks()` to TaskIdentityManager with TSK directory scan