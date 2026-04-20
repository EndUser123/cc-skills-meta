# Neural Cache - Detailed Lessons

**86 lessons migrated to CKS vector database** (2026-01-05)

Full context searchable via CKS. Migration: P:/__csf/src/csf/cks/integration/commands/neural_cache_migration.py

## Core Reflexes (L1 - kept for quick reference)

- **git index.lock**: rm -f .git/index.lock when git operations fail
- **datetime.utcnow()**: Use datetime.now(timezone.utc) instead (Python 3.12+ deprecation)
- **Glob first, then Grep**: Search for files with Glob, then search content with Grep
- **RELAY Pattern**: Hook stdout -> system-reminder -> LLM must relay to user
- **TDD**: RED (write failing test) -> GREEN (implement) -> REFACTOR (improve)

## Quality & /learn Improvements (2026-01-13)

- [FEATURE] **Actionable lesson format**: Added `is_actionable_lesson()` to validate "If X then Y" format. Filters out observations like "Created 4 docs". Usage: `python scripts/misc/retro.py --actionable`. Ref: `scripts/misc/retro_common.py:173-231`
- [FEATURE] **Lesson confidence scoring**: Added `score_lesson_confidence()` to rate lessons 1-5 on behavioral impact. Criteria: actionable (+1), specific details (+1), non-obvious (+1), generic advice (-1). Usage: `--min-confidence 3` for quality filter. Ref: `scripts/misc/retro_common.py:286-338`
- [FEATURE] **Cross-session pattern detection**: Added `detect_recurring_patterns()` to find lessons appearing in 2+ sessions. Identifies persistent mistakes needing architectural fixes. Usage: `python scripts/misc/retro.py --recurring`. Ref: `scripts/misc/retro_common.py:385-399`
- [REFACTOR] **Complexity reduction via extraction**: When CC > 10, extract scoring/pattern logic into helper functions with `_` prefix. `score_lesson_confidence` reduced from CC 12->9 by extracting 5 helpers. `detect_recurring_patterns` reduced from CC 12->1 by extracting 3 helpers.

## Async & Performance (2026-01-05)

- [OPTIM] **asyncio.TaskGroup > ThreadPoolExecutor**: For Python 3.14, native async with TaskGroup is optimal for I/O-bound subprocess work. Reduces health check time from ~170s sequential to ~10s.
- [FIX] **Health check timeout root cause**: Sequential subprocess calls accumulated timeouts. Parallel execution reduces total time to max(single_timeout). Ref: `unified_health.py:1175`
- [FIX] **Rich Progress + console.print anti-pattern**: console.print() during Rich Progress Live display breaks visualization. Suppress ALL prints in the call chain.
- [FIX] **Quality orchestrator analyzer registration**: `_auto_discover_analyzers()` imported modules but never called `registry.register()`. Result: empty analyzer list, false 100/100 scores.
- [FIX] **TaskMaster DAL missing**: Integration code complete but `speckit/taskmaster/db.py` doesn't exist.
- [PATTERN] **Async subprocess anti-pattern**: `subprocess.run()` blocks event loop in async contexts. Use `asyncio.create_subprocess_exec()`.

## PowerShell & Windows (2026-01-06)

- [FIX] **PowerShell Where-Object empty string filter**: Direct property access fails. Assign to variable first: `$sid = $_.session_id; $sid -eq ""`.
- [FIX] **Statusline UTF-8 BOM requirement**: PowerShell 7 defaults to legacy encoding without BOM. Add BOM via `content.encode('utf-8')`.
- [PATTERN] **Global vs session-scoped notifications**: `session_id=""` shows in ALL terminals. Specific `session_id` only in that session.
- [FIX] **PowerShell -Idle trigger not available**: Use `-Once` with `-RepetitionInterval` instead.

## FAISS & GPU (2026-01-06)

- [PERF] **FAISS GPU speedup by dataset size**: GPU 6-7x for 100 vectors, only 1.0-1.5x for 1k-10k. Use GPU for 100k+ vectors; CPU sufficient for <10k.
- [GOTCHA] **dict.get() with None values**: `.get("key", default)` returns None if key exists with value None. Use `.get("key") or default`.
- [FACT] **faiss-gpu 1.9.0 does NOT support Python 3.14**: conda-forge builds only for Python 3.10/3.11.
- [GOTCHA] **FAISS IndexFlatIP compresses better than INT8 at small scales**: ~14x compression vs minimal benefit for INT8 at <1M vectors.
- [FIX] **FAISS IndexScalarQuantizer constructor**: Only takes 2 args - dimension and QuantizerType. Not `(inner_index, quantizer)`.
- [FIX] **IndexScalarQuantizer requires training**: Must call `index.train(embeddings)` before `add()`.
- [FIX] **INT8 metadata bloat**: Storing full message content in metadata creates 63 MB file. Only store IDs.

### FAISS GPU Troubleshooting Flow

```bash
# STEP 1: Check GPU detection
python -c "import faiss; print('GPU attrs:', hasattr(faiss, 'StandardGpuResources'), hasattr(faiss, 'index_cpu_to_gpu'))"

# STEP 2: Check which faiss is installed
python -c "import faiss; print('Version:', faiss.__version__); print('Path:', faiss.__file__)"

# STEP 3: Check conda packages
conda list faiss

# STEP 4: Fix shadowing (if both present)
pip uninstall faiss-cpu

# STEP 5: Install faiss-gpu via conda-forge (if missing)
conda install -c conda-forge faiss-gpu>=1.9.0

# STEP 6: Verify GPU works
python -c "from src.lib.search.backends.chs_gpu import HAS_GPU; print('HAS_GPU:', HAS_GPU)"
```

### Symptom -> Fix Mapping

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `HAS_GPU=False` with NVIDIA GPU | faiss-cpu shadowing | `pip uninstall faiss-cpu` |
| `ImportError: StandardGpuResources` | Using pip instead of conda-forge | `conda install -c conda-forge faiss-gpu` |
| `ModuleNotFoundError: faiss` | Wrong Python version (3.12/3.14) | Use Python 3.11 environment |
| `faiss.__version__ = 1.13.2` | faiss-cpu from pip | Uninstall, use conda-forge |
| Python 3.14 + GPU request | faiss-gpu has no py314 builds | Use Python 3.11 environment or WSL2 |

### GPU Wrapper Scripts

For Python 3.14 development, use GPU wrapper scripts when GPU acceleration is needed (>100k vectors):

```powershell
# PowerShell (preferred)
P:\__csf\tools\run_gpu.ps1 script.py [args...]
P:\__csf\tools\run_gpu.ps1 -m module.name [args...]

# Windows Batch
P:\__csf\tools\run_gpu.bat script.py [args...]
```

**When to use GPU:**
- **< 10k vectors**: CPU is sufficient (GPU overhead dominates)
- **10k - 100k vectors**: Minimal benefit (~1.1-1.5x speedup)
- **> 100k vectors**: GPU provides 6-7x speedup

## Verification & Testing (2026-01-06)

- [PATTERN] **3-Tier Verification Protocol**: Tier 1 (Syntax) -> Tier 2 (Entry Point) -> Tier 3 (Integration pytest).
- [SUCCESS] **LiteLLM proxy with multiple providers**: Chutes API key + LiteLLM proxy on port 8787.
- [PATTERN] **TDD for documentation**: RED/GREEN/REFACTOR works for documentation changes too.
- [PATTERN] **Enhanced /retro lesson detection**: 4 new categories (CONFIGURATION, TRADEOFF, PERFORMANCE, EDGE_CASE) with 806+ segments detectable.
- [PATTERN] **Fragment vs complete pattern detection**: Fragment patterns require 6+ words. Complete patterns bypass word count at >= 4 words.

## Session Analysis (2026-01-06)

- [FIX] **Quality orchestrator analyzer registration** (duplicate): Explicit registration for each analyzer class after import.
- [FIX] **Parameter rename context timing**: Set context on entry with `@ast.visit`, not exit.
- [PATTERN] **CLI interface unification**: Commands should have consistent target interfaces.
- [FIX] **Path manager SRC_ROOT definition**: Wrong SRC_ROOT caused health check failures.

## Contradiction Detection (2026-01-06)

- [FIX] **Quoted vs unquoted terms**: Quote pattern only finds quoted values. Also extract key terms directly.
- [FIX] **Non-value quotes**: Filter out words like "also", "both", "either" from quotes sets.
- [FIX] **Test failure root cause**: Added `quotes_a != quotes_b` check with quoted_diff validation.

## Fix Quality Gate (2026-01-06)

- [PATTERN] **Band-aid detection patterns**: Returning empty/null, commenting out code, try/except that swallows errors silently.
- [PATTERN] **Fix quality block criteria**: Band-aid + (NO root cause OR NO verification) = BLOCK.
- [FIX] **Flexible regex for natural language**: Add `.*?` wildcards between key terms.

## Pipeline Testing (2026-01-06)

- [SUCCESS] **Smart retro hook testing**: topics_already_covered function tested with 6 realistic queries.
- [SUCCESS] **Optimized search pipeline**: All 19 tests pass. 5 optimization components verified.
- [PATTERN] **Jaccard similarity for MMR**: Token-based similarity. Similar content 0.3-0.5, different 0.1-0.2.

## Hooks & Notifications (2026-01-06)

- [FIX] **DUF dismissal logic**: Auto-dismissing on git commands is wrong. `/duf` is the reflection signal.
- [PATTERN] **Sloppiness signals**: "String to replace not found" = edited without reading. "File has been modified" = didn't re-read.
- [FIX] **Claude Code hooks configuration**: Hooks use `settings.json` ONLY, not file-based discovery.
- [PATTERN] **Hook stdin input format**: JSON via stdin with fields: `tool`, `tool_input`, `output`, `duration_ms`, `cwd`.

## Constitutional Amendments (2026-01-06)

- [RULE] **GIT/ACTION recommendation gate**: Present information BEFORE suggesting actions. Never recommend without being asked.
- [RULE] **HOOK disable protocol**: NEVER disable by renaming. Replace content with no-op while preserving filename.

## Search Optimization (2026-01-06)

- [SUCCESS] **Integrated search pipeline with 5 optimizations**: Query Expansion, Hybrid Search, RRF Fusion, MMR Diversification.
- [PATTERN] **Pipeline stages**: Pre-search (query expansion) -> Search (hybrid) -> Fusion (RRF) -> Post-processing (MMR).
- [PATTERN] **RRF fusion formula**: score = sum of 1/(k+rank), k=60 default.
- [GOTCHA] **SQLite threading limitation**: SQLite objects created in a thread can only be used in that same thread.

## Smart Retro Hook (2026-01-06)

- [FIX] **Retro hook false-positive notifications**: Added topics_already_covered() to check if topics already covered.
- [FIX] **Syntax errors from string literals**: Use regex to replace literal newlines with backslash-n escape.
- [PATTERN] **Path resolution in hooks**: Use `Path(__file__).parent.parent` to resolve relative to hook location.

## Feature Contract & Poka-Yoke (2026-01-06)

- [FIX] **Git index.lock from commit hook validation**: `rm -f .git/index.lock` before retrying.
- [PATTERN] **Two-tier poka-yoke escalation**: Self-review -> independent hostile review. Don't auto-invoke.
- [FIX] **Escalation logic missed LOOP + code issues**: `(cleared > 0 and issue_types >= 1) or issue_types >= 2`.
- [FIX] **Duplicate poka-yoke notifications**: Added check before adding. Only ONE per session.
- [FIX] **Session-scoped notification persistence**: Old notifications persisted across sessions. Manual clear needed.

## Terminal vs Session ID (2026-01-07)

- [FIX] **Notification scoping**: session_id changes per conversation, terminal_id is constant per terminal window. Use `detect_terminal_id()`.

## Command Consolidation (2026-01-07)

- [PATTERN] **LLM command namespace consolidation**: Consolidate under /llm-* prefix with multi-provider support.
- [CLEANUP] **Delete demo files after consolidation**: Keep core implementation only.
- [PATTERN] **File rename cascades**: Renaming requires updating documentation references and grep for old name.

## Quality System (2026-01-07)

- [FIX] **QualityOrchestrator auto-discover never registered**: Explicitly register each analyzer class after import.
- [PATTERN] **MD vs Python phase mismatch**: Always verify MD against Python for consistency.

## Path Management (2026-01-07)

- [FIX] **Path manager SRC_ROOT wrong definition**: Corrected to point to actual project root.
- [FIX] **Hook stderr causes UserPromptSubmit error**: ANY stderr triggers error even with exit code 0. Never write to stderr from hooks.
- [FIX] **Statusline gear icon persisted across CC restarts**: Changed to terminal_id scoping.

## Import & Module Patterns (2026-01-08)

- [PATTERN] **Module import path**: Use `src.module.name` NOT `__csf.src.module.name`.
- [PATTERN] **Optional shared module integration**: Use `try/except ImportError` with availability flag.
- [FIX] **PowerShell subprocess stderr contamination**: Use Python stat.st_mtime instead of PowerShell subprocess.
- [FIX] **Command registry path validation**: Added `validate_command_paths()` that checks existence.
- [FIX] **PowerShell numeric literal syntax**: PowerShell does NOT support underscore separators. Use plain numbers.
- [PATTERN] **Session timestamp for cross-context state sync**: Use shared timestamp file for subprocess-parent sync.
- [PATTERN] **Cross-directory import via __file__ traversal**: Walk up directory tree until finding project root markers.
- [PATTERN] **Cross-platform file locking with retry**: Non-blocking locks with retry loop and timeout.
- [GOTCHA] **pytest-in-pytest subprocess tests timeout**: Avoid subprocess pytest in tests.

## Search Crossover (2026-01-08)

- [PATTERN] **TDD subagent delegation for crossover features**: Each subagent specializes in one phase.
- [PATTERN] **Result ranking with RANKING_ALGORITHMS constant**: Tuple of valid algorithm names as single source of truth.
- [FIX] **Test metadata compatibility**: Check for field presence, not exact dictionary equality.

## Code Context Research (2026-01-08)

- [RESEARCH] **Claude Context vs CTX distinction**: Different projects from different organizations.
- [RESEARCH] **AST chunking preserves code boundaries**: tree-sitter respects function/class boundaries.
- [RESEARCH] **LSP-based symbol search**: Provides 60-90% token reduction.
- [ARCH] **Programmatic code context architecture**: 5 layers without MCP dependency.

## Code Semantic Search (2026-01-08)

- [SUCCESS] **Code semantic search with tree-sitter**: SemanticCPGBuilder using AST and tree-sitter.
- [PATTERN] **CPG node extraction pattern**: Extract entities with id, type, name, file_path, signature, docstring.
- [PATTERN] **Backend integration pattern**: 5-step pattern for UnifiedSearchRouter.
- [GOTCHA] **:memory: SQLite with thread-local connections**: Each connection creates SEPARATE database.

## Serena Integration (2026-01-08)

- [FIX] **MemorySystem auto-save delay**: Added `force=True` parameter for immediate persistence.
- [FIX] **Import path mismatch**: Must use `from src.modules.serena_wrapper`.
- [CLEANUP] **BUC deprecation and migration to DUF**: All BUC references removed.
- [FIX] **Commit emoji was duplicate of DUF**: Removed `commit` emoji mapping.

## Settings Drift & Notifications (2026-01-08)

- [FIX] **Settings drift per-terminal tracking**: Per-terminal `cc_settings_mtime_<terminal_id>.txt` files.
- [FIX] **Terminal_id mismatch Python vs PowerShell**: Updated Python to also try `GetConsoleWindow()` via ctypes.
- [FIX] **Get-Notifications filters**: Must filter by both session_id and terminal_id.
- [PATTERN] **Poka-yoke replaces entire statusline**: When warning notification exists, full message replaces normal display.

## Vector Search Optimization (2026-01-08)

- [PERF] **HNSW 1.3x faster than FAISS Flat with 90% recall**: At 10K vectors, HNSW achieves 6,317 QPS.
- [PERF] **HNSW parameter tuning**: Default M=16 gives only 64% recall at 50K. Need M=32 for 90%.
- [GOTCHA] **FAISS IVF poor recall at small scales**: Only 31.8% recall at 10K vectors.
- [FIX] **FAISS file lock contention**: Use exponential backoff with FAISSLockTimeoutError.
- [API] **hnswlib knn_query returns tuple**: Different from FAISS API.

## CHS/Qdrant Architecture (2026-01-09)

- [ARCH] **Dropped FAISS for Qdrant**: FAISS index files on Windows get locked by dead processes.
- [FIX] **CHS path inconsistency**: chs_config.py pointed to wrong database location.
- [CONFIG] **Vector store backend changed to qdrant**: Prevents FAISS lock issues.

## RCA Workflow (2026-01-09)

- [ARCH] **Swarm split rejected**: Adds complexity without evidence of improvement.
- [FEATURE] **Preflight check closes learning loop**: Check metrics for similar problems before RCA.
- [FEATURE] **Mental model selector tool-ified**: Saves LLM tokens.
- [PATTERN] **ADF evaluation workflow**: External LLM review -> ADF analysis -> Complexity Tax -> Decision.

## Subagent Architecture (2026-01-09)

- [RESEARCH] **Task tool vs Subagents**: Task tool = parallel processing, Subagents = persistent management.
- [ARCH] **Subagent split by expertise not workflow**: Right split is by problem type, NOT workflow phase.

## Regex & Pattern Catalog (2026-01-09)

- [FIX] **Regex lookbehind requires fixed-width**: Use direct pattern matching instead.
- [FIX] **YAML single-quote regex escaping**: Use (^|\s) instead of \b for word boundary in YAML.
- [FIX] **DOTALL flag breaks single-line patterns**: Use only MULTILINE for line anchors.

## CHS Real-Time Indexing (2026-01-09)

- [SUCCESS] **TDD for real-time CHS indexing**: RED->GREEN->REFACTOR cycle.
- [GOTCHA] **Windows file lock during test cleanup**: Background process holds Qdrant lock files.
- [PATTERN] **CHS real-time indexing via add_message()**: Automatically generates embedding and upserts to Qdrant.

## Notification Scoping (2026-01-09)

- [FIX] **Notification scoping**: terminal_id persists, session_id doesn't.
- [PATTERN] **Three notification scopes**: global (all terminals), terminal-scoped (same terminal), session-scoped (this conversation).

## Smart Commit & Anti-Bleed (2026-01-09)

- [CLEANUP] **CWO architecture analyzer deleted**: 476 lines of dead code removed.
- [FIX] **CC 2.1.2 PreToolUse hook JSON format**: Must return `{"permissionDecision": "deny", ...}`.
- [GOTCHA] **PreToolUse hooks not invoked for Bash execution**: Anti-bleed checks only catch direct tool commands.
- [FEATURE] **Smart-commit with directory coherence check**: Analyzes staged files, checks directory coherence.

## Code Quality (2026-01-09)

- [SUCCESS] **code-simplifier agent: 62% size reduction**: Refactored test from 298 to 112 lines.
- [PATTERN] **Authority gate hook practical testing**: Hook fires on UserPromptSubmit.

## Memory & Performance (2026-01-09)

- [PERF] **CUDA batch_size proportional to RAM usage**: batch_size=512 used ~9.7 GB. Reduced to 64 uses ~1 GB.
- [FIX] **Numpy array truth ambiguity**: Use `is not None` first, then `len() > 0`, then `isinstance()`.

## Recent (2026-01-10)

- [CONFIG] **mypy follow_imports=skip for project compatibility**: Use in `diag/mypy.ini`.
- [SUCCESS] **LiteLLM proxy with Chutes API**: Multi-provider routing on port 8787.
- [FIX] **Git index.lock cleanup**: `rm -f .git/index.lock` before retrying.
- [PATTERN] **AI-generated testing has low marginal cost**: Traditional "over-testing" concerns don't apply.
- [PATTERN] **Backend API consistency with limit parameter**: All concrete backends must implement `limit` parameter.
- [FIX] **__future__ annotations false positive**: PEP 563 directive, not a regular import.
- [PATTERN] **Project data directories in .gitignore**: `projects/*/data/` catches runtime data.
